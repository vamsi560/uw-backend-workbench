"""
Corrected Guidewire PolicyCenter API Client
Implements the proper flow:
1. Email → Logic Apps → Data extraction → Database
2. Trigger Guidewire composite API → Create ACCOUNT in PolicyCenter  
3. Use account number + organization → Create SUBMISSION in PolicyCenter

This is the CORRECT two-step flow as explained by the user.
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
    base_url: str = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net"
    composite_endpoint: str = "/rest/composite/v1/composite"
    username: str = "su"
    password: str = "gw"
    timeout: int = 60

    @property
    def full_url(self) -> str:
        return f"{self.base_url}{self.composite_endpoint}"

class CorrectedGuidewireClient:
    """
    CORRECTED Guidewire Client implementing the proper two-step flow:
    Step 1: Create Account in PolicyCenter
    Step 2: Create Submission using the account
    """
    
    def __init__(self, config: Optional[GuidewireConfig] = None):
        self.config = config or GuidewireConfig()
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with authentication and headers"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'UW-Workbench-Corrected/1.0'
        })
        # Use HTTP Basic Auth as confirmed working
        self.session.auth = (self.config.username, self.config.password)
        logger.info("Corrected Guidewire client initialized with proper two-step flow")

    def create_cyber_submission_correct_flow(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CORRECTED IMPLEMENTATION: Two-step process
        Step 1: Create Account in PolicyCenter
        Step 2: Create Submission using account number + organization
        """
        try:
            logger.info("🔧 CORRECTED FLOW: Starting two-step Guidewire process")
            
            # STEP 1: Create Account in PolicyCenter
            logger.info("📋 STEP 1: Creating Account in PolicyCenter...")
            account_result = self._create_account_in_policy_center(submission_data)
            
            if not account_result.get("success"):
                logger.error("❌ Account creation failed in Step 1")
                return {
                    "success": False,
                    "error": "Account creation failed",
                    "message": account_result.get("message", "Unknown error in account creation"),
                    "step_failed": "account_creation"
                }
            
            account_id = account_result.get("account_id")
            account_number = account_result.get("account_number")
            organization_name = account_result.get("organization_name")
            
            logger.info(f"✅ STEP 1 SUCCESS: Account created")
            logger.info(f"   Account ID: {account_id}")
            logger.info(f"   Account Number: {account_number}")
            logger.info(f"   Organization: {organization_name}")
            
            # STEP 2: Create Submission using account number + organization
            logger.info("📄 STEP 2: Creating Submission using account...")
            submission_result = self._create_submission_with_account(
                account_id=account_id,
                account_number=account_number, 
                organization_name=organization_name,
                submission_data=submission_data
            )
            
            if not submission_result.get("success"):
                logger.error("❌ Submission creation failed in Step 2")
                # Still return account info since account was created successfully
                return {
                    "success": False,
                    "error": "Submission creation failed", 
                    "message": submission_result.get("message", "Unknown error in submission creation"),
                    "step_failed": "submission_creation",
                    "account_id": account_id,
                    "account_number": account_number,
                    "organization_name": organization_name
                }
            
            job_id = submission_result.get("job_id")
            job_number = submission_result.get("job_number")
            
            logger.info(f"✅ STEP 2 SUCCESS: Submission created")
            logger.info(f"   Job ID: {job_id}")
            logger.info(f"   Job Number: {job_number}")
            
            # COMPLETE SUCCESS - Both steps completed
            final_result = {
                "success": True,
                "simulation_mode": False,  # Real Guidewire integration
                "flow_type": "two_step_corrected",
                
                # Account information
                "account_id": account_id,
                "account_number": account_number,
                "organization_name": organization_name,
                
                # Submission information  
                "job_id": job_id,
                "job_number": job_number,
                
                # Combined data for database storage
                "parsed_data": {
                    **account_result.get("parsed_data", {}),
                    **submission_result.get("parsed_data", {})
                },
                "raw_response": {
                    "step1_account": account_result.get("raw_response", {}),
                    "step2_submission": submission_result.get("raw_response", {})
                },
                
                "message": "🎉 CORRECTED FLOW SUCCESS: Account and Submission created in PolicyCenter!"
            }
            
            logger.info("🎉 CORRECTED FLOW COMPLETE: Both account and submission created successfully!")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Error in corrected two-step flow: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "Two-step flow error",
                "message": f"Exception in corrected flow: {str(e)}",
                "flow_type": "two_step_corrected"
            }

    def _create_account_in_policy_center(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP 1: Create Account in PolicyCenter
        This creates the account that will be used for the submission
        """
        try:
            company_name = (submission_data.get("company_name") or 
                           submission_data.get("named_insured", "New Insurance Account"))
            
            # Add timestamp to ensure unique account names
            import random
            unique_suffix = f"{random.randint(100000, 999999)}"
            company_name_unique = f"{company_name} {unique_suffix}"
            
            # Create account payload - STEP 1 ONLY
            account_payload = {
                "requests": [
                    {
                        "method": "post",
                        "uri": "/account/v1/accounts",
                        "body": {
                            "data": {
                                "attributes": {
                                    "initialAccountHolder": {
                                        "contactSubtype": "Company",
                                        "companyName": company_name_unique,
                                        "taxId": submission_data.get("company_ein", "12-3456789"),
                                        "primaryAddress": {
                                            "addressLine1": submission_data.get("business_address", "123 Business St"),
                                            "city": submission_data.get("business_city", "San Francisco"),
                                            "postalCode": submission_data.get("business_zip", "94105"),
                                            "state": {"code": submission_data.get("business_state", "CA")}
                                        }
                                    },
                                    "initialPrimaryLocation": {
                                        "addressLine1": submission_data.get("business_address", "123 Business St"),
                                        "city": submission_data.get("business_city", "San Francisco"),
                                        "postalCode": submission_data.get("business_zip", "94105"),
                                        "state": {"code": submission_data.get("business_state", "CA")}
                                    },
                                    "producerCodes": [{"id": "pc:2"}],
                                    "organizationType": {"code": self._map_entity_type(submission_data.get("entity_type", "other"))}
                                }
                            }
                        }
                    }
                ]
            }
            
            logger.info(f"Creating account for: {company_name_unique}")
            
            # Submit account creation request
            response = self._submit_composite_request(account_payload)
            
            if response.get("success"):
                # Extract account information from response
                response_data = response.get("data", {})
                responses = response_data.get("responses", [])
                
                if responses and len(responses) > 0:
                    account_response = responses[0].get("body", {}).get("data", {}).get("attributes", {})
                    account_id = account_response.get("id")
                    account_number = account_response.get("accountNumber")
                    organization_name = account_response.get("accountHolderContact", {}).get("displayName", company_name_unique)
                    
                    return {
                        "success": True,
                        "account_id": account_id,
                        "account_number": account_number,
                        "organization_name": organization_name,
                        "parsed_data": {
                            "account_info": {
                                "guidewire_account_id": account_id,
                                "account_number": account_number,
                                "organization_name": organization_name,
                                "account_status": account_response.get("accountStatus", {}).get("code")
                            }
                        },
                        "raw_response": response
                    }
                else:
                    return {
                        "success": False,
                        "message": "No account response received",
                        "raw_response": response
                    }
            else:
                return {
                    "success": False,
                    "message": f"Account creation failed: {response.get('message', 'Unknown error')}",
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            return {
                "success": False,
                "message": f"Exception during account creation: {str(e)}"
            }

    def _create_submission_with_account(self, account_id: str, account_number: str, 
                                      organization_name: str, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP 2: Create Submission using the account number + organization
        This creates the actual insurance submission/job
        """
        try:
            # Create submission payload using the account we just created
            submission_payload = {
                "requests": [
                    {
                        "method": "post",
                        "uri": "/job/v1/jobs",
                        "body": {
                            "data": {
                                "attributes": {
                                    "accountId": account_id,  # Use the account ID from Step 1
                                    "jobType": "Submission",
                                    "product": {"code": "CyberLine"},
                                    "producerCodeId": "pc:2",
                                    "effectiveDate": submission_data.get("effective_date", "2025-01-01"),
                                    "expirationDate": self._calculate_expiry_date(submission_data.get("effective_date", "2025-01-01")),
                                    
                                    # Business and policy details
                                    "policyDetails": {
                                        "coverageAmount": submission_data.get("coverage_amount", "1000000"),
                                        "deductible": submission_data.get("deductible", "25000"),
                                        "policyType": submission_data.get("policy_type", "Cyber Liability"),
                                        "aggregateLimit": submission_data.get("coverage_amount", "1000000"),
                                        "perOccurrenceLimit": submission_data.get("coverage_amount", "1000000")
                                    },
                                    
                                    # Business information
                                    "businessDetails": {
                                        "industry": submission_data.get("industry", "technology"),
                                        "employeeCount": submission_data.get("employee_count", "50"),
                                        "annualRevenue": submission_data.get("annual_revenue", "5000000"),
                                        "dataTypes": submission_data.get("data_types", "Business Records"),
                                        "securityMeasures": submission_data.get("security_measures", "Standard Security"),
                                        "businessDescription": submission_data.get("business_description", f"Cyber insurance for {organization_name}")
                                    }
                                }
                            }
                        }
                    }
                ]
            }
            
            logger.info(f"Creating submission for account: {account_number} ({organization_name})")
            
            # Submit job/submission creation request
            response = self._submit_composite_request(submission_payload)
            
            if response.get("success"):
                # Extract submission information from response
                response_data = response.get("data", {})
                responses = response_data.get("responses", [])
                
                if responses and len(responses) > 0:
                    job_response = responses[0].get("body", {}).get("data", {}).get("attributes", {})
                    job_id = job_response.get("id")
                    job_number = job_response.get("jobNumber")
                    job_status = job_response.get("jobStatus", {}).get("code", "Draft")
                    
                    return {
                        "success": True,
                        "job_id": job_id,
                        "job_number": job_number,
                        "job_status": job_status,
                        "parsed_data": {
                            "job_info": {
                                "guidewire_job_id": job_id,
                                "job_number": job_number,
                                "job_status": job_status,
                                "job_effective_date": job_response.get("jobEffectiveDate"),
                                "base_state": job_response.get("baseState", {}).get("code"),
                                "policy_type": job_response.get("product", {}).get("code"),
                                "producer_code": job_response.get("producerCode", {}).get("id")
                            }
                        },
                        "raw_response": response
                    }
                else:
                    return {
                        "success": False,
                        "message": "No submission response received",
                        "raw_response": response
                    }
            else:
                return {
                    "success": False,
                    "message": f"Submission creation failed: {response.get('message', 'Unknown error')}",
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"Error creating submission: {str(e)}")
            return {
                "success": False,
                "message": f"Exception during submission creation: {str(e)}"
            }

    def _submit_composite_request(self, requests_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit composite request to Guidewire"""
        try:
            logger.debug(f"Submitting to {self.config.full_url}")
            
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
            
            # Parse JSON response
            try:
                result["data"] = response.json()
            except ValueError:
                result["data"] = response.text
            
            # Add error details if needed
            if not result["success"]:
                result["error"] = f"HTTP {response.status_code}"
                result["message"] = response.reason
                logger.error(f"Guidewire API error: {response.status_code} {response.reason}")
            else:
                logger.info(f"Guidewire API success: {response.status_code}")
            
            return result
            
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {
                "success": False,
                "error": "Request exception",
                "message": str(e)
            }

    def _calculate_expiry_date(self, effective_date: str) -> str:
        """Calculate policy expiry date (1 year from effective date)"""
        try:
            from datetime import datetime, timedelta
            if effective_date:
                dt = datetime.strptime(effective_date, "%Y-%m-%d")
                expiry_dt = dt.replace(year=dt.year + 1)
                return expiry_dt.strftime("%Y-%m-%d")
            else:
                expiry_dt = datetime.now() + timedelta(days=365)
                return expiry_dt.strftime("%Y-%m-%d")
        except:
            return "2026-01-01"

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
            "sole proprietorship": "soleproprietorship",
            "nonprofit": "nonprofit"
        }
        
        return entity_mapping.get(entity_type.lower(), "other")

    def store_guidewire_response(self, db: Session, work_item_id: int, submission_id: int, 
                                parsed_data: Dict[str, Any], raw_response: Dict[str, Any]) -> int:
        """Store Guidewire response data in database"""
        try:
            from database import GuidewireResponse
            
            # Extract account and job info
            account_info = parsed_data.get("account_info", {})
            job_info = parsed_data.get("job_info", {})
            
            guidewire_response = GuidewireResponse(
                work_item_id=work_item_id,
                submission_id=submission_id,
                
                # Account Information from Step 1
                guidewire_account_id=account_info.get("guidewire_account_id"),
                account_number=account_info.get("account_number"),
                account_status=account_info.get("account_status"),
                organization_name=account_info.get("organization_name"),
                
                # Job Information from Step 2  
                guidewire_job_id=job_info.get("guidewire_job_id"),
                job_number=job_info.get("job_number"),
                job_status=job_info.get("job_status"),
                policy_type=job_info.get("policy_type"),
                producer_code=job_info.get("producer_code"),
                
                # Response metadata
                api_response_raw=raw_response,
                submission_success=True,
                quote_generated=False  # May add quote generation as Step 3 later
            )
            
            db.add(guidewire_response)
            db.commit()
            db.refresh(guidewire_response)
            
            logger.info(f"Stored corrected flow Guidewire response for work item {work_item_id}")
            return guidewire_response.id
            
        except Exception as e:
            logger.error(f"Error storing Guidewire response: {str(e)}")
            db.rollback()
            raise

# Create the corrected global instance
corrected_guidewire_client = CorrectedGuidewireClient()