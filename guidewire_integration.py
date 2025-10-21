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
                logger.info(f"Full Guidewire response data structure: {json.dumps(data, indent=2)}")
                
                # Extract both internal IDs and human-readable numbers from composite response
                account_id = None
                job_id = None
                account_number = None
                job_number = None
                
                # Check if response has the expected composite structure
                if "responses" in data and isinstance(data["responses"], list):
                    logger.info(f"Found {len(data['responses'])} responses in composite result")
                    
                    # The quote response (last response) contains all the IDs we need
                    for i, response in enumerate(data["responses"]):
                        logger.info(f"Response {i}: Status={response.get('status')}")
                        
                        if response.get("status") == 200 or response.get("status") == 201:
                            body = response.get("body", {})
                            
                            # Check if this response has the job/quote information
                            if "data" in body and "attributes" in body["data"]:
                                attrs = body["data"]["attributes"]
                                
                                # Look for job ID and job number (human-readable identifier)
                                if "id" in attrs and str(attrs["id"]).startswith("pc:S"):
                                    job_id = attrs["id"]
                                    logger.info(f"Found job ID: {job_id}")
                                
                                if "jobNumber" in attrs:
                                    job_number = attrs["jobNumber"]
                                    logger.info(f"Found job number: {job_number}")
                                
                                # Extract account information from nested account object
                                if "account" in attrs and isinstance(attrs["account"], dict):
                                    account_info = attrs["account"]
                                    if "id" in account_info:
                                        account_id = account_info["id"]
                                        logger.info(f"Found account ID: {account_id}")
                                    if "displayName" in account_info:
                                        account_number = account_info["displayName"]
                                        logger.info(f"Found account number: {account_number}")
                
                # If we have job_id but no account_id, try to extract from other responses
                if job_id and not account_id:
                    # Look through earlier responses for account creation
                    for i, response in enumerate(data["responses"]):
                        if response.get("status") in [200, 201]:
                            body = response.get("body", {})
                            if "data" in body and "attributes" in body["data"]:
                                attrs = body["data"]["attributes"]
                                # Look for account creation response (has accountHolder, primaryAddress, etc.)
                                if "accountHolder" in attrs or "initialAccountHolder" in attrs:
                                    if "id" in attrs:
                                        account_id = attrs["id"]
                                        logger.info(f"Found account ID from account creation response: {account_id}")
                                        break
                
                logger.info(f"Final extracted IDs - Account: {account_id} (#{account_number}), Job: {job_id} (#{job_number})")
                
                return {
                    "success": True,
                    "account_id": account_id,
                    "job_id": job_id,
                    "account_number": account_number,
                    "job_number": job_number,
                    "full_response": data,
                    "message": f"Account and submission created successfully. Search in Guidewire using Account: {account_number} or Job: {job_number}"
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
        Step 2: Approve submission in Guidewire using UW Issues workflow
        This is called when underwriter clicks approve
        
        Based on Postman collection, the workflow is:
        1. Get UW issues for the job
        2. Approve each UW issue individually
        """
        logger.info(f"Approving Guidewire submission: {job_id}")
        
        try:
            # Step 1: Get UW issues for the job using direct REST API
            uw_issues_url = f"https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/job/v1/jobs/{job_id}/uw-issues"
            
            headers = {
                'Accept': 'application/json'
            }
            
            logger.info(f"Getting UW issues for job: {job_id}")
            response = requests.get(
                uw_issues_url,
                auth=(self.username, self.password),
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"UW issues response status: {response.status_code}")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": f"Failed to get UW issues: {response.text}"
                }
            
            uw_issues_data = response.json()
            logger.info(f"UW issues response: {json.dumps(uw_issues_data, indent=2)}")
            
            # Extract UW issues
            uw_issues = []
            if "data" in uw_issues_data:
                if isinstance(uw_issues_data["data"], list):
                    uw_issues = uw_issues_data["data"]
                else:
                    uw_issues = [uw_issues_data["data"]]
            
            if not uw_issues:
                return {
                    "success": True,
                    "job_id": job_id,
                    "message": "No UW issues found - submission may already be approved",
                    "uw_issues_count": 0
                }
            
            # Step 2: Approve each UW issue
            approved_issues = []
            failed_approvals = []
            
            for issue in uw_issues:
                try:
                    issue_id = issue.get("attributes", {}).get("id")
                    if not issue_id:
                        logger.warning(f"UW issue missing ID: {issue}")
                        continue
                    
                    logger.info(f"Approving UW issue: {issue_id}")
                    
                    # Approval payload based on Postman collection
                    approval_body = {
                        "data": {
                            "attributes": {
                                "canEditApprovalBeforeBind": False,
                                "approvalBlockingPoint": {
                                    "code": "BlocksIssuance"
                                },
                                "approvalDurationType": {
                                    "code": "ThreeYears"
                                }
                            }
                        }
                    }
                    
                    # Add underwriter notes if provided
                    if underwriter_notes:
                        approval_body["data"]["attributes"]["approvalNotes"] = underwriter_notes
                    
                    approve_url = f"https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/job/v1/jobs/{job_id}/uw-issues/{issue_id}/approve"
                    
                    approve_response = requests.post(
                        approve_url,
                        json=approval_body,
                        auth=(self.username, self.password),
                        headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                        timeout=self.timeout
                    )
                    
                    logger.info(f"UW issue {issue_id} approval status: {approve_response.status_code}")
                    
                    if approve_response.status_code in [200, 201]:
                        approved_issues.append(issue_id)
                        logger.info(f"Successfully approved UW issue: {issue_id}")
                    else:
                        failed_approvals.append({
                            "issue_id": issue_id,
                            "status_code": approve_response.status_code,
                            "error": approve_response.text
                        })
                        logger.error(f"Failed to approve UW issue {issue_id}: {approve_response.status_code} - {approve_response.text}")
                
                except Exception as issue_error:
                    logger.error(f"Error approving UW issue {issue_id}: {str(issue_error)}")
                    failed_approvals.append({
                        "issue_id": issue_id,
                        "error": str(issue_error)
                    })
            
            # Determine overall success
            total_issues = len(uw_issues)
            successful_approvals = len(approved_issues)
            
            if successful_approvals == total_issues:
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "approved",
                    "message": f"All {total_issues} UW issues approved successfully",
                    "approved_issues": approved_issues,
                    "uw_issues_count": total_issues
                }
            elif successful_approvals > 0:
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "partially_approved",
                    "message": f"{successful_approvals}/{total_issues} UW issues approved",
                    "approved_issues": approved_issues,
                    "failed_approvals": failed_approvals,
                    "uw_issues_count": total_issues
                }
            else:
                return {
                    "success": False,
                    "job_id": job_id,
                    "error": "ApprovalFailed",
                    "message": f"Failed to approve any of {total_issues} UW issues",
                    "failed_approvals": failed_approvals,
                    "uw_issues_count": total_issues
                }
        
        except Exception as e:
            logger.error(f"Error in approval workflow: {str(e)}")
            return {
                "success": False,
                "job_id": job_id,
                "error": "Exception",
                "message": f"Approval workflow failed: {str(e)}"
            }

    def reject_submission(self, job_id: str, rejection_reason: str, rejected_by: str = "") -> Dict[str, Any]:
        """
        Step 2B: Reject submission in Guidewire
        This is called when underwriter clicks reject
        """
        logger.info(f"Rejecting Guidewire submission: {job_id}")
        
        try:
            # Use the decline endpoint from the Guidewire API
            decline_url = f"https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/job/v1/jobs/{job_id}/decline"
            
            # Rejection payload
            rejection_body = {
                "data": {
                    "attributes": {
                        "declineReason": {
                            "code": "other",  # or specific decline reason codes like "underwriting", "coverage", etc.
                            "name": "Underwriter Decision"
                        },
                        "declineExplanation": rejection_reason
                    }
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info(f"Making rejection request to: {decline_url}")
            logger.info(f"Rejection payload: {json.dumps(rejection_body, indent=2)}")
            
            response = requests.post(
                decline_url,
                json=rejection_body,
                auth=(self.username, self.password),
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"Decline response status: {response.status_code}")
            logger.info(f"Decline response: {response.text}")
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "rejected",
                    "message": f"Submission declined successfully in Guidewire",
                    "rejection_reason": rejection_reason,
                    "rejected_by": rejected_by
                }
            else:
                logger.error(f"Failed to decline submission: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "job_id": job_id,
                    "error": f"HTTP {response.status_code}",
                    "message": f"Failed to decline submission: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error in rejection workflow: {str(e)}")
            return {
                "success": False,
                "job_id": job_id,
                "error": "Exception",
                "message": f"Rejection workflow failed: {str(e)}"
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
        
        # Use a direct REST API call instead of composite for connection test
        try:
            test_url = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/account/v1/account-organization-types"
            
            headers = {
                'Accept': 'application/json'
            }
            
            response = requests.get(
                test_url,
                auth=(self.username, self.password),
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": "Successfully connected to Guidewire"
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "success": False,
                "error": "ConnectionError",
                "message": str(e)
            }

    def get_uw_issues(self, job_id: str) -> Dict[str, Any]:
        """
        Get UW issues for a specific job ID
        This is useful for checking what needs to be approved
        """
        logger.info(f"Getting UW issues for job: {job_id}")
        
        try:
            # Use direct REST API call for UW issues
            uw_issues_url = f"https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/job/v1/jobs/{job_id}/uw-issues"
            
            headers = {
                'Accept': 'application/json'
            }
            
            response = requests.get(
                uw_issues_url,
                auth=(self.username, self.password),
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"UW issues API response status: {response.status_code}")
            
            if response.status_code == 200:
                uw_issues_data = response.json()
                logger.info(f"UW issues response: {json.dumps(uw_issues_data, indent=2)}")
                
                # Extract UW issues list
                uw_issues = []
                if "data" in uw_issues_data:
                    if isinstance(uw_issues_data["data"], list):
                        uw_issues = uw_issues_data["data"]
                    else:
                        uw_issues = [uw_issues_data["data"]]
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "uw_issues": uw_issues,
                    "uw_issues_count": len(uw_issues),
                    "message": f"Found {len(uw_issues)} UW issues for job {job_id}"
                }
            else:
                logger.error(f"UW issues API failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "job_id": job_id,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error retrieving UW issues: {str(e)}")
            return {
                "success": False,
                "job_id": job_id,
                "error": "Exception",
                "message": str(e)
            }

    def get_quote_documents(self, job_id: str) -> Dict[str, Any]:
        """
        Get quote documents for a specific job ID
        This uses the direct REST API to retrieve documents for a quoted job
        """
        logger.info(f"Retrieving documents for job: {job_id}")
        
        try:
            # Use direct REST API call for documents
            documents_url = f"https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/job/v1/jobs/{job_id}/documents"
            
            headers = {
                'Accept': 'application/json'
            }
            
            response = requests.get(
                documents_url,
                auth=(self.username, self.password),
                headers=headers,
                timeout=self.timeout
            )
            
            logger.info(f"Documents API response status: {response.status_code}")
            
            if response.status_code == 200:
                documents_data = response.json()
                logger.info(f"Documents response: {json.dumps(documents_data, indent=2)}")
                
                # Extract document list
                documents = []
                if "data" in documents_data:
                    if isinstance(documents_data["data"], list):
                        documents = documents_data["data"]
                    else:
                        documents = [documents_data["data"]]
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "documents": documents,
                    "documents_count": len(documents),
                    "message": f"Found {len(documents)} documents for job {job_id}"
                }
            else:
                logger.error(f"Documents API failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "job_id": job_id,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return {
                "success": False,
                "job_id": job_id,
                "error": "Exception",
                "message": str(e)
            }

# Create global instance
guidewire_integration = GuidewireIntegration()