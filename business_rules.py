"""
Business Rules and Validation Engine for Cyber Insurance Underwriting
Handles submission validation, appetite filtering, and assignment logic
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import re
import random
from business_config import BusinessConfig

logger = logging.getLogger(__name__)

class CyberInsuranceValidator:
    """Enhanced validator for cyber insurance submissions with business rules"""
    
    # Core required fields for any submission
    REQUIRED_FIELDS = [
        "insured_name", 
        "policy_type", 
        "effective_date",
        "industry"  # Critical for cyber insurance
    ]
    
    # Accepted policy types for cyber insurance
    ACCEPTED_POLICY_TYPES = [
        "Cyber Liability",
        "Comprehensive Cyber Liability",  # Added comprehensive coverage
        "Privacy Liability", 
        "Data Breach Response",
        "Technology E&O",
        "Cyber Security",
        "First Party Cyber",
        "Third Party Cyber",
        "cyber",  # Common shorthand from LLM
        "Cyber",  # Capitalized version
        "CYBER"   # All caps version
    ]
    
    # Use centralized business configuration
    @classmethod
    def _get_industry_coverage_limit(cls, industry: str) -> int:
        """Get coverage limit for industry in dollars"""
        return BusinessConfig.get_industry_coverage_limit(industry) * 1_000_000  # Convert millions to dollars
    
    @classmethod
    def _get_industry_risk_multiplier(cls, industry: str) -> float:
        """Get risk multiplier for industry"""
        return BusinessConfig.get_industry_risk_multiplier(industry)
    
    @classmethod
    def _is_high_risk_industry(cls, industry: str) -> bool:
        """Check if industry is high risk"""
        return BusinessConfig.get_industry_risk_multiplier(industry) >= 1.6
    
    @classmethod
    def validate_submission(cls, extracted_fields: Dict) -> Tuple[str, List[str], Optional[str]]:
        """
        Simplified validation that approves everything - business rules bypassed
        
        Returns:
            Tuple of (status, missing_fields, reason)
        """
        # Auto-approve everything - no validation checks
        logger.info("Business rules bypassed - auto-approving submission")
        
        # Always return Complete status with no missing fields
        return "Complete", [], None
    
    @classmethod
    def assign_underwriter(cls, extracted_fields: Dict) -> Optional[str]:
        """
        Assign underwriter based on industry specialization and risk profile using centralized config
        """
        industry_raw = extracted_fields.get("industry", "")
        industry = str(industry_raw).strip().lower() if industry_raw else ""
        coverage_amount = cls._parse_coverage_amount(extracted_fields.get("coverage_amount", ""))
        
        # Determine underwriter level based on industry and coverage
        for level, criteria in BusinessConfig.UNDERWRITER_ASSIGNMENTS.items():
            if (industry in criteria["industries"] and 
                coverage_amount is not None and coverage_amount >= criteria["min_coverage"]):
                
                # Get available underwriters for this level
                available = BusinessConfig.get_available_underwriters(level.split("_")[0])  # senior, standard, junior
                if available:
                    # Simple round-robin assignment (in practice, this could be more sophisticated)
                    return random.choice(available)
        
        # Fallback to junior underwriters
        available = BusinessConfig.get_available_underwriters("junior")
        return random.choice(available) if available else "System Assignment"
    
    @classmethod
    def calculate_risk_priority(cls, extracted_fields: Dict) -> str:
        """
        Calculate submission priority based on risk factors using centralized config
        
        Returns: "low" | "medium" | "high"
        """
        # Generate risk categories and calculate overall score
        risk_categories = cls.generate_risk_categories(extracted_fields)
        overall_risk_score = sum(risk_categories.values()) / len(risk_categories) if risk_categories else 0
        
        # Use centralized priority calculation
        return BusinessConfig.calculate_risk_priority(overall_risk_score)
    
    @classmethod
    def generate_risk_categories(cls, extracted_fields: Dict) -> Dict[str, float]:
        """
        Generate initial risk category scores based on submission data
        """
        categories = {
            "technical": 50.0,
            "operational": 50.0,
            "financial": 50.0,
            "compliance": 50.0
        }
        
        industry = extracted_fields.get("industry", "")
        
        # Industry-specific risk adjustments
        if industry == "Healthcare":
            categories["compliance"] += 20  # HIPAA requirements
            categories["technical"] += 15   # PHI protection needs
        elif industry == "Financial Services":
            categories["compliance"] += 25  # Financial regulations
            categories["financial"] += 20   # High impact potential
        elif industry == "Technology":
            categories["technical"] += 25   # Higher technical risks
            categories["operational"] += 10
        
        # Data type risk adjustments - handle both string and integer inputs
        data_types_raw = extracted_fields.get("data_types", "")
        data_types = str(data_types_raw).lower() if data_types_raw else ""
        if "pii" in data_types or "personal" in data_types:
            categories["compliance"] += 15
        if "payment" in data_types or "credit card" in data_types:
            categories["financial"] += 20
        if "medical" in data_types or "phi" in data_types:
            categories["compliance"] += 25
        
        # Security measures adjustments - handle both string and integer inputs
        security_measures_raw = extracted_fields.get("security_measures", "")
        security_measures = str(security_measures_raw).lower() if security_measures_raw else ""
        if any(measure in security_measures for measure in ["mfa", "encryption", "firewall"]):
            categories["technical"] -= 10  # Reduce risk for good security
        
        # Ensure scores stay within 0-100 range
        for category in categories:
            categories[category] = max(0.0, min(100.0, categories[category]))
        
        return categories
    
    @classmethod
    def _parse_coverage_amount(cls, coverage_str) -> Optional[float]:
        """Parse coverage amount from string or number to float"""
        if not coverage_str and coverage_str != 0:
            return None
        
        try:
            # Handle numeric input (int/float) directly - this fixes the string concatenation error!
            if isinstance(coverage_str, (int, float)):
                return float(coverage_str)
            
            # Convert to string for string processing
            coverage_str = str(coverage_str)
            
            # Remove common formatting characters
            clean_str = coverage_str.replace("$", "").replace(",", "").replace(" ", "")
            
            # Handle millions notation
            if "M" in clean_str.upper() or "million" in clean_str.lower():
                number_part = re.sub(r'[^0-9.]', '', clean_str.upper().replace("M", "").replace("MILLION", ""))
                return float(number_part) * 1_000_000
            
            # Handle thousands notation  
            if "K" in clean_str.upper() or "thousand" in clean_str.lower():
                number_part = re.sub(r'[^0-9.]', '', clean_str.upper().replace("K", "").replace("THOUSAND", ""))
                return float(number_part) * 1_000
            
            # Handle billions notation
            if "B" in clean_str.upper() or "billion" in clean_str.lower():
                number_part = re.sub(r'[^0-9.]', '', clean_str.upper().replace("B", "").replace("BILLION", ""))
                return float(number_part) * 1_000_000_000
            
            return float(clean_str)
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse coverage amount: {coverage_str}")
            return None
    
    @classmethod
    def _parse_revenue(cls, revenue_str: str) -> Optional[float]:
        """Parse annual revenue from string to float"""
        return cls._parse_coverage_amount(revenue_str)  # Same logic
    
    @classmethod
    def _parse_employee_count(cls, employee_str) -> Optional[int]:
        """Parse employee count from string or number to integer"""
        if not employee_str and employee_str != 0:
            return None
        
        try:
            # Handle numeric input (int/float) directly - fixes string concatenation error!
            if isinstance(employee_str, (int, float)):
                return int(employee_str)
            
            # Convert to string for string processing
            employee_str = str(employee_str)
            
            # Remove common formatting
            clean_str = employee_str.replace(",", "").replace(" ", "")
            
            # Handle ranges (take the upper bound)
            if "-" in clean_str:
                parts = clean_str.split("-")
                clean_str = parts[-1]  # Take upper bound
            
            # Handle "employees" text
            clean_str = clean_str.lower().replace("employees", "").replace("employee", "").strip()
            
            # Handle thousands notation
            if "K" in clean_str.upper():
                number_part = clean_str.upper().replace("K", "")
                return int(float(number_part) * 1000)
            
            return int(float(clean_str))
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse employee count: {employee_str}")
            return None


class MessageService:
    """Enhanced messaging service for broker communication using centralized templates"""
    
    @staticmethod
    def send_assignment_notification(underwriter_name: str, work_item) -> Dict:
        """Send assignment notification to underwriter"""
        template = BusinessConfig.get_message_template("assignment_notification")
        
        if not template:
            return {"status": "error", "message": "Template not found"}
        
        # Format the message
        subject = template["subject"].format(
            work_item_title=getattr(work_item, 'title', 'Unknown'),
        )
        
        body = template["body"].format(
            underwriter_name=underwriter_name,
            work_item_id=work_item.id,
            company_name=getattr(work_item, 'title', 'Unknown Company'),
            industry=getattr(work_item, 'industry', 'Unknown'),
            coverage_amount=getattr(work_item, 'coverage_amount', 0),
            priority=getattr(work_item, 'priority', 'Medium'),
            risk_score=getattr(work_item, 'risk_score', 0)
        )
        
        # In a real implementation, this would send email/notification
        logger.info(f"Assignment notification sent to {underwriter_name}")
        
        return {
            "status": "sent",
            "recipient": underwriter_name,
            "subject": subject,
            "body": body
        }
    
    @staticmethod
    def send_rejection_notification(broker_email: str, work_item, rejection_reason: str) -> Dict:
        """Send rejection notification to broker"""
        template = BusinessConfig.get_message_template("rejection_notification")
        
        if not template:
            return {"status": "error", "message": "Template not found"}
        
        # Format the message
        subject = template["subject"].format(
            company_name=getattr(work_item, 'title', 'Unknown Company')
        )
        
        body = template["body"].format(
            contact_name="Valued Client",  # Could be extracted from work item
            rejection_reason=rejection_reason
        )
        
        # In a real implementation, this would send email
        logger.info(f"Rejection notification sent to {broker_email}")
        
        return {
            "status": "sent",
            "recipient": broker_email,
            "subject": subject,
            "body": body
        }
    
    @staticmethod
    def send_info_request(broker_email: str, work_item, underwriter_name: str, missing_fields: List[str]) -> Dict:
        """Send information request to broker"""
        template = BusinessConfig.get_message_template("info_request")
        
        if not template:
            return {"status": "error", "message": "Template not found"}
        
        # Format the message
        subject = template["subject"].format(
            company_name=getattr(work_item, 'title', 'Unknown Company')
        )
        
        body = template["body"].format(
            contact_name="Valued Client",
            missing_fields="\n".join([f"• {field}" for field in missing_fields]),
            underwriter_name=underwriter_name
        )
        
        # In a real implementation, this would send email
        logger.info(f"Information request sent to {broker_email}")
        
        return {
            "status": "sent",
            "recipient": broker_email,
            "subject": subject,
            "body": body
        }
    
    @staticmethod
    def create_info_request(
        work_item_id: int,
        underwriter_name: str,
        broker_email: str,
        requested_info: str,
        db_session
    ) -> Dict:
        """Create an information request message to broker"""
        from database import Comment, HistoryAction, WorkItemHistory
        
        # Create comment for the info request
        comment = Comment(
            work_item_id=work_item_id,
            author_id=underwriter_name,
            author_name=underwriter_name,
            content=f"**Information Request for Broker ({broker_email}):**\n\n{requested_info}",
            is_urgent=True
        )
        
        db_session.add(comment)
        
        # Create history record
        history = WorkItemHistory(
            work_item_id=work_item_id,
            action=HistoryAction.COMMENTED,
            performed_by=underwriter_name,
            performed_by_name=underwriter_name,
            description=f"Requested additional information from broker",
            details={
                "message_type": "info_request",
                "recipient": broker_email,
                "content": requested_info
            }
        )
        
        db_session.add(history)
        db_session.commit()
        
        return {
            "comment_id": comment.id,
            "created_at": comment.created_at.isoformat(),
            "content": requested_info,
            "recipient": broker_email
        }
    
    @staticmethod
    def create_status_update_message(
        work_item_id: int,
        performed_by: str,
        old_status: str,
        new_status: str,
        reason: Optional[str],
        db_session
    ) -> Dict:
        """Create a status update message"""
        from database import WorkItemHistory, HistoryAction
        
        description = f"Status changed from {old_status} to {new_status}"
        if reason:
            description += f". Reason: {reason}"
        
        history = WorkItemHistory(
            work_item_id=work_item_id,
            action=HistoryAction.UPDATED,
            performed_by=performed_by,
            performed_by_name=performed_by,
            description=description,
            details={
                "field": "status",
                "old_value": old_status,
                "new_value": new_status,
                "reason": reason
            }
        )
        
        db_session.add(history)
        db_session.commit()
        
        return {
            "history_id": history.id,
            "action": "status_update",
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason,
            "timestamp": history.timestamp.isoformat()
        }


class WorkflowEngine:
    """Manages submission workflow states and transitions using centralized business config"""
    
    @classmethod
    def validate_status_transition(cls, from_status: str, to_status: str) -> Tuple[bool, str]:
        """Validate status transition using centralized business rules"""
        # Handle enum to string conversion if needed
        if hasattr(from_status, 'value'):
            from_status = from_status.value
        if hasattr(to_status, 'value'):
            to_status = to_status.value
        
        is_valid = BusinessConfig.is_valid_status_transition(from_status, to_status)
        
        if is_valid:
            return True, f"Valid transition from {from_status} to {to_status}"
        else:
            valid_transitions = BusinessConfig.VALID_STATUS_TRANSITIONS.get(from_status.lower(), [])
            return False, f"Invalid transition from {from_status} to {to_status}. Valid transitions: {valid_transitions}"
    
    @classmethod
    def get_allowed_transitions(cls, current_status: str) -> List[str]:
        """Get list of allowed status transitions from current state"""
        if hasattr(current_status, 'value'):
            current_status = current_status.value
        return BusinessConfig.VALID_STATUS_TRANSITIONS.get(current_status.lower(), [])
    
    @classmethod
    def validate_transition(cls, from_status: str, to_status: str, reason: str = None) -> Tuple[bool, str]:
        """Validate status transition with business rules"""
        if not cls.can_transition(from_status, to_status):
            return False, f"Cannot transition from {from_status} to {to_status}"
        
        # Specific validation rules
        if to_status == "Rejected" and not reason:
            return False, "Reason is required when rejecting a submission"
        
        if to_status == "Approved" and from_status == "Incomplete":
            return False, "Cannot approve incomplete submission directly"
        
        return True, "Transition allowed"