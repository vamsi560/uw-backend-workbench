"""
Guidewire Synchronization Service
Handles syncing policy status changes from Guidewire back to portal
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from pydantic import BaseModel

from database import get_db, WorkItem, Submission, WorkItemHistory, GuidewireResponse
from guidewire_client import guidewire_client

logger = logging.getLogger(__name__)

# Create router
sync_router = APIRouter(prefix="/api/guidewire-sync", tags=["Guidewire Sync"])

class PolicyStatusUpdate(BaseModel):
    job_id: str
    new_status: str
    policy_number: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    premium_amount: Optional[float] = None
    updated_by: str = "Guidewire System"

class SyncRequest(BaseModel):
    work_item_ids: Optional[List[int]] = None
    job_ids: Optional[List[str]] = None
    sync_all_pending: bool = False

@sync_router.post("/manual-sync")
async def manual_sync_from_guidewire(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger sync from Guidewire to update policy statuses
    """
    try:
        sync_count = 0
        
        if request.sync_all_pending:
            # Sync all submissions that are in Quoted status
            guidewire_responses = db.query(GuidewireResponse).filter(
                GuidewireResponse.job_status.in_(["Draft", "Quoted"])
            ).all()
            
            for response in guidewire_responses:
                background_tasks.add_task(
                    sync_single_submission,
                    response.guidewire_job_id,
                    response.work_item_id
                )
                sync_count += 1
        
        elif request.work_item_ids:
            # Sync specific work items
            for work_item_id in request.work_item_ids:
                guidewire_response = db.query(GuidewireResponse).filter(
                    GuidewireResponse.work_item_id == work_item_id
                ).first()
                
                if guidewire_response:
                    background_tasks.add_task(
                        sync_single_submission,
                        guidewire_response.guidewire_job_id,
                        work_item_id
                    )
                    sync_count += 1
        
        elif request.job_ids:
            # Sync specific Guidewire jobs
            for job_id in request.job_ids:
                guidewire_response = db.query(GuidewireResponse).filter(
                    GuidewireResponse.guidewire_job_id == job_id
                ).first()
                
                if guidewire_response:
                    background_tasks.add_task(
                        sync_single_submission,
                        job_id,
                        guidewire_response.work_item_id
                    )
                    sync_count += 1
        
        return {
            "sync_initiated": True,
            "submissions_queued": sync_count,
            "message": f"Sync initiated for {sync_count} submissions",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error initiating Guidewire sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error initiating sync: {str(e)}"
        )

@sync_router.get("/status/{work_item_id}")
async def get_guidewire_status(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current Guidewire status for a work item and check for updates
    """
    try:
        # Get existing Guidewire data
        guidewire_response = db.query(GuidewireResponse).filter(
            GuidewireResponse.work_item_id == work_item_id
        ).first()
        
        if not guidewire_response:
            raise HTTPException(
                status_code=404,
                detail="No Guidewire submission found for this work item"
            )
        
        # Get current status from Guidewire
        current_status = await get_job_status_from_guidewire(
            guidewire_response.guidewire_job_id
        )
        
        # Check if status has changed
        status_changed = current_status['status'] != guidewire_response.job_status
        
        # Update database if status changed
        if status_changed:
            await update_work_item_from_guidewire_status(
                work_item_id,
                current_status,
                db
            )
        
        return {
            "work_item_id": work_item_id,
            "guidewire_job_id": guidewire_response.guidewire_job_id,
            "previous_status": guidewire_response.job_status,
            "current_status": current_status['status'],
            "status_changed": status_changed,
            "policy_details": current_status,
            "last_sync": datetime.utcnow(),
            "available_actions": get_available_guidewire_actions(current_status)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Guidewire status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting status: {str(e)}"
        )

@sync_router.post("/webhook/status-update")
async def guidewire_status_webhook(
    update: PolicyStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for Guidewire to notify us of status changes
    This would be called by Guidewire when policies are created/bound/cancelled
    """
    try:
        # Find the work item associated with this Guidewire job
        guidewire_response = db.query(GuidewireResponse).filter(
            GuidewireResponse.guidewire_job_id == update.job_id
        ).first()
        
        if not guidewire_response:
            logger.warning(f"Received webhook for unknown job ID: {update.job_id}")
            return {"status": "ignored", "reason": "Job ID not found"}
        
        # Update the Guidewire response record
        guidewire_response.job_status = update.new_status
        if update.policy_number:
            guidewire_response.policy_number = update.policy_number
        if update.premium_amount:
            guidewire_response.total_premium_amount = update.premium_amount
        
        # Update work item status based on Guidewire status
        work_item = db.query(WorkItem).filter(
            WorkItem.id == guidewire_response.work_item_id
        ).first()
        
        if work_item:
            new_work_item_status = map_guidewire_to_work_item_status(update.new_status)
            if work_item.status != new_work_item_status:
                work_item.status = new_work_item_status
                work_item.updated_at = datetime.utcnow()
                
                # Create history entry
                history_entry = WorkItemHistory(
                    work_item_id=work_item.id,
                    action="guidewire_status_update",
                    changed_by=update.updated_by,
                    timestamp=datetime.utcnow(),
                    details={
                        "previous_guidewire_status": guidewire_response.job_status,
                        "new_guidewire_status": update.new_status,
                        "policy_number": update.policy_number,
                        "premium_amount": update.premium_amount
                    }
                )
                db.add(history_entry)
        
        db.commit()
        
        logger.info(f"Updated work item {guidewire_response.work_item_id} from Guidewire webhook: {update.new_status}")
        
        return {
            "status": "updated",
            "work_item_id": guidewire_response.work_item_id,
            "new_status": update.new_status,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error processing Guidewire webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )

@sync_router.get("/dashboard/sync-status")
async def get_sync_dashboard(db: Session = Depends(get_db)):
    """
    Get dashboard showing sync status across all submissions
    """
    try:
        # Get all Guidewire submissions
        all_submissions = db.query(GuidewireResponse).all()
        
        # Categorize by status
        status_counts = {}
        recent_updates = []
        needs_sync = []
        
        for submission in all_submissions:
            status = submission.job_status or "Unknown"
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Check if needs sync (older than 1 hour and not bound)
            if (submission.updated_at < datetime.utcnow() - timedelta(hours=1) 
                and status not in ["Bound", "Cancelled"]):
                needs_sync.append({
                    "work_item_id": submission.work_item_id,
                    "job_id": submission.guidewire_job_id,
                    "status": status,
                    "last_update": submission.updated_at
                })
            
            # Recent updates (last 24 hours)
            if submission.updated_at > datetime.utcnow() - timedelta(hours=24):
                recent_updates.append({
                    "work_item_id": submission.work_item_id,
                    "job_id": submission.guidewire_job_id,
                    "status": status,
                    "updated_at": submission.updated_at
                })
        
        return {
            "total_submissions": len(all_submissions),
            "status_distribution": status_counts,
            "needs_sync_count": len(needs_sync),
            "needs_sync": needs_sync[:10],  # Top 10
            "recent_updates_count": len(recent_updates),
            "recent_updates": recent_updates[:10],  # Top 10
            "sync_recommendations": {
                "auto_sync_frequency": "every_30_minutes",
                "manual_sync_suggested": len(needs_sync) > 5
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting sync dashboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting dashboard: {str(e)}"
        )

# Background task functions
async def sync_single_submission(job_id: str, work_item_id: int):
    """Background task to sync a single submission"""
    try:
        # Get current job status from Guidewire
        job_data = await get_job_status_from_guidewire(job_id)
        
        # Update database
        from database import SessionLocal
        db = SessionLocal()
        try:
            await update_work_item_from_guidewire_status(work_item_id, job_data, db)
            logger.info(f"Synced submission {job_id} for work item {work_item_id}")
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error syncing submission {job_id}: {str(e)}")

async def get_job_status_from_guidewire(job_id: str) -> Dict[str, Any]:
    """Get current job status from Guidewire"""
    try:
        # Use the Guidewire client to get job status
        # For now, we'll simulate this - in production you'd make the actual API call
        
        # Example of what this would look like with real Guidewire API:
        # job_url = f"/job/v1/jobs/{job_id}"
        # response = guidewire_client.make_request("GET", job_url)
        
        # Simulated response for now
        return {
            "job_id": job_id,
            "status": "Quoted",  # Could be Draft, Quoted, Bound, Cancelled
            "policy_number": None,  # Would be populated when bound
            "effective_date": datetime.utcnow(),
            "premium_amount": 1250.75,
            "last_updated": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting job status from Guidewire: {str(e)}")
        return {
            "job_id": job_id,
            "status": "Unknown",
            "error": str(e)
        }

async def update_work_item_from_guidewire_status(
    work_item_id: int, 
    guidewire_data: Dict[str, Any], 
    db: Session
):
    """Update work item based on Guidewire status"""
    try:
        # Update Guidewire response record
        guidewire_response = db.query(GuidewireResponse).filter(
            GuidewireResponse.work_item_id == work_item_id
        ).first()
        
        if guidewire_response:
            guidewire_response.job_status = guidewire_data['status']
            if 'policy_number' in guidewire_data and guidewire_data['policy_number']:
                guidewire_response.policy_number = guidewire_data['policy_number']
            if 'premium_amount' in guidewire_data and guidewire_data['premium_amount']:
                guidewire_response.total_premium_amount = guidewire_data['premium_amount']
            guidewire_response.updated_at = datetime.utcnow()
        
        # Update work item status
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if work_item:
            new_status = map_guidewire_to_work_item_status(guidewire_data['status'])
            if work_item.status != new_status:
                work_item.status = new_status
                work_item.updated_at = datetime.utcnow()
                
                # Create history entry
                history_entry = WorkItemHistory(
                    work_item_id=work_item_id,
                    action="status_sync_from_guidewire",
                    changed_by="Guidewire Sync",
                    timestamp=datetime.utcnow(),
                    details=guidewire_data
                )
                db.add(history_entry)
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error updating work item from Guidewire status: {str(e)}")
        db.rollback()

def map_guidewire_to_work_item_status(guidewire_status: str) -> str:
    """Map Guidewire job status to work item status"""
    from database import WorkItemStatus
    
    mapping = {
        "Draft": WorkItemStatus.IN_REVIEW,
        "Quoted": WorkItemStatus.QUOTED,
        "Bound": WorkItemStatus.POLICY_ISSUED,
        "Cancelled": WorkItemStatus.CANCELLED,
        "Declined": WorkItemStatus.DECLINED,
        "Withdrawn": WorkItemStatus.WITHDRAWN
    }
    return mapping.get(guidewire_status, WorkItemStatus.UNKNOWN)

def get_available_guidewire_actions(status_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Get available actions based on current Guidewire status"""
    status = status_data.get('status')
    
    actions = []
    
    if status == "Draft":
        actions.extend([
            {"action": "generate_quote", "label": "Generate Quote"},
            {"action": "edit_submission", "label": "Edit Submission"},
            {"action": "withdraw", "label": "Withdraw"}
        ])
    elif status == "Quoted":
        actions.extend([
            {"action": "bind_policy", "label": "Bind Policy"},
            {"action": "modify_quote", "label": "Modify Quote"},
            {"action": "decline", "label": "Decline"}
        ])
    elif status == "Bound":
        actions.extend([
            {"action": "view_policy", "label": "View Policy"},
            {"action": "create_endorsement", "label": "Create Endorsement"},
            {"action": "renew", "label": "Renew Policy"}
        ])
    
    return actions

# Export router
__all__ = ["sync_router"]