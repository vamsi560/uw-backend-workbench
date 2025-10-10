import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Google Gemini LLM"""
    
    def __init__(self):
        self.google_client = None
        
        # Initialize Google Gemini client with configured model
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.google_client = genai.GenerativeModel(settings.gemini_model)
    
    def extract_insurance_data(self, combined_text: str) -> Dict[str, Any]:
        """Extract structured insurance data from text using Google Gemini"""
        
        prompt = self._create_extraction_prompt(combined_text)
        
        try:
            if self.google_client:
                return self._extract_with_google(prompt)
            else:
                raise Exception("Google Gemini not configured")
                
        except Exception as e:
            logger.error(f"Error extracting data with Gemini: {str(e)}")
            # Return default structure if LLM fails
            return self._get_default_response()
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create the prompt for data extraction"""
        return f"""
You are an expert cyber insurance underwriter analyzing an insurance submission.
Extract the following information from the text and return ONLY a valid JSON object.

Text to analyze:
{text}

Extract these fields for comprehensive cyber insurance submission:
{{
        "agency_id": "Insurance agency or broker identifier",
        "agency_name": "Insurance agency or broker name",
        "agency_contact": "Agency contact person",
        "agency_email": "Agency contact email",
        "agency_phone": "Agency contact phone",
        "producer_name": "Producer or agent name",
        "producer_code": "Producer code or ID",
        "broker_name": "Insurance broker name (if different from agency)",
        "broker_contact": "Broker contact person",
        "broker_email": "Broker contact email",
        "broker_phone": "Broker contact phone",
        "company_name": "Name of the company requesting insurance",
        "named_insured": "Full legal name of the named insured",
        "dba_name": "Doing Business As name (if applicable)",
        "company_ein": "Company EIN/Tax ID number",
        "company_duns": "Company DUNS number",
        "company_naic": "NAIC code",
        "entity_type": "Entity type (Corporation, LLC, Partnership, etc.)",
        "insured_name": "Primary contact name or insured party name",
        "contact_name": "Primary contact person's name",
        "contact_title": "Primary contact's job title",
        "contact_email": "Primary contact email address",
        "contact_phone": "Primary contact phone number",
        "mailing_address": "Mailing address (street, city, state, zip)",
        "mailing_city": "Mailing address city",
        "mailing_state": "Mailing address state",
        "mailing_zip": "Mailing address ZIP code",
        "business_address": "Business address (street, city, state, zip)",
        "business_city": "Business address city",
        "business_state": "Business address state",
        "business_zip": "Business address ZIP code",
        "industry": "Industry sector (healthcare, technology, financial_services, etc.)",
        "industry_code": "SIC or NAICS industry code",
        "business_description": "Description of business operations",
        "company_size": "Company size (small, medium, large, enterprise)",
        "employee_count": "Number of employees",
        "annual_revenue": "Annual revenue amount",
        "years_in_business": "Years the company has been in operation",
        "current_policy_number": "Current policy number (if renewal)",
        "current_carrier": "Current insurance carrier",
        "current_expiration": "Current policy expiration date",
        "renewal_indicator": "Is this a renewal (yes/no)",
        "policy_type": "Type of cyber insurance policy",
        "coverage_amount": "Requested coverage amount/limit",
        "aggregate_limit": "Aggregate coverage limit",
        "per_occurrence_limit": "Per occurrence limit",
        "deductible": "Policy deductible amount",
        "self_insured_retention": "Self-insured retention amount",
        "effective_date": "Requested policy effective date",
        "expiry_date": "Requested policy expiry date",
        "policy_term": "Policy term (6 months, 1 year, etc.)",
        "privacy_liability_limit": "Privacy liability coverage limit",
        "network_security_limit": "Network security coverage limit",
        "data_breach_response_limit": "Data breach response coverage limit",
        "business_interruption_limit": "Business interruption coverage limit",
        "cyber_extortion_limit": "Cyber extortion coverage limit",
        "regulatory_fines_limit": "Regulatory fines coverage limit",
        "forensic_costs_limit": "Forensic costs coverage limit",
        "notification_costs_limit": "Notification costs coverage limit",
        "credit_monitoring_limit": "Credit monitoring coverage limit",
        "crisis_management_limit": "Crisis management coverage limit",
        "data_types": "Types of data handled (PII, PHI, payment data, etc.)",
        "records_count": "Number of records/data subjects",
        "pci_compliance": "PCI DSS compliance status",
        "hipaa_compliance": "HIPAA compliance status (if applicable)",
        "sox_compliance": "SOX compliance status (if applicable)",
        "gdpr_compliance": "GDPR compliance status (if applicable)",
        "ccpa_compliance": "CCPA compliance status (if applicable)",
        "iso27001_certified": "ISO 27001 certification status",
        "soc2_certified": "SOC 2 certification status",
        "other_certifications": "Other security certifications",
        "security_measures": "Security measures and controls in place",
        "incident_response_plan": "Incident response plan status",
        "business_continuity_plan": "Business continuity plan status",
        "disaster_recovery_plan": "Disaster recovery plan status",
        "employee_training": "Security awareness training program",
        "penetration_testing": "Penetration testing frequency",
        "vulnerability_scanning": "Vulnerability scanning program",
        "multi_factor_auth": "Multi-factor authentication implementation",
        "encryption_at_rest": "Data encryption at rest",
        "encryption_in_transit": "Data encryption in transit",
        "endpoint_protection": "Endpoint protection solution",
        "email_security": "Email security measures",
        "network_monitoring": "Network monitoring and logging",
        "access_controls": "Access control measures",
        "patch_management": "Patch management process",
        "cloud_services": "Cloud services usage",
        "cloud_providers": "Cloud service providers used",
        "remote_workforce_pct": "Percentage of remote workforce",
        "third_party_vendors": "Third party vendor relationships",
        "vendor_risk_management": "Vendor risk management program",
        "previous_breach": "Previous security incidents or breaches",
        "breach_details": "Details of previous breaches",
        "breach_costs": "Costs associated with previous breaches",
        "litigation_history": "Cyber-related litigation history",
        "regulatory_actions": "Previous regulatory actions",
        "website_url": "Company website URL",
        "annual_website_revenue": "Annual revenue from website/e-commerce",
        "mobile_apps": "Mobile applications operated",
        "api_endpoints": "Number of API endpoints",
        "databases": "Number and types of databases",
        "payment_processing": "Payment processing systems",
        "underwriter_name": "Assigned underwriter name",
        "underwriter_email": "Underwriter contact email",
        "submission_date": "Date of submission",
        "quote_deadline": "Quote deadline date",
        "bind_date": "Target bind date",
        "special_terms": "Special terms or conditions requested",
        "exclusions": "Requested exclusions",
        "additional_coverages": "Additional coverages requested",
        "remarks": "Additional remarks or notes"
}}

CRITICAL INSTRUCTIONS:
- Extract ALL available information, mark "Not specified" if information is not found
- For amounts: Convert to full numeric values (e.g., "$5 million" → "5000000", "$2.5M" → "2500000")
- For dates: Use YYYY-MM-DD format when possible
- For percentages: Extract as numbers (e.g., "25%" → "25")
- For yes/no fields: Use lowercase "yes" or "no"
- For company_name: Look for "Company Name:", organization names, or sender company
- For contact_email: Use the "From:" email address from the email header if no specific contact given
- For addresses: Extract complete addresses including street, city, state, zip
- For industry: Use lowercase (healthcare, technology, financial_services, manufacturing, etc.)
- For company_size: Use lowercase (small, medium, large, enterprise)
- For compliance fields: Look for certifications, standards compliance (SOC2, HIPAA, ISO27001, etc.)
- For security measures: Extract all mentioned security controls and technologies
- For coverage limits: Look for specific sublimits by coverage type
- For policy information: Extract renewal status, current carrier, expiration dates
- Return ONLY the JSON object, no additional text
- Ensure all field names match exactly as specified above
"""
    
    def _extract_with_google(self, prompt: str) -> Dict[str, Any]:
        """Extract data using Google Gemini"""
        try:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=settings.max_tokens,
                temperature=0.1,
            )
            
            response = self.google_client.generate_content(
                prompt, 
                generation_config=generation_config
            )
            content = response.text.strip()
            logger.info(f"Google Gemini response: {content}")
            return self._parse_json_response(content)
            
        except Exception as e:
            logger.error(f"Error with Google Gemini: {str(e)}")
            raise
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with improved error handling"""
        try:
            # Clean up response - remove any markdown formatting
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Handle truncated JSON by finding the last complete field
            if not content.endswith('}'):
                # Find the last comma and try to close the JSON
                last_comma = content.rfind(',')
                if last_comma != -1:
                    # Remove incomplete field after last comma and close JSON
                    content = content[:last_comma] + '\n}'
                    logger.warning("JSON response was truncated, attempting to fix")
                else:
                    # If no comma found, try just closing the brace
                    content = content + '\n}'
            
            # Parse JSON
            data = json.loads(content)
            
            # Validate required fields for cyber insurance
            required_fields = ["company_name", "insured_name", "contact_email", "industry", "coverage_amount", "policy_type", "effective_date"]
            for field in required_fields:
                if field not in data:
                    data[field] = "Not specified"
            
            # If policy_type is not specified, default to "cyber" since this is a cyber insurance system
            if data.get("policy_type") == "Not specified" or not data.get("policy_type"):
                data["policy_type"] = "cyber"
            
            logger.info(f"Successfully parsed JSON response with {len(data)} fields")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            logger.error(f"Raw content length: {len(content)}")
            # Try extracting partial data from malformed JSON
            return self._extract_partial_data(content)
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return self._get_default_response()
    
    def _extract_partial_data(self, content: str) -> Dict[str, Any]:
        """Extract partial data from malformed JSON"""
        try:
            # Start with default response
            data = self._get_default_response()
            
            # Try to extract key-value pairs using regex
            import re
            
            # Look for JSON field patterns
            patterns = [
                r'"company_name":\s*"([^"]*)"',
                r'"industry":\s*"([^"]*)"',
                r'"policy_type":\s*"([^"]*)"',
                r'"insured_name":\s*"([^"]*)"',
                r'"contact_email":\s*"([^"]*)"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    field_name = pattern.split('"')[1]
                    data[field_name] = match.group(1)
            
            logger.info(f"Extracted partial data from malformed JSON: {data}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to extract partial data: {e}")
            return self._get_default_response()
    
    def _get_default_response(self) -> Dict[str, Any]:
        """Return default response when LLM fails"""
        return {
            "company_name": "Not specified",
            "insured_name": "Not specified",
            "contact_email": "Not specified",
            "contact_name": "Not specified",
            "industry": "Not specified",
            "company_size": "Not specified",
            "coverage_amount": "Not specified",
            "policy_type": "cyber",  # Default to cyber since this is a cyber insurance system
            "effective_date": "Not specified",
            "expiry_date": "Not specified",
            "data_types": "Not specified",
            "security_measures": "Not specified",
            "compliance_certifications": "Not specified",
            "previous_incidents": "Not specified",
            "business_type": "Not specified"
        }

    def summarize_submission(self, subject: Optional[str], body_text: Optional[str], extracted_fields: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a concise underwriting-oriented summary for a submission.

        Returns a dict with keys: summary, key_points, risk_flags.
        """
        try:
            extracted_json = json.dumps(extracted_fields or {}, ensure_ascii=False)
            subject_text = subject or ""
            body = body_text or ""
            prompt = f"""
You are an expert cyber insurance underwriter. Summarize the submission succinctly for triage.

Subject: {subject_text}

Extracted Fields JSON:
{extracted_json}

Email/Notes:
{body}

Return ONLY valid JSON with the following structure:
{{
  "summary": "1-2 sentences overall context",
  "key_points": ["3-6 short bullets with concrete facts"],
  "risk_flags": ["0-5 bullets highlighting potential underwriting risks if any"]
}}
"""

            if not self.google_client:
                key_points = []
                if extracted_fields:
                    for k in [
                        "company_name", "industry", "coverage_amount", "policy_type", "effective_date"
                    ]:
                        v = extracted_fields.get(k)
                        if v is not None and str(v) != "Not specified":
                            # Convert to string safely to handle both string and numeric values
                            key_points.append(f"{k.replace('_',' ').title()}: {str(v)}")
                summary = subject_text or "Submission summary not available"
                risk_flags = []
                return {"summary": summary, "key_points": key_points[:6], "risk_flags": risk_flags}

            generation_config = genai.types.GenerationConfig(
                max_output_tokens=min(getattr(settings, "max_tokens", 512), 768),
                temperature=0.2,
            )
            response = self.google_client.generate_content(prompt, generation_config=generation_config)
            content = (response.text or "").strip()
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)

            if not isinstance(data, dict):
                raise ValueError("LLM summarize response not a JSON object")
            for key in ["summary", "key_points", "risk_flags"]:
                if key not in data:
                    data[key] = [] if key != "summary" else ""
            if not isinstance(data.get("key_points"), list):
                data["key_points"] = [str(data.get("key_points"))]
            if not isinstance(data.get("risk_flags"), list):
                data["risk_flags"] = [str(data.get("risk_flags"))]
            data["summary"] = str(data.get("summary", ""))
            return data
        except Exception as e:
            logger.error("Error generating submission summary", exc_info=e)
            return {
                "summary": subject or "Submission",
                "key_points": [],
                "risk_flags": []
            }


# Global instance
llm_service = LLMService()
