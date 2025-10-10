"""
Business Configuration for Cyber Insurance Underwriting
Centralizes all business rules, thresholds, and settings
"""

from typing import Dict, List, Any
from enum import Enum

class BusinessConfig:
    """Central configuration for all business rules and settings"""
    
    # Coverage limits by industry (in millions)
    INDUSTRY_COVERAGE_LIMITS = {
        "healthcare": 25,
        "financial_services": 50,
        "banking": 50,
        "insurance": 40,
        "technology": 30,
        "manufacturing": 20,
        "retail": 15,
        "education": 10,
        "government": 35,
        "energy": 30,
        "telecommunications": 25,
        "legal": 20,
        "consulting": 10,
        "real_estate": 15,
        "transportation": 20,
        "hospitality": 15,
        "media": 15,
        "nonprofit": 5,
        "other": 10
    }
    
    # Risk scoring weights
    RISK_WEIGHTS = {
        "industry_risk": 0.25,
        "coverage_amount": 0.20,
        "company_size": 0.15,
        "security_measures": 0.20,
        "compliance_certifications": 0.10,
        "previous_incidents": 0.10
    }
    
    # Industry risk multipliers
    INDUSTRY_RISK_MULTIPLIERS = {
        "healthcare": 1.8,
        "financial_services": 1.9,
        "banking": 1.9,
        "insurance": 1.7,
        "technology": 1.6,
        "government": 1.8,
        "energy": 1.7,
        "telecommunications": 1.6,
        "legal": 1.5,
        "manufacturing": 1.3,
        "retail": 1.4,
        "education": 1.2,
        "consulting": 1.1,
        "real_estate": 1.0,
        "transportation": 1.2,
        "hospitality": 1.1,
        "media": 1.2,
        "nonprofit": 0.9,
        "other": 1.0
    }
    
    # Company size risk factors
    COMPANY_SIZE_RISK_FACTORS = {
        "small": 0.8,      # Less complex infrastructure
        "medium": 1.0,     # Baseline
        "large": 1.3,      # More complex, higher exposure
        "enterprise": 1.6  # Highest complexity and exposure
    }
    
    # Underwriter assignments by industry and coverage
    UNDERWRITER_ASSIGNMENTS = {
        "senior_underwriters": {
            "industries": ["healthcare", "financial_services", "banking", "government"],
            "min_coverage": 20_000_000
        },
        "standard_underwriters": {
            "industries": ["technology", "insurance", "energy", "telecommunications", "legal"],
            "min_coverage": 5_000_000
        },
        "junior_underwriters": {
            "industries": ["manufacturing", "retail", "education", "consulting", "real_estate", 
                         "transportation", "hospitality", "media", "nonprofit", "other"],
            "min_coverage": 0
        }
    }
    
    # Available underwriters
    UNDERWRITER_POOL = {
        "senior": ["Sarah Mitchell", "Robert Chen", "Maria Rodriguez"],
        "standard": ["James Wilson", "Lisa Thompson", "David Park", "Jennifer Lee"],
        "junior": ["Michael Brown", "Ashley Davis", "Kevin Zhang", "Rachel Green", "Alex Johnson"]
    }
    
    # Status transition rules
    VALID_STATUS_TRANSITIONS = {
        "pending": ["assigned", "rejected", "under_review"],
        "assigned": ["under_review", "pending_info", "rejected"],
        "under_review": ["pending_info", "quote_ready", "rejected", "assigned"],
        "pending_info": ["under_review", "rejected"],
        "quote_ready": ["approved", "rejected", "under_review"],
        "approved": ["policy_issued", "rejected"],
        "rejected": [],  # Terminal state
        "policy_issued": []  # Terminal state
    }
    
    # Required fields by validation level
    REQUIRED_FIELDS = {
        "basic": [
            "company_name", "industry", "contact_email"
        ],
        "standard": [
            "company_name", "industry", "contact_email", "company_size", 
            "coverage_amount", "policy_type"
        ],
        "complete": [
            "company_name", "industry", "contact_email", "company_size",
            "coverage_amount", "policy_type", "revenue", "employee_count",
            "data_types", "security_measures"
        ]
    }
    
    # Auto-rejection criteria
    AUTO_REJECTION_CRITERIA = {
        "min_coverage": 100_000,     # Minimum viable coverage
        "max_coverage": 100_000_000, # Maximum coverage without special approval
        "high_risk_industries": [],   # Industries requiring special review
        "blacklisted_domains": [      # Email domains to auto-reject
            "spam.com", "test.com", "fake.com"
        ]
    }
    
    # Risk category thresholds
    RISK_THRESHOLDS = {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.8,
        "critical": 1.0
    }
    
    # Priority calculation thresholds
    PRIORITY_THRESHOLDS = {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.8
    }
    
    # Message templates
    MESSAGE_TEMPLATES = {
        "assignment_notification": {
            "subject": "New Cyber Insurance Submission Assigned - {work_item_title}",
            "body": """
Dear {underwriter_name},

A new cyber insurance submission has been assigned to you:

Work Item ID: {work_item_id}
Company: {company_name}
Industry: {industry}
Coverage Amount: ${coverage_amount:,.2f}
Priority: {priority}
Risk Score: {risk_score:.2f}

Please review the submission in the underwriting workbench.

Best regards,
Cyber Insurance System
            """
        },
        "rejection_notification": {
            "subject": "Cyber Insurance Application Status - {company_name}",
            "body": """
Dear {contact_name},

Thank you for your interest in our cyber insurance coverage. After reviewing your application, we regret to inform you that we cannot proceed with your request at this time.

Reason: {rejection_reason}

If you believe this decision was made in error or if your circumstances have changed, please don't hesitate to contact us.

Best regards,
Underwriting Team
            """
        },
        "info_request": {
            "subject": "Additional Information Required - {company_name}",
            "body": """
Dear {contact_name},

We are reviewing your cyber insurance application and require additional information to proceed:

Missing Information:
{missing_fields}

Please provide this information at your earliest convenience so we can continue processing your application.

Best regards,
{underwriter_name}
Underwriting Team
            """
        }
    }
    
    @classmethod
    def get_industry_coverage_limit(cls, industry: str) -> int:
        """Get maximum coverage limit for an industry (in millions)"""
        industry_str = str(industry).lower() if industry else ""
        return cls.INDUSTRY_COVERAGE_LIMITS.get(industry_str, cls.INDUSTRY_COVERAGE_LIMITS["other"])
    
    @classmethod
    def get_industry_risk_multiplier(cls, industry: str) -> float:
        """Get risk multiplier for an industry"""
        industry_str = str(industry).lower() if industry else ""
        return cls.INDUSTRY_RISK_MULTIPLIERS.get(industry_str, 1.0)
    
    @classmethod
    def get_company_size_risk_factor(cls, company_size: str) -> float:
        """Get risk factor for company size"""
        company_size_str = str(company_size).lower() if company_size else ""
        return cls.COMPANY_SIZE_RISK_FACTORS.get(company_size_str, 1.0)
    
    @classmethod
    def get_available_underwriters(cls, level: str) -> List[str]:
        """Get list of available underwriters by level"""
        return cls.UNDERWRITER_POOL.get(level, [])
    
    @classmethod
    def is_valid_status_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if status transition is valid"""
        from_status_str = str(from_status).lower() if from_status else ""
        to_status_str = str(to_status).lower() if to_status else ""
        valid_transitions = cls.VALID_STATUS_TRANSITIONS.get(from_status_str, [])
        return to_status_str in valid_transitions
    
    @classmethod
    def get_required_fields(cls, validation_level: str = "standard") -> List[str]:
        """Get required fields for validation level"""
        return cls.REQUIRED_FIELDS.get(validation_level, cls.REQUIRED_FIELDS["standard"])
    
    @classmethod
    def should_auto_reject(cls, extracted_data: Dict[str, Any]) -> tuple[bool, str]:
        """Check if submission should be auto-rejected"""
        
        # Check coverage amount
        coverage = extracted_data.get("coverage_amount", 0)
        if isinstance(coverage, str):
            try:
                coverage = float(coverage.replace("$", "").replace(",", ""))
            except:
                coverage = 0
        
        if coverage < cls.AUTO_REJECTION_CRITERIA["min_coverage"]:
            return True, f"Coverage amount too low (minimum ${cls.AUTO_REJECTION_CRITERIA['min_coverage']:,})"
        
        if coverage > cls.AUTO_REJECTION_CRITERIA["max_coverage"]:
            return True, f"Coverage amount too high (maximum ${cls.AUTO_REJECTION_CRITERIA['max_coverage']:,} without special approval)"
        
        # Check email domain
        email = extracted_data.get("contact_email", "")
        if email:
            domain = email.split("@")[-1].lower()
            if domain in cls.AUTO_REJECTION_CRITERIA["blacklisted_domains"]:
                return True, f"Email domain not accepted: {domain}"
        
        return False, ""
    
    @classmethod
    def calculate_risk_priority(cls, risk_score: float) -> str:
        """Calculate priority based on risk score"""
        if risk_score >= cls.PRIORITY_THRESHOLDS["high"]:
            return "high"
        elif risk_score >= cls.PRIORITY_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "low"
    
    @classmethod
    def get_message_template(cls, template_name: str) -> Dict[str, str]:
        """Get message template by name"""
        return cls.MESSAGE_TEMPLATES.get(template_name, {})


# Export main config class
__all__ = ["BusinessConfig"]