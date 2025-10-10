from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class AttachmentPayload(BaseModel):
    # Support both Logic Apps format and existing format
    filename: Optional[str] = Field(None, description="Name of the attachment file")
    name: Optional[str] = Field(None, description="Name of the attachment file (Logic Apps format)")
    contentBase64: Optional[str] = Field(None, description="Base64 encoded file content")
    contentBytes: Optional[str] = Field(None, description="Base64 encoded file content (Logic Apps format)")
    contentType: Optional[str] = Field(None, description="MIME type of the attachment")
    
    @property
    def get_filename(self) -> str:
        """Get filename from either format"""
        return self.filename or self.name or "unknown_file"
    
    @property 
    def get_content_base64(self) -> str:
        """Get base64 content from either format"""
        return self.contentBase64 or self.contentBytes or ""


class EmailIntakePayload(BaseModel):
    subject: Optional[str] = Field(None, description="Email subject line")
    sender_email: Optional[str] = Field(None, description="Email sender address")
    from_email: Optional[str] = Field(None, description="Email sender address (legacy)")
    from_: Optional[str] = Field(None, alias="from", description="Email sender address (Logic Apps format)")
    received_at: Optional[str] = Field(None, description="Email received timestamp")
    body: Optional[str] = Field(None, description="Email body content")
    attachments: List[AttachmentPayload] = Field(default_factory=list, description="List of email attachments")
    
    @property
    def get_sender_email(self) -> str:
        """Get sender email from any available format"""
        return self.sender_email or self.from_email or self.from_ or "unknown@sender.com"


class LogicAppsAttachment(BaseModel):
    """Logic Apps specific attachment format"""
    name: str = Field(..., description="Name of the attachment file")
    contentType: str = Field(..., description="MIME type of the attachment")
    contentBytes: str = Field(..., description="Base64 encoded file content")


class LogicAppsEmailPayload(BaseModel):
    """Logic Apps specific email payload format"""
    subject: Optional[str] = Field(default="", description="Email subject line")
    from_: Optional[str] = Field(default="", alias="from", description="Email sender address")
    received_at: Optional[str] = Field(default="", description="Email received timestamp in ISO format")
    receivedDateTime: Optional[str] = Field(default="", description="Email received timestamp (Logic Apps format)")
    body: Optional[str] = Field(default="", description="Email body content")
    attachments: List[LogicAppsAttachment] = Field(default_factory=list, description="List of email attachments")
    
    @property
    def safe_subject(self) -> str:
        """Get subject with fallback for empty/None values"""
        return str(self.subject or "No Subject")
    
    @property
    def safe_from(self) -> str:
        """Get sender with fallback for empty/None values"""
        return str(self.from_ or "unknown@sender.com")
    
    @property
    def safe_body(self) -> str:
        """Get body with fallback for empty/None values"""
        return str(self.body or "")
    
    @property
    def safe_received_at(self) -> str:
        """Get received_at with fallback for empty/None values, supporting both field names"""
        timestamp = self.received_at or self.receivedDateTime or datetime.utcnow().isoformat()
        return str(timestamp)


class EmailIntakeResponse(BaseModel):
    submission_ref: str
    submission_id: str  # Changed from int to str
    status: str
    message: str


class SubmissionResponse(BaseModel):
    id: int
    submission_id: str  # Changed from int to str
    submission_ref: str
    subject: str
    sender_email: str
    body_text: Optional[str] = None
    attachment_content: Optional[str] = None
    extracted_fields: Optional[Dict[str, Any]] = None
    assigned_to: Optional[str] = None
    task_status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SubmissionConfirmRequest(BaseModel):
    underwriter_email: Optional[str] = None


class SubmissionConfirmResponse(BaseModel):
    submission_id: str  # Changed from int to str to support string IDs like 'TEST-2025-001'
    submission_ref: str
    work_item_id: int
    assigned_to: str
    task_status: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# Enums for API responses
class WorkItemStatusEnum(str, Enum):
    PENDING = "Pending"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class WorkItemPriorityEnum(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class CompanySizeEnum(str, Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    ENTERPRISE = "Enterprise"


class UserRoleEnum(str, Enum):
    UNDERWRITER = "Underwriter"
    SENIOR_UNDERWRITER = "Senior_Underwriter"
    MANAGER = "Manager"
    RISK_ANALYST = "Risk_Analyst"


# Risk Assessment Models
class RiskCategories(BaseModel):
    technical: float = Field(..., ge=0, le=100, description="Technical risk score (0-100)")
    operational: float = Field(..., ge=0, le=100, description="Operational risk score (0-100)")
    financial: float = Field(..., ge=0, le=100, description="Financial risk score (0-100)")
    compliance: float = Field(..., ge=0, le=100, description="Compliance risk score (0-100)")


class RiskFactor(BaseModel):
    category: str = Field(..., description="Risk category")
    factor: str = Field(..., description="Risk factor description")
    impact: str = Field(..., description="Impact level (Low, Medium, High)")
    score: float = Field(..., ge=0, le=100, description="Risk factor score")


class RiskRecommendation(BaseModel):
    category: str = Field(..., description="Risk category")
    recommendation: str = Field(..., description="Recommendation text")
    priority: str = Field(..., description="Priority level (Low, Medium, High)")


class RiskAssessmentDetail(BaseModel):
    id: int
    work_item_id: int
    overall_risk_score: float = Field(..., ge=0, le=100)
    risk_categories: RiskCategories
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    recommendations: List[RiskRecommendation] = Field(default_factory=list)
    assessed_by: str
    assessed_by_name: str
    created_at: datetime
    updated_at: datetime


class RiskAssessmentRequest(BaseModel):
    overall_risk_score: float = Field(..., ge=0, le=100)
    risk_categories: RiskCategories
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    recommendations: List[RiskRecommendation] = Field(default_factory=list)


# Comment Models
class CommentDetail(BaseModel):
    id: int
    work_item_id: int
    author_id: str
    author_name: str
    content: str
    is_urgent: bool = False
    mentions: List[str] = Field(default_factory=list)
    parent_comment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    replies: List['CommentDetail'] = Field(default_factory=list)


class CommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    is_urgent: bool = False
    mentions: List[str] = Field(default_factory=list)
    parent_comment_id: Optional[int] = None


# User Models
class UserDetail(BaseModel):
    id: str
    name: str
    email: str
    role: UserRoleEnum
    specializations: List[str] = Field(default_factory=list)
    max_capacity: int = 25
    current_workload: int = 0
    is_available: bool = True
    avg_processing_time_days: Optional[float] = None
    success_rate: Optional[float] = None
    last_assignment: Optional[datetime] = None


class UserSearchResult(BaseModel):
    id: str
    name: str
    email: str


# Work Item Models
class WorkItemSummary(BaseModel):
    id: int
    submission_id: int
    submission_ref: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: WorkItemStatusEnum
    priority: WorkItemPriorityEnum
    assigned_to: Optional[str] = None
    risk_score: Optional[float] = None
    risk_categories: Optional[RiskCategories] = None
    industry: Optional[str] = None
    company_size: Optional[CompanySizeEnum] = None
    policy_type: Optional[str] = None
    coverage_amount: Optional[float] = None
    last_risk_assessment: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    comments_count: int = 0
    has_urgent_comments: bool = False
    extracted_fields: Optional[Dict[str, Any]] = None


class WorkItemDetail(BaseModel):
    id: int
    submission_id: int
    submission_ref: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: WorkItemStatusEnum
    priority: WorkItemPriorityEnum
    assigned_to: Optional[str] = None
    risk_score: Optional[float] = None
    risk_categories: Optional[RiskCategories] = None
    industry: Optional[str] = None
    company_size: Optional[CompanySizeEnum] = None
    policy_type: Optional[str] = None
    coverage_amount: Optional[float] = None
    last_risk_assessment: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    subject: Optional[str] = None  # From submission
    sender_email: Optional[str] = None  # From submission
    body_text: Optional[str] = None  # From submission
    attachment_content: Optional[str] = None  # From submission
    extracted_fields: Optional[Dict[str, Any]] = None  # From submission


class WorkItemUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkItemStatusEnum] = None
    priority: Optional[WorkItemPriorityEnum] = None
    assigned_to: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[CompanySizeEnum] = None
    policy_type: Optional[str] = None
    coverage_amount: Optional[float] = None


# History Models
class HistoryRecord(BaseModel):
    id: int
    action: str
    performed_by: str
    performed_by_name: str
    details: Optional[Dict[str, Any]] = None
    description: str
    timestamp: datetime


# Response Models
class PaginationInfo(BaseModel):
    page: int
    limit: int
    total_pages: int
    total_items: int


class WorkItemListResponse(BaseModel):
    work_items: List[WorkItemSummary]
    total: int
    pagination: PaginationInfo


class WorkItemDetailResponse(BaseModel):
    work_item: WorkItemDetail
    risk_assessment: Optional[RiskAssessmentDetail] = None
    comments: List[CommentDetail] = Field(default_factory=list)
    history: List[HistoryRecord] = Field(default_factory=list)


# Enhanced Polling Response (maintains compatibility)
class EnhancedPollingResponse(BaseModel):
    items: List[WorkItemSummary]
    count: int
    timestamp: str


# Assignment Models
class UnderwriterRecommendation(BaseModel):
    underwriter: UserDetail
    score: int = Field(..., ge=0, le=100)
    reasons: List[str]


class AssignmentRecommendationsResponse(BaseModel):
    recommendations: List[UnderwriterRecommendation]


class AssignmentRequest(BaseModel):
    assigned_to: str = Field(..., description="Email or ID of underwriter to assign")
    reason: Optional[str] = None


# Analytics Models
class IndustryRiskData(BaseModel):
    name: str
    average_risk_score: float
    application_count: int


class CoverageTypeData(BaseModel):
    name: str
    count: int
    percentage: float


class StatusDistributionData(BaseModel):
    status: str
    count: int


class RiskDistributionData(BaseModel):
    range: str
    count: int
    percentage: float


class CyberRiskByIndustryResponse(BaseModel):
    industries: List[IndustryRiskData]


class PolicyCoverageDistributionResponse(BaseModel):
    coverage_types: List[CoverageTypeData]


class WorkItemStatusDistributionResponse(BaseModel):
    status_distribution: List[StatusDistributionData]


class RiskScoreDistributionResponse(BaseModel):
    risk_distribution: List[RiskDistributionData]


# Guidewire Models
class GuidewireAccountInfo(BaseModel):
    """Account information from Guidewire"""
    guidewire_account_id: Optional[str] = None
    account_number: Optional[str] = None
    account_status: Optional[str] = None
    organization_name: Optional[str] = None
    number_of_contacts: Optional[int] = None


class GuidewireJobInfo(BaseModel):
    """Job/Submission information from Guidewire"""
    guidewire_job_id: Optional[str] = None
    job_number: Optional[str] = None
    job_status: Optional[str] = None
    job_effective_date: Optional[datetime] = None
    base_state: Optional[str] = None
    policy_number: Optional[str] = None
    policy_type: Optional[str] = None
    underwriting_company: Optional[str] = None
    producer_code: Optional[str] = None


class GuidewirePricingInfo(BaseModel):
    """Pricing information from Guidewire"""
    total_cost_amount: Optional[float] = None
    total_cost_currency: Optional[str] = None
    total_premium_amount: Optional[float] = None
    total_premium_currency: Optional[str] = None
    rate_as_of_date: Optional[datetime] = None


class GuidewireCoverageInfo(BaseModel):
    """Coverage information from Guidewire"""
    coverage_terms: Optional[Dict[str, Any]] = None
    coverage_display_values: Optional[Dict[str, Any]] = None


class GuidewireBusinessData(BaseModel):
    """Business data from Guidewire"""
    business_started_date: Optional[datetime] = None
    total_employees: Optional[int] = None
    total_revenues: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    industry_type: Optional[str] = None


class GuidewireResponseData(BaseModel):
    """Complete Guidewire response data for UI display"""
    id: int
    work_item_id: int
    submission_id: int
    
    # Account Information
    account_info: GuidewireAccountInfo
    
    # Job Information
    job_info: GuidewireJobInfo
    
    # Pricing Information
    pricing_info: GuidewirePricingInfo
    
    # Coverage Information
    coverage_info: GuidewireCoverageInfo
    
    # Business Data
    business_data: GuidewireBusinessData
    
    # Response Metadata
    response_checksum: Optional[str] = None
    submission_success: bool = False
    quote_generated: bool = False
    api_links: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuidewireSubmissionSummary(BaseModel):
    """Summary of Guidewire submission for dashboard display"""
    work_item_id: int
    account_number: Optional[str] = None
    job_number: Optional[str] = None
    organization_name: Optional[str] = None
    job_status: Optional[str] = None
    policy_type: Optional[str] = None
    total_cost_amount: Optional[float] = None
    total_cost_currency: Optional[str] = None
    job_effective_date: Optional[datetime] = None
    submission_success: bool = False
    quote_generated: bool = False
    created_at: datetime


# Fix forward reference
CommentDetail.model_rebuild()
