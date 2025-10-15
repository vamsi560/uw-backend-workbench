#!/usr/bin/env python3
"""
API endpoints for Guidewire lookup and quick search functionality
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from database import get_db, GuidewireLookup, WorkItem, Submission
from datetime import datetime
from pydantic import BaseModel

guidewire_lookup_router = APIRouter(prefix="/api/guidewire-lookups", tags=["Guidewire Lookups"])

# Response models
class GuidewireLookupOut(BaseModel):
    id: int
    work_item_id: int
    submission_id: int
    
    # Guidewire identifiers
    account_number: Optional[str]
    job_number: Optional[str] 
    organization_name: Optional[str]
    
    # Status
    account_created: bool
    submission_created: bool
    sync_status: str
    
    # Business context
    coverage_amount: Optional[float]
    industry: Optional[str]
    contact_email: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    account_created_at: Optional[datetime]
    submission_created_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class GuidewireSearchResult(BaseModel):
    """Quick search results for Guidewire PolicyCenter"""
    total_records: int
    complete_syncs: int
    partial_syncs: int
    failed_syncs: int
    recent_lookups: List[GuidewireLookupOut]

@guidewire_lookup_router.get("/", response_model=GuidewireSearchResult)
async def get_all_guidewire_lookups(
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all Guidewire lookup records for quick PolicyCenter search"""
    
    # Base query
    query = db.query(GuidewireLookup).order_by(desc(GuidewireLookup.updated_at))
    
    # Filter by status if provided
    if status:
        query = query.filter(GuidewireLookup.sync_status == status)
    
    # Get records
    lookups = query.limit(limit).all()
    
    # Calculate summary statistics
    total_query = db.query(GuidewireLookup)
    total_records = total_query.count()
    complete_syncs = total_query.filter(GuidewireLookup.sync_status == "complete").count()
    partial_syncs = total_query.filter(GuidewireLookup.sync_status == "partial").count()
    failed_syncs = total_query.filter(GuidewireLookup.sync_status == "failed").count()
    
    return GuidewireSearchResult(
        total_records=total_records,
        complete_syncs=complete_syncs,
        partial_syncs=partial_syncs,
        failed_syncs=failed_syncs,
        recent_lookups=[GuidewireLookupOut.model_validate(lookup) for lookup in lookups]
    )

@guidewire_lookup_router.get("/search/{search_term}")
async def search_guidewire_numbers(
    search_term: str,
    db: Session = Depends(get_db)
):
    """Search for Guidewire account/job numbers or organization names"""
    
    # Search across account numbers, job numbers, and organization names
    lookups = db.query(GuidewireLookup).filter(
        (GuidewireLookup.account_number.ilike(f"%{search_term}%")) |
        (GuidewireLookup.job_number.ilike(f"%{search_term}%")) |
        (GuidewireLookup.organization_name.ilike(f"%{search_term}%"))
    ).order_by(desc(GuidewireLookup.updated_at)).limit(10).all()
    
    results = []
    for lookup in lookups:
        results.append({
            "work_item_id": lookup.work_item_id,
            "account_number": lookup.account_number,
            "job_number": lookup.job_number,
            "organization_name": lookup.organization_name,
            "sync_status": lookup.sync_status,
            "coverage_amount": lookup.coverage_amount,
            "industry": lookup.industry,
            "updated_at": lookup.updated_at.isoformat() if lookup.updated_at else None
        })
    
    return {
        "search_term": search_term,
        "total_found": len(results),
        "results": results
    }

@guidewire_lookup_router.get("/work-item/{work_item_id}")
async def get_guidewire_lookup_by_work_item(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """Get Guidewire lookup information for a specific work item"""
    
    lookup = db.query(GuidewireLookup).filter(GuidewireLookup.work_item_id == work_item_id).first()
    
    if not lookup:
        # Check if work item exists but has no Guidewire data
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        return {
            "work_item_id": work_item_id,
            "guidewire_synced": False,
            "message": "Work item exists but no Guidewire integration found"
        }
    
    return {
        "work_item_id": work_item_id,
        "guidewire_synced": True,
        "account_number": lookup.account_number,
        "job_number": lookup.job_number,
        "organization_name": lookup.organization_name,
        "sync_status": lookup.sync_status,
        "account_created": lookup.account_created,
        "submission_created": lookup.submission_created,
        "coverage_amount": lookup.coverage_amount,
        "industry": lookup.industry,
        "contact_email": lookup.contact_email,
        "created_at": lookup.created_at.isoformat() if lookup.created_at else None,
        "updated_at": lookup.updated_at.isoformat() if lookup.updated_at else None,
        "policycenter_search_info": {
            "account_number": lookup.account_number,
            "job_number": lookup.job_number,
            "organization_name": lookup.organization_name,
            "search_instructions": "Use these numbers to search in Guidewire PolicyCenter"
        } if lookup.account_number else None
    }

@guidewire_lookup_router.get("/latest")
async def get_latest_guidewire_lookups(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get the most recent Guidewire lookups for quick checking"""
    
    lookups = db.query(GuidewireLookup).order_by(
        desc(GuidewireLookup.updated_at)
    ).limit(limit).all()
    
    results = []
    for lookup in lookups:
        # Get related work item title for context
        work_item = db.query(WorkItem).filter(WorkItem.id == lookup.work_item_id).first()
        submission = db.query(Submission).filter(Submission.id == lookup.submission_id).first()
        
        results.append({
            "work_item_id": lookup.work_item_id,
            "title": work_item.title if work_item else "Unknown",
            "sender_email": submission.sender_email if submission else "Unknown",
            "account_number": lookup.account_number,
            "job_number": lookup.job_number,
            "organization_name": lookup.organization_name,
            "sync_status": lookup.sync_status,
            "coverage_amount": f"${lookup.coverage_amount:,.0f}" if lookup.coverage_amount else "N/A",
            "industry": lookup.industry,
            "updated_at": lookup.updated_at.isoformat() if lookup.updated_at else None,
            "guidewire_search_ready": bool(lookup.account_number)
        })
    
    return {
        "message": "Latest Guidewire lookup records",
        "count": len(results),
        "lookups": results
    }