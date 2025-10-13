"""
User Management and Notification System
Handles user roles, permissions, assignments, and notifications
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from database import get_db, User, Underwriter, WorkItem, WorkItemHistory, SubmissionMessage
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)

# Create router
user_router = APIRouter(prefix="/api/users", tags=["User Management"])
notification_router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    UNDERWRITER = "underwriter"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"

class NotificationType(str, Enum):
    ASSIGNMENT = "assignment"
    STATUS_CHANGE = "status_change"
    HIGH_RISK_ALERT = "high_risk_alert"
    DEADLINE_REMINDER = "deadline_reminder"
    SYSTEM_ALERT = "system_alert"

# Pydantic models
class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    department: Optional[str] = None
    manager_email: Optional[EmailStr] = None
    specializations: Optional[List[str]] = []
    max_coverage_limit: Optional[int] = None
    is_active: bool = True

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    specializations: Optional[List[str]] = None
    max_coverage_limit: Optional[int] = None
    is_active: Optional[bool] = None

class NotificationRequest(BaseModel):
    recipient_email: EmailStr
    notification_type: NotificationType
    subject: str
    message: str
    work_item_id: Optional[int] = None
    priority: str = Field(default="medium", regex="^(low|medium|high|critical)$")
    send_email: bool = Field(default=True, description="Whether to send email notification")

class BulkAssignmentRequest(BaseModel):
    work_item_ids: List[int]
    underwriter_email: EmailStr
    assigned_by: str
    notes: Optional[str] = None

class WorkloadBalancingRequest(BaseModel):
    target_underwriter_count: int = Field(default=3, ge=1, le=10)
    max_items_per_underwriter: int = Field(default=20, ge=1, le=100)
    balance_by_coverage_amount: bool = Field(default=True)
    assigned_by: str

# In-memory notification store (in production, use database or message queue)
class NotificationStore:
    def __init__(self):
        self.notifications = {}
        self.user_preferences = {}
    
    def add_notification(self, notification_id: str, notification_data: Dict[str, Any]):
        """Add notification to store"""
        self.notifications[notification_id] = {
            **notification_data,
            'created_at': datetime.utcnow().isoformat(),
            'is_read': False
        }
    
    def get_user_notifications(self, user_email: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        user_notifications = []
        
        for notif_id, notif_data in self.notifications.items():
            if notif_data.get('recipient_email') == user_email:
                if not unread_only or not notif_data.get('is_read', False):
                    user_notifications.append({
                        'notification_id': notif_id,
                        **notif_data
                    })
        
        # Sort by creation date (newest first)
        user_notifications.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return user_notifications
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        if notification_id in self.notifications:
            self.notifications[notification_id]['is_read'] = True
            return True
        return False

# Global notification store
notification_store = NotificationStore()

@user_router.post("/create")
async def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new user account
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create new user
        user = User(
            name=request.name,
            email=request.email,
            role=request.role.value,
            department=request.department,
            is_active=request.is_active,
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        db.flush()  # Get user ID
        
        # If user is an underwriter, create underwriter record
        if request.role == UserRole.UNDERWRITER:
            underwriter = Underwriter(
                name=request.name,
                email=request.email,
                specializations=request.specializations or [],
                max_coverage_limit=request.max_coverage_limit or 1000000,
                is_active=request.is_active,
                current_workload=0
            )
            db.add(underwriter)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created: {request.name} ({request.email}) with role {request.role}")
        
        return {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "message": "User created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )

@user_router.get("/list")
async def list_users(
    role: Optional[UserRole] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    List users with optional filtering
    """
    try:
        query = db.query(User)
        
        if role:
            query = query.filter(User.role == role.value)
        
        if active_only:
            query = query.filter(User.is_active == True)
        
        users = query.order_by(User.name).all()
        
        return {
            "users": [
                {
                    "user_id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "department": user.department,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                }
                for user in users
            ],
            "count": len(users),
            "filters": {
                "role": role.value if role else None,
                "active_only": active_only
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing users: {str(e)}"
        )

@user_router.put("/{user_id}")
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update user information
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user fields
        if request.name is not None:
            user.name = request.name
        if request.role is not None:
            user.role = request.role.value
        if request.department is not None:
            user.department = request.department
        if request.is_active is not None:
            user.is_active = request.is_active
        
        # Update underwriter record if exists
        if user.role == "underwriter":
            underwriter = db.query(Underwriter).filter(Underwriter.email == user.email).first()
            if underwriter:
                if request.name is not None:
                    underwriter.name = request.name
                if request.specializations is not None:
                    underwriter.specializations = request.specializations
                if request.max_coverage_limit is not None:
                    underwriter.max_coverage_limit = request.max_coverage_limit
                if request.is_active is not None:
                    underwriter.is_active = request.is_active
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {user.name} ({user.email})")
        
        return {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "is_active": user.is_active,
            "message": "User updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating user: {str(e)}"
        )

@user_router.get("/underwriters/workload")
async def get_underwriter_workloads(db: Session = Depends(get_db)):
    """
    Get current workload for all underwriters
    """
    try:
        from sqlalchemy import func
        
        # Get underwriter workloads from active work items
        workload_query = db.query(
            WorkItem.assigned_to.label('underwriter_email'),
            func.count(WorkItem.id).label('active_items')
        ).filter(
            WorkItem.assigned_to.isnot(None),
            WorkItem.status.in_(['pending', 'in_review'])
        ).group_by(WorkItem.assigned_to).all()
        
        # Get all underwriters
        underwriters = db.query(Underwriter).filter(Underwriter.is_active == True).all()
        
        workload_map = {uw.underwriter_email: uw.active_items for uw in workload_query}
        
        underwriter_workloads = []
        for underwriter in underwriters:
            current_workload = workload_map.get(underwriter.email, 0)
            
            underwriter_workloads.append({
                "underwriter_name": underwriter.name,
                "underwriter_email": underwriter.email,
                "current_workload": current_workload,
                "max_coverage_limit": underwriter.max_coverage_limit,
                "specializations": underwriter.specializations or [],
                "workload_percentage": round((current_workload / 20) * 100, 1) if current_workload else 0,
                "availability": "available" if current_workload < 15 else "busy" if current_workload < 20 else "overloaded"
            })
        
        # Sort by workload (least busy first)
        underwriter_workloads.sort(key=lambda x: x['current_workload'])
        
        return {
            "underwriters": underwriter_workloads,
            "summary": {
                "total_underwriters": len(underwriter_workloads),
                "available_underwriters": len([uw for uw in underwriter_workloads if uw['availability'] == 'available']),
                "total_active_items": sum(uw['current_workload'] for uw in underwriter_workloads)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting underwriter workloads: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting underwriter workloads: {str(e)}"
        )

@user_router.post("/assign/bulk")
async def bulk_assign_work_items(
    request: BulkAssignmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Assign multiple work items to an underwriter
    """
    try:
        # Validate underwriter exists
        underwriter = db.query(Underwriter).filter(
            Underwriter.email == request.underwriter_email,
            Underwriter.is_active == True
        ).first()
        
        if not underwriter:
            raise HTTPException(status_code=404, detail="Active underwriter not found")
        
        # Get work items
        work_items = db.query(WorkItem).filter(WorkItem.id.in_(request.work_item_ids)).all()
        
        if not work_items:
            raise HTTPException(status_code=404, detail="No work items found")
        
        assigned_items = []
        errors = []
        
        for work_item in work_items:
            try:
                # Check if item is already assigned
                if work_item.assigned_to and work_item.assigned_to != request.underwriter_email:
                    errors.append(f"Work item {work_item.id} is already assigned to {work_item.assigned_to}")
                    continue
                
                # Assign work item
                work_item.assigned_to = request.underwriter_email
                work_item.updated_at = datetime.utcnow()
                
                # Create history entry
                history_entry = WorkItemHistory(
                    work_item_id=work_item.id,
                    action="bulk_assigned",
                    changed_by=request.assigned_by,
                    timestamp=datetime.utcnow(),
                    details={
                        "assigned_to": request.underwriter_email,
                        "notes": request.notes,
                        "assignment_type": "bulk"
                    }
                )
                db.add(history_entry)
                
                assigned_items.append(work_item.id)
                
            except Exception as e:
                errors.append(f"Work item {work_item.id}: {str(e)}")
        
        db.commit()
        
        # Send notification
        if assigned_items:
            background_tasks.add_task(
                send_bulk_assignment_notification,
                request.underwriter_email,
                len(assigned_items),
                request.assigned_by
            )
        
        logger.info(f"Bulk assignment completed: {len(assigned_items)} items assigned to {request.underwriter_email}")
        
        return {
            "assigned_items": assigned_items,
            "assigned_count": len(assigned_items),
            "errors": errors,
            "underwriter_email": request.underwriter_email,
            "assigned_by": request.assigned_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk assignment: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error in bulk assignment: {str(e)}"
        )

@user_router.post("/workload/balance")
async def balance_workload(
    request: WorkloadBalancingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Automatically balance workload across underwriters
    """
    try:
        from sqlalchemy import func
        
        # Get unassigned work items
        unassigned_items = db.query(WorkItem).filter(
            WorkItem.assigned_to.is_(None),
            WorkItem.status.in_(['pending', 'in_review'])
        ).order_by(WorkItem.created_at).all()
        
        if not unassigned_items:
            return {
                "message": "No unassigned work items to balance",
                "assignments": [],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get active underwriters and their current workloads
        underwriters = db.query(Underwriter).filter(Underwriter.is_active == True).all()
        
        if not underwriters:
            raise HTTPException(status_code=404, detail="No active underwriters found")
        
        # Calculate current workloads
        current_workloads = {}
        for underwriter in underwriters:
            workload = db.query(func.count(WorkItem.id)).filter(
                WorkItem.assigned_to == underwriter.email,
                WorkItem.status.in_(['pending', 'in_review'])
            ).scalar() or 0
            current_workloads[underwriter.email] = workload
        
        # Sort underwriters by current workload (least busy first)
        sorted_underwriters = sorted(underwriters, key=lambda uw: current_workloads[uw.email])
        
        assignments = []
        underwriter_index = 0
        
        for work_item in unassigned_items:
            # Find the least busy underwriter who can handle this item
            assigned = False
            attempts = 0
            
            while not assigned and attempts < len(sorted_underwriters):
                current_uw = sorted_underwriters[underwriter_index]
                current_load = current_workloads[current_uw.email]
                
                # Check if underwriter can take more items
                if current_load < request.max_items_per_underwriter:
                    # Check coverage limit if balancing by coverage amount
                    can_assign = True
                    if request.balance_by_coverage_amount and work_item.coverage_amount:
                        if work_item.coverage_amount > current_uw.max_coverage_limit:
                            can_assign = False
                    
                    if can_assign:
                        # Assign work item
                        work_item.assigned_to = current_uw.email
                        work_item.updated_at = datetime.utcnow()
                        
                        # Create history entry
                        history_entry = WorkItemHistory(
                            work_item_id=work_item.id,
                            action="auto_assigned",
                            changed_by=request.assigned_by,
                            timestamp=datetime.utcnow(),
                            details={
                                "assigned_to": current_uw.email,
                                "assignment_type": "workload_balancing",
                                "previous_workload": current_load
                            }
                        )
                        db.add(history_entry)
                        
                        assignments.append({
                            "work_item_id": work_item.id,
                            "assigned_to": current_uw.email,
                            "previous_workload": current_load
                        })
                        
                        current_workloads[current_uw.email] += 1
                        assigned = True
                
                underwriter_index = (underwriter_index + 1) % len(sorted_underwriters)
                attempts += 1
            
            if not assigned:
                logger.warning(f"Could not assign work item {work_item.id} - all underwriters at capacity")
        
        db.commit()
        
        # Send notifications
        assignment_counts = {}
        for assignment in assignments:
            email = assignment['assigned_to']
            assignment_counts[email] = assignment_counts.get(email, 0) + 1
        
        for underwriter_email, count in assignment_counts.items():
            background_tasks.add_task(
                send_workload_balance_notification,
                underwriter_email,
                count,
                request.assigned_by
            )
        
        logger.info(f"Workload balancing completed: {len(assignments)} items assigned")
        
        return {
            "assignments": assignments,
            "assigned_count": len(assignments),
            "unassigned_remaining": len(unassigned_items) - len(assignments),
            "assignment_summary": assignment_counts,
            "assigned_by": request.assigned_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error balancing workload: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error balancing workload: {str(e)}"
        )

# Notification endpoints
@notification_router.post("/send")
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send a notification to a user
    """
    try:
        # Generate notification ID
        notification_id = str(uuid.uuid4())
        
        # Store notification
        notification_data = {
            "notification_id": notification_id,
            "recipient_email": request.recipient_email,
            "notification_type": request.notification_type.value,
            "subject": request.subject,
            "message": request.message,
            "work_item_id": request.work_item_id,
            "priority": request.priority
        }
        
        notification_store.add_notification(notification_id, notification_data)
        
        # Create database record if work item is specified
        if request.work_item_id:
            submission = db.query(WorkItem).filter(WorkItem.id == request.work_item_id).first()
            if submission:
                message_record = SubmissionMessage(
                    submission_id=submission.submission_id,
                    message_type=request.notification_type.value,
                    sender="system",
                    recipient=request.recipient_email,
                    subject=request.subject,
                    message=request.message,
                    is_read=False
                )
                db.add(message_record)
                db.commit()
        
        # Send email notification if requested
        if request.send_email:
            background_tasks.add_task(
                send_email_notification,
                request.recipient_email,
                request.subject,
                request.message,
                request.priority
            )
        
        logger.info(f"Notification sent to {request.recipient_email}: {request.notification_type}")
        
        return {
            "notification_id": notification_id,
            "recipient_email": request.recipient_email,
            "notification_type": request.notification_type,
            "status": "sent",
            "email_sent": request.send_email,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending notification: {str(e)}"
        )

@notification_router.get("/user/{user_email}")
async def get_user_notifications(
    user_email: str,
    unread_only: bool = False,
    limit: int = 50
):
    """
    Get notifications for a specific user
    """
    try:
        notifications = notification_store.get_user_notifications(user_email, unread_only)
        
        # Limit results
        notifications = notifications[:limit]
        
        return {
            "user_email": user_email,
            "notifications": notifications,
            "count": len(notifications),
            "unread_only": unread_only,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting user notifications: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting user notifications: {str(e)}"
        )

@notification_router.put("/{notification_id}/read")
async def mark_notification_as_read(notification_id: str):
    """
    Mark a notification as read
    """
    try:
        success = notification_store.mark_as_read(notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {
            "notification_id": notification_id,
            "status": "marked_as_read",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error marking notification as read: {str(e)}"
        )

# Background tasks for notifications
async def send_bulk_assignment_notification(underwriter_email: str, item_count: int, assigned_by: str):
    """Send notification for bulk assignment"""
    try:
        subject = f"Bulk Assignment: {item_count} New Work Items"
        message = f"You have been assigned {item_count} new work items by {assigned_by}. Please review them in your dashboard."
        
        notification_data = {
            "recipient_email": underwriter_email,
            "notification_type": NotificationType.ASSIGNMENT.value,
            "subject": subject,
            "message": message,
            "priority": "medium"
        }
        
        notification_id = str(uuid.uuid4())
        notification_store.add_notification(notification_id, notification_data)
        
        # Also send email
        await send_email_notification(underwriter_email, subject, message, "medium")
        
    except Exception as e:
        logger.error(f"Error sending bulk assignment notification: {str(e)}")

async def send_workload_balance_notification(underwriter_email: str, item_count: int, assigned_by: str):
    """Send notification for workload balancing"""
    try:
        subject = f"Workload Balancing: {item_count} New Assignments"
        message = f"As part of workload balancing by {assigned_by}, you have been assigned {item_count} additional work items."
        
        notification_data = {
            "recipient_email": underwriter_email,
            "notification_type": NotificationType.ASSIGNMENT.value,
            "subject": subject,
            "message": message,
            "priority": "low"
        }
        
        notification_id = str(uuid.uuid4())
        notification_store.add_notification(notification_id, notification_data)
        
        # Also send email
        await send_email_notification(underwriter_email, subject, message, "low")
        
    except Exception as e:
        logger.error(f"Error sending workload balance notification: {str(e)}")

async def send_email_notification(recipient_email: str, subject: str, message: str, priority: str = "medium"):
    """Send email notification (placeholder implementation)"""
    try:
        # In production, this would use actual SMTP configuration
        logger.info(f"EMAIL NOTIFICATION - To: {recipient_email}, Subject: {subject}, Priority: {priority}")
        logger.info(f"EMAIL CONTENT: {message}")
        
        # Placeholder for actual email sending
        # smtp_config = get_smtp_config()
        # send_actual_email(smtp_config, recipient_email, subject, message)
        
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")

# Export routers
__all__ = ["user_router", "notification_router"]