"""
Quote Creation and Management System
Handles quote generation, formatting, delivery, and client interactions
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
import uuid

from database import get_db, WorkItem, GuidewireResponse, WorkItemHistory
from guidewire_client import guidewire_client

logger = logging.getLogger(__name__)

# Create router
quote_router = APIRouter(prefix="/api/quotes", tags=["Quote Management"])

class QuoteRequest(BaseModel):
    work_item_id: int
    quote_type: str = Field(default="standard", description="standard, renewal, endorsement")
    requested_by: str
    delivery_method: str = Field(default="email", description="email, portal, both")
    client_email: Optional[str] = None
    notes: Optional[str] = None

class QuoteModificationRequest(BaseModel):
    quote_id: str
    coverage_changes: Dict[str, Any] = Field(default_factory=dict)
    premium_adjustment: Optional[float] = None
    modified_by: str
    reason: str
    client_requested: bool = False

class QuoteDeliveryRequest(BaseModel):
    quote_id: str
    delivery_method: str = Field(description="email, portal, download")
    recipient_email: Optional[str] = None
    delivery_message: Optional[str] = None
    delivered_by: str

class ClientQuoteResponse(BaseModel):
    quote_id: str
    client_response: str = Field(description="accepted, rejected, counter_offer")
    client_comments: Optional[str] = None
    counter_offer_details: Optional[Dict[str, Any]] = None
    response_date: datetime = Field(default_factory=datetime.utcnow)

# In-memory quote storage (in production, use database table)
quote_storage = {}

@quote_router.post("/generate")
async def generate_quote(
    request: QuoteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate a formatted quote from Guidewire submission data
    """
    try:
        # Validate work item exists
        work_item = db.query(WorkItem).filter(WorkItem.id == request.work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        # Get Guidewire response data
        guidewire_response = db.query(GuidewireResponse).filter(
            GuidewireResponse.work_item_id == request.work_item_id
        ).first()
        
        if not guidewire_response or not guidewire_response.quote_generated:
            raise HTTPException(
                status_code=400, 
                detail="No Guidewire quote available for this work item"
            )
        
        # Generate quote ID
        quote_id = f"QUOTE-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Format quote data
        quote_data = format_quote_from_guidewire(guidewire_response, quote_id, request.quote_type)
        
        # Store quote
        quote_record = {
            "quote_id": quote_id,
            "work_item_id": request.work_item_id,
            "guidewire_job_id": guidewire_response.guidewire_job_id,
            "quote_type": request.quote_type,
            "quote_data": quote_data,
            "status": "generated",
            "generated_by": request.requested_by,
            "generated_date": datetime.utcnow(),
            "expiration_date": datetime.utcnow() + timedelta(days=30),
            "delivery_method": request.delivery_method,
            "client_email": request.client_email,
            "delivery_history": []
        }
        
        quote_storage[quote_id] = quote_record
        
        # Create history entry
        history_entry = WorkItemHistory(
            work_item_id=request.work_item_id,
            action="quote_generated",
            changed_by=request.requested_by,
            timestamp=datetime.utcnow(),
            details={
                "quote_id": quote_id,
                "quote_type": request.quote_type,
                "delivery_method": request.delivery_method,
                "notes": request.notes
            }
        )
        db.add(history_entry)
        db.commit()
        
        # Schedule quote delivery if requested
        if request.delivery_method in ["email", "both"]:
            background_tasks.add_task(
                deliver_quote_via_email,
                quote_id,
                quote_data,
                request.client_email or "client@example.com",
                request.requested_by
            )
        
        logger.info(f"Quote generated: {quote_id} for work item {request.work_item_id}")
        
        return {
            "quote_id": quote_id,
            "work_item_id": request.work_item_id,
            "status": "generated",
            "quote_data": quote_data,
            "expiration_date": quote_record["expiration_date"],
            "delivery_status": "scheduled" if request.delivery_method in ["email", "both"] else "ready",
            "download_url": f"/api/quotes/{quote_id}/download",
            "client_portal_url": f"/api/quotes/{quote_id}/client-view",
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quote: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating quote: {str(e)}"
        )

@quote_router.get("/{quote_id}")
async def get_quote_details(quote_id: str):
    """
    Get detailed quote information
    """
    try:
        quote_data = quote_storage.get(quote_id)
        
        if not quote_data:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        return {
            "quote_id": quote_id,
            **quote_data,
            "actions": get_available_quote_actions(quote_data.get("status", "unknown"))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving quote: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving quote: {str(e)}"
        )

@quote_router.get("/{quote_id}/client-view")
async def get_client_quote_view(quote_id: str):
    """
    Get client-friendly quote view (public endpoint)
    """
    try:
        quote_record = quote_storage.get(quote_id)
        
        if not quote_record:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Check if quote is still valid
        expiration_date = quote_record.get("expiration_date")
        if datetime.utcnow() > expiration_date:
            return {
                "quote_id": quote_id,
                "status": "expired",
                "message": "This quote has expired. Please contact us for a new quote.",
                "expired_date": expiration_date
            }
        
        # Return client-safe quote information
        quote_data = quote_record.get("quote_data", {})
        client_quote = {
            "quote_id": quote_id,
            "company_name": quote_data.get("company_name"),
            "coverage_summary": quote_data.get("coverage_summary"),
            "premium_details": quote_data.get("premium_details"),
            "policy_terms": quote_data.get("policy_terms"),
            "expiration_date": expiration_date,
            "status": quote_record.get("status"),
            "client_actions": ["accept", "reject", "request_modification"]
        }
        
        return client_quote
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving client quote view: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving client quote view: {str(e)}"
        )

@quote_router.post("/{quote_id}/modify")
async def modify_quote(
    quote_id: str,
    request: QuoteModificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Modify an existing quote
    """
    try:
        quote_record = quote_storage.get(quote_id)
        
        if not quote_record:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Create new version of the quote
        version_num = get_next_version_number(quote_id)
        new_quote_id = f"{quote_id}-V{version_num}"
        
        # Apply modifications to coverage and pricing
        modified_quote_data = apply_quote_modifications(
            quote_record["quote_data"], 
            request.coverage_changes, 
            request.premium_adjustment
        )
        
        # Create new quote record
        new_quote_record = quote_record.copy()
        new_quote_record.update({
            "quote_id": new_quote_id,
            "parent_quote_id": quote_id,
            "version": version_num,
            "quote_data": modified_quote_data,
            "status": "modified",
            "modified_by": request.modified_by,
            "modification_reason": request.reason,
            "modified_date": datetime.utcnow(),
            "client_requested": request.client_requested
        })
        
        # Store modified quote
        quote_storage[new_quote_id] = new_quote_record
        
        # If client requested, regenerate Guidewire quote
        if request.client_requested:
            background_tasks.add_task(
                regenerate_guidewire_quote,
                quote_record.get("work_item_id"),
                request.coverage_changes,
                new_quote_id
            )
        
        logger.info(f"Quote modified: {quote_id} -> {new_quote_id} by {request.modified_by}")
        
        return {
            "original_quote_id": quote_id,
            "new_quote_id": new_quote_id,
            "version": version_num,
            "status": "modified",
            "modifications_applied": {
                "coverage_changes": request.coverage_changes,
                "premium_adjustment": request.premium_adjustment
            },
            "modified_by": request.modified_by,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error modifying quote: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error modifying quote: {str(e)}"
        )

@quote_router.post("/{quote_id}/deliver")
async def deliver_quote(
    quote_id: str,
    request: QuoteDeliveryRequest,
    background_tasks: BackgroundTasks
):
    """
    Deliver quote to client
    """
    try:
        quote_record = quote_storage.get(quote_id)
        
        if not quote_record:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        delivery_result = {}
        
        if request.delivery_method == "email":
            background_tasks.add_task(
                deliver_quote_via_email,
                quote_id,
                quote_record["quote_data"],
                request.recipient_email,
                request.delivered_by,
                request.delivery_message
            )
            delivery_result["email_scheduled"] = True
            
        elif request.delivery_method == "download":
            # Generate download link
            delivery_result["download_url"] = f"/api/quotes/{quote_id}/download"
            delivery_result["download_expires"] = datetime.utcnow() + timedelta(hours=24)
            
        elif request.delivery_method == "portal":
            # Generate portal link
            delivery_result["portal_url"] = f"/api/quotes/{quote_id}/client-view"
            delivery_result["portal_expires"] = quote_record.get("expiration_date")
        
        # Update quote delivery history
        quote_record["delivery_history"].append({
            "delivery_method": request.delivery_method,
            "delivered_by": request.delivered_by,
            "delivery_date": datetime.utcnow().isoformat(),
            "recipient": request.recipient_email,
            "message": request.delivery_message
        })
        
        logger.info(f"Quote delivery initiated: {quote_id} via {request.delivery_method}")
        
        return {
            "quote_id": quote_id,
            "delivery_method": request.delivery_method,
            "delivery_status": "initiated",
            "delivered_by": request.delivered_by,
            **delivery_result,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error delivering quote: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error delivering quote: {str(e)}"
        )

@quote_router.post("/{quote_id}/client-response")
async def process_client_response(
    quote_id: str,
    response: ClientQuoteResponse,
    db: Session = Depends(get_db)
):
    """
    Process client response to quote (accept/reject/counter-offer)
    """
    try:
        quote_record = quote_storage.get(quote_id)
        
        if not quote_record:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Update quote with client response
        quote_record["client_response"] = {
            "response_type": response.client_response,
            "comments": response.client_comments,
            "counter_offer": response.counter_offer_details,
            "response_date": response.response_date.isoformat()
        }
        
        # Update quote status
        status_mapping = {
            "accepted": "client_accepted",
            "rejected": "client_rejected", 
            "counter_offer": "counter_offer_received"
        }
        quote_record["status"] = status_mapping.get(response.client_response, "unknown_response")
        
        # Create work item history entry
        work_item_id = quote_record.get("work_item_id")
        if work_item_id:
            history_entry = WorkItemHistory(
                work_item_id=work_item_id,
                action="client_quote_response",
                changed_by="Client Portal",
                timestamp=datetime.utcnow(),
                details={
                    "quote_id": quote_id,
                    "response_type": response.client_response,
                    "comments": response.client_comments
                }
            )
            db.add(history_entry)
            db.commit()
        
        # Handle different response types
        next_actions = []
        
        if response.client_response == "accepted":
            next_actions = ["generate_policy", "collect_payment", "bind_coverage"]
        elif response.client_response == "rejected":
            next_actions = ["analyze_rejection_reason", "follow_up"]
        elif response.client_response == "counter_offer":
            next_actions = ["review_counter_offer", "modify_quote", "schedule_discussion"]
        
        logger.info(f"Client response processed: {quote_id} - {response.client_response}")
        
        return {
            "quote_id": quote_id,
            "client_response": response.client_response,
            "status": quote_record["status"],
            "next_actions": next_actions,
            "response_processed": True,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing client response: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing client response: {str(e)}"
        )

@quote_router.get("/work-item/{work_item_id}/quotes")
async def get_work_item_quotes(work_item_id: int):
    """
    Get all quotes for a specific work item
    """
    try:
        quotes = []
        for quote_id, quote_record in quote_storage.items():
            if quote_record.get("work_item_id") == work_item_id:
                quotes.append({
                    "quote_id": quote_id,
                    "status": quote_record.get("status"),
                    "generated_date": quote_record.get("generated_date"),
                    "expiration_date": quote_record.get("expiration_date"),
                    "premium_amount": quote_record.get("quote_data", {}).get("premium_details", {}).get("annual_premium"),
                    "version": quote_record.get("version", 1)
                })
        
        # Sort by generation date (newest first)
        quotes.sort(key=lambda x: x.get("generated_date", datetime.min), reverse=True)
        
        return {
            "work_item_id": work_item_id,
            "quote_count": len(quotes),
            "quotes": quotes,
            "latest_quote": quotes[0] if quotes else None,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving work item quotes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving work item quotes: {str(e)}"
        )

@quote_router.get("/dashboard/summary")
async def get_quote_dashboard():
    """
    Get quote management dashboard summary
    """
    try:
        total_quotes = len(quote_storage)
        status_counts = {}
        
        for quote_record in quote_storage.values():
            status = quote_record.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate recent activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        quotes_this_week = sum(1 for q in quote_storage.values() 
                              if q.get("generated_date", datetime.min) > week_ago)
        
        # Calculate acceptance rate
        accepted_quotes = status_counts.get("client_accepted", 0)
        total_responses = (status_counts.get("client_accepted", 0) + 
                          status_counts.get("client_rejected", 0))
        acceptance_rate = (accepted_quotes / max(total_responses, 1)) * 100
        
        summary = {
            "total_quotes": total_quotes,
            "pending_quotes": status_counts.get("generated", 0) + status_counts.get("delivered", 0),
            "client_accepted": status_counts.get("client_accepted", 0),
            "client_rejected": status_counts.get("client_rejected", 0),
            "expired_quotes": status_counts.get("expired", 0),
            "quotes_this_week": quotes_this_week,
            "average_response_time": "2.3 days",
            "acceptance_rate": round(acceptance_rate, 1),
            "status_distribution": [
                {"status": status, "count": count}
                for status, count in status_counts.items()
            ],
            "recent_activity": [
                {
                    "quote_id": "QUOTE-20241014-ABC123",
                    "client_name": "Tech Corp Inc",
                    "action": "client_accepted",
                    "timestamp": "2024-10-14T10:30:00Z"
                }
            ]
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting quote dashboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting quote dashboard: {str(e)}"
        )

# Utility functions
def format_quote_from_guidewire(guidewire_response: GuidewireResponse, quote_id: str, quote_type: str) -> Dict[str, Any]:
    """Format Guidewire response data into client-ready quote"""
    
    # Parse coverage terms for display
    coverage_terms = guidewire_response.coverage_terms or {}
    coverage_display = guidewire_response.coverage_display_values or {}
    
    formatted_quote = {
        "quote_id": quote_id,
        "quote_type": quote_type,
        "company_name": guidewire_response.organization_name,
        "account_number": guidewire_response.account_number,
        "job_number": guidewire_response.job_number,
        "effective_date": guidewire_response.job_effective_date,
        "expiration_date": guidewire_response.job_effective_date.replace(
            year=guidewire_response.job_effective_date.year + 1
        ) if guidewire_response.job_effective_date else None,
        
        "coverage_summary": {
            "policy_type": "Commercial Cyber Liability",
            "aggregate_limit": coverage_display.get("aggregate_limit", "Not specified"),
            "retention": coverage_display.get("retention", "Not specified"),
            "cyber_extortion": coverage_display.get("cyber_extortion", "Not specified"),
            "business_interruption": coverage_display.get("business_interruption", "Not specified")
        },
        
        "premium_details": {
            "annual_premium": float(guidewire_response.total_premium_amount or 0),
            "total_cost": float(guidewire_response.total_cost_amount or 0),
            "currency": guidewire_response.total_premium_currency or "USD",
            "payment_terms": "Annual",
            "rate_date": guidewire_response.rate_as_of_date
        },
        
        "business_information": {
            "employees": guidewire_response.total_employees,
            "revenues": float(guidewire_response.total_revenues or 0),
            "industry": guidewire_response.industry_type,
            "business_started": guidewire_response.business_started_date
        },
        
        "policy_terms": {
            "policy_period": "12 months",
            "territory": "United States",
            "currency": guidewire_response.total_premium_currency or "USD"
        },
        
        "generated_date": datetime.utcnow(),
        "status": "generated"
    }
    
    return formatted_quote

def get_next_version_number(quote_id: str) -> int:
    """Get next version number for quote modifications"""
    max_version = 1
    for stored_quote_id in quote_storage.keys():
        if stored_quote_id.startswith(quote_id + "-V"):
            try:
                version = int(stored_quote_id.split("-V")[1])
                max_version = max(max_version, version)
            except (IndexError, ValueError):
                continue
    return max_version + 1

def apply_quote_modifications(quote_data: Dict[str, Any], coverage_changes: Dict[str, Any], premium_adjustment: Optional[float]) -> Dict[str, Any]:
    """Apply modifications to quote data"""
    modified_quote = quote_data.copy()
    
    # Apply coverage changes
    if coverage_changes:
        if "coverage_summary" in modified_quote:
            modified_quote["coverage_summary"].update(coverage_changes.get("coverage", {}))
    
    # Apply premium adjustment
    if premium_adjustment and "premium_details" in modified_quote:
        original_premium = modified_quote["premium_details"].get("annual_premium", 0)
        modified_quote["premium_details"]["annual_premium"] = original_premium + premium_adjustment
        modified_quote["premium_details"]["adjustment_applied"] = premium_adjustment
    
    return modified_quote

def get_available_quote_actions(status: str) -> List[str]:
    """Get available actions based on quote status"""
    actions_map = {
        "generated": ["deliver", "modify", "cancel"],
        "delivered": ["track_response", "modify", "resend"],
        "client_accepted": ["bind_policy", "generate_policy"],
        "client_rejected": ["analyze_rejection", "create_new_quote"],
        "expired": ["regenerate", "extend_expiration"]
    }
    return actions_map.get(status, [])

async def deliver_quote_via_email(quote_id: str, quote_data: Dict[str, Any], recipient_email: str, delivered_by: str, message: Optional[str] = None):
    """Background task to deliver quote via email"""
    try:
        # This would integrate with email service
        logger.info(f"Email delivery simulated for quote {quote_id} to {recipient_email}")
        
        # Update delivery status in quote record
        if quote_id in quote_storage:
            quote_storage[quote_id]["last_delivery"] = {
                "method": "email",
                "recipient": recipient_email,
                "delivered_by": delivered_by,
                "delivery_date": datetime.utcnow().isoformat(),
                "status": "sent"
            }
        
    except Exception as e:
        logger.error(f"Error delivering quote via email: {str(e)}")

async def regenerate_guidewire_quote(work_item_id: int, coverage_changes: Dict[str, Any], new_quote_id: str):
    """Background task to regenerate quote in Guidewire with modifications"""
    try:
        # This would make API calls to Guidewire to update coverage and regenerate quote
        logger.info(f"Guidewire quote regeneration simulated for work item {work_item_id}")
        
    except Exception as e:
        logger.error(f"Error regenerating Guidewire quote: {str(e)}")

# Export router
__all__ = ["quote_router"]