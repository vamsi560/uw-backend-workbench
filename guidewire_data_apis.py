"""
Guidewire Data APIs for Frontend
Comprehensive endpoints to expose Guidewire PolicyCenter data to the UI
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from database import get_db, GuidewireResponse, WorkItem, Submission

# Create router for Guidewire data APIs
guidewire_router = APIRouter(prefix="/api/guidewire", tags=["Guidewire Data"])

# ================================
# SUMMARY & DASHBOARD APIs
# ================================

@guidewire_router.get("/dashboard/summary", response_model=Dict[str, Any])
async def get_guidewire_dashboard_summary(
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days to include in summary")
):
    """
    Get Guidewire integration dashboard summary
    - Total submissions created
    - Success/failure rates  
    - Recent activity
    - Status distribution
    """
    try:
        # Get date range
        from_date = datetime.now() - timedelta(days=days)
        
        # Query summary statistics
        total_submissions = db.query(GuidewireResponse).count()
        recent_submissions = db.query(GuidewireResponse).filter(
            GuidewireResponse.created_at >= from_date
        ).count()
        
        successful_submissions = db.query(GuidewireResponse).filter(
            GuidewireResponse.submission_success == True
        ).count()
        
        quoted_submissions = db.query(GuidewireResponse).filter(
            GuidewireResponse.quote_generated == True
        ).count()
        
        # Status distribution
        status_counts = db.query(
            GuidewireResponse.job_status,
            func.count(GuidewireResponse.id).label('count')
        ).group_by(GuidewireResponse.job_status).all()
        
        # Recent activity
        recent_activity = db.query(GuidewireResponse).filter(
            GuidewireResponse.created_at >= from_date
        ).order_by(GuidewireResponse.created_at.desc()).limit(10).all()
        
        return {
            "summary": {
                "total_submissions": total_submissions,
                "recent_submissions": recent_submissions,
                "success_rate": round((successful_submissions / total_submissions * 100) if total_submissions > 0 else 0, 2),
                "quote_rate": round((quoted_submissions / total_submissions * 100) if total_submissions > 0 else 0, 2)
            },
            "status_distribution": [
                {"status": status or "Unknown", "count": count}
                for status, count in status_counts
            ],
            "recent_activity": [
                {
                    "id": response.id,
                    "account_number": response.account_number,
                    "job_number": response.job_number,
                    "job_status": response.job_status,
                    "organization_name": response.organization_name,
                    "created_at": response.created_at.isoformat() if response.created_at else None,
                    "success": response.submission_success
                }
                for response in recent_activity
            ],
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard summary: {str(e)}")

# ================================
# ACCOUNT & CUSTOMER APIs  
# ================================

@guidewire_router.get("/accounts", response_model=List[Dict[str, Any]])
async def get_guidewire_accounts(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by account status"),
    limit: int = Query(50, le=200, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Get list of Guidewire accounts with basic information
    - Account numbers and organization names
    - Account status and creation dates
    - Contact information
    - Navigation links
    """
    try:
        query = db.query(GuidewireResponse).filter(
            GuidewireResponse.guidewire_account_id.isnot(None)
        )
        
        if status:
            query = query.filter(GuidewireResponse.account_status == status)
            
        accounts = query.offset(offset).limit(limit).all()
        
        return [
            {
                "guidewire_account_id": account.guidewire_account_id,
                "account_number": account.account_number,
                "organization_name": account.organization_name,
                "account_status": account.account_status,
                "number_of_contacts": account.number_of_contacts,
                "created_at": account.created_at.isoformat() if account.created_at else None,
                "work_item_id": account.work_item_id,
                "submission_id": account.submission_id
            }
            for account in accounts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accounts: {str(e)}")

@guidewire_router.get("/accounts/{account_id}", response_model=Dict[str, Any])
async def get_guidewire_account_details(
    account_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific Guidewire account
    - Complete account information
    - Associated jobs and policies
    - Contact details
    - Activity links
    """
    try:
        response = db.query(GuidewireResponse).filter(
            GuidewireResponse.guidewire_account_id == account_id
        ).first()
        
        if not response:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Extract account details from raw response if available
        account_links = {}
        if response.api_links:
            account_links = response.api_links
        
        return {
            "account_info": {
                "guidewire_account_id": response.guidewire_account_id,
                "account_number": response.account_number,
                "organization_name": response.organization_name,
                "account_status": response.account_status,
                "number_of_contacts": response.number_of_contacts
            },
            "business_info": {
                "total_employees": response.total_employees,
                "total_revenues": response.total_revenues,
                "total_assets": response.total_assets,
                "total_liabilities": response.total_liabilities,
                "industry_type": response.industry_type,
                "business_started_date": response.business_started_date.isoformat() if response.business_started_date else None
            },
            "system_info": {
                "created_at": response.created_at.isoformat() if response.created_at else None,
                "updated_at": response.updated_at.isoformat() if response.updated_at else None,
                "response_checksum": response.response_checksum
            },
            "navigation": {
                "work_item_id": response.work_item_id,
                "submission_id": response.submission_id,
                "api_links": account_links
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching account details: {str(e)}")

# ================================
# JOBS & SUBMISSIONS APIs
# ================================

@guidewire_router.get("/jobs", response_model=List[Dict[str, Any]])
async def get_guidewire_jobs(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by job status (Draft, Quoted, etc.)"),
    product: Optional[str] = Query(None, description="Filter by product type"),
    limit: int = Query(50, le=200, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Get list of Guidewire jobs/submissions
    - Job numbers and status
    - Policy information
    - Pricing summary
    - Effective dates
    """
    try:
        query = db.query(GuidewireResponse).filter(
            GuidewireResponse.guidewire_job_id.isnot(None)
        )
        
        if status:
            query = query.filter(GuidewireResponse.job_status == status)
            
        if product:
            query = query.filter(GuidewireResponse.policy_type == product)
            
        jobs = query.order_by(GuidewireResponse.created_at.desc()).offset(offset).limit(limit).all()
        
        return [
            {
                "guidewire_job_id": job.guidewire_job_id,
                "job_number": job.job_number,
                "job_status": job.job_status,
                "organization_name": job.organization_name,
                "policy_type": job.policy_type,
                "job_effective_date": job.job_effective_date.isoformat() if job.job_effective_date else None,
                "base_state": job.base_state,
                "underwriting_company": job.underwriting_company,
                "total_premium": {
                    "amount": job.total_premium_amount,
                    "currency": job.total_premium_currency
                } if job.total_premium_amount else None,
                "quote_generated": job.quote_generated,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "account_number": job.account_number,
                "work_item_id": job.work_item_id
            }
            for job in jobs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@guidewire_router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_guidewire_job_details(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific Guidewire job
    - Complete job/submission details
    - Coverage information
    - Pricing breakdown
    - Business data
    - Available actions
    """
    try:
        response = db.query(GuidewireResponse).filter(
            GuidewireResponse.guidewire_job_id == job_id
        ).first()
        
        if not response:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_info": {
                "guidewire_job_id": response.guidewire_job_id,
                "job_number": response.job_number,
                "job_status": response.job_status,
                "job_effective_date": response.job_effective_date.isoformat() if response.job_effective_date else None,
                "policy_type": response.policy_type,
                "base_state": response.base_state,
                "underwriting_company": response.underwriting_company,
                "producer_code": response.producer_code
            },
            "account_info": {
                "guidewire_account_id": response.guidewire_account_id,
                "account_number": response.account_number,
                "organization_name": response.organization_name
            },
            "pricing_info": {
                "total_cost": {
                    "amount": response.total_cost_amount,
                    "currency": response.total_cost_currency
                } if response.total_cost_amount else None,
                "total_premium": {
                    "amount": response.total_premium_amount, 
                    "currency": response.total_premium_currency
                } if response.total_premium_amount else None,
                "rate_as_of_date": response.rate_as_of_date.isoformat() if response.rate_as_of_date else None
            },
            "coverage_info": {
                "coverage_terms": response.coverage_terms,
                "coverage_display": response.coverage_display_values
            },
            "business_data": {
                "total_employees": response.total_employees,
                "total_revenues": response.total_revenues,
                "business_started_date": response.business_started_date.isoformat() if response.business_started_date else None
            },
            "status": {
                "submission_success": response.submission_success,
                "quote_generated": response.quote_generated,
                "created_at": response.created_at.isoformat() if response.created_at else None,
                "updated_at": response.updated_at.isoformat() if response.updated_at else None
            },
            "navigation": {
                "work_item_id": response.work_item_id,
                "submission_id": response.submission_id,
                "api_links": response.api_links
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job details: {str(e)}")

# ================================
# COVERAGE & PRICING APIs
# ================================

@guidewire_router.get("/coverage/summary", response_model=List[Dict[str, Any]])
async def get_coverage_summary(
    db: Session = Depends(get_db),
    limit: int = Query(50, le=200)
):
    """
    Get summary of coverage terms across all submissions
    - Coverage limits distribution
    - Popular coverage selections
    - Pricing trends
    """
    try:
        responses = db.query(GuidewireResponse).filter(
            GuidewireResponse.coverage_terms.isnot(None)
        ).limit(limit).all()
        
        coverage_summary = []
        
        for response in responses:
            if response.coverage_terms:
                # Extract key coverage information
                coverage_info = {
                    "job_number": response.job_number,
                    "organization_name": response.organization_name,
                    "coverage_terms": response.coverage_terms,
                    "coverage_display": response.coverage_display_values,
                    "total_premium": response.total_premium_amount,
                    "created_at": response.created_at.isoformat() if response.created_at else None
                }
                coverage_summary.append(coverage_info)
        
        return coverage_summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching coverage summary: {str(e)}")

@guidewire_router.get("/pricing/analysis", response_model=Dict[str, Any])
async def get_pricing_analysis(
    db: Session = Depends(get_db),
    days: int = Query(90, description="Analysis period in days")
):
    """
    Get pricing analysis and trends
    - Average premiums
    - Pricing distribution
    - Quote success rates
    """
    try:
        from_date = datetime.now() - timedelta(days=days)
        
        responses = db.query(GuidewireResponse).filter(
            GuidewireResponse.created_at >= from_date,
            GuidewireResponse.total_premium_amount.isnot(None)
        ).all()
        
        if not responses:
            return {
                "analysis_period": days,
                "total_quotes": 0,
                "average_premium": 0,
                "premium_range": {"min": 0, "max": 0},
                "distribution": []
            }
        
        premiums = [r.total_premium_amount for r in responses if r.total_premium_amount]
        
        return {
            "analysis_period": days,
            "total_quotes": len(responses),
            "average_premium": round(sum(premiums) / len(premiums), 2) if premiums else 0,
            "premium_range": {
                "min": min(premiums) if premiums else 0,
                "max": max(premiums) if premiums else 0
            },
            "quote_success_rate": round(
                len([r for r in responses if r.quote_generated]) / len(responses) * 100, 2
            ) if responses else 0,
            "distribution": [
                {
                    "job_number": r.job_number,
                    "organization": r.organization_name,
                    "premium": r.total_premium_amount,
                    "status": r.job_status,
                    "date": r.created_at.isoformat() if r.created_at else None
                }
                for r in responses[-20:]  # Latest 20 for distribution view
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in pricing analysis: {str(e)}")

# ================================
# WORK ITEM INTEGRATION APIs
# ================================

@guidewire_router.get("/workitem/{work_item_id}/guidewire-data", response_model=Dict[str, Any])
async def get_workitem_guidewire_data(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all Guidewire data associated with a work item
    - Account and job information
    - Coverage and pricing details
    - Submission status
    - Available Guidewire actions
    """
    try:
        # Get work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        # Get Guidewire response
        guidewire_response = db.query(GuidewireResponse).filter(
            GuidewireResponse.work_item_id == work_item_id
        ).first()
        
        if not guidewire_response:
            return {
                "work_item_id": work_item_id,
                "has_guidewire_data": False,
                "message": "No Guidewire submission found for this work item"
            }
        
        # Get submission details
        submission = db.query(Submission).filter(
            Submission.id == guidewire_response.submission_id
        ).first()
        
        return {
            "work_item_id": work_item_id,
            "has_guidewire_data": True,
            "guidewire_info": {
                "account": {
                    "guidewire_account_id": guidewire_response.guidewire_account_id,
                    "account_number": guidewire_response.account_number,
                    "organization_name": guidewire_response.organization_name,
                    "account_status": guidewire_response.account_status
                },
                "job": {
                    "guidewire_job_id": guidewire_response.guidewire_job_id,
                    "job_number": guidewire_response.job_number,
                    "job_status": guidewire_response.job_status,
                    "policy_type": guidewire_response.policy_type,
                    "effective_date": guidewire_response.job_effective_date.isoformat() if guidewire_response.job_effective_date else None
                },
                "pricing": {
                    "total_premium": guidewire_response.total_premium_amount,
                    "currency": guidewire_response.total_premium_currency,
                    "quote_generated": guidewire_response.quote_generated,
                    "rate_date": guidewire_response.rate_as_of_date.isoformat() if guidewire_response.rate_as_of_date else None
                },
                "coverage": {
                    "terms": guidewire_response.coverage_terms,
                    "display_values": guidewire_response.coverage_display_values
                },
                "status": {
                    "submission_success": guidewire_response.submission_success,
                    "created_at": guidewire_response.created_at.isoformat() if guidewire_response.created_at else None,
                    "last_updated": guidewire_response.updated_at.isoformat() if guidewire_response.updated_at else None
                }
            },
            "original_submission": {
                "submission_id": submission.id if submission else None,
                "extracted_data": submission.extracted_data if submission else None
            } if submission else None,
            "available_actions": {
                "view_in_guidewire": True,
                "update_submission": guidewire_response.job_status in ["Draft", "Quoted"],
                "bind_policy": guidewire_response.job_status == "Quoted",
                "api_links": guidewire_response.api_links
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching work item Guidewire data: {str(e)}")

# ================================
# SEARCH & FILTER APIs
# ================================

@guidewire_router.get("/search", response_model=List[Dict[str, Any]])
async def search_guidewire_data(
    q: str = Query(..., description="Search query"),
    type: str = Query("all", description="Search type: all, accounts, jobs, organizations"),
    db: Session = Depends(get_db),
    limit: int = Query(20, le=100)
):
    """
    Search Guidewire data across accounts, jobs, and organizations
    - Search by account number, job number, organization name
    - Filter by type (accounts, jobs, organizations)
    - Full-text search capabilities
    """
    try:
        query_obj = db.query(GuidewireResponse)
        
        # Build search conditions
        search_conditions = []
        
        if type in ["all", "accounts"]:
            search_conditions.extend([
                GuidewireResponse.account_number.ilike(f"%{q}%"),
                GuidewireResponse.organization_name.ilike(f"%{q}%")
            ])
        
        if type in ["all", "jobs"]:
            search_conditions.extend([
                GuidewireResponse.job_number.ilike(f"%{q}%"),
                GuidewireResponse.policy_type.ilike(f"%{q}%")
            ])
        
        if search_conditions:
            from sqlalchemy import or_
            query_obj = query_obj.filter(or_(*search_conditions))
        
        results = query_obj.limit(limit).all()
        
        return [
            {
                "type": "account" if result.guidewire_account_id else "job",
                "guidewire_account_id": result.guidewire_account_id,
                "guidewire_job_id": result.guidewire_job_id,
                "account_number": result.account_number,
                "job_number": result.job_number,
                "organization_name": result.organization_name,
                "job_status": result.job_status,
                "policy_type": result.policy_type,
                "created_at": result.created_at.isoformat() if result.created_at else None,
                "work_item_id": result.work_item_id
            }
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in search: {str(e)}")

# ================================
# EXPORT & REPORTING APIs
# ================================

@guidewire_router.get("/export/submissions", response_model=Dict[str, Any])
async def export_submissions_data(
    format: str = Query("json", description="Export format: json, csv"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    Export Guidewire submissions data for reporting
    - Multiple export formats (JSON, CSV)
    - Date range filtering
    - Status filtering
    - Complete submission details
    """
    try:
        query = db.query(GuidewireResponse)
        
        # Apply filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(GuidewireResponse.created_at >= start_dt)
            
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(GuidewireResponse.created_at <= end_dt)
            
        if status:
            query = query.filter(GuidewireResponse.job_status == status)
        
        submissions = query.all()
        
        export_data = []
        for submission in submissions:
            export_data.append({
                "account_number": submission.account_number,
                "job_number": submission.job_number,
                "organization_name": submission.organization_name,
                "job_status": submission.job_status,
                "policy_type": submission.policy_type,
                "total_premium": submission.total_premium_amount,
                "currency": submission.total_premium_currency,
                "effective_date": submission.job_effective_date.isoformat() if submission.job_effective_date else None,
                "created_at": submission.created_at.isoformat() if submission.created_at else None,
                "quote_generated": submission.quote_generated,
                "submission_success": submission.submission_success,
                "work_item_id": submission.work_item_id,
                "base_state": submission.base_state,
                "underwriting_company": submission.underwriting_company
            })
        
        return {
            "format": format,
            "total_records": len(export_data),
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "status": status
            },
            "data": export_data,
            "export_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")