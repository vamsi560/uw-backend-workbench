
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
from database import get_db, Submission, WorkItem, RiskAssessment, Comment, User, WorkItemHistory, WorkItemStatus, WorkItemPriority, CompanySize, Underwriter, SubmissionMessage, create_tables, SubmissionStatus, SubmissionHistory
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

# Include Guidewire data APIs for UI integration
try:
    from guidewire_data_apis import guidewire_router
    app.include_router(guidewire_router)
    logger.info("Guidewire data APIs successfully loaded")
except Exception as e:
    logger.error(f"Failed to load Guidewire data APIs: {str(e)}")

# Include test Guidewire router for debugging
try:
    from guidewire_test_apis import test_guidewire_router
    app.include_router(test_guidewire_router)
    logger.info("Test Guidewire APIs loaded")
except Exception as e:
    logger.error(f"Failed to load test Guidewire APIs: {str(e)}")

# Test endpoint to verify deployment
@app.get("/api/test/deployment")
async def test_deployment():
    """Test endpoint to verify latest deployment"""
    return {
        "message": "Latest deployment active",
        "timestamp": datetime.now().isoformat(),
        "guidewire_apis_loaded": any("/api/guidewire" in str(route.path) for route in app.routes if hasattr(route, 'path'))
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
    query = db.query(Submission)

    if since_id is not None:
        query = query.filter(Submission.id > since_id)
    elif since is not None:
        query = query.filter(Submission.created_at > since)
    else:
        # No filters, return 20 most recent
        query = query.order_by(Submission.created_at.desc()).limit(20)

    # Always order by created_at ASC for output
    results = query.order_by(Submission.created_at.asc()).all()

    # Remove duplicates by id (shouldn't be needed if id is PK, but for safety)
    seen = set()
    unique_submissions = []
    for sub in results:
        if sub.id not in seen:
            seen.add(sub.id)
            unique_submissions.append(sub)

    return [
        SubmissionOut(
            id=sub.id,
            subject=sub.subject,
            from_email=getattr(sub, "from_email", None),
            created_at=sub.created_at,
            status=sub.status
        )
        for sub in unique_submissions
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
                overall_score=overall_risk_score,
                risk_categories=risk_categories,
                assessment_date=datetime.utcnow(),
                assessed_by="System",
                assessment_notes=f"Initial automated assessment based on submission data. Validation status: {validation_status}"
            )
            db.add(risk_assessment)
        
        # Create history entry for validation results
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action="created",
            changed_by="System",
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
        
        # Broadcast new work item to all connected WebSocket clients with enhanced data
        await broadcast_new_workitem(work_item, submission, {
            "validation_status": validation_status,
            "risk_score": overall_risk_score,
            "assigned_underwriter": assigned_underwriter
        })
        
        return EmailIntakeResponse(
            submission_ref=str(submission_ref),
            submission_id=submission.submission_id,
            status="success",
            message="Email processed successfully and submission created"
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
                overall_score=float(overall_risk_score),
                risk_categories=risk_categories,
                assessment_date=datetime.utcnow(),
                assessed_by="System",
                assessment_notes=f"Initial automated assessment based on Logic Apps submission data. Validation status: {str(validation_status)}"
            )
            db.add(risk_assessment)
        
        # Create history entry for validation results with safe string handling
        history_entry = WorkItemHistory(
            work_item_id=work_item.id,
            action="created",
            changed_by="System",
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
        
        return EmailIntakeResponse(
            submission_ref=str(submission_ref),
            submission_id=submission.submission_id,
            status="success",
            message="Logic Apps email processed successfully and submission created"
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
        
        # Get latest work item
        latest_work_item = db.query(WorkItem).order_by(WorkItem.created_at.desc()).first()
        
        return {
            "database_status": "connected",
            "work_items_count": work_item_count,
            "submissions_count": submission_count,
            "latest_work_item": {
                "id": latest_work_item.id if latest_work_item else None,
                "created_at": latest_work_item.created_at.isoformat() if latest_work_item else None,
                "title": latest_work_item.title if latest_work_item else None
            } if latest_work_item else None,
            "database_url_host": settings.database_url.split('@')[1].split('/')[0] if '@' in settings.database_url else "hidden"
        }
    except Exception as e:
        return {
            "database_status": "error",
            "error": str(e),
            "database_url_host": settings.database_url.split('@')[1].split('/')[0] if '@' in settings.database_url else "hidden"
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
            changed_by=changed_by,
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
        from guidewire_client import guidewire_client
        
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
        
        # Submit to Guidewire
        result = guidewire_client.create_cyber_submission(submission_data)
        
        if result.get("success"):
            # Store the Guidewire response data
            try:
                guidewire_response_id = guidewire_client.store_guidewire_response(
                    db=db,
                    work_item_id=work_item_id,
                    submission_id=work_item.submission_id,
                    parsed_data=result.get("parsed_data", {}),
                    raw_response=result.get("raw_response", {})
                )
                
                # Update work item status
                work_item.status = WorkItemStatus.IN_REVIEW
                work_item.assigned_to = result.get("assigned_underwriter") or work_item.assigned_to
                work_item.updated_at = datetime.utcnow()
                
                # Add history entry
                history_entry = WorkItemHistory(
                    work_item_id=work_item.id,
                    action="submitted_to_guidewire",
                    changed_by="System",
                    timestamp=datetime.utcnow(),
                    details={
                        "guidewire_account_id": result.get("account_id"),
                        "guidewire_job_id": result.get("job_id"),
                        "account_number": result.get("account_number"),
                        "job_number": result.get("job_number"),
                        "guidewire_response_id": guidewire_response_id
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
                    "account_number": result.get("account_number"),
                    "job_number": result.get("job_number"),
                    "quote_info": result.get("quote_info", {}),
                    "guidewire_response_id": guidewire_response_id,
                    "message": "Work item successfully submitted to Guidewire PolicyCenter"
                }
            except Exception as db_error:
                logger.error(f"Error storing Guidewire response: {str(db_error)}")
                # Still return success since Guidewire submission worked
                return {
                    "success": True,
                    "work_item_id": work_item_id,
                    "guidewire_result": result,
                    "warning": f"Guidewire submission successful but failed to store response: {str(db_error)}",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
