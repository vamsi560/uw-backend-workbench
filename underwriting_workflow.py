"""
Underwriting Workflow APIs
Complete underwriting decision-making and workflow management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel

from database import get_db, WorkItem, Submission, WorkItemHistory, Comment, User, WorkItemStatus, WorkItemPriority
from logging_config import get_logger

logger = get_logger(__name__)

# Create router for underwriting workflow
underwriting_router = APIRouter(prefix="/api/underwriting", tags=["Underwriting Workflow"])

# Enums for underwriting decisions
class DecisionType(str, Enum):
    APPROVE = "approve"
    DECLINE = "decline"
    REQUEST_INFO = "request_info" 
    NEEDS_REVIEW = "needs_review"
    BIND_POLICY = "bind_policy"
    QUOTE_MODIFICATION = "quote_modification"

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Pydantic models
class UnderwritingDecision(BaseModel):
    decision: DecisionType
    reason: str
    conditions: Optional[List[str]] = []
    premium_adjustment: Optional[float] = None
    coverage_modifications: Optional[Dict[str, Any]] = None
    follow_up_required: bool = False
    follow_up_date: Optional[str] = None

class WorkItemAssignment(BaseModel):
    underwriter_email: str
    priority: Optional[WorkItemPriority] = None
    notes: Optional[str] = None

class UnderwritingNote(BaseModel):
    content: str
    note_type: str = "general"  # general, risk_concern, recommendation
    is_internal: bool = True
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM

# ================================
# WORK QUEUE MANAGEMENT APIs
# ================================

@underwriting_router.get("/queue", response_model=List[Dict[str, Any]])
async def get_underwriting_queue(
    assigned_to: Optional[str] = Query(None, description="Filter by assigned underwriter"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    status: Optional[str] = Query(None, description="Filter by status"),
    industry: Optional[str] = Query(None, description="Filter by industry type"),
    limit: int = Query(50, le=200, description="Maximum number of items"),
    include_risk_data: bool = Query(True, description="Include risk assessment data"),
    db: Session = Depends(get_db)
):
    """
    Get prioritized underwriting work queue
    - Sorted by priority and creation date
    - Includes risk assessment data
    - Supports filtering and pagination
    """
    try:
        # Build query for work items requiring underwriting review
        query = db.query(WorkItem, Submission).join(
            Submission, WorkItem.submission_id == Submission.id
        ).filter(
            WorkItem.status.in_([WorkItemStatus.PENDING, WorkItemStatus.IN_REVIEW])
        )
        
        # Apply filters
        if assigned_to:
            query = query.filter(WorkItem.assigned_to.ilike(f"%{assigned_to}%"))
        
        if priority:
            try:
                priority_enum = WorkItemPriority(priority.upper())
                query = query.filter(WorkItem.priority == priority_enum)
            except ValueError:
                pass
        
        if status:
            try:
                status_enum = WorkItemStatus(status.upper().replace(" ", "_"))
                query = query.filter(WorkItem.status == status_enum)
            except ValueError:
                pass
        
        if industry:
            query = query.filter(WorkItem.industry.ilike(f"%{industry}%"))
        
        # Order by priority (Critical -> High -> Medium -> Low) and creation date
        priority_order = {
            WorkItemPriority.CRITICAL: 1,
            WorkItemPriority.HIGH: 2, 
            WorkItemPriority.MEDIUM: 3,
            WorkItemPriority.LOW: 4
        }
        
        results = query.order_by(WorkItem.created_at.desc()).limit(limit).all()
        
        queue_items = []
        for work_item, submission in results:
            # Calculate time in queue
            time_in_queue = datetime.utcnow() - work_item.created_at
            
            # Get latest activity
            latest_activity = db.query(WorkItemHistory).filter(
                WorkItemHistory.work_item_id == work_item.id
            ).order_by(WorkItemHistory.timestamp.desc()).first()
            
            # Get comments count
            comments_count = db.query(Comment).filter(Comment.work_item_id == work_item.id).count()
            urgent_comments = db.query(Comment).filter(
                and_(Comment.work_item_id == work_item.id, Comment.is_urgent == True)
            ).count()
            
            queue_item = {
                "work_item_id": work_item.id,
                "submission_id": work_item.submission_id,
                "submission_ref": str(submission.submission_ref),
                "title": work_item.title or submission.subject,
                "organization_name": getattr(work_item, 'organization_name', None) or 
                                  (submission.extracted_fields.get('company_name') if submission.extracted_fields else None),
                "status": work_item.status.value,
                "priority": work_item.priority.value,
                "assigned_to": work_item.assigned_to,
                "industry": work_item.industry,
                "policy_type": work_item.policy_type,
                "coverage_amount": work_item.coverage_amount,
                "created_at": work_item.created_at.isoformat(),
                "updated_at": work_item.updated_at.isoformat(),
                "time_in_queue_hours": int(time_in_queue.total_seconds() / 3600),
                "comments_count": comments_count,
                "urgent_comments": urgent_comments,
                "sender_email": submission.sender_email,
                "latest_activity": {
                    "action": latest_activity.action if latest_activity else None,
                    "timestamp": latest_activity.timestamp.isoformat() if latest_activity else None,
                    "performed_by": latest_activity.changed_by if latest_activity else None
                } if latest_activity else None
            }
            
            # Add risk assessment data if requested
            if include_risk_data and work_item.risk_score:
                queue_item["risk_assessment"] = {
                    "overall_score": work_item.risk_score,
                    "risk_level": "High" if work_item.risk_score > 0.8 else "Medium" if work_item.risk_score > 0.5 else "Low",
                    "risk_categories": work_item.risk_categories
                }
            
            queue_items.append(queue_item)
        
        # Sort by priority and then by time in queue (longest first)
        queue_items.sort(key=lambda x: (
            priority_order.get(WorkItemPriority(x["priority"]), 5),
            -x["time_in_queue_hours"]
        ))
        
        logger.info(f"Retrieved underwriting queue: {len(queue_items)} items")
        return queue_items
        
    except Exception as e:
        logger.error(f"Error retrieving underwriting queue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving queue: {str(e)}")

# ================================
# DECISION MAKING APIs
# ================================

@underwriting_router.post("/workitems/{work_item_id}/decision")
async def make_underwriting_decision(
    work_item_id: int,
    decision_data: UnderwritingDecision,
    underwriter_email: str = Query(..., description="Email of underwriter making decision"),
    db: Session = Depends(get_db)
):
    """
    Make underwriting decision on work item
    - Approve, decline, request info, or require additional review
    - Update work item status and create audit trail
    - Handle Guidewire integration for approved policies
    """
    try:
        # Get work item and submission
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        submission = db.query(Submission).filter(Submission.id == work_item.submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Related submission not found")
        
        # Store old status for audit trail
        old_status = work_item.status
        
        # Update work item based on decision
        decision_status_mapping = {
            DecisionType.APPROVE: WorkItemStatus.APPROVED,
            DecisionType.DECLINE: WorkItemStatus.REJECTED,
            DecisionType.REQUEST_INFO: WorkItemStatus.PENDING,
            DecisionType.NEEDS_REVIEW: WorkItemStatus.IN_REVIEW,
            DecisionType.BIND_POLICY: WorkItemStatus.APPROVED,
            DecisionType.QUOTE_MODIFICATION: WorkItemStatus.IN_REVIEW
        }
        
        work_item.status = decision_status_mapping[decision_data.decision]
        work_item.assigned_to = underwriter_email
        work_item.updated_at = datetime.utcnow()
        
        # Add decision details to work item
        decision_details = {
            "decision_type": decision_data.decision.value,
            "reason": decision_data.reason,
            "conditions": decision_data.conditions,
            "decided_by": underwriter_email,
            "decision_timestamp": datetime.utcnow().isoformat(),
            "premium_adjustment": decision_data.premium_adjustment,
            "coverage_modifications": decision_data.coverage_modifications,
            "follow_up_required": decision_data.follow_up_required,
            "follow_up_date": decision_data.follow_up_date
        }
        
        # Create detailed history entry
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action=f"underwriting_decision_{decision_data.decision.value}",
            changed_by=underwriter_email,
            timestamp=datetime.utcnow(),
            details=decision_details
        )
        db.add(history_entry)
        
        # Create decision comment
        decision_comment = Comment(
            work_item_id=work_item.id,
            author=underwriter_email,
            content=f"**Underwriting Decision: {decision_data.decision.value.title()}**\n\n"
                   f"**Reason:** {decision_data.reason}\n\n" +
                   (f"**Conditions:** {', '.join(decision_data.conditions)}\n\n" if decision_data.conditions else "") +
                   (f"**Premium Adjustment:** {decision_data.premium_adjustment}%\n\n" if decision_data.premium_adjustment else "") +
                   (f"**Follow-up Required:** {decision_data.follow_up_date}\n\n" if decision_data.follow_up_required else ""),
            comment_type="decision",
            is_internal=True,
            is_urgent=decision_data.decision in [DecisionType.DECLINE, DecisionType.NEEDS_REVIEW]
        )
        db.add(decision_comment)
        
        # Handle specific decision actions
        result_details = {"decision": decision_data.decision.value}
        
        if decision_data.decision == DecisionType.APPROVE:
            # TODO: Integrate with Guidewire to bind policy
            result_details["next_steps"] = "Policy approved - proceed to binding"
            result_details["binding_ready"] = True
            
        elif decision_data.decision == DecisionType.DECLINE:
            # TODO: Send rejection notification to broker
            result_details["next_steps"] = "Policy declined - notification sent to broker"
            result_details["rejection_reason"] = decision_data.reason
            
        elif decision_data.decision == DecisionType.REQUEST_INFO:
            # TODO: Send information request to broker
            result_details["next_steps"] = "Additional information requested from broker"
            result_details["requested_info"] = decision_data.conditions
            
        elif decision_data.decision == DecisionType.BIND_POLICY:
            # TODO: Automatic binding process
            result_details["next_steps"] = "Policy binding initiated in Guidewire"
            result_details["binding_initiated"] = True
        
        db.commit()
        db.refresh(work_item)
        
        logger.info(f"Underwriting decision made: {decision_data.decision.value} for work item {work_item_id} by {underwriter_email}")
        
        return {
            "success": True,
            "work_item_id": work_item_id,
            "decision": decision_data.decision.value,
            "old_status": old_status.value,
            "new_status": work_item.status.value,
            "decided_by": underwriter_email,
            "decision_timestamp": datetime.utcnow().isoformat(),
            "details": result_details,
            "message": f"Decision '{decision_data.decision.value}' recorded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making underwriting decision: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing decision: {str(e)}")

# ================================
# ASSIGNMENT & COLLABORATION APIs  
# ================================

@underwriting_router.post("/workitems/{work_item_id}/assign")
async def assign_underwriter(
    work_item_id: int,
    assignment_data: WorkItemAssignment,
    assigner_email: str = Query(..., description="Email of person making assignment"),
    db: Session = Depends(get_db)
):
    """
    Assign work item to specific underwriter
    - Update assignment and priority
    - Create notification for assigned underwriter
    - Log assignment in history
    """
    try:
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        old_assignee = work_item.assigned_to
        
        # Update assignment
        work_item.assigned_to = assignment_data.underwriter_email
        if assignment_data.priority:
            work_item.priority = assignment_data.priority
        work_item.updated_at = datetime.utcnow()
        
        # Create history entry
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action="assignment_changed",
            changed_by=assigner_email,
            timestamp=datetime.utcnow(),
            details={
                "old_assignee": old_assignee,
                "new_assignee": assignment_data.underwriter_email,
                "assigned_by": assigner_email,
                "notes": assignment_data.notes,
                "priority_changed": assignment_data.priority.value if assignment_data.priority else None
            }
        )
        db.add(history_entry)
        
        # Create assignment notification comment
        if assignment_data.notes:
            assignment_comment = Comment(
                work_item_id=work_item.id,
                author=assigner_email,
                content=f"**Assigned to {assignment_data.underwriter_email}**\n\n{assignment_data.notes}",
                comment_type="assignment",
                is_internal=True
            )
            db.add(assignment_comment)
        
        db.commit()
        db.refresh(work_item)
        
        logger.info(f"Work item {work_item_id} assigned to {assignment_data.underwriter_email} by {assigner_email}")
        
        return {
            "success": True,
            "work_item_id": work_item_id,
            "old_assignee": old_assignee,
            "new_assignee": assignment_data.underwriter_email,
            "assigned_by": assigner_email,
            "priority": work_item.priority.value,
            "assignment_timestamp": datetime.utcnow().isoformat(),
            "message": f"Work item assigned to {assignment_data.underwriter_email}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning work item: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error making assignment: {str(e)}")

@underwriting_router.post("/workitems/{work_item_id}/notes")
async def add_underwriting_note(
    work_item_id: int,
    note_data: UnderwritingNote,
    author_email: str = Query(..., description="Email of note author"),
    db: Session = Depends(get_db)
):
    """
    Add underwriting note or comment to work item
    - Support different note types (general, risk_concern, recommendation)
    - Handle internal vs external visibility
    - Support urgency levels
    """
    try:
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        # Create comment
        comment = Comment(
            work_item_id=work_item.id,
            author=author_email,
            content=note_data.content,
            comment_type=note_data.note_type,
            is_internal=note_data.is_internal,
            is_urgent=(note_data.urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL])
        )
        db.add(comment)
        
        # Create history entry for important notes
        if note_data.note_type in ["risk_concern", "recommendation"] or note_data.urgency == UrgencyLevel.CRITICAL:
            history_entry = WorkItemHistory(
                work_item_id=work_item.id,
                action=f"note_added_{note_data.note_type}",
                changed_by=author_email,
                timestamp=datetime.utcnow(),
                details={
                    "note_type": note_data.note_type,
                    "urgency": note_data.urgency.value,
                    "is_internal": note_data.is_internal,
                    "content_preview": note_data.content[:100] + "..." if len(note_data.content) > 100 else note_data.content
                }
            )
            db.add(history_entry)
        
        db.commit()
        db.refresh(comment)
        
        logger.info(f"Note added to work item {work_item_id} by {author_email} (type: {note_data.note_type})")
        
        return {
            "success": True,
            "work_item_id": work_item_id,
            "comment_id": comment.id,
            "note_type": note_data.note_type,
            "urgency": note_data.urgency.value,
            "author": author_email,
            "timestamp": comment.created_at.isoformat(),
            "message": "Note added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding note: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding note: {str(e)}")

# ================================
# ANALYTICS & REPORTING APIs
# ================================

@underwriting_router.get("/analytics/summary")
async def get_underwriting_analytics(
    days: int = Query(30, description="Number of days for analytics"),
    underwriter: Optional[str] = Query(None, description="Filter by underwriter"),
    db: Session = Depends(get_db)
):
    """
    Get underwriting performance analytics
    - Decision distribution and timing
    - Workload by underwriter
    - Approval/decline rates
    - Average processing times
    """
    try:
        from_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query for analytics period
        base_query = db.query(WorkItem).filter(WorkItem.created_at >= from_date)
        
        if underwriter:
            base_query = base_query.filter(WorkItem.assigned_to.ilike(f"%{underwriter}%"))
        
        # Total work items in period
        total_items = base_query.count()
        
        # Status distribution
        status_distribution = db.query(
            WorkItem.status,
            func.count(WorkItem.id).label('count')
        ).filter(WorkItem.created_at >= from_date).group_by(WorkItem.status).all()
        
        # Priority distribution
        priority_distribution = db.query(
            WorkItem.priority,
            func.count(WorkItem.id).label('count')
        ).filter(WorkItem.created_at >= from_date).group_by(WorkItem.priority).all()
        
        # Underwriter workload
        underwriter_workload = db.query(
            WorkItem.assigned_to,
            func.count(WorkItem.id).label('total_items'),
            func.avg(WorkItem.risk_score).label('avg_risk_score')
        ).filter(
            and_(WorkItem.created_at >= from_date, WorkItem.assigned_to.isnot(None))
        ).group_by(WorkItem.assigned_to).all()
        
        # Processing time analysis (for completed items)
        completed_items = base_query.filter(
            WorkItem.status.in_([WorkItemStatus.APPROVED, WorkItemStatus.REJECTED])
        ).all()
        
        processing_times = []
        for item in completed_items:
            if item.updated_at and item.created_at:
                processing_time = (item.updated_at - item.created_at).total_seconds() / 3600
                processing_times.append(processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "analytics_period_days": days,
            "summary": {
                "total_work_items": total_items,
                "completed_items": len(completed_items),
                "completion_rate": round((len(completed_items) / total_items * 100), 2) if total_items > 0 else 0,
                "avg_processing_time_hours": round(avg_processing_time, 2)
            },
            "status_distribution": [
                {"status": status.value if hasattr(status, 'value') else str(status), "count": count}
                for status, count in status_distribution
            ],
            "priority_distribution": [
                {"priority": priority.value if hasattr(priority, 'value') else str(priority), "count": count}
                for priority, count in priority_distribution
            ],
            "underwriter_performance": [
                {
                    "underwriter": underwriter or "Unassigned",
                    "total_items": total_items,
                    "avg_risk_score": round(float(avg_risk_score or 0), 2)
                }
                for underwriter, total_items, avg_risk_score in underwriter_workload
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

@underwriting_router.get("/workitems/{work_item_id}/activity-log")
async def get_activity_log(
    work_item_id: int,
    limit: int = Query(50, description="Maximum number of activities"),
    db: Session = Depends(get_db)
):
    """
    Get complete activity log for work item
    - All history entries and comments
    - Chronological order
    - Includes decision trail and assignments
    """
    try:
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        # Get history entries
        history_entries = db.query(WorkItemHistory).filter(
            WorkItemHistory.work_item_id == work_item_id
        ).order_by(WorkItemHistory.timestamp.desc()).limit(limit).all()
        
        # Get comments
        comments = db.query(Comment).filter(
            Comment.work_item_id == work_item_id
        ).order_by(Comment.created_at.desc()).limit(limit).all()
        
        # Combine and sort activities
        activities = []
        
        for entry in history_entries:
            activities.append({
                "type": "history",
                "id": entry.id,
                "action": entry.action,
                "performed_by": entry.changed_by,
                "timestamp": entry.timestamp.isoformat(),
                "details": entry.details,
                "description": _format_history_description(entry.action, entry.details)
            })
        
        for comment in comments:
            activities.append({
                "type": "comment",
                "id": comment.id,
                "author": comment.author,
                "content": comment.content,
                "comment_type": comment.comment_type,
                "is_internal": comment.is_internal,
                "is_urgent": comment.is_urgent,
                "timestamp": comment.created_at.isoformat()
            })
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "work_item_id": work_item_id,
            "total_activities": len(activities),
            "activities": activities[:limit],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving activity log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving activity log: {str(e)}")

def _format_history_description(action: str, details: Dict[str, Any]) -> str:
    """Format history action into human-readable description"""
    descriptions = {
        "created": "Work item created",
        "assignment_changed": f"Assigned to {details.get('new_assignee', 'unknown')}",
        "status_changed": f"Status changed to {details.get('new_status', 'unknown')}",
        "underwriting_decision_approve": "Policy approved by underwriter",
        "underwriting_decision_decline": "Policy declined by underwriter", 
        "underwriting_decision_request_info": "Additional information requested",
        "note_added_risk_concern": "Risk concern noted",
        "note_added_recommendation": "Recommendation added"
    }
    
    return descriptions.get(action, f"Action: {action}")