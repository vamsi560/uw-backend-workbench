
import logging
from typing import List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
import uuid
import json
from pydantic import BaseModel
from dateutil import parser as date_parser
from database import get_db, Submission, WorkItem, RiskAssessment, Comment, User, WorkItemHistory, WorkItemStatus, WorkItemPriority, CompanySize, Underwriter, SubmissionMessage, create_tables, SubmissionStatus, SubmissionHistory, HistoryAction, QuoteDocument, DocumentType, DocumentStatus
from llm_service import llm_service
from models import (
    EmailIntakePayload, EmailIntakeResponse, LogicAppsEmailPayload,
    SubmissionResponse, SubmissionConfirmRequest, 
    SubmissionConfirmResponse, ErrorResponse,
    WorkItemSummary, WorkItemDetail, WorkItemListResponse,
    EnhancedPollingResponse, RiskCategories,
    WorkItemStatusEnum, WorkItemPriorityEnum, CompanySizeEnum
)
from config import settings
from logging_config import configure_logging, get_logger

# Configure logging first
configure_logging()
logger = get_logger(__name__)

# Use full file parser with all dependencies
try:
    from file_parsers import parse_attachments
    logger.info("Using full file parser with all capabilities")
except ImportError:
    from file_parsers_minimal import parse_attachments
    logger.info("Falling back to minimal file parser (limited functionality)")

# Helper function to parse extracted fields
def _parse_extracted_fields(extracted_fields):
    """Parse extracted fields from JSON string or return dict as-is"""
    if isinstance(extracted_fields, str):
        try:
            return json.loads(extracted_fields)
        except json.JSONDecodeError:
            logger.warning("Failed to parse extracted_fields JSON string")
            return {}
    elif isinstance(extracted_fields, dict):
        return extracted_fields
    else:
        return {}

# Create FastAPI app
app = FastAPI(
    title="Underwriting Workbench API",
    description="Backend API for insurance submission processing",
    version="1.0.0"
)

# Configure CORS for Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=settings.cors_credentials,
    allow_methods=["*"] if settings.cors_methods == "*" else settings.cors_methods.split(","),
    allow_headers=["*"] if settings.cors_headers == "*" else settings.cors_headers.split(","),
)

# Guidewire integration removed - will be implemented fresh

# Include underwriting workflow APIs
try:
    from underwriting_workflow import underwriting_router
    app.include_router(underwriting_router)
    logger.info("Underwriting workflow APIs loaded")
except Exception as e:
    logger.error(f"Failed to load underwriting workflow APIs: {str(e)}")

# Include risk assessment APIs
try:
    from risk_assessment_api import risk_router
    app.include_router(risk_router)
    logger.info("Risk assessment APIs loaded")
except Exception as e:
    logger.error(f"Failed to load risk assessment APIs: {str(e)}")

# Include document management APIs
try:
    from document_management import document_router
    app.include_router(document_router)
    logger.info("Document management APIs loaded")
except Exception as e:
    logger.error(f"Failed to load document management APIs: {str(e)}")

# Include user management and notification APIs
try:
    from user_notification_system import user_router, notification_router
    app.include_router(user_router)
    app.include_router(notification_router)
    logger.info("User management and notification APIs loaded")
except Exception as e:
    logger.error(f"Failed to load user management and notification APIs: {str(e)}")

# Include system dashboard APIs
try:
    from system_dashboard import dashboard_router
    app.include_router(dashboard_router)
    logger.info("System dashboard APIs loaded")
except Exception as e:
    logger.error(f"Failed to load system dashboard APIs: {str(e)}")

# Guidewire sync service removed - will be implemented fresh

# Include quote management APIs
try:
    from quote_management import quote_router
    app.include_router(quote_router)
    logger.info("Quote management APIs loaded")
except Exception as e:
    logger.error(f"Failed to load quote management APIs: {str(e)}")

# Guidewire lookup APIs removed - will be implemented fresh

# Test endpoint to verify deployment
@app.get("/api/test/deployment")
async def test_deployment():
    """Test endpoint to verify latest deployment"""
    routes = [str(route.path) for route in app.routes if hasattr(route, 'path')]
    guidewire_routes = [r for r in routes if '/api/guidewire' in r]
    underwriting_routes = [r for r in routes if '/api/underwriting' in r]
    risk_routes = [r for r in routes if '/api/risk' in r]
    document_routes = [r for r in routes if '/api/documents' in r]
    user_routes = [r for r in routes if '/api/users' in r or '/api/notifications' in r]
    dashboard_routes = [r for r in routes if '/api/dashboard' in r]
    
    return {
        "message": "Complete underwriting workbench deployment active",
        "timestamp": datetime.now().isoformat(),
        "total_routes": len(routes),
        "api_modules": {
            "guidewire_apis": {
                "count": len(guidewire_routes),
                "routes": guidewire_routes[:5]  # Show first 5
            },
            "underwriting_workflow": {
                "count": len(underwriting_routes),
                "routes": underwriting_routes[:5]
            },
            "risk_assessment": {
                "count": len(risk_routes),
                "routes": risk_routes[:5]
            },
            "document_management": {
                "count": len(document_routes),
                "routes": document_routes[:5]
            },
            "user_notifications": {
                "count": len(user_routes),
                "routes": user_routes[:5]
            },
            "system_dashboard": {
                "count": len(dashboard_routes),
                "routes": dashboard_routes[:5]
            },
            "sync_service": {
                "count": len([r for r in routes if '/api/guidewire-sync' in r]),
                "routes": [r for r in routes if '/api/guidewire-sync' in r][:5]
            },
            "quote_management": {
                "count": len([r for r in routes if '/api/quotes' in r]),
                "routes": [r for r in routes if '/api/quotes' in r][:5]
            }
        },
        "features_loaded": {
            "guidewire_integration": len(guidewire_routes) > 0,
            "underwriting_workflow": len(underwriting_routes) > 0,
            "risk_assessment": len(risk_routes) > 0,
            "document_management": len(document_routes) > 0,
            "user_management": len(user_routes) > 0,
            "system_dashboard": len(dashboard_routes) > 0,
            "sync_service": len([r for r in routes if '/api/guidewire-sync' in r]) > 0,
            "quote_management": len([r for r in routes if '/api/quotes' in r]) > 0
        }
    }

# Pydantic model for audit trail response
class SubmissionHistoryOut(BaseModel):
    id: int
    submission_id: int
    old_status: str
    new_status: str
    changed_by: str
    reason: str | None = None
    timestamp: datetime

# Pydantic model for status update request
class SubmissionStatusUpdateRequest(BaseModel):
    new_status: str
    changed_by: str
    reason: str | None = None

# Allowed status transitions (real-world underwriting)
ALLOWED_STATUS_TRANSITIONS = {
    SubmissionStatus.NEW.value: [SubmissionStatus.INTAKE.value, SubmissionStatus.WITHDRAWN.value],
    SubmissionStatus.INTAKE.value: [SubmissionStatus.IN_REVIEW.value, SubmissionStatus.WITHDRAWN.value],
    SubmissionStatus.IN_REVIEW.value: [SubmissionStatus.ASSIGNED.value, SubmissionStatus.QUOTED.value, SubmissionStatus.DECLINED.value, SubmissionStatus.WITHDRAWN.value],
    SubmissionStatus.ASSIGNED.value: [SubmissionStatus.QUOTED.value, SubmissionStatus.DECLINED.value, SubmissionStatus.WITHDRAWN.value],
    SubmissionStatus.QUOTED.value: [SubmissionStatus.BOUND.value, SubmissionStatus.DECLINED.value, SubmissionStatus.WITHDRAWN.value],
    SubmissionStatus.BOUND.value: [SubmissionStatus.COMPLETED.value],
    SubmissionStatus.DECLINED.value: [],
    SubmissionStatus.WITHDRAWN.value: [],
    SubmissionStatus.COMPLETED.value: [],
}

# Duplicate-free polling endpoint for submissions
class SubmissionOut(BaseModel):
    id: int
    subject: str
    from_email: str | None = None
    created_at: datetime
    status: str

# Endpoint to fetch audit trail for a submission
@app.get("/api/submissions/{submission_id}/history", response_model=List[SubmissionHistoryOut])
async def get_submission_history(submission_id: int, db: Session = Depends(get_db)):
    history = db.query(SubmissionHistory).filter(SubmissionHistory.submission_id == submission_id).order_by(SubmissionHistory.timestamp.asc()).all()
    return [
        SubmissionHistoryOut(
            id=h.id,
            submission_id=h.submission_id,
            old_status=h.old_status.value if hasattr(h.old_status, 'value') else str(h.old_status),
            new_status=h.new_status.value if hasattr(h.new_status, 'value') else str(h.new_status),
            changed_by=h.changed_by,
            reason=h.reason,
            timestamp=h.timestamp
        )
        for h in history
    ]

# Endpoint to update submission status with validation and audit logging
@app.put("/api/submissions/{submission_id}/status")
async def update_submission_status(
    submission_id: int,
    req: SubmissionStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    old_status = submission.status.value if hasattr(submission.status, 'value') else str(submission.status)
    new_status = req.new_status

    # Validate transition
    allowed = ALLOWED_STATUS_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status transition from {old_status} to {new_status}")

    # Update status
    submission.status = SubmissionStatus(new_status)
    db.add(submission)

    # Audit log
    audit = SubmissionHistory(
        submission_id=submission.id,
        old_status=SubmissionStatus(old_status),
        new_status=SubmissionStatus(new_status),
        changed_by=req.changed_by,
        reason=req.reason,
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()
    db.refresh(submission)
    db.refresh(audit)

    return {
        "submission_id": submission.id,
        "old_status": old_status,
        "new_status": new_status,
        "changed_by": req.changed_by,
        "reason": req.reason,
        "audit_id": audit.id,
        "timestamp": audit.timestamp.isoformat() + "Z"
    }

# Generate a concise summary for a submission (used by Summarize button)
@app.post("/api/submissions/{submission_id}/summarize")
async def summarize_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Compose text from submission fields
    subject = getattr(submission, "subject", None)
    body_text = getattr(submission, "body_text", None)
    extracted_fields = getattr(submission, "extracted_fields", None)

    summary = llm_service.summarize_submission(subject, body_text, extracted_fields)
    return {
        "submission_id": submission_id,
        "summary": summary
    }

@app.get("/api/workitems", response_model=List[SubmissionOut])
def get_workitems(
    since_id: int = None,
    since: datetime = None,
    db: Session = Depends(get_db)
):
    # Query WorkItem table with joined Submission data
    query = db.query(WorkItem).join(Submission, WorkItem.submission_id == Submission.id)

    if since_id is not None:
        query = query.filter(WorkItem.id > since_id)
    elif since is not None:
        query = query.filter(WorkItem.created_at > since)
    else:
        # No filters, return 20 most recent
        query = query.order_by(WorkItem.created_at.desc()).limit(20)

    # Always order by created_at ASC for output
    results = query.order_by(WorkItem.created_at.asc()).all()

    # Remove duplicates by id (shouldn't be needed if id is PK, but for safety)
    seen = set()
    unique_workitems = []
    for wi in results:
        if wi.id not in seen:
            seen.add(wi.id)
            unique_workitems.append(wi)

    return [
        SubmissionOut(
            id=wi.id,
            subject=wi.submission.subject,
            from_email=getattr(wi.submission, "from_email", None) or wi.submission.sender_email,
            created_at=wi.created_at,
            status=wi.status.value if wi.status else "pending"
        )
        for wi in unique_workitems
    ]

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Underwriting Workbench API")
    create_tables()
    logger.info("Database tables created successfully")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


@app.post("/api/email/intake", response_model=EmailIntakeResponse)
async def email_intake(
    request: EmailIntakePayload,
    db: Session = Depends(get_db)
):
    """
    Process incoming email with attachments and extract insurance data
    """
    # Extract sender email from any available field (Logic Apps compatibility)
    sender_email = request.get_sender_email
    
    # Parse received_at timestamp if provided
    received_at_dt = None
    if request.received_at:
        try:
            received_at_dt = date_parser.isoparse(request.received_at.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Could not parse received_at timestamp: {request.received_at}, error: {e}")
    
    logger.info("Processing email intake", subject=request.subject, sender_email=sender_email)
    
    try:
        # Check for duplicate submissions (same subject and sender within last hour)
        from datetime import timedelta
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        existing_submission = db.query(Submission).filter(
            Submission.subject == (request.subject or "No subject"),
            Submission.sender_email == sender_email,
            Submission.created_at > one_hour_ago
        ).first()
        
        if existing_submission:
            logger.warning("Duplicate submission detected", 
                         subject=request.subject, 
                         sender_email=sender_email,
                         existing_ref=existing_submission.submission_ref)
            
            # Return existing submission instead of creating new one
            return EmailIntakeResponse(
                submission_ref=str(existing_submission.submission_ref),
                submission_id=existing_submission.submission_id,
                status="duplicate",
                message="Duplicate submission detected - returning existing submission"
            )
        
        # Generate unique submission reference
        submission_ref = str(uuid.uuid4())
        
        # Parse attachments if any (supports both formats)
        attachment_text = ""
        if request.attachments:
            logger.info("Processing attachments", count=len(request.attachments))
            # Filter out attachments with missing data, support both formats
            valid_attachments = []
            for att in request.attachments:
                filename = att.get_filename
                content_base64 = att.get_content_base64
                if filename and content_base64:
                    valid_attachments.append({
                        "filename": filename, 
                        "contentBase64": content_base64
                    })
            
            if valid_attachments:
                attachment_text = parse_attachments(valid_attachments, settings.upload_dir)
        
        # Process body content (handle HTML if present)
        processed_body = str(request.body) if request.body else 'No body content'
        if '<html>' in processed_body.lower() or '<body>' in processed_body.lower():
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(processed_body, 'html.parser')
                text_content = soup.get_text(strip=True, separator=' ')
                if text_content and text_content.strip():
                    processed_body = text_content
                    logger.info("HTML content converted to text", 
                               html_length=len(str(request.body)), 
                               text_length=len(text_content))
            except Exception as html_error:
                logger.warning("HTML processing failed, using original content", 
                              error=str(html_error))
        
        # Combine email body and attachment text with null safety
        combined_text = f"Email Subject: {str(request.subject) if request.subject else 'No subject'}\n"
        combined_text += f"From: {str(sender_email) if sender_email else 'Unknown sender'}\n"
        combined_text += f"Email Body:\n{processed_body}\n\n"
        
        if attachment_text is not None:
            # Ensure attachment_text is always treated as string
            attachment_content = str(attachment_text) if not isinstance(attachment_text, str) else attachment_text
            combined_text += f"Attachment Content:\n{attachment_content}"

        
        logger.info("Extracting structured data with LLM")
        
        # Extract structured data using LLM
        extracted_data = llm_service.extract_insurance_data(combined_text)
        
        # Generate unique submission ID with timestamp
        next_submission_id = f"SUB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Prepare safe field lengths for database (VARCHAR(255) constraints)
        safe_subject = (request.subject or "No subject")[:240]  # Truncate subject if too long
        safe_sender = str(sender_email)[:240]  # Truncate email if too long
        
        # Handle body_text safely - must fit database VARCHAR(255) constraint
        safe_body = processed_body[:240] + "..." if len(processed_body) > 240 else processed_body
        
        # Create submission record directly with safe field lengths
        submission = Submission(
            submission_id=next_submission_id,
            submission_ref=submission_ref,
            subject=safe_subject,
            sender_email=safe_sender,
            body_text=safe_body,
            attachment_content=str(attachment_text) if attachment_text else None,  # Store decoded attachment content
            extracted_fields=extracted_data,
            received_at=received_at_dt,  # Store original email received timestamp
            task_status="pending"
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        # Create corresponding work item with enhanced fields
        work_item = WorkItem(
            submission_id=submission.id,
            title=request.subject or "Email Submission",
            description=f"Email from {sender_email}",
            status=WorkItemStatus.PENDING,
            priority=WorkItemPriority.MEDIUM,
            assigned_to=None  # Will be assigned later
        )
        
        # Apply business rules and validation
        from business_rules import CyberInsuranceValidator, WorkflowEngine
        
        # Run comprehensive validation
        validation_status, missing_fields, rejection_reason = CyberInsuranceValidator.validate_submission(extracted_data or {})
        
        # Calculate risk priority
        risk_priority = CyberInsuranceValidator.calculate_risk_priority(extracted_data or {})
        
        # Assign underwriter based on business rules
        assigned_underwriter = None
        if validation_status == "Complete":
            assigned_underwriter = CyberInsuranceValidator.assign_underwriter(extracted_data or {})
        
        # Generate initial risk assessment
        risk_categories = CyberInsuranceValidator.generate_risk_categories(extracted_data or {})
        overall_risk_score = sum(risk_categories.values()) / len(risk_categories)
        
        # Extract cyber insurance specific data from LLM results
        if extracted_data and isinstance(extracted_data, dict):
            work_item.industry = extracted_data.get('industry')
            work_item.policy_type = extracted_data.get('policy_type') or extracted_data.get('coverage_type')
            
            # Use business rules parser for coverage amount
            work_item.coverage_amount = CyberInsuranceValidator._parse_coverage_amount(
                extracted_data.get('coverage_amount') or extracted_data.get('policy_limit') or ''
            )
            
            # Set company size if available
            company_size = extracted_data.get('company_size')
            if company_size:
                try:
                    work_item.company_size = CompanySize(company_size)
                except ValueError:
                    # Try mapping common variations
                    size_mapping = {
                        'small': CompanySize.SMALL,
                        'medium': CompanySize.MEDIUM,
                        'large': CompanySize.LARGE,
                        'enterprise': CompanySize.ENTERPRISE,
                        'startup': CompanySize.SMALL,
                        'sme': CompanySize.MEDIUM,
                        'multinational': CompanySize.ENTERPRISE
                    }
                    work_item.company_size = size_mapping.get(str(company_size).lower() if company_size else "")
        
        # Apply validation results to work item
        if validation_status == "Complete":
            work_item.status = WorkItemStatus.PENDING
        elif validation_status == "Incomplete":
            work_item.status = WorkItemStatus.PENDING
            work_item.description += f"\n\nMissing fields: {', '.join(str(field) for field in missing_fields)}"
        elif validation_status == "Rejected":
            work_item.status = WorkItemStatus.REJECTED
            work_item.description += f"\n\nRejection reason: {str(rejection_reason) if rejection_reason else ''}"
        
        # Set priority based on risk calculation
        try:
            work_item.priority = WorkItemPriority(risk_priority)
        except ValueError:
            work_item.priority = WorkItemPriority.MEDIUM
        
        # Set assigned underwriter
        work_item.assigned_to = assigned_underwriter
        
        # Set risk data
        work_item.risk_score = overall_risk_score
        work_item.risk_categories = risk_categories
        
        db.add(work_item)
        db.flush()  # Get ID before commit
        
        # Create initial risk assessment if we have risk data
        if risk_categories and overall_risk_score > 0:
            risk_assessment = RiskAssessment(
                work_item_id=work_item.id,
                overall_risk_score=overall_risk_score,
                risk_categories=risk_categories,
                assessed_by="System",
                assessed_by_name="System"
            )
            db.add(risk_assessment)
        
        # Create history entry for validation results
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action=HistoryAction.CREATED,
            performed_by="System",
            performed_by_name="System",
            timestamp=datetime.utcnow(),
            details={
                "validation_status": validation_status,
                "missing_fields": missing_fields,
                "rejection_reason": rejection_reason,
                "risk_priority": risk_priority,
                "assigned_underwriter": assigned_underwriter
            }
        )
        db.add(history_entry)
        
        db.commit()
        db.refresh(work_item)
        
        logger.info("Submission and work item created", 
                   submission_id=submission.submission_id, 
                   work_item_id=work_item.id,
                   submission_ref=submission_ref,
                   validation_status=validation_status,
                   risk_priority=risk_priority)
        
        # Guidewire integration will be implemented fresh
        logger.info("Work item created successfully", 
                   work_item_id=work_item.id,
                   validation_status=validation_status)
        
        # Step 1: Create Guidewire Account and Submission when work item is created
        guidewire_success = False
        
        try:
            from guidewire_integration import guidewire_integration
            
            logger.info("Creating Guidewire account and submission", 
                       work_item_id=work_item.id,
                       validation_status=validation_status)
            
            # Call our new clean Guidewire integration
            guidewire_result = guidewire_integration.create_account_and_submission(extracted_data or {})
            
            if guidewire_result["success"]:
                # Update work item with both internal IDs and human-readable numbers
                if guidewire_result.get("account_id"):
                    work_item.guidewire_account_id = guidewire_result["account_id"]
                if guidewire_result.get("job_id"):
                    work_item.guidewire_job_id = guidewire_result["job_id"]
                if guidewire_result.get("account_number"):
                    work_item.guidewire_account_number = guidewire_result["account_number"]
                if guidewire_result.get("job_number"):
                    work_item.guidewire_job_number = guidewire_result["job_number"]
                
                db.commit()
                guidewire_success = True
                
                logger.info("Guidewire account and submission created successfully",
                          work_item_id=work_item.id,
                          account_id=guidewire_result.get("account_id"),
                          job_id=guidewire_result.get("job_id"))
                
                # Add success to work item history
                guidewire_history = WorkItemHistory(
                    work_item_id=work_item.id,
                    action=HistoryAction.UPDATED,
                    performed_by="System",
                    performed_by_name="System",
                    timestamp=datetime.utcnow(),
                    details={
                        "guidewire_account_id": guidewire_result.get("account_id"),
                        "guidewire_job_id": guidewire_result.get("job_id"),
                        "status": "account_and_submission_created"
                    }
                )
                db.add(guidewire_history)
                db.commit()
            
            else:
                logger.error("Failed to create Guidewire account and submission",
                           work_item_id=work_item.id,
                           error=guidewire_result.get("error"),
                           message=guidewire_result.get("message"))
                
                # Add failure to work item history
                guidewire_history = WorkItemHistory(
                    work_item_id=work_item.id,
                    action=HistoryAction.UPDATED,
                    performed_by="System",
                    performed_by_name="System",
                    timestamp=datetime.utcnow(),
                    details={
                        "error": guidewire_result.get("error"),
                        "message": guidewire_result.get("message"),
                        "status": "failed_to_create_account_submission"
                    }
                )
                db.add(guidewire_history)
                db.commit()
                
        except Exception as gw_error:
            logger.error("Exception during Guidewire account and submission creation",
                       work_item_id=work_item.id,
                       error=str(gw_error),
                       exc_info=True)
            
            # Add exception to work item history
            guidewire_history = WorkItemHistory(
                work_item_id=work_item.id,
                action=HistoryAction.UPDATED,
                performed_by="System",
                performed_by_name="System",
                timestamp=datetime.utcnow(),
                details={
                    "error": "Exception during Guidewire integration",
                    "message": str(gw_error),
                    "status": "exception_occurred"
                }
            )
            db.add(guidewire_history)
            db.commit()
        
        # Broadcast new work item to all connected WebSocket clients with enhanced data
        await broadcast_new_workitem(work_item, submission, {
            "validation_status": validation_status,
            "risk_score": overall_risk_score,
            "assigned_underwriter": assigned_underwriter,
            "guidewire_success": guidewire_success
        })
        
        # Enhanced response message with Guidewire sync status
        if guidewire_success:
            response_message = f"Email processed successfully. Work item created and synced to Guidewire PolicyCenter."
        else:
            response_message = f"Email processed successfully and work item created. Guidewire sync: {'skipped (validation failed)' if validation_status == 'Rejected' else 'failed (check logs)'}"
        
        return EmailIntakeResponse(
            submission_ref=str(submission_ref),
            submission_id=submission.submission_id,
            status="success",
            message=response_message
        )
        
    except Exception as e:
        logger.error("Error processing email intake", error=str(e), exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing email: {str(e)}"
        )


@app.post("/api/logicapps/email/intake", response_model=EmailIntakeResponse)
async def logic_apps_email_intake(
    request: LogicAppsEmailPayload,
    db: Session = Depends(get_db)
):
    """
    Process incoming email from Logic Apps with native Logic Apps format
    """
    logger.info(f"Processing Logic Apps email intake: subject={str(request.safe_subject)}, sender_email={str(request.safe_from)}")
    
    try:
        # Parse received_at timestamp with safe string conversion, supporting both field names
        received_at_dt = None
        received_timestamp = request.received_at or request.receivedDateTime
        if received_timestamp:
            try:
                received_at_str = str(received_timestamp)
                received_at_dt = date_parser.isoparse(received_at_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Could not parse received timestamp: {received_timestamp}, error: {e}")
        
        # Check for duplicate submissions (same subject and sender within last hour)
        from datetime import timedelta
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        existing_submission = db.query(Submission).filter(
            Submission.subject == str(request.safe_subject),
            Submission.sender_email == str(request.safe_from),
            Submission.created_at > one_hour_ago
        ).first()
        
        if existing_submission:
            logger.warning(f"Duplicate submission detected: subject={str(request.safe_subject)}, sender_email={str(request.safe_from)}, existing_ref={str(existing_submission.submission_ref)}")
            
            return EmailIntakeResponse(
                submission_ref=str(existing_submission.submission_ref),
                submission_id=existing_submission.submission_id,
                status="duplicate",
                message="Duplicate submission detected - returning existing submission"
            )
        
        # Generate unique submission reference
        submission_ref = str(uuid.uuid4())
        
        # Parse attachments in Logic Apps format with safe string handling
        attachment_text = ""
        if hasattr(request, 'attachments') and request.attachments:
            logger.info("Processing Logic Apps attachments", count=len(request.attachments))
            valid_attachments = []
            for att in request.attachments:
                # Safely get attachment properties with string conversion
                att_name = str(att.name) if hasattr(att, 'name') and att.name is not None else None
                att_content = str(att.contentBytes) if hasattr(att, 'contentBytes') and att.contentBytes is not None else None
                
                if att_name and att_content:
                    valid_attachments.append({
                        "filename": att_name, 
                        "contentBase64": att_content
                    })
            
            if valid_attachments:
                attachment_text = parse_attachments(valid_attachments, settings.upload_dir)
                # Ensure attachment_text is always a string
                attachment_text = str(attachment_text) if attachment_text is not None else ""
        
        # Process body content (handle HTML and potential base64 encoding)
        safe_body = str(request.safe_body)
        decoded_body_for_llm = safe_body  # Default fallback
        
        # First, check if body is base64 encoded (common in some Logic Apps scenarios)
        is_base64_encoded = False
        try:
            import base64
            import re
            # Simple heuristic: if it's a long string with only base64 chars and no HTML tags
            if len(safe_body) > 100 and re.match(r'^[A-Za-z0-9+/=]+$', safe_body) and '<' not in safe_body:
                decoded_body = base64.b64decode(safe_body).decode('utf-8')
                decoded_body_for_llm = decoded_body
                is_base64_encoded = True
                logger.info("Body decoded from base64 for processing", 
                           original_length=len(safe_body), 
                           decoded_length=len(decoded_body))
        except Exception as decode_error:
            logger.debug("Body is not base64 encoded", error=str(decode_error))
        
        # Process HTML content if present (whether base64 decoded or original)
        if '<html>' in decoded_body_for_llm.lower() or '<body>' in decoded_body_for_llm.lower():
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(decoded_body_for_llm, 'html.parser')
                # Extract text content, removing HTML tags
                text_content = soup.get_text(strip=True, separator=' ')
                if text_content and text_content.strip():
                    decoded_body_for_llm = text_content
                    logger.info("HTML content converted to text", 
                               html_length=len(str(request.safe_body)), 
                               text_length=len(text_content))
                else:
                    # If no meaningful text extracted, keep original
                    decoded_body_for_llm = "Email body contains HTML with no readable text content"
            except Exception as html_error:
                logger.warning("HTML processing failed, using original content", 
                              error=str(html_error))
        
        # Combine email body and attachment text using decoded content
        # Extract company name from subject if available
        subject_text = str(request.safe_subject)
        company_from_subject = ""
        if "–" in subject_text or "-" in subject_text:
            # Try to extract company name after dash or em-dash
            parts = subject_text.replace("–", "-").split("-")
            if len(parts) > 1:
                company_from_subject = parts[-1].strip()
        
        combined_text = f"Email Subject: {subject_text}\n"
        combined_text += f"From: {str(request.safe_from)}\n"
        if company_from_subject:
            combined_text += f"Company Name (from subject): {company_from_subject}\n"
        combined_text += f"Email Body:\n{decoded_body_for_llm}\n\n"
        
        if attachment_text:
            combined_text += f"Attachment Content:\n{attachment_text}"
        else:
            combined_text += "Note: This appears to be a new insurance submission. Please extract any available information and infer reasonable defaults based on context."
        
        logger.info("Extracting structured data with LLM using decoded content")
        
        # Extract structured data using LLM with decoded content
        extracted_data = llm_service.extract_insurance_data(combined_text)
        
        # Generate unique submission ID with timestamp
        next_submission_id = f"SUB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Prepare body_text for database storage with safe length handling
        # Truncate the decoded content for database storage
        if decoded_body_for_llm != safe_body:  # Successfully decoded
            body_text = decoded_body_for_llm[:240] + "..." if len(decoded_body_for_llm) > 240 else decoded_body_for_llm
        else:  # Decoding failed, use original but truncate
            body_text = safe_body[:240] + "..." if len(safe_body) > 240 else safe_body
        
        # Create submission record with safe field lengths (VARCHAR(255) constraints)
        submission = Submission(
            submission_id=next_submission_id,
            submission_ref=submission_ref,
            subject=str(request.safe_subject)[:240],  # Truncate subject to fit database
            sender_email=str(request.safe_from)[:240],  # Truncate email to fit database  
            body_text=body_text,
            attachment_content=attachment_text,  # Store decoded attachment content
            extracted_fields=extracted_data,
            received_at=received_at_dt,
            task_status="pending"
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        # Apply business rules and validation (same as regular email intake)
        from business_rules import CyberInsuranceValidator, WorkflowEngine
        
        # Run comprehensive validation
        validation_status, missing_fields, rejection_reason = CyberInsuranceValidator.validate_submission(extracted_data or {})
        
        # Calculate risk priority
        risk_priority = CyberInsuranceValidator.calculate_risk_priority(extracted_data or {})
        
        # Assign underwriter based on business rules
        assigned_underwriter = None
        if validation_status == "Complete":
            assigned_underwriter = CyberInsuranceValidator.assign_underwriter(extracted_data or {})
        
        # Generate initial risk assessment
        risk_categories = CyberInsuranceValidator.generate_risk_categories(extracted_data or {})
        overall_risk_score = sum(risk_categories.values()) / len(risk_categories)
        
        # Create work item with business rule results
        work_item = WorkItem(
            submission_id=submission.id,
            title=str(request.safe_subject),
            description=f"Email from {str(request.safe_from)}",
            status=WorkItemStatus.PENDING,
            priority=WorkItemPriority.MEDIUM
        )
        
        # Extract cyber insurance specific data from LLM results with safe handling
        if extracted_data and isinstance(extracted_data, dict):
            # Safely get string values from extracted data
            industry_raw = extracted_data.get('industry')
            work_item.industry = str(industry_raw) if industry_raw is not None else None
            
            policy_type_raw = extracted_data.get('policy_type') or extracted_data.get('coverage_type')
            work_item.policy_type = str(policy_type_raw) if policy_type_raw is not None else None
            
            # Use business rules parser for coverage amount
            coverage_raw = extracted_data.get('coverage_amount') or extracted_data.get('policy_limit')
            work_item.coverage_amount = CyberInsuranceValidator._parse_coverage_amount(coverage_raw)
            
            # Set company size if available with safe string handling
            company_size_raw = extracted_data.get('company_size')
            if company_size_raw is not None:
                try:
                    work_item.company_size = CompanySize(str(company_size_raw))
                except ValueError:
                    # Try mapping common variations with safe string conversion
                    size_mapping = {
                        'small': CompanySize.SMALL,
                        'medium': CompanySize.MEDIUM,
                        'large': CompanySize.LARGE,
                        'enterprise': CompanySize.ENTERPRISE,
                        'startup': CompanySize.SMALL,
                        'sme': CompanySize.MEDIUM,
                        'multinational': CompanySize.ENTERPRISE
                    }
                    company_size_str = str(company_size_raw).lower() if company_size_raw else ""
                    work_item.company_size = size_mapping.get(company_size_str)
        
        # Apply validation results to work item
        if validation_status == "Complete":
            work_item.status = WorkItemStatus.PENDING
        elif validation_status == "Incomplete":
            work_item.status = WorkItemStatus.PENDING
            work_item.description += f"\n\nMissing fields: {', '.join(str(field) for field in missing_fields)}"
        elif validation_status == "Rejected":
            work_item.status = WorkItemStatus.REJECTED
            work_item.description += f"\n\nRejection reason: {str(rejection_reason) if rejection_reason else ''}"
        
        # Set priority based on risk calculation with safe handling
        try:
            work_item.priority = WorkItemPriority(str(risk_priority)) if risk_priority else WorkItemPriority.MEDIUM
        except ValueError:
            work_item.priority = WorkItemPriority.MEDIUM
        
        # Set assigned underwriter with safe string handling
        work_item.assigned_to = str(assigned_underwriter) if assigned_underwriter is not None else None
        
        # Set risk data with safe numeric handling
        work_item.risk_score = float(overall_risk_score) if overall_risk_score is not None else None
        work_item.risk_categories = risk_categories
        
        db.add(work_item)
        db.flush()  # Get ID before commit
        
        # Create initial risk assessment if we have risk data
        if risk_categories and overall_risk_score > 0:
            risk_assessment = RiskAssessment(
                work_item_id=work_item.id,
                overall_risk_score=float(overall_risk_score),
                risk_categories=risk_categories,
                assessed_by="System",
                assessed_by_name="System"
            )
            db.add(risk_assessment)
        
        # Create history entry for validation results with safe string handling
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action=HistoryAction.CREATED,
            performed_by="System",
            performed_by_name="System",
            timestamp=datetime.utcnow(),
            details={
                "validation_status": str(validation_status) if validation_status else "Unknown",
                "missing_fields": [str(field) for field in (missing_fields or [])],
                "rejection_reason": str(rejection_reason) if rejection_reason else None,
                "risk_priority": str(risk_priority) if risk_priority else None,
                "assigned_underwriter": str(assigned_underwriter) if assigned_underwriter else None
            }
        )
        db.add(history_entry)
        
        db.commit()
        db.refresh(work_item)
        
        logger.info("Logic Apps submission and work item created", 
                   submission_id=submission.submission_id, 
                   work_item_id=work_item.id,
                   submission_ref=submission_ref)
        
        # Step 1: Create Guidewire Account and Submission when work item is created (Logic Apps)
        guidewire_success = False
        
        try:
            from guidewire_integration import guidewire_integration
            
            logger.info("Creating Guidewire account and submission (Logic Apps)", 
                       work_item_id=work_item.id,
                       validation_status=validation_status)
            
            # Call our new clean Guidewire integration
            guidewire_result = guidewire_integration.create_account_and_submission(extracted_data or {})
            
            if guidewire_result["success"]:
                # Update work item with Guidewire IDs
                if guidewire_result.get("account_id"):
                    work_item.guidewire_account_id = guidewire_result["account_id"]
                if guidewire_result.get("job_id"):
                    work_item.guidewire_job_id = guidewire_result["job_id"]
                
                db.commit()
                guidewire_success = True
                
                logger.info("Guidewire account and submission created successfully (Logic Apps)",
                          work_item_id=work_item.id,
                          account_id=guidewire_result.get("account_id"),
                          job_id=guidewire_result.get("job_id"))
                
                # Add success to work item history
                guidewire_history = WorkItemHistory(
                    work_item_id=work_item.id,
                    action=HistoryAction.UPDATED,
                    performed_by="System",
                    performed_by_name="System",
                    timestamp=datetime.utcnow(),
                    details={
                        "guidewire_account_id": guidewire_result.get("account_id"),
                        "guidewire_job_id": guidewire_result.get("job_id"),
                        "status": "account_and_submission_created",
                        "source": "logic_apps"
                    }
                )
                db.add(guidewire_history)
                db.commit()
            
            else:
                logger.error("Failed to create Guidewire account and submission (Logic Apps)",
                           work_item_id=work_item.id,
                           error=guidewire_result.get("error"),
                           message=guidewire_result.get("message"))
                
                # Add failure to work item history
                guidewire_history = WorkItemHistory(
                    work_item_id=work_item.id,
                    action=HistoryAction.UPDATED,
                    performed_by="System",
                    performed_by_name="System",
                    timestamp=datetime.utcnow(),
                    details={
                        "error": guidewire_result.get("error"),
                        "message": guidewire_result.get("message"),
                        "status": "failed_to_create_account_submission",
                        "source": "logic_apps"
                    }
                )
                db.add(guidewire_history)
                db.commit()
                
        except Exception as gw_error:
            logger.error("Exception during Guidewire account and submission creation (Logic Apps)",
                       work_item_id=work_item.id,
                       error=str(gw_error),
                       exc_info=True)
            
            # Add exception to work item history
            guidewire_history = WorkItemHistory(
                work_item_id=work_item.id,
                action=HistoryAction.UPDATED,
                performed_by="System",
                performed_by_name="System",
                timestamp=datetime.utcnow(),
                details={
                    "error": "Exception during Guidewire integration",
                    "message": str(gw_error),
                    "status": "exception_occurred",
                    "source": "logic_apps"
                }
            )
            db.add(guidewire_history)
            db.commit()
        
        return EmailIntakeResponse(
            submission_ref=str(submission_ref),
            submission_id=submission.submission_id,
            status="success",
            message=f"Logic Apps email processed successfully and submission created. Guidewire: {'Success' if guidewire_success else 'Skipped/Failed'}"
        )
        
    except Exception as e:
        logger.error("Error processing Logic Apps email intake", error=str(e), exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Logic Apps email: {str(e)}"
        )


@app.post("/api/submissions/confirm/{submission_ref}", response_model=SubmissionConfirmResponse)
async def confirm_submission(
    submission_ref: str,
    request: SubmissionConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm a submission and assign to underwriter - Updates existing work item instead of creating duplicate
    """
    logger.info("Confirming submission", submission_ref=submission_ref)
    
    try:
        # Get the submission
        submission = db.query(Submission).filter(Submission.submission_ref == submission_ref).first()
        
        if not submission:
            raise HTTPException(
                status_code=404,
                detail="Submission not found"
            )
        
        # Assign underwriter
        assigned_underwriter = assign_underwriter(request.underwriter_email)
        
        # Update submission with assignment
        submission.assigned_to = assigned_underwriter
        submission.task_status = "in_progress"
        
        # Find existing work item for this submission (should already exist from email_intake)
        work_item = db.query(WorkItem).filter(WorkItem.submission_id == submission.id).first()
        
        if work_item:
            # Update existing work item
            work_item.assigned_to = assigned_underwriter
            work_item.status = WorkItemStatus.IN_REVIEW
            work_item.updated_at = datetime.utcnow()
            logger.info("Updated existing work item", work_item_id=work_item.id, assigned_to=assigned_underwriter)
        else:
            # Create work item only if none exists (fallback scenario)
            work_item = WorkItem(
                submission_id=submission.id,
                title=submission.subject or "Confirmed Submission",
                description=f"Email from {submission.sender_email}",
                assigned_to=assigned_underwriter,
                status=WorkItemStatus.IN_REVIEW,
                priority=WorkItemPriority.MEDIUM
            )
            db.add(work_item)
            logger.info("Created new work item (fallback)", assigned_to=assigned_underwriter)
        
        db.commit()
        db.refresh(work_item)
        
        return SubmissionConfirmResponse(
            submission_id=submission.submission_id,
            submission_ref=str(submission.submission_ref),
            work_item_id=work_item.id,
            assigned_to=assigned_underwriter,
            task_status="in_progress"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error confirming submission", submission_ref=submission_ref, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error confirming submission: {str(e)}"
        )


def assign_underwriter(preferred_email: str = None) -> str:
    """
    Simple round-robin underwriter assignment
    In a real system, this would query a database of available underwriters
    """
    if preferred_email:
        return preferred_email
    
    # Simple list of underwriters for round-robin assignment
    underwriters = [
        "underwriter1@company.com",
        "underwriter2@company.com", 
        "underwriter3@company.com"
    ]
    
    # For now, just return the first one
    # In production, you'd implement proper round-robin logic
    return underwriters[0]


def get_or_create_work_item(submission_id: int, db: Session) -> WorkItem:
    """
    Get existing work item for submission or create one if none exists
    Prevents duplicate work item creation
    """
    # Check if work item already exists
    existing_work_item = db.query(WorkItem).filter(WorkItem.submission_id == submission_id).first()
    
    if existing_work_item:
        return existing_work_item
    
    # If no work item exists, this is likely an edge case
    # Log it and return None to let calling code handle appropriately
    logger.warning(f"No work item found for submission_id {submission_id}")
    return None


@app.get("/api/submissions", response_model=List[SubmissionResponse])
async def get_all_submissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all submissions with pagination
    """
    logger.info("Retrieving all submissions", skip=skip, limit=limit)
    
    try:
        submissions = db.query(Submission).offset(skip).limit(limit).all()
        
        result = []
        for submission in submissions:
            result.append(SubmissionResponse(
                id=submission.id,
                submission_id=submission.submission_id,
                submission_ref=str(submission.submission_ref),
                subject=submission.subject,
                sender_email=submission.sender_email,
                body_text=submission.body_text,
                attachment_content=submission.attachment_content,
                extracted_fields=submission.extracted_fields,
                assigned_to=submission.assigned_to,
                task_status=submission.task_status,
                created_at=submission.created_at
            ))
        
        logger.info("Retrieved submissions", count=len(result))
        return result
        
    except Exception as e:
        logger.error("Error retrieving submissions", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving submissions: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Underwriting Workbench API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "email_intake": "/api/email/intake",
            "submissions": "/api/submissions",
            "submission_detail": "/api/submissions/{submission_ref}",
            "confirm_submission": "/api/submissions/confirm/{submission_ref}"
        }
    }


@app.get("/api/debug/database")
async def debug_database(db: Session = Depends(get_db)):
    """Debug endpoint to check database connectivity and data"""
    try:
        # Test basic database connection
        work_item_count = db.query(WorkItem).count()
        submission_count = db.query(Submission).count()
        
        # Get latest work item and submission
        latest_work_item = db.query(WorkItem).order_by(WorkItem.created_at.desc()).first()
        latest_submission = db.query(Submission).order_by(Submission.created_at.desc()).first()
        
        # Get recent work items (last 5)
        recent_work_items = db.query(WorkItem).order_by(WorkItem.created_at.desc()).limit(5).all()
        
        return {
            "database_status": "connected",
            "work_items_count": work_item_count,
            "submissions_count": submission_count,
            "latest_work_item": {
                "id": latest_work_item.id if latest_work_item else None,
                "created_at": latest_work_item.created_at.isoformat() if latest_work_item else None,
                "title": latest_work_item.title if latest_work_item else None,
                "status": latest_work_item.status.value if latest_work_item and latest_work_item.status else None,
                "submission_id": latest_work_item.submission_id if latest_work_item else None
            } if latest_work_item else None,
            "latest_submission": {
                "id": latest_submission.id if latest_submission else None,
                "created_at": latest_submission.created_at.isoformat() if latest_submission else None,
                "subject": latest_submission.subject if latest_submission else None,
                "sender_email": latest_submission.sender_email if latest_submission else None
            } if latest_submission else None,
            "recent_work_items": [
                {
                    "id": wi.id,
                    "title": wi.title,
                    "status": wi.status.value if wi.status else None,
                    "created_at": wi.created_at.isoformat(),
                    "submission_id": wi.submission_id
                }
                for wi in recent_work_items
            ],
            "database_url_host": settings.database_url.split('@')[1].split('/')[0] if '@' in settings.database_url else "hidden"
        }
    except Exception as e:
        return {
            "database_status": "error",
            "error": str(e),
            "database_url_host": settings.database_url.split('@')[1].split('/')[0] if '@' in settings.database_url else "hidden"
        }

@app.get("/api/debug/poll")
async def debug_poll(db: Session = Depends(get_db)):
    """Debug version of work items poll to see what data is returned"""
    try:
        # Replicate the exact polling logic
        query = db.query(WorkItem, Submission).join(
            Submission, WorkItem.submission_id == Submission.id
        ).order_by(WorkItem.created_at.desc())
        
        results = query.limit(20).all()
        
        debug_data = []
        for work_item, submission in results:
            debug_data.append({
                "work_item_id": work_item.id,
                "submission_id": work_item.submission_id,
                "submission_ref": str(submission.submission_ref),
                "title": work_item.title or submission.subject,
                "status": work_item.status.value if work_item.status else "Unknown",
                "created_at": work_item.created_at.isoformat(),
                "assigned_to": work_item.assigned_to,
                "raw_status": work_item.status,
                "has_submission": submission is not None,
                "submission_subject": submission.subject if submission else None
            })
        
        return {
            "total_found": len(debug_data),
            "work_items": debug_data,
            "query_executed": "WorkItem JOIN Submission ORDER BY created_at DESC LIMIT 20"
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.post("/api/debug/test-guidewire-numbers")
async def test_guidewire_numbers_extraction(db: Session = Depends(get_db)):
    """Test extracting human-readable numbers from Guidewire and updating work items"""
    try:
        from guidewire_integration import guidewire_integration
        
        # Test data with unique identifier
        test_data = {
            "company_name": f"Number Test {datetime.utcnow().strftime('%H%M%S')}",
            "business_address": "123 Test Street",
            "business_city": "San Francisco", 
            "business_state": "CA",
            "business_zip": "94105"
        }
        
        logger.info(f"Testing Guidewire number extraction with data: {test_data}")
        
        # Create test submission in Guidewire
        result = guidewire_integration.create_account_and_submission(test_data)
        
        # Get the latest work item to potentially update
        latest_work_item = db.query(WorkItem).order_by(WorkItem.created_at.desc()).first()
        
        response_data = {
            "test_type": "guidewire_number_extraction_test",
            "timestamp": datetime.utcnow().isoformat(),
            "test_data": test_data,
            "guidewire_result": result,
            "latest_work_item": {
                "id": latest_work_item.id if latest_work_item else None,
                "current_account_number": latest_work_item.guidewire_account_number if latest_work_item else None,
                "current_job_number": latest_work_item.guidewire_job_number if latest_work_item else None
            } if latest_work_item else None
        }
        
        if result.get("success"):
            # Check if we extracted human-readable numbers
            account_number = result.get("account_number")
            job_number = result.get("job_number")
            
            if account_number and job_number:
                response_data["extraction_success"] = True
                response_data["extracted_numbers"] = {
                    "account_number": account_number,
                    "job_number": job_number
                }
                
                # Update the latest work item with these numbers as a demonstration
                if latest_work_item:
                    latest_work_item.guidewire_account_number = account_number
                    latest_work_item.guidewire_job_number = job_number
                    db.commit()
                    
                    response_data["updated_work_item"] = {
                        "id": latest_work_item.id,
                        "updated_account_number": account_number,
                        "updated_job_number": job_number,
                        "message": "Work item updated with extracted numbers"
                    }
            else:
                response_data["extraction_success"] = False
                response_data["message"] = "Human-readable numbers not found in Guidewire response"
        else:
            response_data["extraction_success"] = False
            response_data["error"] = result.get("error", "Unknown error")
            
        return response_data
        
    except Exception as e:
        logger.error(f"Error testing Guidewire number extraction: {str(e)}", exc_info=True)
        return {
            "test_type": "guidewire_number_extraction_test",
            "timestamp": datetime.utcnow().isoformat(),
            "extraction_success": False,
            "error": str(e)
        }


@app.put("/api/work-items/{work_item_id}/status")
async def update_work_item_status(
    work_item_id: int,
    status_update: dict,
    db: Session = Depends(get_db)
):
    """Update work item status with business rule validation"""
    from business_rules import WorkflowEngine, MessageService
    
    try:
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        current_status = work_item.status
        new_status = status_update.get("status")
        changed_by = status_update.get("changed_by", "System")
        notes = status_update.get("notes", "")
        
        # Validate status transition using WorkflowEngine
        is_valid, message = WorkflowEngine.validate_status_transition(current_status, new_status)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid status transition: {message}")
        
        # Update the work item
        old_status = work_item.status
        work_item.status = WorkItemStatus(new_status)
        work_item.updated_at = datetime.utcnow()
        
        # Add history entry
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action=f"status_changed_from_{old_status}_to_{new_status}",
            performed_by=changed_by,
            performed_by_name=changed_by,
            timestamp=datetime.utcnow(),
            details={
                "old_status": old_status,
                "new_status": new_status,
                "notes": notes
            }
        )
        db.add(history_entry)
        
        # Handle special status transitions
        if new_status == "assigned" and work_item.assigned_to:
            # Send notification to underwriter
            MessageService.send_assignment_notification(work_item.assigned_to, work_item)
        elif new_status == "rejected":
            # Send rejection notification to broker
            submission = db.query(Submission).filter(Submission.submission_id == work_item.submission_id).first()
            if submission:
                MessageService.send_rejection_notification(submission.sender_email, work_item, notes)
        
        db.commit()
        db.refresh(work_item)
        
        # Broadcast status update (websocket functionality temporarily disabled for deployment)
        logger.info(f"Status update broadcast: work_item {work_item.id} changed from {old_status} to {new_status} by {changed_by}")
        
        return {
            "message": "Status updated successfully",
            "work_item_id": work_item.id,
            "old_status": old_status,
            "new_status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating work item status", work_item_id=work_item_id, error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")







# Step 2: Underwriter Approval Endpoint
@app.post("/api/workitems/{work_item_id}/approve")
async def approve_work_item(
    work_item_id: int, 
    approval_data: dict = None,
    db: Session = Depends(get_db)
):
    """
    Approve a work item and update Guidewire submission status
    This is called when underwriter clicks approve in the portal
    """
    try:
        from guidewire_integration import guidewire_integration
        
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        if not work_item.guidewire_job_id:
            raise HTTPException(status_code=400, detail="Work item not yet synced to Guidewire")
        
        # Extract approval data
        approval_data = approval_data or {}
        underwriter_notes = approval_data.get("notes", "")
        approved_by = approval_data.get("approved_by", "System")
        
        logger.info(f"Approving work item {work_item_id} in Guidewire", 
                   job_id=work_item.guidewire_job_id,
                   approved_by=approved_by)
        
        # Call Guidewire approval API
        result = guidewire_integration.approve_submission(
            job_id=work_item.guidewire_job_id,
            underwriter_notes=underwriter_notes
        )
        
        if result["success"]:
            # Update work item status to approved
            work_item.status = WorkItemStatus.APPROVED
            work_item.updated_at = datetime.utcnow()
            
            # Add approval to work item history
            approval_history = WorkItemHistory(
                work_item_id=work_item.id,
                action=HistoryAction.UPDATED,
                performed_by=approved_by,
                performed_by_name=approved_by,
                timestamp=datetime.utcnow(),
                details={
                    "status": "approved",
                    "guidewire_job_id": work_item.guidewire_job_id,
                    "underwriter_notes": underwriter_notes,
                    "guidewire_approval_success": True
                }
            )
            db.add(approval_history)
            db.commit()
            db.refresh(work_item)
            
            return {
                "success": True,
                "work_item_id": work_item_id,
                "status": "approved",
                "guidewire_job_id": work_item.guidewire_job_id,
                "message": "Work item approved successfully and updated in Guidewire"
            }
        else:
            # Update work item but note Guidewire failure
            work_item.updated_at = datetime.utcnow()
            
            failure_history = WorkItemHistory(
                work_item_id=work_item.id,
                action=HistoryAction.UPDATED,
                performed_by=approved_by,
                performed_by_name=approved_by,
                timestamp=datetime.utcnow(),
                details={
                    "status": "approval_failed_in_guidewire",
                    "guidewire_job_id": work_item.guidewire_job_id,
                    "error": result.get("error"),
                    "message": result.get("message")
                }
            )
            db.add(failure_history)
            db.commit()
            
            return {
                "success": False,
                "work_item_id": work_item_id,
                "error": result.get("error"),
                "message": result.get("message"),
                "guidewire_job_id": work_item.guidewire_job_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving work item {work_item_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error approving work item: {str(e)}"
        )


# Step 3: Quote Creation and Document Retrieval Endpoints
@app.post("/api/workitems/{work_item_id}/create-quote")
async def create_quote_for_work_item(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Create quote and retrieve documents for an approved work item
    This is called after the work item has been approved
    """
    try:
        from guidewire_integration import guidewire_integration
        
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        if not work_item.guidewire_job_id:
            raise HTTPException(status_code=400, detail="Work item not yet synced to Guidewire")
        
        if work_item.status != WorkItemStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Work item must be approved before creating quote")
        
        logger.info(f"Creating quote for work item {work_item_id}", 
                   job_id=work_item.guidewire_job_id)
        
        # Call Guidewire quote creation API
        result = guidewire_integration.create_quote_and_get_document(work_item.guidewire_job_id)
        
        if result["success"]:
            # Update work item with quote information
            work_item.updated_at = datetime.utcnow()
            
            # Add quote creation to work item history
            quote_history = WorkItemHistory(
                work_item_id=work_item.id,
                action=HistoryAction.UPDATED,
                performed_by="System",
                performed_by_name="System",
                timestamp=datetime.utcnow(),
                details={
                    "status": "quote_created",
                    "guidewire_job_id": work_item.guidewire_job_id,
                    "quote_info": result.get("quote_info", {}),
                    "documents_count": len(result.get("documents", []))
                }
            )
            db.add(quote_history)
            db.commit()
            db.refresh(work_item)
            
            return {
                "success": True,
                "work_item_id": work_item_id,
                "guidewire_job_id": work_item.guidewire_job_id,
                "quote_info": result.get("quote_info", {}),
                "documents": result.get("documents", []),
                "message": "Quote created successfully and documents retrieved"
            }
        else:
            # Log failure
            failure_history = WorkItemHistory(
                work_item_id=work_item.id,
                action=HistoryAction.UPDATED,
                performed_by="System",
                performed_by_name="System",
                timestamp=datetime.utcnow(),
                details={
                    "status": "quote_creation_failed",
                    "guidewire_job_id": work_item.guidewire_job_id,
                    "error": result.get("error"),
                    "message": result.get("message")
                }
            )
            db.add(failure_history)
            db.commit()
            
            return {
                "success": False,
                "work_item_id": work_item_id,
                "error": result.get("error"),
                "message": result.get("message"),
                "guidewire_job_id": work_item.guidewire_job_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating quote for work item {work_item_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating quote: {str(e)}"
        )


@app.get("/api/workitems/{work_item_id}/quote-document/{document_id}")
async def get_quote_document_url(
    work_item_id: int,
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get download URL for a specific quote document
    """
    try:
        from guidewire_integration import guidewire_integration
        
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        if not work_item.guidewire_job_id:
            raise HTTPException(status_code=400, detail="Work item not yet synced to Guidewire")
        
        logger.info(f"Getting document URL for work item {work_item_id}", 
                   job_id=work_item.guidewire_job_id,
                   document_id=document_id)
        
        # Call Guidewire document URL API
        result = guidewire_integration.get_quote_document_url(work_item.guidewire_job_id, document_id)
        
        if result["success"]:
            return {
                "success": True,
                "work_item_id": work_item_id,
                "document_id": document_id,
                "download_url": result.get("download_url"),
                "message": "Document URL retrieved successfully"
            }
        else:
            return {
                "success": False,
                "work_item_id": work_item_id,
                "document_id": document_id,
                "error": result.get("error"),
                "message": result.get("message")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document URL for work item {work_item_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document URL: {str(e)}"
        )


@app.get("/api/guidewire/test-integration")
async def test_guidewire_integration():
    """
    Test our new clean Guidewire integration
    Shows the 3-step process we've implemented
    """
    try:
        from guidewire_integration import guidewire_integration
        
        # Test sample data
        sample_data = {
            "company_name": "Test Cyber Insurance Co",
            "business_address": "123 Test Street",
            "business_city": "San Francisco", 
            "business_state": "CA",
            "business_zip": "94105"
        }
        
        return {
            "integration_status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "implementation": {
                "step_1": {
                    "description": "Work Item Creation → Account & Submission Creation",
                    "endpoint": "Automatically called when work item is created",
                    "method": "guidewire_integration.create_account_and_submission()",
                    "team_format": "Uses exact 5-step composite request from Guidewire team",
                    "status": "✅ Implemented"
                },
                "step_2": {
                    "description": "Underwriter Approval → Guidewire Approval API",
                    "endpoint": "POST /api/workitems/{id}/approve",
                    "method": "guidewire_integration.approve_submission()",
                    "status": "✅ Implemented"
                },
                "step_3": {
                    "description": "Quote Creation → Get Quote Document",
                    "endpoint": "POST /api/workitems/{id}/create-quote",
                    "method": "guidewire_integration.create_quote_and_get_document()",
                    "status": "✅ Implemented"
                }
            },
            "endpoints": {
                "automatic_submission": {
                    "description": "Automatically creates Guidewire account & submission when work item is created",
                    "trigger": "Email intake creates work item",
                    "format": "Uses exact team Postman request format"
                },
                "underwriter_approval": {
                    "url": "/api/workitems/{work_item_id}/approve",
                    "method": "POST",
                    "description": "Approve work item and update Guidewire submission"
                },
                "quote_creation": {
                    "url": "/api/workitems/{work_item_id}/create-quote", 
                    "method": "POST",
                    "description": "Create quote and retrieve documents from Guidewire"
                },
                "document_download": {
                    "url": "/api/workitems/{work_item_id}/quote-document/{document_id}",
                    "method": "GET",
                    "description": "Get download URL for specific quote document"
                }
            },
            "guidewire_config": {
                "base_url": "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/composite/v1/composite",
                "username": "su",
                "authentication": "Basic Auth",
                "format": "Composite API requests with exact team specifications"
            },
            "network_status": "Ready to test with whitelisted IP"
        }
        
    except Exception as e:
        return {
            "integration_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/guidewire/test-connection")
async def test_guidewire_connection_live():
    """
    Test actual Guidewire connection from the deployed backend
    This runs from the whitelisted IP address
    """
    try:
        from guidewire_integration import guidewire_integration
        
        # Test the connection
        connection_result = guidewire_integration.test_connection()
        
        return {
            "test_type": "live_connection_test",
            "timestamp": datetime.utcnow().isoformat(),
            "deployment_url": "wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net",
            "guidewire_connection": connection_result,
            "ip_whitelisted": connection_result.get("success", False),
            "message": "Testing from whitelisted IP address" if connection_result.get("success", False) else "Connection failed - check IP whitelisting"
        }
        
    except Exception as e:
        return {
            "test_type": "live_connection_test",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "message": "Exception during connection test"
        }


@app.post("/api/guidewire/test-submission")
async def test_guidewire_submission_live():
    """
    Test actual Guidewire submission creation from the deployed backend
    This uses the exact team format and runs from the whitelisted IP
    """
    try:
        from guidewire_integration import guidewire_integration
        
        # Test data with unique identifier for tracking
        test_data = {
            "company_name": f"Debug Test Company {datetime.utcnow().strftime('%H%M%S')}",
            "business_address": "123 Debug Test Street",
            "business_city": "San Francisco",
            "business_state": "CA",
            "business_zip": "94105"
        }
        
        # Test the full submission creation
        submission_result = guidewire_integration.create_account_and_submission(test_data)
        
        # Return full details for debugging
        return {
            "test_type": "live_submission_test_with_debug", 
            "timestamp": datetime.utcnow().isoformat(),
            "deployment_url": "wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net",
            "test_data": test_data,
            "guidewire_result": submission_result,
            "success": submission_result.get("success", False),
            "account_id": submission_result.get("account_id"),
            "job_id": submission_result.get("job_id"),
            "full_response_structure": submission_result.get("full_response", {}),
            "parse_details": {
                "has_responses": "responses" in submission_result.get("full_response", {}),
                "response_count": len(submission_result.get("full_response", {}).get("responses", [])),
                "response_statuses": [r.get("status") for r in submission_result.get("full_response", {}).get("responses", [])]
            },
            "message": "Live submission test with enhanced debugging"
        }
        
    except Exception as e:
        return {
            "test_type": "live_submission_test",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "message": "Exception during submission test"
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/test/guidewire")
async def test_guidewire_connection():
    """Test Guidewire connection and authentication"""
    try:
        from guidewire_client import guidewire_client
        
        logger.info("Testing Guidewire connection...")
        result = guidewire_client.test_connection()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "guidewire_test": result,
            "configuration": {
                "base_url": guidewire_client.config.base_url,
                "auth_method": "basic_auth" if guidewire_client.config.username else "bearer_token",
                "username": guidewire_client.config.username if guidewire_client.config.username else None
            }
        }
    except Exception as e:
        logger.error(f"Guidewire test failed: {str(e)}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "guidewire_test": {
                "success": False,
                "error": "Connection test failed",
                "message": str(e)
            }
        }


@app.get("/api/test/outbound-ip")
async def test_outbound_ip():
    """Test what outbound IP address this app is using"""
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Test multiple IP detection services
            results = {}
            
            try:
                response = await client.get("https://api.ipify.org")
                results["ipify"] = response.text.strip()
            except Exception as e:
                results["ipify"] = f"Error: {str(e)}"
            
            try:
                response = await client.get("https://httpbin.org/ip")
                data = response.json()
                results["httpbin"] = data.get("origin", "").split(",")[0].strip()
            except Exception as e:
                results["httpbin"] = f"Error: {str(e)}"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "outbound_ip_results": results,
            "message": "Current outbound IP address(es)"
        }
        
    except Exception as e:
        return {
            "error": f"Failed to check outbound IP: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@app.post("/api/test/guidewire-submission")
async def test_guidewire_submission(test_data: dict = None, db: Session = Depends(get_db)):
    """Test creating a complete Guidewire submission using sample data"""
    try:
        from guidewire_client import guidewire_client
        
        # Use provided test data or create sample data
        sample_submission_data = test_data or {
            "company_name": "Test Insurance Company LLC",
            "named_insured": "Test Insurance Company LLC", 
            "contact_name": "John Smith",
            "contact_email": "john.smith@testcompany.com",
            "contact_phone": "555-123-4567",
            "business_address": "123 Business St",
            "business_city": "Seattle",
            "business_state": "WA",
            "business_zip": "98101",
            "industry": "technology",
            "employee_count": "50",
            "annual_revenue": "5000000",
            "coverage_amount": "1000000",
            "policy_type": "cyber liability",
            "effective_date": "2025-01-01",
            "entity_type": "llc"
        }
        
        logger.info(f"Testing Guidewire submission with data: {sample_submission_data}")
        
        # Create the submission in Guidewire
        result = guidewire_client.create_cyber_submission(sample_submission_data)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "test_submission_data": sample_submission_data,
            "guidewire_result": result,
            "success": result.get("success", False)
        }
        
    except Exception as e:
        logger.error(f"Guidewire submission test failed: {str(e)}", exc_info=True)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": f"Submission test failed: {str(e)}",
            "success": False
        }


@app.post("/api/test/guidewire-simple")
async def test_guidewire_simple_request():
    """Test a simple Guidewire request to debug the 400 error"""
    try:
        from guidewire_client import guidewire_client
        
        # Test a simple request first - just get account types or product info
        simple_payload = {
            "requests": [
                {
                    "method": "get",
                    "uri": "/account/v1/account-organization-types"
                }
            ]
        }
        
        logger.info(f"Testing simple Guidewire request: {simple_payload}")
        
        result = guidewire_client.submit_composite_request(simple_payload)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "simple_request": simple_payload,
            "guidewire_result": result,
            "success": result.get("success", False)
        }
        
    except Exception as e:
        logger.error(f"Simple Guidewire test failed: {str(e)}", exc_info=True)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": f"Simple test failed: {str(e)}",
            "success": False
        }


@app.post("/api/workitems/{work_item_id}/submit-to-guidewire")
async def submit_work_item_to_guidewire(work_item_id: int, db: Session = Depends(get_db)):
    """Submit a work item to Guidewire PolicyCenter"""
    try:
        from guidewire_integration import guidewire_integration
        
        # Get the work item and related submission
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        submission = db.query(Submission).filter(Submission.id == work_item.submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Related submission not found")
        
        # Parse extracted fields from submission
        extracted_data = _parse_extracted_fields(submission.extracted_fields) if submission.extracted_fields else {}
        
        # Combine work item and submission data
        submission_data = {
            # Company information
            "company_name": extracted_data.get("company_name") or extracted_data.get("named_insured", "Unknown Company"),
            "named_insured": extracted_data.get("named_insured", "Unknown Company"),
            "contact_name": extracted_data.get("contact_name") or extracted_data.get("insured_name", "Unknown Contact"),
            "contact_email": submission.sender_email or extracted_data.get("contact_email", "unknown@example.com"),
            "contact_phone": extracted_data.get("contact_phone", "555-000-0000"),
            
            # Business address
            "business_address": extracted_data.get("business_address") or extracted_data.get("mailing_address", "Address Not Provided"),
            "business_city": extracted_data.get("business_city") or extracted_data.get("mailing_city", "Unknown"),
            "business_state": extracted_data.get("business_state") or extracted_data.get("mailing_state", "CA"),
            "business_zip": extracted_data.get("business_zip") or extracted_data.get("mailing_zip", "00000"),
            
            # Business details from work item
            "industry": work_item.industry or extracted_data.get("industry", "other"),
            "employee_count": str(extracted_data.get("employee_count", "1")),
            "annual_revenue": str(work_item.coverage_amount or extracted_data.get("annual_revenue", "100000")),
            "coverage_amount": str(work_item.coverage_amount or extracted_data.get("coverage_amount", "50000")),
            "policy_type": work_item.policy_type or extracted_data.get("policy_type", "cyber liability"),
            "effective_date": extracted_data.get("effective_date", datetime.now().strftime("%Y-%m-%d")),
            "entity_type": extracted_data.get("entity_type", "other"),
            
            # Additional fields
            "years_in_business": extracted_data.get("years_in_business", "5"),
            "data_types": extracted_data.get("data_types", "general"),
            "business_description": extracted_data.get("business_description", work_item.description)
        }
        
        logger.info(f"Submitting work item {work_item_id} to Guidewire with data: {submission_data}")
        
        # Submit to Guidewire using our new clean integration
        result = guidewire_integration.create_account_and_submission(submission_data)
        
        if result.get("success"):
            # Update work item with Guidewire IDs
            if result.get("account_id"):
                work_item.guidewire_account_id = result["account_id"]
            if result.get("job_id"):
                work_item.guidewire_job_id = result["job_id"]
                
            # Update work item status
            work_item.status = WorkItemStatus.IN_REVIEW
            work_item.updated_at = datetime.utcnow()
            
            # Add history entry
            history_entry = WorkItemHistory(
                work_item_id=work_item.id,
                action=HistoryAction.UPDATED,
                performed_by="System",
                performed_by_name="System",
                timestamp=datetime.utcnow(),
                details={
                    "guidewire_account_id": result.get("account_id"),
                    "guidewire_job_id": result.get("job_id"),
                    "status": "manual_submission_to_guidewire"
                }
            )
            db.add(history_entry)
            
            db.commit()
            db.refresh(work_item)
            
            return {
                "success": True,
                "work_item_id": work_item_id,
                "guidewire_account_id": result.get("account_id"),
                "guidewire_job_id": result.get("job_id"),
                "message": "Work item successfully submitted to Guidewire PolicyCenter"
            }
        else:
            return {
                "success": False,
                "work_item_id": work_item_id,
                "error": result.get("error", "Unknown error"),
                "message": result.get("message", "Guidewire submission failed"),
                "details": result
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting work item {work_item_id} to Guidewire: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting to Guidewire: {str(e)}"
        )


# ===== Polling-based updates for Vercel compatibility =====

@app.get("/api/workitems/poll", response_model=EnhancedPollingResponse)
async def poll_workitems(
    since: str = None,
    limit: int = 50,
    search: str = None,
    priority: str = None,
    status: str = None,
    assigned_to: str = None,
    include_details: bool = False,
    work_item_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Enhanced polling for work items with filtering support and optional detailed data.
    Now includes risk assessment and history data when include_details=true or work_item_id specified.
    
    Args:
        since: ISO timestamp to filter items created after this time
        limit: Maximum number of items to return (default 50, max 100)
        search: Search term to filter across title, description, industry
        priority: Filter by priority (Low, Moderate, Medium, High, Critical)
        status: Filter by status (Pending, In Review, Approved, Rejected)
        assigned_to: Filter by assigned underwriter
        include_details: Include risk assessment and history data
        work_item_id: Get details for specific work item (replaces separate endpoints)
    """
    try:
        # Limit max items to prevent large responses
        limit = min(limit, 100)
        
        # Query work items with their related submission data
        query = db.query(WorkItem, Submission).join(
            Submission, WorkItem.submission_id == Submission.id
        ).order_by(WorkItem.created_at.desc())
        
        # Filter by timestamp if provided
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                query = query.filter(WorkItem.created_at > since_dt)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid 'since' timestamp format. Use ISO format (e.g., 2025-09-28T10:00:00Z)"
                )
        
        # Apply filters
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    WorkItem.title.ilike(search_filter),
                    WorkItem.description.ilike(search_filter),
                    WorkItem.industry.ilike(search_filter),
                    Submission.subject.ilike(search_filter),
                    Submission.sender_email.ilike(search_filter)
                )
            )
        
        if priority:
            try:
                priority_enum = WorkItemPriorityEnum(priority)
                query = query.filter(WorkItem.priority == priority_enum.value)
            except ValueError:
                pass  # Invalid priority, ignore filter
        
        if status:
            # Map common status values to enum values
            status_mapping = {
                "PENDING": WorkItemStatusEnum.PENDING,
                "IN_REVIEW": WorkItemStatusEnum.IN_REVIEW,
                "APPROVED": WorkItemStatusEnum.APPROVED,
                "REJECTED": WorkItemStatusEnum.REJECTED,
                "COMPLETED": WorkItemStatusEnum.APPROVED,  # Map COMPLETED to APPROVED
                # Also support direct enum values
                "Pending": WorkItemStatusEnum.PENDING,
                "In Review": WorkItemStatusEnum.IN_REVIEW,
                "Approved": WorkItemStatusEnum.APPROVED,
                "Rejected": WorkItemStatusEnum.REJECTED,
            }
            
            if status in status_mapping:
                status_enum = status_mapping[status]
                query = query.filter(WorkItem.status == status_enum.value)
        
        if assigned_to:
            query = query.filter(WorkItem.assigned_to.ilike(f"%{assigned_to}%"))
        
        results = query.limit(limit).all()
        
        # If specific work item requested, return detailed data
        if work_item_id:
            work_item_detail = db.query(WorkItem, Submission).join(
                Submission, WorkItem.submission_id == Submission.id
            ).filter(WorkItem.id == work_item_id).first()
            
            if not work_item_detail:
                raise HTTPException(status_code=404, detail="Work item not found")
            
            work_item, submission = work_item_detail
            
            # Get risk assessment
            risk_assessment = db.query(RiskAssessment).filter(
                RiskAssessment.work_item_id == work_item_id
            ).order_by(RiskAssessment.assessment_date.desc()).first()
            
            # Get history
            history = db.query(WorkItemHistory).filter(
                WorkItemHistory.work_item_id == work_item_id
            ).order_by(WorkItemHistory.timestamp.desc()).limit(10).all()
            
            return {
                "work_item": {
                    "id": work_item.id,
                    "submission_id": work_item.submission_id,
                    "submission_ref": str(submission.submission_ref),
                    "title": work_item.title or submission.subject,
                    "description": work_item.description,
                    "status": work_item.status.value if work_item.status else "Pending",
                    "priority": work_item.priority.value if work_item.priority else "Medium",
                    "assigned_to": work_item.assigned_to,
                    "risk_score": work_item.risk_score,
                    "risk_categories": work_item.risk_categories,
                    "industry": work_item.industry,
                    "policy_type": work_item.policy_type,
                    "coverage_amount": work_item.coverage_amount,
                    "created_at": work_item.created_at.isoformat() + "Z",
                    "updated_at": work_item.updated_at.isoformat() + "Z",
                    "extracted_fields": _parse_extracted_fields(submission.extracted_fields) if submission.extracted_fields else {}
                },
                "risk_assessment": {
                    "overall_score": risk_assessment.overall_risk_score if risk_assessment else work_item.risk_score,
                    "risk_categories": risk_assessment.risk_categories if risk_assessment else work_item.risk_categories,
                    "assessed_by": risk_assessment.assessed_by if risk_assessment else "System",
                    "assessment_date": risk_assessment.created_at.isoformat() + "Z" if risk_assessment else None
                } if risk_assessment or work_item.risk_score else None,
                "history": [
                    {
                        "id": h.id,
                        "action": h.action.value if hasattr(h.action, 'value') else str(h.action),
                        "performed_by": h.performed_by,
                        "timestamp": h.timestamp.isoformat() + "Z",
                        "details": h.details
                    } for h in history
                ],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        # Format response with enhanced data structure
        items = []
        for work_item, submission in results:
            # Count comments for this work item
            comments_count = db.query(Comment).filter(Comment.work_item_id == work_item.id).count()
            has_urgent_comments = db.query(Comment).filter(
                Comment.work_item_id == work_item.id,
                Comment.is_urgent == True
            ).first() is not None
            
            # Parse risk categories if available
            risk_categories = None
            if work_item.risk_categories:
                try:
                    risk_categories = RiskCategories(**work_item.risk_categories)
                except Exception:
                    risk_categories = None
            
            item_data = WorkItemSummary(
                id=work_item.id,
                submission_id=work_item.submission_id,
                submission_ref=str(submission.submission_ref),
                title=work_item.title or submission.subject or "No title",
                description=work_item.description,
                status=WorkItemStatusEnum(work_item.status.value) if work_item.status else WorkItemStatusEnum.PENDING,
                priority=WorkItemPriorityEnum(work_item.priority.value) if work_item.priority else WorkItemPriorityEnum.MEDIUM,
                assigned_to=work_item.assigned_to,
                risk_score=work_item.risk_score,
                risk_categories=risk_categories,
                industry=work_item.industry,
                company_size=CompanySizeEnum(work_item.company_size.value) if work_item.company_size else None,
                policy_type=work_item.policy_type,
                coverage_amount=work_item.coverage_amount,
                last_risk_assessment=work_item.last_risk_assessment,
                created_at=work_item.created_at,
                updated_at=work_item.updated_at,
                comments_count=comments_count,
                has_urgent_comments=has_urgent_comments,
                extracted_fields=_parse_extracted_fields(submission.extracted_fields) if submission.extracted_fields else {}
            )
            
            # Include detailed data if requested
            if include_details:
                # Get risk assessment for this item
                risk_assessment = db.query(RiskAssessment).filter(
                    RiskAssessment.work_item_id == work_item.id
                ).order_by(RiskAssessment.assessment_date.desc()).first()
                
                # Add risk assessment data to item
                if risk_assessment:
                    item_data.__dict__['risk_assessment'] = {
                        "overall_score": risk_assessment.overall_risk_score,
                        "assessed_by": risk_assessment.assessed_by,
                        "assessment_date": risk_assessment.created_at.isoformat() + "Z"
                    }
            
            items.append(item_data)
        
        return EnhancedPollingResponse(
            items=items,
            count=len(items),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error polling work items", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error polling work items: {str(e)}"
        )


@app.get("/api/debug/orphaned-submissions")
async def debug_orphaned_submissions(db: Session = Depends(get_db)):
    """Check for submissions that don't have corresponding work items"""
    try:
        # Find submissions that don't have work items
        orphaned_submissions = db.query(Submission).filter(
            ~Submission.id.in_(
                db.query(WorkItem.submission_id).subquery()
            )
        ).order_by(Submission.created_at.desc()).all()
        
        orphaned_data = []
        for submission in orphaned_submissions:
            orphaned_data.append({
                "submission_id": submission.submission_id,
                "id": submission.id,
                "subject": submission.subject,
                "sender_email": submission.sender_email,
                "created_at": submission.created_at.isoformat(),
                "task_status": submission.task_status,
                "extracted_fields": submission.extracted_fields
            })
        
        return {
            "orphaned_count": len(orphaned_data),
            "orphaned_submissions": orphaned_data,
            "total_submissions": db.query(Submission).count(),
            "total_work_items": db.query(WorkItem).count()
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.post("/api/debug/create-missing-work-items")
async def create_missing_work_items(db: Session = Depends(get_db)):
    """Create work items for submissions that don't have them"""
    try:
        # Find submissions that don't have work items
        orphaned_submissions = db.query(Submission).filter(
            ~Submission.id.in_(
                db.query(WorkItem.submission_id).subquery()
            )
        ).all()
        
        created_work_items = []
        errors = []
        
        for submission in orphaned_submissions:
            try:
                # Create work item for this submission
                work_item = WorkItem(
                    submission_id=submission.id,
                    title=submission.subject or "Email Submission",
                    description=f"Email from {submission.sender_email}",
                    status=WorkItemStatus.PENDING,
                    priority=WorkItemPriority.MEDIUM,
                    assigned_to=None
                )
                
                # Try to apply extracted data if available
                if submission.extracted_fields:
                    extracted_data = submission.extracted_fields
                    if isinstance(extracted_data, dict):
                        # Set basic fields
                        work_item.industry = extracted_data.get('industry')
                        work_item.policy_type = extracted_data.get('policy_type') or extracted_data.get('coverage_type')
                        
                        # Parse coverage amount
                        coverage_raw = extracted_data.get('coverage_amount') or extracted_data.get('policy_limit')
                        if coverage_raw:
                            try:
                                # Remove currency symbols and parse
                                coverage_clean = str(coverage_raw).replace('$', '').replace(',', '')
                                work_item.coverage_amount = float(coverage_clean)
                            except:
                                pass
                        
                        # Set company size if available
                        company_size = extracted_data.get('company_size')
                        if company_size:
                            try:
                                work_item.company_size = CompanySize(company_size)
                            except ValueError:
                                # Try mapping common variations
                                size_mapping = {
                                    'small': CompanySize.SMALL,
                                    'medium': CompanySize.MEDIUM,
                                    'large': CompanySize.LARGE,
                                    'enterprise': CompanySize.ENTERPRISE
                                }
                                work_item.company_size = size_mapping.get(str(company_size).lower())
                
                db.add(work_item)
                db.flush()  # Get ID
                
                # Create history entry
                history_entry = WorkItemHistory(
                    work_item_id=work_item.id,
                    action=HistoryAction.CREATED,
                    performed_by="System-Repair",
                    performed_by_name="System-Repair",
                    timestamp=datetime.utcnow(),
                    details={
                        "repair_action": "Created missing work item for orphaned submission",
                        "submission_ref": submission.submission_ref
                    }
                )
                db.add(history_entry)
                
                created_work_items.append({
                    "work_item_id": work_item.id,
                    "submission_id": submission.id,
                    "submission_ref": submission.submission_ref,
                    "title": work_item.title
                })
                
            except Exception as e:
                errors.append({
                    "submission_id": submission.id,
                    "submission_ref": submission.submission_ref,
                    "error": str(e)
                })
        
        if created_work_items:
            db.commit()
        
        return {
            "created_count": len(created_work_items),
            "error_count": len(errors),
            "created_work_items": created_work_items,
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }


# ===== Frontend Integration API Endpoints =====

@app.put("/api/submissions/{submission_id}")
async def update_submission(
    submission_id: int,
    updates: dict,
    db: Session = Depends(get_db)
):
    """Update submission fields (for inline editing) - Also updates related work item"""
    
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Update allowed fields
    allowed_fields = ['subject', 'sender_email', 'assigned_to', 'task_status']
    
    for field, value in updates.items():
        if field in allowed_fields and hasattr(submission, field):
            setattr(submission, field, value)
    
    # Also update related work item if exists
    work_item = db.query(WorkItem).filter(WorkItem.submission_id == submission.id).first()
    if work_item:
        if 'assigned_to' in updates:
            work_item.assigned_to = updates['assigned_to']
        if 'subject' in updates:
            work_item.title = updates['subject']
        work_item.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(submission)
    
    return {
        "message": f"Submission {submission_id} updated successfully",
        "updated_fields": list(updates.keys())
    }


@app.put("/api/workitems/{workitem_id}")
async def update_workitem(
    workitem_id: int,
    updates: dict,
    db: Session = Depends(get_db)
):
    """Update work item fields (for inline editing)"""
    
    work_item = db.query(WorkItem).filter(WorkItem.id == workitem_id).first()
    if not work_item:
        raise HTTPException(status_code=404, detail="Work item not found")
    
    # Update allowed fields
    allowed_fields = ['title', 'description', 'status', 'priority', 'assigned_to', 'industry', 'policy_type', 'coverage_amount']
    
    for field, value in updates.items():
        if field in allowed_fields and hasattr(work_item, field):
            # Handle enum fields
            if field == 'status' and value:
                try:
                    setattr(work_item, field, WorkItemStatus(value))
                except ValueError:
                    continue
            elif field == 'priority' and value:
                try:
                    setattr(work_item, field, WorkItemPriority(value))
                except ValueError:
                    continue
            else:
                setattr(work_item, field, value)
    
    work_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(work_item)
    
    return {
        "message": f"Work item {workitem_id} updated successfully",
        "updated_fields": list(updates.keys())
    }


@app.post("/api/workitems/{workitem_id}/assign")
async def assign_workitem(
    workitem_id: int,
    assignment_data: dict,
    db: Session = Depends(get_db)
):
    """Assign work item to underwriter and create submission"""
    
    underwriter = assignment_data.get('underwriter')
    if not underwriter:
        raise HTTPException(status_code=400, detail="Underwriter is required")
    
    # Get the work item
    work_item = db.query(WorkItem).filter(WorkItem.id == workitem_id).first()
    if not work_item:
        raise HTTPException(status_code=404, detail="Work item not found")
    
    # Get related submission
    submission = db.query(Submission).filter(Submission.id == work_item.submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Related submission not found")
    
    # Update assignment
    work_item.assigned_to = underwriter
    work_item.status = WorkItemStatus.IN_REVIEW
    work_item.updated_at = datetime.utcnow()
    
    submission.assigned_to = underwriter
    submission.task_status = "assigned"
    
    # Create assignment notification message
    message = SubmissionMessage(
        submission_id=submission.id,
        message_type="assignment_notification",
        sender="system",
        recipient=underwriter,
        subject=f"New Assignment - Work Item #{workitem_id}",
        message=f"You have been assigned work item #{workitem_id} for {submission.subject}",
        is_read=False
    )
    
    db.add(message)
    db.commit()
    
    return {
        "message": f"Work item {workitem_id} assigned to {underwriter}",
        "submission_id": submission.submission_id,
        "assigned_to": underwriter,
        "status": "Assigned"
    }


@app.get("/api/underwriters")
async def list_underwriters(db: Session = Depends(get_db)):
    """Get list of available underwriters"""
    
    underwriters = db.query(Underwriter).filter(Underwriter.is_active == True).all()
    
    return {
        "underwriters": [
            {
                "id": uw.id,
                "name": uw.name,
                "email": uw.email,
                "specializations": uw.specializations or [],
                "max_coverage_limit": uw.max_coverage_limit,
                "workload": uw.current_workload or 0
            }
            for uw in underwriters
        ]
    }


@app.get("/api/refresh-data")
async def refresh_data(db: Session = Depends(get_db)):
    """Endpoint for frontend refresh functionality"""
    
    # Get fresh counts and summary data
    total_submissions = db.query(Submission).count()
    pending_workitems = db.query(WorkItem).filter(WorkItem.status.in_([WorkItemStatus.PENDING, WorkItemStatus.IN_REVIEW])).count()
    new_workitems = db.query(WorkItem).filter(WorkItem.status == WorkItemStatus.PENDING).count()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_submissions": total_submissions,
            "pending_submissions": pending_workitems,
            "new_submissions": new_workitems
        },
        "message": "Data refreshed successfully"
    }


@app.post("/api/cleanup-duplicates")
async def cleanup_duplicate_work_items(db: Session = Depends(get_db)):
    """Cleanup duplicate work items - keeps the most recent one per submission"""
    try:
        # Find submissions with multiple work items
        from sqlalchemy import func
        
        duplicates = db.query(WorkItem.submission_id, func.count(WorkItem.id).label('count')).group_by(WorkItem.submission_id).having(func.count(WorkItem.id) > 1).all()
        
        removed_count = 0
        for submission_id, count in duplicates:
            # Get all work items for this submission, ordered by creation date (keep newest)
            work_items = db.query(WorkItem).filter(WorkItem.submission_id == submission_id).order_by(WorkItem.created_at.desc()).all()
            
            # Remove all except the first (most recent)
            for work_item in work_items[1:]:
                db.delete(work_item)
                removed_count += 1
        
        db.commit()
        
        return {
            "message": f"Cleanup completed. Removed {removed_count} duplicate work items.",
            "duplicates_found": len(duplicates),
            "items_removed": removed_count
        }
        
    except Exception as e:
        logger.error("Error during cleanup", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@app.get("/api/debug/duplicates")
async def debug_duplicate_work_items(db: Session = Depends(get_db)):
    """Debug endpoint to identify duplicate work items"""
    from sqlalchemy import func
    
    # Find submissions with multiple work items
    duplicates = db.query(
        WorkItem.submission_id, 
        func.count(WorkItem.id).label('work_item_count'),
        func.array_agg(WorkItem.id).label('work_item_ids')
    ).group_by(WorkItem.submission_id).having(func.count(WorkItem.id) > 1).all()
    
    total_work_items = db.query(WorkItem).count()
    total_submissions = db.query(Submission).count()
    
    duplicate_details = []
    for submission_id, count, work_item_ids in duplicates:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        duplicate_details.append({
            "submission_id": submission_id,
            "submission_ref": str(submission.submission_ref) if submission else "Unknown",
            "work_item_count": count,
            "work_item_ids": work_item_ids
        })
    
    return {
        "total_work_items": total_work_items,
        "total_submissions": total_submissions,
        "submissions_with_duplicates": len(duplicates),
        "duplicate_details": duplicate_details,
        "expected_work_items": total_submissions,
        "excess_work_items": total_work_items - total_submissions
    }


# ===== GUIDEWIRE API ENDPOINTS FOR UI TEAM =====

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
        from sqlalchemy import and_
        
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
    Includes all Guidewire identifiers and business data
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
    Returns matching work items with their Guidewire numbers
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
        from sqlalchemy import and_
        
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


# WebSocket endpoint temporarily disabled for deployment
# @app.websocket("/ws/workitems")
# async def websocket_endpoint(websocket: WebSocket):
#     """WebSocket endpoint for real-time work item updates"""
#     logger.info("WebSocket connection attempt - temporarily disabled")
#     pass





async def broadcast_new_workitem(work_item: WorkItem, submission: Submission, business_data: dict = None):
    """Broadcast a new work item to all connected WebSocket clients"""
    try:
        # Parse risk categories if available
        risk_categories = None
        if work_item.risk_categories:
            try:
                risk_categories = work_item.risk_categories
            except Exception:
                pass
        
        workitem_data = {
            "id": work_item.id,
            "submission_id": work_item.submission_id,
            "submission_ref": str(submission.submission_ref),
            "title": work_item.title or submission.subject or "No title",
            "description": work_item.description,
            "status": work_item.status.value if work_item.status else "Pending",
            "priority": work_item.priority.value if work_item.priority else "Medium",
            "assigned_to": work_item.assigned_to,
            "risk_score": work_item.risk_score,
            "risk_categories": risk_categories,
            "industry": work_item.industry,
            "company_size": work_item.company_size.value if work_item.company_size else None,
            "policy_type": work_item.policy_type,
            "coverage_amount": work_item.coverage_amount,
            "created_at": work_item.created_at.isoformat() + "Z" if work_item.created_at else None,
            "updated_at": work_item.updated_at.isoformat() + "Z" if work_item.updated_at else None,
            "comments_count": 0,
            "has_urgent_comments": False,
            # Include submission data for backward compatibility
            "subject": submission.subject or "No subject",
            "from_email": submission.sender_email or "Unknown sender",
            "extracted_fields": submission.extracted_fields or {}
        }
        
        # Add business validation data if provided
        if business_data:
            workitem_data.update({
                "validation_status": business_data.get("validation_status"),
                "business_risk_score": business_data.get("risk_score"),
                "assigned_underwriter": business_data.get("assigned_underwriter")
            })
        
        # WebSocket broadcast temporarily disabled for deployment
        logger.info(f"New work item created: {work_item.id} (submission: {submission.submission_id}) - broadcast would occur here")
        
    except Exception as e:
        logger.error(f"Error broadcasting work item: {str(e)}")


@app.get("/api/debug/test-guidewire-connection")
async def test_guidewire_connection():
    """Test direct Guidewire composite API endpoint as recommended by Guidewire team"""
    try:
        from guidewire_client import guidewire_client
        
        logger.info("Testing direct Guidewire composite API")
        
        # Test connection to base URL
        connection_test = guidewire_client.test_connection()
        
        # Test a sample submission using the direct composite endpoint
        sample_data = {
            "company_name": "Direct API Test Company Inc",
            "contact_email": "directapi@testcompany.com", 
            "contact_first_name": "Direct",
            "contact_last_name": "API",
            "industry": "technology",
            "employees": 30,
            "annual_revenue": 2000000,
            "coverage_amount": 1000000,
            "business_description": "Direct API test using composite endpoint",
            "business_state": "CA",
            "mailing_city": "San Francisco", 
            "mailing_zip": "94105"
        }
        
        logger.info("Testing submission creation via direct composite API")
        result = guidewire_client.create_cyber_submission(sample_data)
        
        return {
            "test_type": "DIRECT_COMPOSITE_API",
            "guidewire_endpoint": guidewire_client.config.full_url,
            "connection_test": connection_test,
            "submission_test": {
                "status": "COMPLETED",
                "success": result.get("success", False),
                "simulation_mode": result.get("simulation_mode", False),
                "account_id": result.get("account_id"),
                "account_number": result.get("account_number"), 
                "job_id": result.get("job_id"),
                "job_number": result.get("job_number"),
                "message": result.get("message"),
                "error": result.get("error")
            },
            "api_details": {
                "base_url": guidewire_client.config.base_url,
                "username": guidewire_client.config.username,
                "timeout": guidewire_client.config.timeout,
                "direct_endpoint": guidewire_client.config.full_url
            },
            "guidewire_team_recommendation": "Using direct composite endpoint",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
            
    except Exception as e:
        logger.error(f"Direct Guidewire API test failed: {str(e)}")
        return {
            "test_type": "DIRECT_COMPOSITE_API", 
            "status": "ERROR",
            "error": str(e),
            "message": "Direct composite API test failed",
            "endpoint": "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/composite/v1/composite",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


@app.get("/api/debug/test-simple-guidewire")
async def test_simple_guidewire():
    """Test simple Guidewire requests to debug API issues"""
    import requests
    import json
    
    composite_url = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/composite/v1/composite"
    username = "su"
    password = "gw"
    
    session = requests.Session()
    session.auth = (username, password)
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    results = {}
    
    # Test 1: Simple ping - composite endpoint only accepts POST/PUT/PATCH/DELETE
    try:
        ping_request = {
            "requests": [
                {
                    "uri": "/common/v1/ping",  # Removed /rest prefix
                    "method": "post"           # Lowercase to match template
                }
            ]
        }
        
        response = session.post(composite_url, json=ping_request, timeout=30)
        results["ping_test"] = {
            "status_code": response.status_code,
            "response": response.text,
            "success": response.status_code == 200
        }
        
    except Exception as e:
        results["ping_test"] = {"error": str(e), "success": False}
    
    # Test 2: Minimal account creation  
    try:
        timestamp = datetime.utcnow().strftime("%H%M%S")
        
        create_request = {
            "requests": [
                {
                    "uri": "/account/v1/accounts",
                    "method": "post",  # Lowercase as in official template
                    "body": {
                        "data": {
                            "attributes": {
                                "initialAccountHolder": {
                                    "contactSubtype": "Company",
                                    "companyName": f"Simple Test {timestamp}",
                                    "taxId": "12-3456789",  # Added required field
                                    "primaryAddress": {
                                        "addressLine1": "123 Test St",
                                        "city": "San Francisco", 
                                        "postalCode": "94105",
                                        "state": {"code": "CA"}
                                    }
                                },
                                "initialPrimaryLocation": {  # Added required field
                                    "addressLine1": "123 Test St",
                                    "city": "San Francisco",
                                    "postalCode": "94105", 
                                    "state": {"code": "CA"}
                                },
                                "producerCodes": [{"id": "pc:2"}],  # Added required field
                                "organizationType": {"code": "other"}
                            }
                        }
                    }
                }
            ]
        }
        
        response = session.post(composite_url, json=create_request, timeout=30)
        results["account_creation"] = {
            "status_code": response.status_code,
            "response": response.text,
            "success": response.status_code == 200
        }
        
        # Check if real account was created
        if response.status_code == 200:
            try:
                data = response.json()
                if 'responses' in data and len(data['responses']) > 0:
                    account_resp = data['responses'][0]
                    if 'body' in account_resp and 'data' in account_resp['body']:
                        account_attrs = account_resp['body']['data']['attributes']
                        results["real_account_created"] = {
                            "account_id": account_attrs.get('id'),
                            "account_number": account_attrs.get('accountNumber'),
                            "success": True
                        }
                    else:
                        results["real_account_created"] = {"success": False, "reason": "No account data in response"}
                else:
                    results["real_account_created"] = {"success": False, "reason": "No responses in data"}
            except Exception as e:
                results["real_account_created"] = {"success": False, "error": str(e)}
        
    except Exception as e:
        results["account_creation"] = {"error": str(e), "success": False}
    
    return {
        "test_type": "SIMPLE_DIRECT_API",
        "endpoint": composite_url,
        "authentication": f"{username}/***",
        "results": results,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/debug/test-submission-parsing")
async def debug_submission_parsing():
    """
    Debug the exact parsing logic used in the main integration
    """
    try:
        from guidewire_client import GuidewireClient
        from business_config import BusinessConfig
        import json
        
        # Create sample submission data
        sample_data = {
            "company_name": "Debug Test Company",
            "named_insured": "Debug Test LLC",
            "business_address": "123 Debug St",
            "business_city": "Test City", 
            "business_state": "CA",
            "business_zip": "94105",
            "effective_date": "2024-01-01",
            "coverage_amount": "$1,000,000"
        }
        
        # Initialize Guidewire client (use the pre-configured instance)
        from guidewire_client import guidewire_client
        client = guidewire_client
        
        # Test the exact same flow as main integration
        logger.info("🔍 DEBUGGING: Testing exact submission parsing flow")
        
        # 1. Map data to Guidewire format (same as main integration)
        guidewire_payload = client._map_to_guidewire_format(sample_data)
        
        # 2. Submit composite request (same as main integration)
        response = client.submit_composite_request(guidewire_payload)
        
        # 3. Extract results (same as main integration)
        if response["success"]:
            result = client._extract_submission_results(response)
            
            return {
                "debug_type": "SUBMISSION_PARSING",
                "payload_generated": True,
                "api_call_success": True,
                "api_response_status": response.get("status_code"),
                "parsing_result": {
                    "success": result.get("success"),
                    "simulation_mode": result.get("simulation_mode"),
                    "account_id": result.get("account_id"),
                    "account_number": result.get("account_number"),
                    "error": result.get("error"),
                    "message": result.get("message")
                },
                "raw_api_response_keys": list(response.keys()),
                "response_data_type": str(type(response.get("data"))),
                "has_responses_array": "responses" in str(response.get("data", {}))
            }
        else:
            return {
                "debug_type": "SUBMISSION_PARSING", 
                "payload_generated": True,
                "api_call_success": False,
                "api_response_status": response.get("status_code"),
                "api_error": response.get("error"),
                "api_message": response.get("message")
            }
            
    except Exception as e:
        return {
            "debug_type": "SUBMISSION_PARSING",
            "error": str(e),
            "success": False
        }

# ===== GUIDEWIRE DOCUMENT API ENDPOINTS FOR UI TEAM =====

@app.get("/api/guidewire/submissions/{work_item_id}/documents")
async def get_submission_documents(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all available quote documents for a work item from Guidewire
    UI team can use this to show available documents to download
    """
    try:
        from guidewire_integration import guidewire_integration
        
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        if not work_item.guidewire_job_id:
            raise HTTPException(
                status_code=400, 
                detail="Work item not yet integrated with Guidewire"
            )
        
        logger.info(f"Getting documents for work item {work_item_id}, job: {work_item.guidewire_job_id}")
        
        # Create quote and get documents from Guidewire
        result = guidewire_integration.create_quote_and_get_document(work_item.guidewire_job_id)
        
        if result.get("success"):
            documents = result.get("documents", [])
            
            # Format documents for UI team
            formatted_docs = []
            for doc in documents:
                if isinstance(doc, dict):
                    doc_info = {
                        "document_id": doc.get("id"),
                        "document_name": doc.get("attributes", {}).get("name", "Unknown Document"),
                        "document_type": doc.get("attributes", {}).get("type", "pdf"),
                        "file_size": doc.get("attributes", {}).get("size"),
                        "created_date": doc.get("attributes", {}).get("createdDate"),
                        "download_url": f"/api/guidewire/submissions/{work_item_id}/documents/{doc.get('id')}/download"
                    }
                    formatted_docs.append(doc_info)
            
            return {
                "work_item_id": work_item_id,
                "guidewire_job_id": work_item.guidewire_job_id,
                "guidewire_account_number": work_item.guidewire_account_number,
                "guidewire_job_number": work_item.guidewire_job_number,
                "documents": formatted_docs,
                "documents_count": len(formatted_docs),
                "quote_info": result.get("quote_info", {}),
                "message": "Documents retrieved successfully"
            }
        else:
            return {
                "work_item_id": work_item_id,
                "documents": [],
                "documents_count": 0,
                "error": result.get("error"),
                "message": result.get("message", "Failed to retrieve documents from Guidewire")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documents for work item {work_item_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving documents: {str(e)}"
        )


@app.get("/api/guidewire/submissions/{work_item_id}/documents/{document_id}/download")
async def download_submission_document(
    work_item_id: int,
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Download a specific quote document from Guidewire
    UI team can use this for direct document download links
    """
    try:
        from guidewire_integration import guidewire_integration
        import httpx
        
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        if not work_item.guidewire_job_id:
            raise HTTPException(
                status_code=400, 
                detail="Work item not yet integrated with Guidewire"
            )
        
        logger.info(f"Downloading document {document_id} for work item {work_item_id}")
        
        # Get document download URL from Guidewire
        result = guidewire_integration.get_quote_document_url(work_item.guidewire_job_id, document_id)
        
        if result.get("success"):
            download_url = result.get("download_url")
            if download_url:
                # Stream the document from Guidewire to the client
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        download_url,
                        auth=(guidewire_integration.username, guidewire_integration.password),
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        # Return the document with proper headers
                        content_type = response.headers.get("content-type", "application/pdf")
                        content_disposition = response.headers.get("content-disposition", f'attachment; filename="document_{document_id}.pdf"')
                        
                        from fastapi.responses import Response
                        return Response(
                            content=response.content,
                            media_type=content_type,
                            headers={"Content-Disposition": content_disposition}
                        )
                    else:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Failed to download document from Guidewire: {response.status_code}"
                        )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Document download URL not available"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get document URL: {result.get('message', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document {document_id} for work item {work_item_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading document: {str(e)}"
        )


@app.post("/api/guidewire/submissions/{work_item_id}/generate-quote")
async def generate_quote_for_submission(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate quote and documents for a work item (if not already generated)
    UI team can call this to trigger quote generation
    """
    try:
        from guidewire_integration import guidewire_integration
        
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        if not work_item.guidewire_job_id:
            raise HTTPException(
                status_code=400, 
                detail="Work item not yet integrated with Guidewire"
            )
        
        logger.info(f"Generating quote for work item {work_item_id}, job: {work_item.guidewire_job_id}")
        
        # Generate quote and get documents
        result = guidewire_integration.create_quote_and_get_document(work_item.guidewire_job_id)
        
        if result.get("success"):
            # Add quote generation to work item history
            history_entry = WorkItemHistory(
                work_item_id=work_item.id,
                action="quote_generated",
                performed_by="System",
                performed_by_name="System",
                timestamp=datetime.utcnow(),
                details={
                    "guidewire_job_id": work_item.guidewire_job_id,
                    "quote_generated": True,
                    "documents_count": len(result.get("documents", [])),
                    "quote_info": result.get("quote_info", {})
                }
            )
            db.add(history_entry)
            db.commit()
            
            return {
                "success": True,
                "work_item_id": work_item_id,
                "guidewire_job_id": work_item.guidewire_job_id,
                "quote_info": result.get("quote_info", {}),
                "documents_count": len(result.get("documents", [])),
                "documents_url": f"/api/guidewire/submissions/{work_item_id}/documents",
                "message": "Quote generated successfully"
            }
        else:
            return {
                "success": False,
                "work_item_id": work_item_id,
                "error": result.get("error"),
                "message": result.get("message", "Failed to generate quote")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quote for work item {work_item_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating quote: {str(e)}"
        )


@app.post("/api/guidewire/submissions/{work_item_id}/fetch-and-store-documents")
async def fetch_and_store_quote_documents(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch quote documents from Guidewire and store them in database for faster access
    This downloads the actual document content and stores it locally
    """
    try:
        from guidewire_integration import guidewire_integration
        import httpx
        import base64
        
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        if not work_item.guidewire_job_id:
            raise HTTPException(
                status_code=400, 
                detail="Work item not yet integrated with Guidewire"
            )
        
        logger.info(f"Fetching and storing documents for work item {work_item_id}")
        
        # Get documents from Guidewire
        result = guidewire_integration.create_quote_and_get_document(work_item.guidewire_job_id)
        
        if not result.get("success"):
            return {
                "success": False,
                "work_item_id": work_item_id,
                "error": result.get("error"),
                "message": "Failed to fetch documents from Guidewire"
            }
        
        documents = result.get("documents", [])
        stored_documents = []
        errors = []
        
        async with httpx.AsyncClient(timeout=60) as client:
            for doc in documents:
                if not isinstance(doc, dict):
                    continue
                
                doc_id = doc.get("id")
                if not doc_id:
                    continue
                
                try:
                    # Check if document already exists in database
                    existing_doc = db.query(QuoteDocument).filter(
                        QuoteDocument.work_item_id == work_item_id,
                        QuoteDocument.guidewire_document_id == doc_id
                    ).first()
                    
                    if existing_doc and existing_doc.status == DocumentStatus.STORED:
                        logger.info(f"Document {doc_id} already stored, skipping")
                        stored_documents.append({
                            "document_id": doc_id,
                            "document_name": existing_doc.document_name,
                            "status": "already_stored",
                            "file_size": existing_doc.file_size_bytes
                        })
                        continue
                    
                    # Get document download URL from Guidewire
                    url_result = guidewire_integration.get_quote_document_url(work_item.guidewire_job_id, doc_id)
                    
                    if not url_result.get("success"):
                        errors.append({
                            "document_id": doc_id,
                            "error": f"Failed to get download URL: {url_result.get('message')}"
                        })
                        continue
                    
                    download_url = url_result.get("download_url")
                    if not download_url:
                        errors.append({
                            "document_id": doc_id,
                            "error": "No download URL provided"
                        })
                        continue
                    
                    # Download the document content
                    logger.info(f"Downloading document {doc_id} from Guidewire")
                    response = await client.get(
                        download_url,
                        auth=(guidewire_integration.username, guidewire_integration.password),
                        timeout=60
                    )
                    
                    if response.status_code != 200:
                        errors.append({
                            "document_id": doc_id,
                            "error": f"Download failed with status {response.status_code}"
                        })
                        continue
                    
                    # Get document metadata
                    doc_attributes = doc.get("attributes", {})
                    document_name = doc_attributes.get("name", f"document_{doc_id}")
                    content_type = response.headers.get("content-type", "application/pdf")
                    file_size = len(response.content)
                    
                    # Encode content as base64 for database storage
                    content_base64 = base64.b64encode(response.content).decode('utf-8')
                    
                    # Determine document type
                    doc_type = DocumentType.OTHER
                    if "quote" in document_name.lower():
                        doc_type = DocumentType.QUOTE
                    elif "terms" in document_name.lower() or "policy" in document_name.lower():
                        doc_type = DocumentType.POLICY_TERMS
                    elif "proposal" in document_name.lower():
                        doc_type = DocumentType.PROPOSAL
                    elif "certificate" in document_name.lower():
                        doc_type = DocumentType.CERTIFICATE
                    
                    # Create or update document record
                    if existing_doc:
                        # Update existing record
                        existing_doc.document_content = content_base64
                        existing_doc.document_name = document_name
                        existing_doc.document_type = doc_type
                        existing_doc.content_type = content_type
                        existing_doc.file_size_bytes = file_size
                        existing_doc.status = DocumentStatus.STORED
                        existing_doc.guidewire_download_url = download_url
                        existing_doc.download_attempts += 1
                        existing_doc.last_download_attempt = datetime.utcnow()
                        existing_doc.error_message = None
                        existing_doc.updated_at = datetime.utcnow()
                        
                        stored_doc = existing_doc
                    else:
                        # Create new document record
                        stored_doc = QuoteDocument(
                            work_item_id=work_item_id,
                            guidewire_document_id=doc_id,
                            guidewire_job_id=work_item.guidewire_job_id,
                            document_name=document_name,
                            document_type=doc_type,
                            content_type=content_type,
                            file_size_bytes=file_size,
                            document_content=content_base64,
                            guidewire_download_url=download_url,
                            status=DocumentStatus.STORED,
                            download_attempts=1,
                            last_download_attempt=datetime.utcnow()
                        )
                        db.add(stored_doc)
                    
                    db.commit()
                    db.refresh(stored_doc)
                    
                    stored_documents.append({
                        "document_id": doc_id,
                        "database_id": stored_doc.id,
                        "document_name": document_name,
                        "document_type": doc_type.value,
                        "content_type": content_type,
                        "file_size": file_size,
                        "status": "stored"
                    })
                    
                    logger.info(f"Successfully stored document {doc_id} ({file_size} bytes)")
                    
                except Exception as e:
                    logger.error(f"Error processing document {doc_id}: {str(e)}", exc_info=True)
                    errors.append({
                        "document_id": doc_id,
                        "error": str(e)
                    })
                    
                    # Update existing record with error status
                    if existing_doc:
                        existing_doc.status = DocumentStatus.ERROR
                        existing_doc.error_message = str(e)
                        existing_doc.download_attempts += 1
                        existing_doc.last_download_attempt = datetime.utcnow()
                        db.commit()
        
        # Add history entry
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action="documents_fetched_and_stored",
            performed_by="System",
            performed_by_name="System",
            timestamp=datetime.utcnow(),
            details={
                "documents_stored": len(stored_documents),
                "errors_count": len(errors),
                "guidewire_job_id": work_item.guidewire_job_id
            }
        )
        db.add(history_entry)
        db.commit()
        
        return {
            "success": True,
            "work_item_id": work_item_id,
            "documents_processed": len(documents),
            "documents_stored": len(stored_documents),
            "errors_count": len(errors),
            "stored_documents": stored_documents,
            "errors": errors,
            "message": f"Successfully processed {len(documents)} documents, stored {len(stored_documents)}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching and storing documents for work item {work_item_id}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching and storing documents: {str(e)}"
        )


@app.get("/api/guidewire/submissions/{work_item_id}/stored-documents")
async def get_stored_documents(
    work_item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get documents stored in database for a work item
    Returns document metadata and provides download links
    """
    try:
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        # Get stored documents
        documents = db.query(QuoteDocument).filter(
            QuoteDocument.work_item_id == work_item_id
        ).order_by(QuoteDocument.created_at.desc()).all()
        
        document_list = []
        for doc in documents:
            document_list.append({
                "id": doc.id,
                "document_id": doc.guidewire_document_id,
                "document_name": doc.document_name,
                "document_type": doc.document_type.value if doc.document_type else "Other",
                "content_type": doc.content_type,
                "file_size": doc.file_size_bytes,
                "status": doc.status.value if doc.status else "Unknown",
                "created_at": doc.created_at.isoformat() + "Z",
                "updated_at": doc.updated_at.isoformat() + "Z",
                "download_url": f"/api/guidewire/submissions/{work_item_id}/stored-documents/{doc.id}/download",
                "has_content": bool(doc.document_content),
                "download_attempts": doc.download_attempts,
                "error_message": doc.error_message
            })
        
        return {
            "work_item_id": work_item_id,
            "guidewire_job_id": work_item.guidewire_job_id,
            "guidewire_account_number": work_item.guidewire_account_number,
            "guidewire_job_number": work_item.guidewire_job_number,
            "documents": document_list,
            "documents_count": len(document_list),
            "stored_count": len([d for d in documents if d.status == DocumentStatus.STORED]),
            "error_count": len([d for d in documents if d.status == DocumentStatus.ERROR])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stored documents for work item {work_item_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving stored documents: {str(e)}"
        )


@app.get("/api/guidewire/submissions/{work_item_id}/stored-documents/{document_id}/download")
async def download_stored_document(
    work_item_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Download a document that's stored in the database
    Much faster than fetching from Guidewire every time
    """
    try:
        # Get the stored document
        document = db.query(QuoteDocument).filter(
            QuoteDocument.id == document_id,
            QuoteDocument.work_item_id == work_item_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.document_content:
            raise HTTPException(status_code=404, detail="Document content not available")
        
        # Decode base64 content
        import base64
        try:
            document_bytes = base64.b64decode(document.document_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error decoding document content: {str(e)}")
        
        # Return the document with proper headers
        from fastapi.responses import Response
        
        # Clean filename for download
        filename = document.document_name
        if not filename.endswith('.pdf') and document.content_type == 'application/pdf':
            filename += '.pdf'
        
        return Response(
            content=document_bytes,
            media_type=document.content_type or "application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(document_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading stored document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading document: {str(e)}"
        )


@app.patch("/api/workitems/{work_item_id}/update-guidewire")
async def update_work_item_guidewire_data(
    work_item_id: int,
    guidewire_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update a work item with real Guidewire data for testing document storage
    """
    try:
        # Get the work item
        work_item = db.query(WorkItem).filter(WorkItem.id == work_item_id).first()
        if not work_item:
            raise HTTPException(status_code=404, detail="Work item not found")
        
        # Update Guidewire fields
        if "guidewire_job_id" in guidewire_data:
            work_item.guidewire_job_id = guidewire_data["guidewire_job_id"]
        if "guidewire_account_id" in guidewire_data:
            work_item.guidewire_account_id = guidewire_data["guidewire_account_id"]
        if "guidewire_job_number" in guidewire_data:
            work_item.guidewire_job_number = guidewire_data["guidewire_job_number"]
        if "guidewire_account_number" in guidewire_data:
            work_item.guidewire_account_number = guidewire_data["guidewire_account_number"]
        
        work_item.updated_at = datetime.utcnow()
        
        # Add history entry
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action=HistoryAction.UPDATED,
            performed_by="System",
            performed_by_name="System",
            timestamp=datetime.utcnow(),
            details={
                "action": "updated_guidewire_data",
                "guidewire_data": guidewire_data
            }
        )
        db.add(history_entry)
        
        db.commit()
        db.refresh(work_item)
        
        return {
            "success": True,
            "work_item_id": work_item_id,
            "message": "Work item updated with Guidewire data",
            "guidewire_data": {
                "job_id": work_item.guidewire_job_id,
                "account_id": work_item.guidewire_account_id,
                "job_number": work_item.guidewire_job_number,
                "account_number": work_item.guidewire_account_number
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating work item {work_item_id} with Guidewire data: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating Guidewire data: {str(e)}"
        )


@app.post("/api/test/guidewire-documents")
async def test_guidewire_documents(
    job_data: dict,
    db: Session = Depends(get_db)
):
    """
    Test document retrieval directly from Guidewire using job ID
    """
    try:
        from guidewire_integration import guidewire_integration
        
        job_id = job_data.get("job_id")
        job_number = job_data.get("job_number", "Unknown")
        
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")
        
        logger.info(f"Testing document retrieval for job {job_number} ({job_id})")
        
        # Test document retrieval using guidewire_integration
        result = guidewire_integration.get_quote_documents(job_id)
        
        return {
            "success": result.get("success", False),
            "job_id": job_id,
            "job_number": job_number,
            "documents": result.get("documents", []),
            "message": result.get("message", "Document retrieval test completed"),
            "error": result.get("error") if not result.get("success") else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing Guidewire documents: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Document retrieval test failed",
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
