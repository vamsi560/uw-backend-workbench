#!/usr/bin/env python3
"""
Minimal FastAPI server to test only the Guidewire API endpoints
"""
import logging
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database components
try:
    from database import get_db, Submission, WorkItem, WorkItemStatus
    from config import settings
    print("✅ Database imports successful")
except Exception as e:
    print(f"❌ Database import error: {e}")
    exit(1)

# Create minimal FastAPI app
app = FastAPI(
    title="Guidewire API Test Server",
    description="Minimal server to test Guidewire API endpoints",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Guidewire API Test Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "guidewire_submissions": "/api/guidewire/submissions",
            "guidewire_stats": "/api/guidewire/stats",
            "guidewire_search": "/api/guidewire/search"
        }
    }

# ===== GUIDEWIRE API ENDPOINTS =====

@app.get("/api/guidewire/submissions")
async def get_guidewire_submissions(
    limit: int = 50,
    offset: int = 0,
    search: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Get work items with Guidewire submission data for UI display
    Returns human-readable numbers for PolicyCenter search
    """
    try:
        # Query work items with Guidewire data
        query = db.query(WorkItem, Submission).join(
            Submission, WorkItem.submission_id == Submission.id
        ).filter(
            or_(
                WorkItem.guidewire_account_number.isnot(None),
                WorkItem.guidewire_job_number.isnot(None)
            )
        ).order_by(WorkItem.created_at.desc())
        
        # Apply filters
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    WorkItem.title.ilike(search_filter),
                    WorkItem.guidewire_account_number.ilike(search_filter),
                    WorkItem.guidewire_job_number.ilike(search_filter),
                    Submission.subject.ilike(search_filter)
                )
            )
        
        if status:
            try:
                status_enum = WorkItemStatus(status)
                query = query.filter(WorkItem.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        results = query.offset(offset).limit(limit).all()
        
        submissions = []
        for work_item, submission in results:
            submissions.append({
                "work_item_id": work_item.id,
                "submission_id": work_item.submission_id,
                "title": work_item.title or submission.subject,
                "status": work_item.status.value if work_item.status else "Pending",
                "priority": work_item.priority.value if work_item.priority else "Medium",
                "industry": work_item.industry,
                "coverage_amount": work_item.coverage_amount,
                
                # Guidewire identifiers
                "guidewire_account_id": work_item.guidewire_account_id,        # Internal ID (pc:xxxx)
                "guidewire_job_id": work_item.guidewire_job_id,                # Internal ID (pc:xxxx)
                "guidewire_account_number": work_item.guidewire_account_number, # Searchable number
                "guidewire_job_number": work_item.guidewire_job_number,         # Searchable number
                
                # Contact and business info
                "sender_email": submission.sender_email,
                "assigned_to": work_item.assigned_to,
                
                # Timestamps
                "created_at": work_item.created_at.isoformat() + "Z",
                "updated_at": work_item.updated_at.isoformat() + "Z",
                
                # UI helpers
                "has_guidewire_numbers": bool(work_item.guidewire_account_number and work_item.guidewire_job_number),
                "policycenter_search_ready": bool(work_item.guidewire_account_number and work_item.guidewire_job_number)
            })
        
        return {
            "submissions": submissions,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving Guidewire submissions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving Guidewire submissions: {str(e)}"
        )

@app.get("/api/guidewire/submissions/{work_item_id}")
async def get_guidewire_submission_detail(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed Guidewire submission data for a specific work item
    """
    try:
        # Get work item with submission data
        result = db.query(WorkItem, Submission).join(
            Submission, WorkItem.submission_id == Submission.id
        ).filter(WorkItem.id == work_item_id).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        work_item, submission = result
        
        # Parse extracted fields if available
        extracted_fields = {}
        if submission.extracted_fields:
            try:
                extracted_fields = submission.extracted_fields if isinstance(submission.extracted_fields, dict) else {}
            except Exception:
                extracted_fields = {}
        
        return {
            "work_item_id": work_item.id,
            "submission_id": work_item.submission_id,
            "title": work_item.title or submission.subject,
            "description": work_item.description,
            "status": work_item.status.value if work_item.status else "Pending",
            "priority": work_item.priority.value if work_item.priority else "Medium",
            
            # Guidewire Integration Data
            "guidewire": {
                "account_id": work_item.guidewire_account_id,              # Internal: pc:S-v7XpouN04iLx8kW8cev
                "job_id": work_item.guidewire_job_id,                      # Internal: pc:Su3nrO9cV2UMd9zYEYEmM
                "account_number": work_item.guidewire_account_number,       # Searchable: 1296620652
                "job_number": work_item.guidewire_job_number,               # Searchable: 0001982331
                "has_complete_data": bool(work_item.guidewire_account_number and work_item.guidewire_job_number),
                "policycenter_search_url": "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/pc/PolicyCenter.do#search",
                "search_instructions": {
                    "account_search": f"Use Account Number: {work_item.guidewire_account_number}" if work_item.guidewire_account_number else "Account number not available",
                    "job_search": f"Use Job Number: {work_item.guidewire_job_number}" if work_item.guidewire_job_number else "Job number not available"
                }
            },
            
            # Business Information
            "business_info": {
                "industry": work_item.industry,
                "policy_type": work_item.policy_type,
                "coverage_amount": work_item.coverage_amount,
                "company_size": work_item.company_size.value if work_item.company_size else None,
                "risk_score": work_item.risk_score
            },
            
            # Contact Information
            "contact_info": {
                "sender_email": submission.sender_email,
                "assigned_to": work_item.assigned_to,
                "contact_name": extracted_fields.get("contact_name"),
                "contact_phone": extracted_fields.get("contact_phone")
            },
            
            # Address Information
            "address_info": {
                "business_address": extracted_fields.get("business_address"),
                "business_city": extracted_fields.get("business_city"),
                "business_state": extracted_fields.get("business_state"),
                "business_zip": extracted_fields.get("business_zip")
            },
            
            # All extracted fields (for debugging/advanced display)
            "extracted_fields": extracted_fields,
            
            # Timestamps
            "created_at": work_item.created_at.isoformat() + "Z",
            "updated_at": work_item.updated_at.isoformat() + "Z",
            
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Guidewire submission detail: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving submission detail: {str(e)}"
        )

@app.get("/api/guidewire/search")
async def search_guidewire_submissions(
    account_number: str = None,
    job_number: str = None,
    company_name: str = None,
    email: str = None,
    db: Session = Depends(get_db)
):
    """
    Search Guidewire submissions by various criteria
    """
    try:
        query = db.query(WorkItem, Submission).join(
            Submission, WorkItem.submission_id == Submission.id
        ).filter(
            # Only return items that have Guidewire data
            or_(
                WorkItem.guidewire_account_number.isnot(None),
                WorkItem.guidewire_job_number.isnot(None)
            )
        )
        
        # Apply search filters
        if account_number:
            query = query.filter(WorkItem.guidewire_account_number.ilike(f"%{account_number}%"))
        
        if job_number:
            query = query.filter(WorkItem.guidewire_job_number.ilike(f"%{job_number}%"))
        
        if company_name:
            query = query.filter(
                or_(
                    WorkItem.title.ilike(f"%{company_name}%"),
                    Submission.subject.ilike(f"%{company_name}%")
                )
            )
        
        if email:
            query = query.filter(Submission.sender_email.ilike(f"%{email}%"))
        
        results = query.order_by(WorkItem.created_at.desc()).limit(20).all()
        
        matches = []
        for work_item, submission in results:
            matches.append({
                "work_item_id": work_item.id,
                "title": work_item.title or submission.subject,
                "guidewire_account_number": work_item.guidewire_account_number,
                "guidewire_job_number": work_item.guidewire_job_number,
                "sender_email": submission.sender_email,
                "status": work_item.status.value if work_item.status else "Pending",
                "created_at": work_item.created_at.isoformat() + "Z",
                "match_score": 1.0  # Could implement actual relevance scoring
            })
        
        return {
            "matches": matches,
            "total_found": len(matches),
            "search_criteria": {
                "account_number": account_number,
                "job_number": job_number, 
                "company_name": company_name,
                "email": email
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error searching Guidewire submissions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching submissions: {str(e)}"
        )

@app.get("/api/guidewire/stats")
async def get_guidewire_integration_stats(db: Session = Depends(get_db)):
    """
    Get statistics about Guidewire integration for dashboard display
    """
    try:        
        # Count work items with different levels of Guidewire integration
        total_work_items = db.query(WorkItem).count()
        
        with_account_numbers = db.query(WorkItem).filter(
            WorkItem.guidewire_account_number.isnot(None)
        ).count()
        
        with_job_numbers = db.query(WorkItem).filter(
            WorkItem.guidewire_job_number.isnot(None)
        ).count()
        
        complete_guidewire_data = db.query(WorkItem).filter(
            and_(
                WorkItem.guidewire_account_number.isnot(None),
                WorkItem.guidewire_job_number.isnot(None)
            )
        ).count()
        
        # Get recent Guidewire activities
        recent_guidewire_items = db.query(WorkItem).filter(
            or_(
                WorkItem.guidewire_account_number.isnot(None),
                WorkItem.guidewire_job_number.isnot(None)
            )
        ).order_by(WorkItem.updated_at.desc()).limit(5).all()
        
        return {
            "integration_stats": {
                "total_work_items": total_work_items,
                "with_account_numbers": with_account_numbers,
                "with_job_numbers": with_job_numbers,
                "complete_guidewire_data": complete_guidewire_data,
                "integration_percentage": round((complete_guidewire_data / total_work_items * 100), 2) if total_work_items > 0 else 0
            },
            "recent_activities": [
                {
                    "work_item_id": item.id,
                    "title": item.title,
                    "account_number": item.guidewire_account_number,
                    "job_number": item.guidewire_job_number,
                    "updated_at": item.updated_at.isoformat() + "Z"
                }
                for item in recent_guidewire_items
            ],
            "guidewire_status": "operational",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving Guidewire stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving integration stats: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    print("Starting Guidewire API Test Server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)