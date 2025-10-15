
import enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, ForeignKey, UUID as SQLAlchemyUUID, Float, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

from config import settings

# Real-world submission status lifecycle
class SubmissionStatus(enum.Enum):
    NEW = "New"
    INTAKE = "Intake"
    IN_REVIEW = "In Review"
    ASSIGNED = "Assigned"
    QUOTED = "Quoted"
    BOUND = "Bound"
    DECLINED = "Declined"
    WITHDRAWN = "Withdrawn"
    COMPLETED = "Completed"

# Create database engine for PostgreSQL
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Enums for cyber insurance workbench
class WorkItemStatus(enum.Enum):
    PENDING = "Pending"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class WorkItemPriority(enum.Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class CompanySize(enum.Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    ENTERPRISE = "Enterprise"


class UserRole(enum.Enum):
    UNDERWRITER = "Underwriter"
    SENIOR_UNDERWRITER = "Senior_Underwriter"
    MANAGER = "Manager"
    RISK_ANALYST = "Risk_Analyst"


class HistoryAction(enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    ASSIGNED = "assigned"
    COMMENTED = "commented"
    RISK_ASSESSED = "risk_assessed"


class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, index=True)  # Internal submission ID
    submission_ref = Column(SQLAlchemyUUID, unique=True, index=True, default=uuid.uuid4)
    subject = Column(Text, nullable=False)
    sender_email = Column(Text, nullable=False)
    body_text = Column(Text)
    attachment_content = Column(Text, nullable=True)  # Decoded attachment text content
    extracted_fields = Column(JSON)  # JSONB equivalent
    assigned_to = Column(Text)  # underwriter email/name
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.NEW, index=True)
    received_at = Column(DateTime, nullable=True)  # Email received timestamp from Logic Apps
    task_status = Column(String(100), default="pending")  # Task status for compatibility
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    work_items = relationship("WorkItem", back_populates="submission", cascade="all, delete-orphan")
# Submission status history/audit trail
class SubmissionHistory(Base):
    __tablename__ = "submission_history"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, index=True)
    old_status = Column(Enum(SubmissionStatus), nullable=False)
    new_status = Column(Enum(SubmissionStatus), nullable=False)
    changed_by = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    submission = relationship("Submission")
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkItem(Base):
    __tablename__ = "work_items"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    
    # Basic work item fields
    title = Column(String(500))
    description = Column(Text)
    assigned_to = Column(String)  # underwriter email/name
    status = Column(Enum(WorkItemStatus), default=WorkItemStatus.PENDING, index=True)
    priority = Column(Enum(WorkItemPriority), default=WorkItemPriority.MEDIUM, index=True)
    
    # Cyber insurance specific fields
    risk_score = Column(Float, nullable=True)
    risk_categories = Column(JSON, nullable=True)  # {technical, operational, financial, compliance}
    industry = Column(String(100), nullable=True)
    company_size = Column(Enum(CompanySize), nullable=True)
    policy_type = Column(String(100), nullable=True)
    coverage_amount = Column(Float, nullable=True)
    last_risk_assessment = Column(DateTime, nullable=True)
    
    # Guidewire integration fields
    guidewire_account_id = Column(String(100), nullable=True)      # Internal Guidewire account ID (pc:xxxx)
    guidewire_job_id = Column(String(100), nullable=True)          # Internal Guidewire job ID (pc:xxxx)
    guidewire_account_number = Column(String(100), nullable=True)  # Human-readable account number (for search)
    guidewire_job_number = Column(String(100), nullable=True)      # Human-readable job number (for search)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add unique constraint to prevent duplicate work items per submission
    __table_args__ = (
        {'extend_existing': True}
    )
    
    # Relationships
    submission = relationship("Submission", back_populates="work_items")
    risk_assessments = relationship("RiskAssessment", back_populates="work_item", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="work_item", cascade="all, delete-orphan")
    history = relationship("WorkItemHistory", back_populates="work_item", cascade="all, delete-orphan")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id"), nullable=False, index=True)
    overall_risk_score = Column(Float, nullable=False)
    risk_categories = Column(JSON)  # {technical, operational, financial, compliance}
    risk_factors = Column(JSON)  # Array of risk factor objects
    recommendations = Column(JSON)  # Array of recommendation objects
    assessed_by = Column(String(255))
    assessed_by_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    work_item = relationship("WorkItem", back_populates="risk_assessments")


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id"), nullable=False, index=True)
    author_id = Column(String(255), nullable=False)
    author_name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_urgent = Column(Boolean, default=False)
    mentions = Column(JSON)  # Array of user IDs mentioned in comment
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    work_item = relationship("WorkItem", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id])
    replies = relationship("Comment", back_populates="parent_comment")


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False)
    specializations = Column(JSON)  # Array of specialization areas
    max_capacity = Column(Integer, default=25)
    current_workload = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    avg_processing_time_days = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)  # Percentage
    last_assignment = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Underwriter(Base):
    __tablename__ = "underwriters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    specializations = Column(JSON)  # Array of insurance specializations
    max_coverage_limit = Column(Float, nullable=True)  # Maximum coverage they can underwrite
    current_workload = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SubmissionMessage(Base):
    __tablename__ = "submission_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, index=True)
    message_type = Column(String(100), nullable=False)  # assignment_notification, status_update, etc.
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    submission = relationship("Submission")


class WorkItemHistory(Base):
    __tablename__ = "work_item_history"
    
    id = Column(Integer, primary_key=True, index=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id"), nullable=False, index=True)
    action = Column(Enum(HistoryAction), nullable=False)
    performed_by = Column(String(255), nullable=False)
    performed_by_name = Column(String(255), nullable=False)
    details = Column(JSON)  # Additional details about the action
    description = Column(Text)  # Human readable description
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    work_item = relationship("WorkItem", back_populates="history")


class GuidewireLookup(Base):
    """Quick lookup table for Guidewire account and submission numbers"""
    __tablename__ = "guidewire_lookups"
    
    id = Column(Integer, primary_key=True, index=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, index=True)
    
    # Essential Guidewire identifiers for quick search
    account_number = Column(String(50), nullable=True, index=True)  # Human-readable account number
    job_number = Column(String(50), nullable=True, index=True)      # Human-readable job/submission number
    organization_name = Column(String(255), nullable=True, index=True)  # Company name in Guidewire
    
    # Internal Guidewire IDs (for API calls)
    guidewire_account_id = Column(String(100), nullable=True)  # pc:ABC123...
    guidewire_job_id = Column(String(100), nullable=True)      # pc:JOB456...
    
    # Status tracking
    account_created = Column(Boolean, default=False, index=True)
    submission_created = Column(Boolean, default=False, index=True)
    sync_status = Column(String(50), default="pending", index=True)  # pending, partial, complete, failed
    
    # Business context for easier identification
    coverage_amount = Column(Float, nullable=True)
    industry = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    account_created_at = Column(DateTime, nullable=True)
    submission_created_at = Column(DateTime, nullable=True)
    
    # Relationships
    work_item = relationship("WorkItem", backref="guidewire_lookup")
    submission = relationship("Submission", backref="guidewire_lookup")


class GuidewireResponse(Base):
    """Store comprehensive Guidewire API response data for UI display"""
    __tablename__ = "guidewire_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    work_item_id = Column(Integer, ForeignKey("work_items.id"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False, index=True)
    
    # Account Information
    guidewire_account_id = Column(String(100), nullable=True, index=True)
    account_number = Column(String(50), nullable=True, index=True)
    account_status = Column(String(50), nullable=True)
    organization_name = Column(String(255), nullable=True)
    number_of_contacts = Column(Integer, nullable=True)
    
    # Job/Submission Information
    guidewire_job_id = Column(String(100), nullable=True, index=True)
    job_number = Column(String(50), nullable=True, index=True)
    job_status = Column(String(50), nullable=True)
    job_effective_date = Column(DateTime, nullable=True)
    base_state = Column(String(10), nullable=True)
    
    # Policy Information  
    policy_number = Column(String(50), nullable=True, index=True)
    policy_type = Column(String(100), nullable=True)
    underwriting_company = Column(String(255), nullable=True)
    producer_code = Column(String(50), nullable=True)
    
    # Coverage Information (JSON to store flexible coverage terms)
    coverage_terms = Column(JSON, nullable=True)  # Store all coverage limits and terms
    coverage_display_values = Column(JSON, nullable=True)  # Human-readable coverage descriptions
    
    # Pricing Information
    total_cost_amount = Column(Float, nullable=True)
    total_cost_currency = Column(String(10), nullable=True)
    total_premium_amount = Column(Float, nullable=True)
    total_premium_currency = Column(String(10), nullable=True)
    rate_as_of_date = Column(DateTime, nullable=True)
    
    # Business Data from Guidewire
    business_started_date = Column(DateTime, nullable=True)
    total_employees = Column(Integer, nullable=True)
    total_revenues = Column(Float, nullable=True)
    total_assets = Column(Float, nullable=True)
    total_liabilities = Column(Float, nullable=True)
    industry_type = Column(String(100), nullable=True)
    
    # Response Metadata
    response_checksum = Column(String(100), nullable=True)  # For detecting changes
    api_response_raw = Column(JSON, nullable=True)  # Store full response for debugging
    submission_success = Column(Boolean, default=False)
    quote_generated = Column(Boolean, default=False)
    
    # Navigation Links (for future API calls)
    api_links = Column(JSON, nullable=True)  # Store Guidewire API navigation links
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    work_item = relationship("WorkItem", backref="guidewire_response")
    submission = relationship("Submission", backref="guidewire_response")


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
