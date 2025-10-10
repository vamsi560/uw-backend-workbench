"""
Guidewire PolicyCenter API Client
Handles authentication and API interactions with Guidewire PC composite endpoint
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import uuid
from dataclasses import dataclass
from config import settings
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

@dataclass
class GuidewireConfig:
    """Configuration for Guidewire API connection"""
    base_url: str = settings.guidewire_base_url
    composite_endpoint: str = "/rest/composite/v1/composite"
    auth_endpoint: str = settings.guidewire_auth_endpoint
    username: str = settings.guidewire_username
    password: str = settings.guidewire_password
    bearer_token: str = settings.guidewire_bearer_token
    timeout: int = settings.guidewire_timeout
    token_buffer: int = settings.guidewire_token_buffer
    
    @property
    def full_url(self) -> str:
        return f"{self.base_url}{self.composite_endpoint}"
    
    @property
    def auth_url(self) -> str:
        return f"{self.base_url}{self.auth_endpoint}"

class GuidewireClient:
    """
    Client for interacting with Guidewire PolicyCenter API
    Supports the composite endpoint for multi-step operations with automatic token refresh
    """
    
    def __init__(self, config: Optional[GuidewireConfig] = None):
        self.config = config or GuidewireConfig()
        self.session = requests.Session()
        self._current_token = None
        self._token_expires_at = None
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with authentication and headers"""
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'UW-Workbench/1.0'
        })
        
        # Setup authentication - will be handled dynamically
        logger.info("Guidewire client initialized - tokens will be generated as needed")
    
    def _generate_token(self) -> Optional[str]:
        """Generate a new bearer token using username/password"""
        if not (self.config.username and self.config.password):
            logger.error("Username and password required for token generation")
            return None
            
        try:
            # Prepare authentication request
            auth_payload = {
                "username": self.config.username,
                "password": self.config.password
            }
            
            logger.info(f"Generating new Guidewire token from {self.config.auth_url}")
            
            # Make authentication request
            response = requests.post(
                self.config.auth_url,
                json=auth_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                token = auth_data.get('token') or auth_data.get('access_token') or auth_data.get('bearerToken')
                
                if token:
                    # Calculate expiration time (usually provided in response)
                    expires_in = auth_data.get('expires_in', 3600)  # Default 1 hour
                    self._token_expires_at = datetime.now().timestamp() + expires_in
                    
                    logger.info(f"Successfully generated Guidewire token (expires in {expires_in}s)")
                    return token
                else:
                    logger.error(f"Token not found in response: {auth_data}")
                    return None
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Token generation failed: {str(e)}")
            return None
    
    def _is_token_valid(self) -> bool:
        """Check if current token is still valid"""
        if not self._current_token or not self._token_expires_at:
            return False
        
        # Check if token expires within buffer time
        current_time = datetime.now().timestamp()
        buffer_time = self.config.token_buffer  # seconds before expiry
        
        return current_time < (self._token_expires_at - buffer_time)
    
    def _ensure_valid_token(self) -> bool:
        """Ensure we have valid authentication"""
        # Priority 1: Use static bearer token if provided
        if self.config.bearer_token:
            if not self._current_token:
                self._current_token = self.config.bearer_token
                self.session.headers.update({
                    'Authorization': f'Bearer {self._current_token}'
                })
                logger.info("Using static bearer token (no expiry management)")
            return True
        
        # Priority 2: Use basic authentication with username/password (RECOMMENDED)
        if self.config.username and self.config.password:
            # Set up basic authentication - no token generation needed
            self.session.auth = (self.config.username, self.config.password)
            logger.info("Using HTTP Basic Authentication (su/gw)")
            return True
        
        # Priority 3: Dynamic token generation (fallback)
        if not self._is_token_valid():
            logger.info("Token expired or missing, generating new token...")
            new_token = self._generate_token()
            if new_token:
                self._current_token = new_token
                # Update session headers
                self.session.headers.update({
                    'Authorization': f'Bearer {self._current_token}'
                })
                return True
            else:
                logger.error("Failed to generate new token")
                return False
        
        return True
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Guidewire API
        Returns connection status and basic info
        """
        try:
            # Ensure we have valid authentication
            if not self._ensure_valid_token():
                return {
                    "success": False,
                    "message": "Failed to authenticate with Guidewire",
                    "error": "Authentication failed"
                }
            
            # Try a simple GET to test connectivity (use basic endpoints)
            response = self.session.get(
                self.config.base_url + "/rest",
                timeout=self.config.timeout
            )
            
            return {
                "success": True,
                "status_code": response.status_code,
                "url": response.url,
                "headers": dict(response.headers),
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "message": "Connection successful"
            }
            
        except requests.exceptions.ConnectTimeout:
            return {
                "success": False,
                "error": "Connection timeout",
                "message": f"Timeout after {self.config.timeout} seconds"
            }
        except requests.exceptions.ConnectionError as e:
            return {
                "success": False,
                "error": "Connection error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Unexpected error",
                "message": str(e)
            }
    
    def submit_composite_request(self, requests_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a composite request to Guidewire PC
        
        Args:
            requests_payload: The composite request payload with multiple operations
            
        Returns:
            Dictionary with response data and status
        """
        try:
            # Ensure we have valid authentication before making the request
            if not self._ensure_valid_token():
                return {
                    "success": False,
                    "error": "Authentication failed",
                    "message": "Could not establish authentication"
                }
            
            logger.info(f"Submitting composite request to {self.config.full_url}")
            logger.debug(f"Payload: {json.dumps(requests_payload, indent=2)}")
            
            response = self.session.post(
                self.config.full_url,
                json=requests_payload,
                timeout=self.config.timeout
            )
            
            result = {
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "url": response.url
            }
            
            # Try to parse JSON response
            try:
                result["data"] = response.json()
            except ValueError:
                result["data"] = response.text
            
            # Add error details if request failed
            if not result["success"]:
                result["error"] = f"HTTP {response.status_code}"
                result["message"] = response.reason
                logger.error(f"Guidewire API error: {response.status_code} {response.reason}")
            else:
                logger.info(f"Guidewire API success: {response.status_code}")
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timeout",
                "message": f"Request timed out after {self.config.timeout} seconds"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": "Request error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Unexpected error",
                "message": str(e)
            }
    
    def create_cyber_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a complete cyber insurance submission using the composite endpoint
        
        Args:
            submission_data: Extracted data from our work item
            
        Returns:
            Dictionary with submission results including account ID, job ID, and quote
        """
        # Map our data to Guidewire format
        guidewire_payload = self._map_to_guidewire_format(submission_data)
        
        # Submit to Guidewire
        response = self.submit_composite_request(guidewire_payload)
        
        if response["success"]:
            # Extract key IDs and information from response
            return self._extract_submission_results(response)
        else:
            return response
    
    def _map_to_guidewire_format(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map our extracted submission data to Guidewire's expected format
        Based on the cyberlinerequest.json template
        """
        # Enhanced mapping with comprehensive field support
        base_request = {
            "requests": [
                {
                    "method": "post",
                    "uri": "/account/v1/accounts",
                    "body": {
                        "data": {
                            "attributes": {
                                "initialAccountHolder": {
                                    "contactSubtype": "Company",
                                    "companyName": submission_data.get("company_name") or submission_data.get("named_insured", "Unknown Company"),
                                    "taxId": submission_data.get("company_ein", "00-0000000"),
                                    "primaryAddress": {
                                        "addressLine1": submission_data.get("business_address") or submission_data.get("mailing_address", "Address Not Provided"),
                                        "city": submission_data.get("business_city") or submission_data.get("mailing_city", "Unknown"),
                                        "postalCode": submission_data.get("business_zip") or submission_data.get("mailing_zip", "00000"),
                                        "state": {
                                            "code": submission_data.get("business_state") or submission_data.get("mailing_state", "CA")
                                        }
                                    },
                                    # Add primary contact information
                                    "primaryContact": {
                                        "name": submission_data.get("contact_name") or submission_data.get("insured_name", "Unknown Contact"),
                                        "emailAddress": submission_data.get("contact_email"),
                                        "phoneNumber": submission_data.get("contact_phone"),
                                        "jobTitle": submission_data.get("contact_title")
                                    }
                                },
                                "initialPrimaryLocation": {
                                    "addressLine1": submission_data.get("business_address") or submission_data.get("mailing_address", "Address Not Provided"),
                                    "city": submission_data.get("business_city") or submission_data.get("mailing_city", "Unknown"),
                                    "postalCode": submission_data.get("business_zip") or submission_data.get("mailing_zip", "00000"),
                                    "state": {
                                        "code": submission_data.get("business_state") or submission_data.get("mailing_state", "CA")
                                    }
                                },
                                "producerCodes": [{"id": self._get_producer_code(submission_data)}],
                                "organizationType": {"code": self._map_entity_type(submission_data.get("entity_type", "other"))},
                                # Add industry classification
                                "industryCode": self._map_industry_code(submission_data.get("industry"))
                            }
                        }
                    },
                    "vars": [
                        {"name": "accountId", "path": "$.data.attributes.id"},
                        {"name": "driverId", "path": "$.data.attributes.accountHolder.id"}
                    ]
                },
                {
                    "method": "post",
                    "uri": "/job/v1/submissions",
                    "body": {
                        "data": {
                            "attributes": {
                                "account": {"id": "${accountId}"},
                                "baseState": {"code": submission_data.get("business_state") or submission_data.get("mailing_state", "CA")},
                                "jobEffectiveDate": submission_data.get("effective_date", datetime.now().strftime("%Y-%m-%d")),
                                "producerCode": {"id": "pc:16"},
                                "product": {"id": "USCyber"},
                                # Add policy information
                                "policyType": self._map_policy_type(submission_data.get("policy_type")),
                                "renewalIndicator": submission_data.get("renewal_indicator", "no") == "yes"
                            }
                        }
                    },
                    "vars": [
                        {"name": "jobId", "path": "$.data.attributes.id"}
                    ]
                }
            ]
        }
        
        # Add coverage configuration
        coverage_limits = self._calculate_coverage_limits(submission_data)
        base_request["requests"].append({
            "method": "post",
            "uri": "/job/v1/jobs/${jobId}/lines/USCyberLine/coverages",
            "body": {
                "data": {
                    "attributes": {
                        "pattern": {"id": "ACLCommlCyberLiability"},
                        "terms": coverage_limits
                    }
                }
            }
        })
        
        # Add business data
        business_data = self._map_business_data(submission_data)
        base_request["requests"].append({
            "method": "patch",
            "uri": "/job/v1/jobs/${jobId}/lines/USCyberLine",
            "body": {
                "data": {
                    "attributes": business_data
                }
            }
        })
        
        # Add quote request
        base_request["requests"].append({
            "method": "post",
            "uri": "/job/v1/jobs/${jobId}/quote"
        })
        
        return base_request
    
    def _calculate_coverage_limits(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate appropriate coverage limits based on submission data with comprehensive mapping"""
        # Parse main coverage amount
        coverage_amount = submission_data.get("coverage_amount", "50000")
        try:
            coverage_value = int(float(str(coverage_amount).replace("$", "").replace(",", "")))
        except:
            coverage_value = 50000
        
        # Parse specific sublimits if provided
        bus_inc_limit = self._parse_limit(submission_data.get("business_interruption_limit"), 10000)
        extortion_limit = self._parse_limit(submission_data.get("cyber_extortion_limit"), 5000)
        deductible = self._parse_limit(submission_data.get("deductible"), 7500)
        
        # Map to Guidewire's coverage codes based on amounts
        if coverage_value >= 1000000:
            return {
                "ACLCommlCyberLiabilityBusIncLimit": {"choiceValue": self._get_coverage_code(bus_inc_limit, "bus_inc")},
                "ACLCommlCyberLiabilityCyberAggLimit": {"choiceValue": self._get_coverage_code(coverage_value, "aggregate")},
                "ACLCommlCyberLiabilityExtortion": {"choiceValue": self._get_coverage_code(extortion_limit, "extortion")},
                "ACLCommlCyberLiabilityPublicRelations": {"choiceValue": {"code": "25Kusd", "name": "25,000"}},
                "ACLCommlCyberLiabilityRetention": {"choiceValue": self._get_coverage_code(deductible, "retention")},
                "ACLCommlCyberLiabilityWaitingPeriod": {"choiceValue": {"code": "12HR", "name": "12 hrs"}}
            }
        else:
            return {
                "ACLCommlCyberLiabilityBusIncLimit": {"choiceValue": self._get_coverage_code(bus_inc_limit, "bus_inc")},
                "ACLCommlCyberLiabilityCyberAggLimit": {"choiceValue": self._get_coverage_code(coverage_value, "aggregate")},
                "ACLCommlCyberLiabilityExtortion": {"choiceValue": self._get_coverage_code(extortion_limit, "extortion")},
                "ACLCommlCyberLiabilityPublicRelations": {"choiceValue": {"code": "5Kusd", "name": "5,000"}},
                "ACLCommlCyberLiabilityRetention": {"choiceValue": self._get_coverage_code(deductible, "retention")},
                "ACLCommlCyberLiabilityWaitingPeriod": {"choiceValue": {"code": "12HR", "name": "12 hrs"}}
            }
    
    def _map_business_data(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map business information to Guidewire format with comprehensive fields"""
        # Parse employee count
        try:
            employees = int(submission_data.get("employee_count", "0"))
        except:
            employees = 0
        
        # Parse revenue
        try:
            revenue = float(str(submission_data.get("annual_revenue", "0")).replace("$", "").replace(",", ""))
        except:
            revenue = 0.0
        
        # Parse years in business for business start date
        business_start_date = submission_data.get("effective_date")
        if submission_data.get("years_in_business"):
            try:
                years_in_business = int(submission_data.get("years_in_business"))
                start_year = datetime.now().year - years_in_business
                business_start_date = f"{start_year}-01-01T00:00:00.000Z"
            except:
                pass
        
        if not business_start_date:
            business_start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        return {
            "aclDateBusinessStarted": business_start_date,
            "aclPolicyType": {"code": "commercialcyber", "name": "Commercial Cyber"},
            "aclTotalAssets": str(revenue * 1.5),  # Estimate assets as 1.5x revenue
            "aclTotalFTEmployees": employees,
            "aclTotalLiabilities": str(revenue * 0.3),  # Estimate liabilities
            "aclTotalPTEmployees": int(submission_data.get("remote_workforce_pct", "0")) * employees // 100 if submission_data.get("remote_workforce_pct") else 0,
            "aclTotalPayroll": str(employees * 50000),  # Estimate $50k per employee
            "aclTotalRevenues": str(revenue),
            # Add additional business fields
            "aclIndustryType": self._map_industry_code(submission_data.get("industry")),
            "aclBusinessDescription": submission_data.get("business_description", "")[:500],  # Truncate to reasonable length
            "aclDataTypes": self._map_data_types(submission_data.get("data_types")),
            "aclRecordsCount": int(submission_data.get("records_count", "0")) if submission_data.get("records_count") else 0,
            "aclWebsiteRevenue": float(str(submission_data.get("annual_website_revenue", "0")).replace("$", "").replace(",", "")) if submission_data.get("annual_website_revenue") else 0.0
        }
    
    def _map_data_types(self, data_types) -> str:
        """Map data types to Guidewire format"""
        if not data_types:
            return "general"
        
        # Convert common data type descriptions to codes
        data_type_mapping = {
            "pii": "personally_identifiable",
            "phi": "protected_health",
            "payment": "payment_card",
            "financial": "financial_data",
            "medical": "protected_health",
            "credit card": "payment_card", 
            "personal": "personally_identifiable",
            "customer pii": "personally_identifiable",
            "intellectual property": "intellectual_property"
        }
        
        # Handle both string and list inputs
        if isinstance(data_types, list):
            # Join list items and convert to lowercase for matching
            data_types_str = " ".join(data_types).lower()
        else:
            data_types_str = str(data_types).lower()
        
        # Find the best match
        for key, value in data_type_mapping.items():
            if key in data_types_str:
                return value
        
        return "general"
    
    def _extract_submission_results(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key information from successful submission response"""
        try:
            responses = response["data"]["responses"]
            
            # Extract account info from first response
            account_response = responses[0]["body"]["data"]["attributes"]
            account_id = account_response["id"]
            account_number = account_response["accountNumber"]
            
            # Extract job info from second response
            job_response = responses[1]["body"]["data"]["attributes"]
            job_id = job_response["id"]
            job_number = job_response["jobNumber"]
            
            # Extract quote info from last response (if available)
            quote_info = {}
            if len(responses) >= 5:
                quote_response = responses[4]["body"]["data"]["attributes"]
                quote_info = {
                    "total_cost": quote_response.get("totalCost", {}),
                    "total_premium": quote_response.get("totalPremium", {}),
                    "job_status": quote_response.get("jobStatus", {}),
                    "rate_date": quote_response.get("rateAsOfDate")
                }
            
            # Parse comprehensive response data for database storage
            parsed_data = self._parse_guidewire_response(responses)
            
            return {
                "success": True,
                "account_id": account_id,
                "account_number": account_number,
                "job_id": job_id,
                "job_number": job_number,
                "quote_info": quote_info,
                "parsed_data": parsed_data,
                "raw_response": response,  # Include raw response for storage
                "message": "Submission created successfully in Guidewire"
            }
            
        except (KeyError, IndexError) as e:
            return {
                "success": False,
                "error": "Response parsing error",
                "message": f"Could not extract submission data: {str(e)}"
            }
    
    def _parse_guidewire_response(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse comprehensive Guidewire response data for database storage"""
        try:
            parsed = {
                "account_info": {},
                "job_info": {},
                "pricing_info": {},
                "coverage_info": {},
                "business_data": {},
                "metadata": {}
            }
            
            # Parse account information (first response)
            if len(responses) > 0:
                account_data = responses[0]["body"]["data"]["attributes"]
                parsed["account_info"] = {
                    "guidewire_account_id": account_data.get("id"),
                    "account_number": account_data.get("accountNumber"),
                    "account_status": account_data.get("accountStatus", {}).get("code"),
                    "organization_name": account_data.get("accountHolderContact", {}).get("displayName"),
                    "number_of_contacts": int(account_data.get("numberOfContacts", "0")) if account_data.get("numberOfContacts") else 0
                }
            
            # Parse job/submission information (second response)
            if len(responses) > 1:
                job_data = responses[1]["body"]["data"]["attributes"]
                parsed["job_info"] = {
                    "guidewire_job_id": job_data.get("id"),
                    "job_number": job_data.get("jobNumber"),
                    "job_status": job_data.get("jobStatus", {}).get("code"),
                    "job_effective_date": job_data.get("jobEffectiveDate"),
                    "base_state": job_data.get("baseState", {}).get("code"),
                    "policy_type": job_data.get("product", {}).get("id"),
                    "producer_code": job_data.get("producerCode", {}).get("id")
                }
            
            # Parse coverage information (third response)
            if len(responses) > 2:
                coverage_data = responses[2]["body"]["data"]["attributes"]
                terms = coverage_data.get("terms", {})
                coverage_display = {}
                coverage_terms = {}
                
                for term_name, term_data in terms.items():
                    if "choiceValue" in term_data:
                        coverage_terms[term_name] = term_data["choiceValue"]
                        coverage_display[term_name] = term_data["choiceValue"].get("name", "")
                
                parsed["coverage_info"] = {
                    "coverage_terms": coverage_terms,
                    "coverage_display_values": coverage_display
                }
            
            # Parse business data (fourth response)
            if len(responses) > 3:
                business_data = responses[3]["body"]["data"]["attributes"]
                parsed["business_data"] = {
                    "business_started_date": business_data.get("aclDateBusinessStarted"),
                    "total_employees": business_data.get("aclTotalFTEmployees"),
                    "total_revenues": float(business_data.get("aclTotalRevenues", 0)) if business_data.get("aclTotalRevenues") else None,
                    "total_assets": float(business_data.get("aclTotalAssets", 0)) if business_data.get("aclTotalAssets") else None,
                    "total_liabilities": float(business_data.get("aclTotalLiabilities", 0)) if business_data.get("aclTotalLiabilities") else None,
                    "industry_type": business_data.get("aclIndustryType")
                }
            
            # Parse quote/pricing information (fifth response)
            if len(responses) > 4:
                quote_data = responses[4]["body"]["data"]["attributes"]
                total_cost = quote_data.get("totalCost", {})
                total_premium = quote_data.get("totalPremium", {})
                
                parsed["pricing_info"] = {
                    "total_cost_amount": float(total_cost.get("amount", 0)) if total_cost.get("amount") else None,
                    "total_cost_currency": total_cost.get("currency"),
                    "total_premium_amount": float(total_premium.get("amount", 0)) if total_premium.get("amount") else None,
                    "total_premium_currency": total_premium.get("currency"),
                    "rate_as_of_date": quote_data.get("rateAsOfDate"),
                    "underwriting_company": quote_data.get("uwCompany", {}).get("displayName")
                }
                
                # Extract API links for future operations
                if "links" in quote_data:
                    parsed["metadata"]["api_links"] = quote_data["links"]
            
            # Add metadata
            parsed["metadata"].update({
                "submission_success": True,
                "quote_generated": len(responses) > 4,
                "response_checksum": self._calculate_checksum(responses)
            })
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing Guidewire response: {str(e)}")
            return {"error": f"Failed to parse response: {str(e)}"}
    
    def _calculate_checksum(self, data: Any) -> str:
        """Calculate checksum for response data to detect changes"""
        import hashlib
        import json
        
        try:
            json_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(json_str.encode()).hexdigest()
        except:
            return "checksum_error"
    
    def store_guidewire_response(self, db: Session, work_item_id: int, submission_id: int, 
                                parsed_data: Dict[str, Any], raw_response: Dict[str, Any]) -> int:
        """Store Guidewire response data in database for UI display"""
        try:
            # Import here to avoid circular imports
            from database import GuidewireResponse
            
            # Parse datetime strings
            def parse_datetime(date_str):
                if not date_str:
                    return None
                try:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    return None
            
            # Create GuidewireResponse record
            guidewire_response = GuidewireResponse(
                work_item_id=work_item_id,
                submission_id=submission_id,
                
                # Account Information
                guidewire_account_id=parsed_data.get("account_info", {}).get("guidewire_account_id"),
                account_number=parsed_data.get("account_info", {}).get("account_number"),
                account_status=parsed_data.get("account_info", {}).get("account_status"),
                organization_name=parsed_data.get("account_info", {}).get("organization_name"),
                number_of_contacts=parsed_data.get("account_info", {}).get("number_of_contacts"),
                
                # Job Information
                guidewire_job_id=parsed_data.get("job_info", {}).get("guidewire_job_id"),
                job_number=parsed_data.get("job_info", {}).get("job_number"),
                job_status=parsed_data.get("job_info", {}).get("job_status"),
                job_effective_date=parse_datetime(parsed_data.get("job_info", {}).get("job_effective_date")),
                base_state=parsed_data.get("job_info", {}).get("base_state"),
                policy_type=parsed_data.get("job_info", {}).get("policy_type"),
                producer_code=parsed_data.get("job_info", {}).get("producer_code"),
                underwriting_company=parsed_data.get("pricing_info", {}).get("underwriting_company"),
                
                # Coverage Information
                coverage_terms=parsed_data.get("coverage_info", {}).get("coverage_terms"),
                coverage_display_values=parsed_data.get("coverage_info", {}).get("coverage_display_values"),
                
                # Pricing Information
                total_cost_amount=parsed_data.get("pricing_info", {}).get("total_cost_amount"),
                total_cost_currency=parsed_data.get("pricing_info", {}).get("total_cost_currency"),
                total_premium_amount=parsed_data.get("pricing_info", {}).get("total_premium_amount"),
                total_premium_currency=parsed_data.get("pricing_info", {}).get("total_premium_currency"),
                rate_as_of_date=parse_datetime(parsed_data.get("pricing_info", {}).get("rate_as_of_date")),
                
                # Business Data
                business_started_date=parse_datetime(parsed_data.get("business_data", {}).get("business_started_date")),
                total_employees=parsed_data.get("business_data", {}).get("total_employees"),
                total_revenues=parsed_data.get("business_data", {}).get("total_revenues"),
                total_assets=parsed_data.get("business_data", {}).get("total_assets"),
                total_liabilities=parsed_data.get("business_data", {}).get("total_liabilities"),
                industry_type=parsed_data.get("business_data", {}).get("industry_type"),
                
                # Response Metadata
                response_checksum=parsed_data.get("metadata", {}).get("response_checksum"),
                api_response_raw=raw_response,
                submission_success=parsed_data.get("metadata", {}).get("submission_success", False),
                quote_generated=parsed_data.get("metadata", {}).get("quote_generated", False),
                api_links=parsed_data.get("metadata", {}).get("api_links")
            )
            
            db.add(guidewire_response)
            db.commit()
            db.refresh(guidewire_response)
            
            logger.info(f"Stored Guidewire response data for work item {work_item_id}")
            return guidewire_response.id
            
        except Exception as e:
            logger.error(f"Error storing Guidewire response: {str(e)}")
            db.rollback()
            raise
    
    def _get_producer_code(self, submission_data: Dict[str, Any]) -> str:
        """Get producer code from submission data"""
        producer_code = submission_data.get("producer_code")
        if producer_code:
            return f"pc:{producer_code}"
        return "pc:2"  # Default
    
    def _map_entity_type(self, entity_type: str) -> str:
        """Map entity type to Guidewire codes"""
        if not entity_type:
            return "other"
        
        entity_mapping = {
            "corporation": "corporation",
            "corp": "corporation", 
            "llc": "llc",
            "limited liability company": "llc",
            "partnership": "partnership",
            "sole proprietorship": "sole_proprietorship",
            "nonprofit": "nonprofit"
        }
        
        return entity_mapping.get(entity_type.lower(), "other")
    
    def _map_industry_code(self, industry: str) -> str:
        """Map industry to appropriate code"""
        if not industry:
            return "other"
        
        industry_mapping = {
            "technology": "tech",
            "healthcare": "healthcare",
            "financial_services": "financial",
            "manufacturing": "manufacturing", 
            "retail": "retail",
            "education": "education",
            "government": "government"
        }
        
        return industry_mapping.get(industry.lower(), "other")
    
    def _map_policy_type(self, policy_type: str) -> str:
        """Map policy type to Guidewire format"""
        if not policy_type:
            return "cyber"
        
        policy_mapping = {
            "cyber": "cyber",
            "cyber liability": "cyber",
            "comprehensive cyber liability": "cyber",
            "data breach": "cyber"
        }
        
        return policy_mapping.get(policy_type.lower(), "cyber")
    
    def _parse_limit(self, limit_str: str, default: int) -> int:
        """Parse coverage limit from string"""
        if not limit_str:
            return default
        
        try:
            # Remove currency symbols and commas
            clean_str = str(limit_str).replace("$", "").replace(",", "")
            
            # Handle K/M suffixes
            if clean_str.lower().endswith('k'):
                return int(float(clean_str[:-1])) * 1000
            elif clean_str.lower().endswith('m'):
                return int(float(clean_str[:-1])) * 1000000
            else:
                return int(float(clean_str))
        except:
            return default
    
    def _get_coverage_code(self, amount: int, coverage_type: str) -> Dict[str, str]:
        """Get Guidewire coverage code based on amount and type"""
        # Standard coverage codes mapping
        coverage_codes = {
            "aggregate": {
                25000: {"code": "25Kusd", "name": "25,000"},
                50000: {"code": "50Kusd", "name": "50,000"},
                100000: {"code": "100Kusd", "name": "100,000"},
                250000: {"code": "250Kusd", "name": "250,000"},
                500000: {"code": "500Kusd", "name": "500,000"},
                1000000: {"code": "1Musd", "name": "1,000,000"},
                2000000: {"code": "2Musd", "name": "2,000,000"},
                5000000: {"code": "5Musd", "name": "5,000,000"}
            },
            "bus_inc": {
                10000: {"code": "10Kusd", "name": "10,000"},
                25000: {"code": "25Kusd", "name": "25,000"},
                50000: {"code": "50Kusd", "name": "50,000"},
                100000: {"code": "100Kusd", "name": "100,000"},
                250000: {"code": "250Kusd", "name": "250,000"}
            },
            "extortion": {
                5000: {"code": "5Kusd", "name": "5,000"},
                10000: {"code": "10Kusd", "name": "10,000"},
                25000: {"code": "25Kusd", "name": "25,000"},
                50000: {"code": "50Kusd", "name": "50,000"}
            },
            "retention": {
                1000: {"code": "1Kusd", "name": "1,000"},
                2500: {"code": "25Kusd", "name": "2,500"},
                5000: {"code": "5Kusd", "name": "5,000"},
                7500: {"code": "75Kusd", "name": "7,500"},
                10000: {"code": "10Kusd", "name": "10,000"}
            }
        }
        
        # Find closest match
        type_codes = coverage_codes.get(coverage_type, coverage_codes["aggregate"])
        
        # Find closest available option
        closest_amount = min(type_codes.keys(), key=lambda x: abs(x - amount))
        return type_codes[closest_amount]

# Global instance
guidewire_client = GuidewireClient()