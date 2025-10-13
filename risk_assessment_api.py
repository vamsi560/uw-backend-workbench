"""
Risk Assessment API Integration
Integrates the advanced risk assessment engine with FastAPI endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from database import get_db, WorkItem, RiskAssessment, Submission, WorkItemHistory
from risk_assessment_engine import risk_assessment_engine, RiskLevel
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
risk_router = APIRouter(prefix="/api/risk", tags=["Risk Assessment"])

# Pydantic models for API requests/responses
class RiskAssessmentRequest(BaseModel):
    work_item_id: int
    force_recalculate: bool = Field(default=False, description="Force recalculation even if recent assessment exists")
    assessment_notes: Optional[str] = Field(default=None, description="Additional notes for the assessment")
    assessed_by: str = Field(default="System", description="Who is performing the assessment")

class RiskAssessmentResponse(BaseModel):
    work_item_id: int
    assessment_id: int
    overall_risk_score: float
    risk_level: str
    assessment_date: datetime
    assessed_by: str
    risk_factors: list
    coverage_recommendations: list
    risk_mitigation_suggestions: list
    assessment_confidence: float
    next_review_date: datetime

class BulkRiskAssessmentRequest(BaseModel):
    work_item_ids: list[int] = Field(description="List of work item IDs to assess")
    assessed_by: str = Field(default="System", description="Who is performing the assessments")
    force_recalculate: bool = Field(default=False, description="Force recalculation for all items")

class RiskScoreUpdateRequest(BaseModel):
    work_item_id: int
    manual_risk_score: float = Field(ge=0.0, le=1.0, description="Manual risk score between 0.0 and 1.0")
    updated_by: str
    reason: str
    notes: Optional[str] = None

@risk_router.post("/assess", response_model=RiskAssessmentResponse)
async def perform_risk_assessment(
    request: RiskAssessmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Perform comprehensive risk assessment for a work item
    Uses advanced risk assessment engine to analyze multiple factors
    """
    try:
        # Get the work item and related submission
        work_item = db.query(WorkItem).filter(WorkItem.id == request.work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        submission = db.query(Submission).filter(Submission.id == work_item.submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Related submission not found")
        
        # Check if recent assessment exists (within last 24 hours)
        from datetime import timedelta
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        
        existing_assessment = db.query(RiskAssessment).filter(
            RiskAssessment.work_item_id == request.work_item_id,
            RiskAssessment.assessment_date > recent_cutoff
        ).order_by(RiskAssessment.assessment_date.desc()).first()
        
        if existing_assessment and not request.force_recalculate:
            logger.info(f"Using existing risk assessment for work item {request.work_item_id}")
            return RiskAssessmentResponse(
                work_item_id=request.work_item_id,
                assessment_id=existing_assessment.id,
                overall_risk_score=existing_assessment.overall_score,
                risk_level=existing_assessment.risk_level or "medium",
                assessment_date=existing_assessment.assessment_date,
                assessed_by=existing_assessment.assessed_by,
                risk_factors=existing_assessment.risk_factors or [],
                coverage_recommendations=existing_assessment.coverage_recommendations or [],
                risk_mitigation_suggestions=existing_assessment.risk_mitigation_suggestions or [],
                assessment_confidence=existing_assessment.assessment_confidence or 0.8,
                next_review_date=existing_assessment.next_review_date or datetime.utcnow()
            )
        
        # Prepare business data for risk assessment
        business_data = {}
        
        # Extract data from work item
        if work_item.industry:
            business_data["industry_type"] = work_item.industry
        if work_item.coverage_amount:
            business_data["total_revenues"] = work_item.coverage_amount
        
        # Extract data from submission's extracted fields
        if submission.extracted_fields:
            extracted_fields = submission.extracted_fields
            if isinstance(extracted_fields, dict):
                business_data.update(extracted_fields)
        
        # Add submission metadata
        business_data.update({
            "business_description": work_item.description or submission.body_text or "",
            "company_name": business_data.get("company_name") or business_data.get("named_insured", "Unknown Company"),
            "business_state": business_data.get("business_state") or business_data.get("mailing_state", ""),
            "mailing_state": business_data.get("mailing_state") or business_data.get("business_state", "")
        })
        
        logger.info(f"Performing comprehensive risk assessment for work item {request.work_item_id}")
        
        # Run comprehensive risk assessment
        assessment_result = risk_assessment_engine.assess_comprehensive_risk(business_data)
        
        # Store assessment in database
        risk_assessment = RiskAssessment(
            work_item_id=request.work_item_id,
            overall_score=assessment_result["overall_risk_score"],
            risk_level=assessment_result["risk_level"],
            risk_categories={"comprehensive": assessment_result["overall_risk_score"]},
            risk_factors=assessment_result["risk_factors"],
            coverage_recommendations=assessment_result["coverage_recommendations"],
            risk_mitigation_suggestions=assessment_result["risk_mitigation_suggestions"],
            assessment_confidence=assessment_result["assessment_confidence"],
            assessment_date=datetime.utcnow(),
            assessed_by=request.assessed_by,
            assessment_notes=request.assessment_notes or "Comprehensive risk assessment using advanced engine",
            next_review_date=datetime.fromisoformat(assessment_result["next_review_date"].replace("Z", "+00:00"))
        )
        
        db.add(risk_assessment)
        
        # Update work item with new risk data
        work_item.risk_score = assessment_result["overall_risk_score"]
        work_item.last_risk_assessment = datetime.utcnow()
        work_item.updated_at = datetime.utcnow()
        
        # Create history entry
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action="risk_assessment_completed",
            changed_by=request.assessed_by,
            timestamp=datetime.utcnow(),
            details={
                "overall_risk_score": assessment_result["overall_risk_score"],
                "risk_level": assessment_result["risk_level"],
                "assessment_confidence": assessment_result["assessment_confidence"],
                "risk_factors_count": len(assessment_result["risk_factors"]),
                "coverage_recommendations_count": len(assessment_result["coverage_recommendations"])
            }
        )
        db.add(history_entry)
        
        db.commit()
        db.refresh(risk_assessment)
        
        logger.info(f"Risk assessment completed for work item {request.work_item_id}: {assessment_result['risk_level']} risk ({assessment_result['overall_risk_score']:.3f})")
        
        # Schedule background task for additional processing if needed
        background_tasks.add_task(
            update_related_assessments,
            work_item.id,
            assessment_result["overall_risk_score"]
        )
        
        return RiskAssessmentResponse(
            work_item_id=request.work_item_id,
            assessment_id=risk_assessment.id,
            overall_risk_score=assessment_result["overall_risk_score"],
            risk_level=assessment_result["risk_level"],
            assessment_date=risk_assessment.assessment_date,
            assessed_by=risk_assessment.assessed_by,
            risk_factors=assessment_result["risk_factors"],
            coverage_recommendations=assessment_result["coverage_recommendations"],
            risk_mitigation_suggestions=assessment_result["risk_mitigation_suggestions"],
            assessment_confidence=assessment_result["assessment_confidence"],
            next_review_date=risk_assessment.next_review_date
        )
        
    except Exception as e:
        logger.error(f"Error performing risk assessment for work item {request.work_item_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Risk assessment failed: {str(e)}"
        )

@risk_router.post("/assess/bulk")
async def bulk_risk_assessment(
    request: BulkRiskAssessmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Perform risk assessment for multiple work items
    Useful for batch processing or re-assessment
    """
    try:
        results = []
        errors = []
        
        for work_item_id in request.work_item_ids:
            try:
                # Create individual assessment request
                individual_request = RiskAssessmentRequest(
                    work_item_id=work_item_id,
                    force_recalculate=request.force_recalculate,
                    assessed_by=request.assessed_by
                )
                
                # Perform assessment
                result = await perform_risk_assessment(
                    individual_request, 
                    background_tasks, 
                    db
                )
                results.append(result)
                
            except Exception as e:
                error_msg = f"Work item {work_item_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Bulk assessment error - {error_msg}")
        
        return {
            "total_requested": len(request.work_item_ids),
            "successful_assessments": len(results),
            "failed_assessments": len(errors),
            "results": results,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in bulk risk assessment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Bulk risk assessment failed: {str(e)}"
        )

@risk_router.get("/work-item/{work_item_id}")
async def get_risk_assessment(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the latest risk assessment for a work item
    """
    try:
        # Get the most recent risk assessment
        risk_assessment = db.query(RiskAssessment).filter(
            RiskAssessment.work_item_id == work_item_id
        ).order_by(RiskAssessment.assessment_date.desc()).first()
        
        if not risk_assessment:
            raise HTTPException(
                status_code=404,
                detail="No risk assessment found for this work item"
            )
        
        return {
            "work_item_id": work_item_id,
            "assessment_id": risk_assessment.id,
            "overall_risk_score": risk_assessment.overall_score,
            "risk_level": risk_assessment.risk_level,
            "risk_categories": risk_assessment.risk_categories,
            "risk_factors": risk_assessment.risk_factors,
            "coverage_recommendations": risk_assessment.coverage_recommendations,
            "risk_mitigation_suggestions": risk_assessment.risk_mitigation_suggestions,
            "assessment_confidence": risk_assessment.assessment_confidence,
            "assessment_date": risk_assessment.assessment_date.isoformat(),
            "assessed_by": risk_assessment.assessed_by,
            "assessment_notes": risk_assessment.assessment_notes,
            "next_review_date": risk_assessment.next_review_date.isoformat() if risk_assessment.next_review_date else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving risk assessment for work item {work_item_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving risk assessment: {str(e)}"
        )

@risk_router.put("/work-item/{work_item_id}/manual-score")
async def update_manual_risk_score(
    work_item_id: int,
    request: RiskScoreUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Manually update risk score for a work item
    Creates audit trail for manual overrides
    """
    try:
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        # Store old score for audit trail
        old_score = work_item.risk_score
        
        # Update work item risk score
        work_item.risk_score = request.manual_risk_score
        work_item.updated_at = datetime.utcnow()
        
        # Create manual risk assessment record
        manual_assessment = RiskAssessment(
            work_item_id=work_item_id,
            overall_score=request.manual_risk_score,
            risk_level=risk_assessment_engine._determine_risk_level(request.manual_risk_score).value,
            risk_categories={"manual_override": request.manual_risk_score},
            assessment_date=datetime.utcnow(),
            assessed_by=request.updated_by,
            assessment_notes=f"Manual risk score override. Reason: {request.reason}. Notes: {request.notes or 'None'}",
            is_manual_override=True
        )
        
        db.add(manual_assessment)
        
        # Create history entry for audit trail
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action="manual_risk_score_update",
            changed_by=request.updated_by,
            timestamp=datetime.utcnow(),
            details={
                "old_risk_score": old_score,
                "new_risk_score": request.manual_risk_score,
                "reason": request.reason,
                "notes": request.notes,
                "manual_override": True
            }
        )
        db.add(history_entry)
        
        db.commit()
        db.refresh(manual_assessment)
        
        logger.info(f"Manual risk score updated for work item {work_item_id}: {old_score} -> {request.manual_risk_score} by {request.updated_by}")
        
        return {
            "message": "Manual risk score updated successfully",
            "work_item_id": work_item_id,
            "old_score": old_score,
            "new_score": request.manual_risk_score,
            "updated_by": request.updated_by,
            "assessment_id": manual_assessment.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating manual risk score for work item {work_item_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating manual risk score: {str(e)}"
        )

@risk_router.get("/statistics")
async def get_risk_statistics(
    db: Session = Depends(get_db)
):
    """
    Get risk assessment statistics across all work items
    """
    try:
        from sqlalchemy import func
        
        # Overall statistics
        total_assessments = db.query(RiskAssessment).count()
        total_work_items = db.query(WorkItem).count()
        
        # Risk level distribution
        risk_level_stats = db.query(
            RiskAssessment.risk_level,
            func.count(RiskAssessment.id).label('count')
        ).group_by(RiskAssessment.risk_level).all()
        
        # Average risk scores by industry
        industry_stats = db.query(
            WorkItem.industry,
            func.avg(WorkItem.risk_score).label('avg_risk_score'),
            func.count(WorkItem.id).label('count')
        ).filter(WorkItem.risk_score.isnot(None)).group_by(WorkItem.industry).all()
        
        # Recent assessment activity (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_assessments = db.query(RiskAssessment).filter(
            RiskAssessment.assessment_date > thirty_days_ago
        ).count()
        
        # Manual overrides count
        manual_overrides = db.query(RiskAssessment).filter(
            RiskAssessment.is_manual_override == True
        ).count()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_statistics": {
                "total_assessments": total_assessments,
                "total_work_items": total_work_items,
                "assessment_coverage": round((total_assessments / max(total_work_items, 1)) * 100, 1),
                "recent_assessments_30_days": recent_assessments,
                "manual_overrides": manual_overrides
            },
            "risk_level_distribution": {
                level: count for level, count in risk_level_stats
            },
            "industry_analysis": [
                {
                    "industry": industry or "Unknown",
                    "average_risk_score": round(float(avg_score), 3) if avg_score else 0,
                    "work_items_count": count
                }
                for industry, avg_score, count in industry_stats
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating risk statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating statistics: {str(e)}"
        )

@risk_router.get("/recommendations/{work_item_id}")
async def get_coverage_recommendations(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed coverage recommendations for a specific work item
    """
    try:
        # Get the latest risk assessment
        risk_assessment = db.query(RiskAssessment).filter(
            RiskAssessment.work_item_id == work_item_id
        ).order_by(RiskAssessment.assessment_date.desc()).first()
        
        if not risk_assessment:
            raise HTTPException(
                status_code=404,
                detail="No risk assessment found. Please run assessment first."
            )
        
        return {
            "work_item_id": work_item_id,
            "assessment_date": risk_assessment.assessment_date.isoformat(),
            "overall_risk_score": risk_assessment.overall_score,
            "risk_level": risk_assessment.risk_level,
            "coverage_recommendations": risk_assessment.coverage_recommendations or [],
            "risk_mitigation_suggestions": risk_assessment.risk_mitigation_suggestions or [],
            "assessment_confidence": risk_assessment.assessment_confidence,
            "next_review_date": risk_assessment.next_review_date.isoformat() if risk_assessment.next_review_date else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving coverage recommendations for work item {work_item_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving recommendations: {str(e)}"
        )

async def update_related_assessments(work_item_id: int, risk_score: float):
    """
    Background task to update related assessments or trigger additional processing
    """
    try:
        logger.info(f"Background task: Updating related assessments for work item {work_item_id} with risk score {risk_score}")
        
        # Here you could implement additional logic such as:
        # - Notify underwriters of high-risk assessments
        # - Update portfolio risk metrics
        # - Trigger additional compliance checks
        # - Update pricing models
        
        # For now, just log the activity
        if risk_score > 0.8:
            logger.warning(f"High risk assessment detected for work item {work_item_id}: {risk_score}")
        
    except Exception as e:
        logger.error(f"Error in background assessment update task: {str(e)}")

# Export router
__all__ = ["risk_router"]