"""
System Overview and Status Dashboard
Provides comprehensive system statistics, health metrics, and workflow insights
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from database import (
    get_db, WorkItem, Submission, RiskAssessment, User, Underwriter, 
    WorkItemHistory, SubmissionHistory, Comment, WorkItemStatus, WorkItemPriority
)

logger = logging.getLogger(__name__)

# Create router
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["System Dashboard"])

@dashboard_router.get("/overview")
async def get_system_overview(db: Session = Depends(get_db)):
    """
    Get comprehensive system overview with key metrics
    """
    try:
        # Current date ranges
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        # Basic counts
        total_submissions = db.query(Submission).count()
        total_work_items = db.query(WorkItem).count()
        active_underwriters = db.query(Underwriter).filter(Underwriter.is_active == True).count()
        total_users = db.query(User).filter(User.is_active == True).count()
        
        # Work item status distribution
        status_counts = db.query(
            WorkItem.status,
            func.count(WorkItem.id)
        ).group_by(WorkItem.status).all()
        
        status_distribution = {
            status.value if hasattr(status, 'value') else str(status): count 
            for status, count in status_counts
        }
        
        # Priority distribution
        priority_counts = db.query(
            WorkItem.priority,
            func.count(WorkItem.id)
        ).group_by(WorkItem.priority).all()
        
        priority_distribution = {
            priority.value if hasattr(priority, 'value') else str(priority): count 
            for priority, count in priority_counts
        }
        
        # Activity metrics (last 24 hours)
        submissions_today = db.query(Submission).filter(
            Submission.created_at >= today_start
        ).count()
        
        work_items_created_today = db.query(WorkItem).filter(
            WorkItem.created_at >= today_start
        ).count()
        
        assessments_completed_today = db.query(RiskAssessment).filter(
            RiskAssessment.assessment_date >= today_start
        ).count()
        
        # Average risk score
        avg_risk_score = db.query(func.avg(WorkItem.risk_score)).filter(
            WorkItem.risk_score.isnot(None)
        ).scalar()
        
        # High risk items count
        high_risk_count = db.query(WorkItem).filter(
            WorkItem.risk_score > 0.7
        ).count()
        
        # Underwriter workload summary
        underwriter_workloads = db.query(
            WorkItem.assigned_to,
            func.count(WorkItem.id).label('workload')
        ).filter(
            WorkItem.assigned_to.isnot(None),
            WorkItem.status.in_(['pending', 'in_review'])
        ).group_by(WorkItem.assigned_to).all()
        
        total_assigned_items = sum(workload for _, workload in underwriter_workloads)
        avg_workload = (total_assigned_items / max(active_underwriters, 1)) if active_underwriters else 0
        
        # Recent activity summary
        recent_history_count = db.query(WorkItemHistory).filter(
            WorkItemHistory.timestamp >= week_start
        ).count()
        
        return {
            "system_overview": {
                "total_submissions": total_submissions,
                "total_work_items": total_work_items,
                "active_underwriters": active_underwriters,
                "total_users": total_users,
                "average_risk_score": round(float(avg_risk_score), 3) if avg_risk_score else 0,
                "high_risk_items": high_risk_count
            },
            "daily_activity": {
                "submissions_today": submissions_today,
                "work_items_created_today": work_items_created_today,
                "assessments_completed_today": assessments_completed_today,
                "activity_score": min(100, (submissions_today + work_items_created_today + assessments_completed_today) * 10)
            },
            "work_item_distribution": {
                "by_status": status_distribution,
                "by_priority": priority_distribution
            },
            "underwriter_metrics": {
                "total_assigned_items": total_assigned_items,
                "average_workload": round(avg_workload, 1),
                "underwriters_with_work": len(underwriter_workloads)
            },
            "recent_activity": {
                "history_entries_last_week": recent_history_count,
                "activity_trend": "increasing" if recent_history_count > 50 else "moderate" if recent_history_count > 20 else "low"
            },
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating system overview: {str(e)}")
        return {
            "error": f"Error generating system overview: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@dashboard_router.get("/workflow-analytics")
async def get_workflow_analytics(
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get detailed workflow analytics and performance metrics
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Submission processing times
        completed_items = db.query(WorkItem).filter(
            WorkItem.status == WorkItemStatus.APPROVED,
            WorkItem.created_at >= cutoff_date
        ).all()
        
        processing_times = []
        for item in completed_items:
            if item.updated_at and item.created_at:
                processing_time = (item.updated_at - item.created_at).total_seconds() / 3600  # hours
                processing_times.append(processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Industry distribution
        industry_stats = db.query(
            WorkItem.industry,
            func.count(WorkItem.id).label('count'),
            func.avg(WorkItem.risk_score).label('avg_risk')
        ).filter(
            WorkItem.created_at >= cutoff_date
        ).group_by(WorkItem.industry).all()
        
        # Risk assessment trends
        risk_assessments_by_day = db.query(
            func.date(RiskAssessment.assessment_date).label('assessment_date'),
            func.count(RiskAssessment.id).label('count'),
            func.avg(RiskAssessment.overall_score).label('avg_score')
        ).filter(
            RiskAssessment.assessment_date >= cutoff_date
        ).group_by(func.date(RiskAssessment.assessment_date)).order_by('assessment_date').all()
        
        # Status transition analysis
        status_transitions = db.query(
            WorkItemHistory.details,
            func.count(WorkItemHistory.id).label('count')
        ).filter(
            WorkItemHistory.timestamp >= cutoff_date,
            WorkItemHistory.action.like('%status_changed%')
        ).group_by(WorkItemHistory.details).all()
        
        # Top performing underwriters
        underwriter_performance = db.query(
            WorkItem.assigned_to,
            func.count(WorkItem.id).label('completed_items'),
            func.avg(WorkItem.risk_score).label('avg_risk_handled')
        ).filter(
            WorkItem.status == WorkItemStatus.APPROVED,
            WorkItem.updated_at >= cutoff_date,
            WorkItem.assigned_to.isnot(None)
        ).group_by(WorkItem.assigned_to).order_by('completed_items desc').limit(10).all()
        
        return {
            "analysis_period": {
                "days_analyzed": days_back,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            "processing_metrics": {
                "average_processing_time_hours": round(avg_processing_time, 2),
                "completed_items_count": len(processing_times),
                "processing_efficiency": "excellent" if avg_processing_time < 24 else "good" if avg_processing_time < 72 else "needs_improvement"
            },
            "industry_analysis": [
                {
                    "industry": industry or "Unknown",
                    "submission_count": count,
                    "average_risk_score": round(float(avg_risk), 3) if avg_risk else 0
                }
                for industry, count, avg_risk in industry_stats
            ],
            "risk_assessment_trends": [
                {
                    "date": assessment_date.isoformat(),
                    "assessments_count": count,
                    "average_score": round(float(avg_score), 3) if avg_score else 0
                }
                for assessment_date, count, avg_score in risk_assessments_by_day
            ],
            "underwriter_performance": [
                {
                    "underwriter_email": assigned_to,
                    "completed_items": completed_items,
                    "average_risk_handled": round(float(avg_risk_handled), 3) if avg_risk_handled else 0
                }
                for assigned_to, completed_items, avg_risk_handled in underwriter_performance
            ],
            "workflow_health": {
                "status": "healthy" if avg_processing_time < 48 and len(processing_times) > 0 else "needs_attention",
                "recommendations": get_workflow_recommendations(avg_processing_time, len(processing_times))
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating workflow analytics: {str(e)}")
        return {
            "error": f"Error generating workflow analytics: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@dashboard_router.get("/real-time-metrics")
async def get_real_time_metrics(db: Session = Depends(get_db)):
    """
    Get real-time system metrics and alerts
    """
    try:
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        
        # Real-time counts
        pending_items = db.query(WorkItem).filter(WorkItem.status == WorkItemStatus.PENDING).count()
        in_review_items = db.query(WorkItem).filter(WorkItem.status == WorkItemStatus.IN_REVIEW).count()
        high_priority_items = db.query(WorkItem).filter(
            WorkItem.priority == WorkItemPriority.HIGH,
            WorkItem.status.in_([WorkItemStatus.PENDING, WorkItemStatus.IN_REVIEW])
        ).count()
        
        # Activity in last hour
        submissions_last_hour = db.query(Submission).filter(
            Submission.created_at >= last_hour
        ).count()
        
        assessments_last_hour = db.query(RiskAssessment).filter(
            RiskAssessment.assessment_date >= last_hour
        ).count()
        
        # System health indicators
        unassigned_items = db.query(WorkItem).filter(
            WorkItem.assigned_to.is_(None),
            WorkItem.status.in_([WorkItemStatus.PENDING, WorkItemStatus.IN_REVIEW])
        ).count()
        
        overdue_items = db.query(WorkItem).filter(
            WorkItem.created_at < (now - timedelta(days=7)),
            WorkItem.status.in_([WorkItemStatus.PENDING, WorkItemStatus.IN_REVIEW])
        ).count()
        
        # Risk alerts
        critical_risk_items = db.query(WorkItem).filter(
            WorkItem.risk_score > 0.9,
            WorkItem.status != WorkItemStatus.APPROVED
        ).count()
        
        # Coverage amount analysis
        high_value_pending = db.query(WorkItem).filter(
            WorkItem.coverage_amount > 1000000,
            WorkItem.status.in_([WorkItemStatus.PENDING, WorkItemStatus.IN_REVIEW])
        ).count()
        
        # Generate alerts
        alerts = []
        
        if unassigned_items > 10:
            alerts.append({
                "type": "workload",
                "severity": "medium",
                "message": f"{unassigned_items} unassigned work items need attention"
            })
        
        if overdue_items > 5:
            alerts.append({
                "type": "processing_delay",
                "severity": "high",
                "message": f"{overdue_items} work items are overdue (>7 days)"
            })
        
        if critical_risk_items > 0:
            alerts.append({
                "type": "high_risk",
                "severity": "critical",
                "message": f"{critical_risk_items} critical risk items require immediate attention"
            })
        
        if high_value_pending > 0:
            alerts.append({
                "type": "high_value",
                "severity": "medium",
                "message": f"{high_value_pending} high-value submissions (>$1M) are pending"
            })
        
        return {
            "current_workload": {
                "pending_items": pending_items,
                "in_review_items": in_review_items,
                "high_priority_items": high_priority_items,
                "unassigned_items": unassigned_items,
                "overdue_items": overdue_items
            },
            "recent_activity": {
                "submissions_last_hour": submissions_last_hour,
                "assessments_last_hour": assessments_last_hour,
                "activity_rate": submissions_last_hour + assessments_last_hour
            },
            "risk_metrics": {
                "critical_risk_items": critical_risk_items,
                "high_value_pending": high_value_pending,
                "risk_alert_level": "critical" if critical_risk_items > 0 else "normal"
            },
            "system_alerts": alerts,
            "alert_summary": {
                "total_alerts": len(alerts),
                "critical_alerts": len([a for a in alerts if a["severity"] == "critical"]),
                "system_status": "critical" if len([a for a in alerts if a["severity"] == "critical"]) > 0 else 
                               "warning" if len(alerts) > 0 else "healthy"
            },
            "timestamp": now.isoformat(),
            "refresh_interval_seconds": 30
        }
        
    except Exception as e:
        logger.error(f"Error generating real-time metrics: {str(e)}")
        return {
            "error": f"Error generating real-time metrics: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@dashboard_router.get("/performance-trends")
async def get_performance_trends(
    period_days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get system performance trends over time
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Daily submission trends
        daily_submissions = db.query(
            func.date(Submission.created_at).label('submission_date'),
            func.count(Submission.id).label('count')
        ).filter(
            Submission.created_at >= start_date
        ).group_by(func.date(Submission.created_at)).order_by('submission_date').all()
        
        # Daily completion trends
        daily_completions = db.query(
            func.date(WorkItem.updated_at).label('completion_date'),
            func.count(WorkItem.id).label('count')
        ).filter(
            WorkItem.status == WorkItemStatus.APPROVED,
            WorkItem.updated_at >= start_date
        ).group_by(func.date(WorkItem.updated_at)).order_by('completion_date').all()
        
        # Risk assessment trends
        daily_assessments = db.query(
            func.date(RiskAssessment.assessment_date).label('assessment_date'),
            func.count(RiskAssessment.id).label('count'),
            func.avg(RiskAssessment.overall_score).label('avg_score')
        ).filter(
            RiskAssessment.assessment_date >= start_date
        ).group_by(func.date(RiskAssessment.assessment_date)).order_by('assessment_date').all()
        
        # Weekly performance summary
        weeks_back = period_days // 7
        weekly_performance = []
        
        for week in range(weeks_back):
            week_start = end_date - timedelta(weeks=week+1)
            week_end = end_date - timedelta(weeks=week)
            
            week_submissions = db.query(Submission).filter(
                and_(Submission.created_at >= week_start, Submission.created_at < week_end)
            ).count()
            
            week_completions = db.query(WorkItem).filter(
                WorkItem.status == WorkItemStatus.APPROVED,
                and_(WorkItem.updated_at >= week_start, WorkItem.updated_at < week_end)
            ).count()
            
            weekly_performance.append({
                "week_start": week_start.date().isoformat(),
                "week_end": week_end.date().isoformat(),
                "submissions": week_submissions,
                "completions": week_completions,
                "completion_rate": round((week_completions / max(week_submissions, 1)) * 100, 1)
            })
        
        # Calculate trends
        submission_trend = calculate_trend([day.count for day in daily_submissions])
        completion_trend = calculate_trend([day.count for day in daily_completions])
        
        return {
            "analysis_period": {
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "days_analyzed": period_days
            },
            "daily_trends": {
                "submissions": [
                    {
                        "date": date.isoformat(),
                        "count": count
                    }
                    for date, count in daily_submissions
                ],
                "completions": [
                    {
                        "date": date.isoformat(),
                        "count": count
                    }
                    for date, count in daily_completions
                ],
                "assessments": [
                    {
                        "date": date.isoformat(),
                        "count": count,
                        "average_risk_score": round(float(avg_score), 3) if avg_score else 0
                    }
                    for date, count, avg_score in daily_assessments
                ]
            },
            "weekly_performance": weekly_performance,
            "trend_analysis": {
                "submission_trend": submission_trend,
                "completion_trend": completion_trend,
                "overall_performance": "improving" if submission_trend == "increasing" and completion_trend == "increasing" else "stable" if submission_trend == "stable" else "declining"
            },
            "timestamp": end_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating performance trends: {str(e)}")
        return {
            "error": f"Error generating performance trends: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

def get_workflow_recommendations(avg_processing_time: float, completed_count: int) -> List[str]:
    """Generate workflow recommendations based on metrics"""
    recommendations = []
    
    if avg_processing_time > 72:
        recommendations.append("Consider automating more of the initial review process")
        recommendations.append("Review underwriter workload distribution")
    
    if avg_processing_time > 48:
        recommendations.append("Implement priority-based processing queues")
    
    if completed_count < 10:
        recommendations.append("Monitor for processing bottlenecks")
    
    if not recommendations:
        recommendations.append("Workflow is performing well - maintain current processes")
    
    return recommendations

def calculate_trend(values: List[int]) -> str:
    """Calculate trend direction from a list of values"""
    if len(values) < 2:
        return "insufficient_data"
    
    # Simple trend calculation
    first_half = sum(values[:len(values)//2])
    second_half = sum(values[len(values)//2:])
    
    if second_half > first_half * 1.1:
        return "increasing"
    elif second_half < first_half * 0.9:
        return "decreasing"
    else:
        return "stable"

# Export router
__all__ = ["dashboard_router"]