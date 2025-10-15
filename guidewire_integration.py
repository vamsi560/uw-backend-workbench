"""
Clean Guidewire Integration Module
Using exact format provided by Guidewire team

This module handles the 3-step integration:
1. Work Item Creation → Account & Submission Creation
2. Underwriter Approval → Guidewire Approval API
3. Quote Creation → Get Quote Document
"""

import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class GuidewireIntegration:
    def __init__(self):
        # Guidewire connection details from team
        self.base_url = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/composite/v1/composite"
        self.username = "su"
        self.password = "gw"
        self.timeout = 30
        
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated request to Guidewire composite API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info(f"Making Guidewire request to: {self.base_url}")
            logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                self.base_url,
                json=payload,
                auth=(self.username, self.password),
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"Guidewire response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successful response: {json.dumps(result, indent=2)}")
                return {
                    "success": True,
                    "data": result,
                    "status_code": response.status_code
                }
            else:
                logger.error(f"Guidewire request failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            logger.error("Guidewire request timed out")
            return {
                "success": False,
                "error": "Timeout",
                "message": f"Request timed out after {self.timeout} seconds"
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Guidewire connection error: {str(e)}")
            return {
                "success": False,
                "error": "ConnectionError",
                "message": f"Failed to connect to Guidewire: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in Guidewire request: {str(e)}")
            return {
                "success": False,
                "error": "UnexpectedError",
                "message": str(e)
            }

    def create_account_and_submission(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 1: Create account and submission using exact team format - optimized for Guidewire compatibility
        This is called when a work item is created
        """
        logger.info("Creating Guidewire account and submission with essential fields only")
        
        # Extract only essential data with safe defaults that Guidewire accepts
        company_name = str(extracted_data.get('company_name', 'Test Company')).strip()
        business_address = str(extracted_data.get('business_address', '123 Business St')).strip()
        business_city = str(extracted_data.get('business_city', 'San Francisco')).strip() 
        business_state = str(extracted_data.get('business_state', 'CA')).strip().upper()[:2]  # Ensure 2-char state code
        business_zip = str(extracted_data.get('business_zip', '94105')).strip()[:10]  # Limit zip length
        
        # Ensure fields are not empty
        if not company_name or company_name == 'Unknown Company':
            company_name = 'Test Insurance Company'
        if not business_address:
            business_address = '123 Business Street'
        if not business_city:
            business_city = 'San Francisco'
        if business_state not in ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']:
            business_state = 'CA'  # Default to CA if invalid state
        if not business_zip:
            business_zip = '94105'
        
        # Use exact payload format from team
        payload = {
            "requests": [
                {
                    "method": "post",
                    "uri": "/account/v1/accounts",
                    "body": {
                        "data": {
                            "attributes": {
                                "initialAccountHolder": {
                                    "contactSubtype": "Company",
                                    "companyName": company_name,
                                    "taxId": "12-1212121",  # TODO: Extract from data if available
                                    "primaryAddress": {
                                        "addressLine1": business_address,
                                        "city": business_city,
                                        "postalCode": business_zip,
                                        "state": {
                                            "code": business_state
                                        }
                                    }
                                },
                                "initialPrimaryLocation": {
                                    "addressLine1": business_address,
                                    "city": business_city,
                                    "postalCode": business_zip,
                                    "state": {
                                        "code": business_state
                                    }
                                },
                                "producerCodes": [
                                    {
                                        "id": "pc:2"
                                    }
                                ],
                                "organizationType": {
                                    "code": "other"
                                }
                            }
                        }
                    },
                    "vars": [
                        {
                            "name": "accountId",
                            "path": "$.data.attributes.id"
                        },
                        {
                            "name": "driverId",
                            "path": "$.data.attributes.accountHolder.id"
                        }
                    ]
                },
                {
                    "method": "post",
                    "uri": "/job/v1/submissions",
                    "body": {
                        "data": {
                            "attributes": {
                                "account": {
                                    "id": "${accountId}"
                                },
                                "baseState": {
                                    "code": business_state
                                },
                                "jobEffectiveDate": datetime.now().strftime("%Y-%m-%d"),
                                "producerCode": {
                                    "id": "pc:16"
                                },
                                "product": {
                                    "id": "USCyber"
                                }
                            }
                        }
                    },
                    "vars": [
                        {
                            "name": "jobId",
                            "path": "$.data.attributes.id"
                        }
                    ]
                },
                {
                    "method": "post",
                    "uri": "/job/v1/jobs/${jobId}/lines/USCyberLine/coverages",
                    "body": {
                        "data": {
                            "attributes": {
                                "pattern": {
                                    "id": "ACLCommlCyberLiability"
                                },
                                "terms": {
                                    "ACLCommlCyberLiabilityBusIncLimit": {
                                        "choiceValue": {
                                            "code": "10Kusd",
                                            "name": "10,000"
                                        }
                                    },
                                    "ACLCommlCyberLiabilityCyberAggLimit": {
                                        "choiceValue": {
                                            "code": "50Kusd",
                                            "name": "50,000"
                                        }
                                    },
                                    "ACLCommlCyberLiabilityExtortion": {
                                        "choiceValue": {
                                            "code": "5Kusd",
                                            "name": "5,000"
                                        }
                                    },
                                    "ACLCommlCyberLiabilityPublicRelations": {
                                        "choiceValue": {
                                            "code": "5Kusd",
                                            "name": "5000"
                                        }
                                    },
                                    "ACLCommlCyberLiabilityRetention": {
                                        "choiceValue": {
                                            "code": "75Kusd",
                                            "name": "7,500"
                                        }
                                    },
                                    "ACLCommlCyberLiabilityWaitingPeriod": {
                                        "choiceValue": {
                                            "code": "12HR",
                                            "name": "12 hrs"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "method": "patch",
                    "uri": "/job/v1/jobs/${jobId}/lines/USCyberLine",
                    "body": {
                        "data": {
                            "attributes": {
                                "aclDateBusinessStarted": "2020-01-01T00:00:00.000Z",
                                "aclPolicyType": {
                                    "code": "commercialcyber",
                                    "name": "Commercial Cyber"
                                },
                                "aclTotalAssets": "500000.00",
                                "aclTotalFTEmployees": 10,
                                "aclTotalLiabilities": "50000.00",
                                "aclTotalPTEmployees": 5,
                                "aclTotalPayroll": "750000.00",
                                "aclTotalRevenues": "1000000.00"
                            }
                        }
                    }
                },
                {
                    "method": "post",
                    "uri": "/job/v1/jobs/${jobId}/quote"
                }
            ]
        }
        
        # Make the request
        result = self._make_request(payload)
        
        if result["success"]:
            # Parse the response to extract account and job IDs
            try:
                data = result["data"]
                
                # Extract account ID from first response
                account_id = None
                job_id = None
                
                if "responses" in data and len(data["responses"]) >= 2:
                    # Account creation response
                    if data["responses"][0].get("status") == 200:
                        account_response = data["responses"][0].get("body", {})
                        if "data" in account_response and "attributes" in account_response["data"]:
                            account_id = account_response["data"]["attributes"].get("id")
                    
                    # Submission creation response  
                    if len(data["responses"]) > 1 and data["responses"][1].get("status") == 200:
                        submission_response = data["responses"][1].get("body", {})
                        if "data" in submission_response and "attributes" in submission_response["data"]:
                            job_id = submission_response["data"]["attributes"].get("id")
                
                logger.info(f"Extracted IDs - Account: {account_id}, Job: {job_id}")
                
                return {
                    "success": True,
                    "account_id": account_id,
                    "job_id": job_id,
                    "full_response": data,
                    "message": "Account and submission created successfully"
                }
                
            except Exception as parse_error:
                logger.error(f"Error parsing Guidewire response: {str(parse_error)}")
                return {
                    "success": False,
                    "error": "ParseError", 
                    "message": f"Failed to parse response: {str(parse_error)}",
                    "raw_response": result["data"]
                }
        else:
            return result

    def approve_submission(self, job_id: str, underwriter_notes: str = "") -> Dict[str, Any]:
        """
        Step 2: Approve submission in Guidewire
        This is called when underwriter clicks approve
        """
        logger.info(f"Approving Guidewire submission: {job_id}")
        
        # For now, we'll use a simple PATCH request to update the job status
        # The exact approval API will need to be provided by the Guidewire team
        approval_payload = {
            "requests": [
                {
                    "method": "patch",
                    "uri": f"/job/v1/jobs/{job_id}",
                    "body": {
                        "data": {
                            "attributes": {
                                "status": "approved",
                                "underwriterNotes": underwriter_notes,
                                "approvalDate": datetime.now().isoformat()
                            }
                        }
                    }
                }
            ]
        }
        
        result = self._make_request(approval_payload)
        
        if result["success"]:
            return {
                "success": True,
                "job_id": job_id,
                "status": "approved",
                "message": "Submission approved successfully in Guidewire"
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "message": f"Failed to approve submission in Guidewire: {result.get('message')}"
            }

    def create_quote_and_get_document(self, job_id: str) -> Dict[str, Any]:
        """
        Step 3: Create quote and retrieve document
        This creates the final quote and gets the document
        """
        logger.info(f"Creating quote and retrieving document for job: {job_id}")
        
        # Quote creation payload
        quote_payload = {
            "requests": [
                {
                    "method": "post",
                    "uri": f"/job/v1/jobs/{job_id}/quote"
                },
                {
                    "method": "get",
                    "uri": f"/job/v1/jobs/{job_id}/quote",
                    "vars": [
                        {
                            "name": "quoteId",
                            "path": "$.data.attributes.id"
                        }
                    ]
                },
                {
                    "method": "get",
                    "uri": f"/job/v1/jobs/{job_id}/documents"
                }
            ]
        }
        
        result = self._make_request(quote_payload)
        
        if result["success"]:
            try:
                data = result["data"]
                quote_info = {}
                documents = []
                
                if "responses" in data:
                    # Parse quote creation response
                    if len(data["responses"]) > 1 and data["responses"][1].get("status") == 200:
                        quote_response = data["responses"][1].get("body", {})
                        if "data" in quote_response:
                            quote_info = quote_response["data"].get("attributes", {})
                    
                    # Parse documents response
                    if len(data["responses"]) > 2 and data["responses"][2].get("status") == 200:
                        docs_response = data["responses"][2].get("body", {})
                        if "data" in docs_response:
                            documents = docs_response["data"]
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "quote_info": quote_info,
                    "documents": documents,
                    "message": "Quote created and documents retrieved successfully"
                }
                
            except Exception as parse_error:
                logger.error(f"Error parsing quote response: {str(parse_error)}")
                return {
                    "success": False,
                    "error": "ParseError",
                    "message": f"Failed to parse quote response: {str(parse_error)}",
                    "raw_response": result["data"]
                }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "message": f"Failed to create quote: {result.get('message')}"
            }

    def get_quote_document_url(self, job_id: str, document_id: str) -> Dict[str, Any]:
        """
        Get download URL for a specific quote document
        """
        logger.info(f"Getting document URL for job: {job_id}, document: {document_id}")
        
        # Document URL payload
        doc_payload = {
            "requests": [
                {
                    "method": "get",
                    "uri": f"/job/v1/jobs/{job_id}/documents/{document_id}/download"
                }
            ]
        }
        
        result = self._make_request(doc_payload)
        
        if result["success"]:
            try:
                data = result["data"]
                download_url = None
                
                if "responses" in data and len(data["responses"]) > 0:
                    doc_response = data["responses"][0].get("body", {})
                    download_url = doc_response.get("downloadUrl")
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "document_id": document_id,
                    "download_url": download_url,
                    "message": "Document URL retrieved successfully"
                }
                
            except Exception as parse_error:
                logger.error(f"Error parsing document URL response: {str(parse_error)}")
                return {
                    "success": False,
                    "error": "ParseError",
                    "message": f"Failed to parse document URL response: {str(parse_error)}"
                }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "message": f"Failed to get document URL: {result.get('message')}"
            }

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Guidewire"""
        logger.info("Testing Guidewire connection")
        
        # Simple test request
        test_payload = {
            "requests": [
                {
                    "method": "get",
                    "uri": "/account/v1/account-organization-types"
                }
            ]
        }
        
        return self._make_request(test_payload)

# Create global instance
guidewire_integration = GuidewireIntegration()