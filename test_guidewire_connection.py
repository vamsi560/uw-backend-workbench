"""
Test Guidewire Connection with Whitelisted IP
This script tests if our Guidewire integration can now connect successfully
"""

import requests
import json
from datetime import datetime

def test_guidewire_connection():
    """Test direct connection to Guidewire API"""
    
    # Guidewire connection details
    base_url = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/composite/v1/composite"
    username = "su"
    password = "gw"
    
    # Simple test payload
    test_payload = {
        "requests": [
            {
                "method": "get",
                "uri": "/account/v1/account-organization-types"
            }
        ]
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print(f"🔗 Testing Guidewire connection...")
    print(f"URL: {base_url}")
    print(f"Username: {username}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(
            base_url,
            json=test_payload,
            auth=(username, password),
            headers=headers,
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"🎉 SUCCESS! Guidewire connection working!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Connection timed out - IP may not be whitelisted yet")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_full_submission_flow():
    """Test the complete submission creation flow"""
    
    base_url = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/composite/v1/composite"
    username = "su"
    password = "gw"
    
    # Full submission payload using exact team format
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
                                "companyName": "Test Cyber Co - Deployment Test",
                                "taxId": "12-1212121",
                                "primaryAddress": {
                                    "addressLine1": "123 Deployment Test St",
                                    "city": "San Mateo",
                                    "postalCode": "94403",
                                    "state": {
                                        "code": "CA"
                                    }
                                }
                            },
                            "initialPrimaryLocation": {
                                "addressLine1": "123 Deployment Test St",
                                "city": "San Mateo",
                                "postalCode": "94403",
                                "state": {
                                    "code": "CA"
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
                                "code": "CA"
                            },
                            "jobEffectiveDate": "2025-08-01",
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
            }
        ]
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print(f"\n🚀 Testing FULL submission creation flow...")
    print("-" * 50)
    
    try:
        response = requests.post(
            base_url,
            json=payload,
            auth=(username, password),
            headers=headers,
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"🎉 SUCCESS! Full submission flow working!")
            
            # Extract account and job IDs if available
            if "responses" in result and len(result["responses"]) >= 2:
                account_response = result["responses"][0]
                submission_response = result["responses"][1]
                
                print(f"Account Creation: Status {account_response.get('status')}")
                print(f"Submission Creation: Status {submission_response.get('status')}")
                
                if account_response.get("status") == 200:
                    account_data = account_response.get("body", {}).get("data", {}).get("attributes", {})
                    account_id = account_data.get("id")
                    print(f"✅ Account ID: {account_id}")
                
                if submission_response.get("status") == 200:
                    job_data = submission_response.get("body", {}).get("data", {}).get("attributes", {})
                    job_id = job_data.get("id")
                    print(f"✅ Job ID: {job_id}")
            
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Connection timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 GUIDEWIRE CONNECTION TEST - WHITELISTED IP")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Testing from deployment: wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net")
    
    # Test 1: Basic connection
    connection_success = test_guidewire_connection()
    
    if connection_success:
        # Test 2: Full submission flow
        submission_success = test_full_submission_flow()
        
        if submission_success:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ Guidewire integration is fully functional!")
        else:
            print(f"\n⚠️ Basic connection works, but submission flow failed")
    else:
        print(f"\n❌ Basic connection failed - IP may not be fully whitelisted yet")
    
    print("=" * 60)