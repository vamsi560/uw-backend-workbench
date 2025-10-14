#!/usr/bin/env python3
"""
Test the direct Guidewire API endpoint provided by the Guidewire team
https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/composite/v1/composite
"""

import requests
import json
from datetime import datetime

# Guidewire credentials
BASE_URL = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net"
COMPOSITE_URL = f"{BASE_URL}/rest/composite/v1/composite"
USERNAME = "su"
PASSWORD = "gw"

def test_direct_api():
    """Test the direct composite API endpoint"""
    
    print("🧪 TESTING DIRECT GUIDEWIRE API")
    print("="*50)
    print(f"URL: {COMPOSITE_URL}")
    print(f"Username: {USERNAME}")
    print(f"Time: {datetime.now()}")
    print()
    
    # Setup session with auth
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    # Test 1: Simple ping request
    print("TEST 1: Simple Composite Request (Ping)")
    print("-" * 40)
    
    simple_request = {
        "requests": [
            {
                "uri": "/rest/common/v1/ping",
                "method": "GET"
            }
        ]
    }
    
    try:
        response = session.post(COMPOSITE_URL, json=simple_request, timeout=20)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Simple composite request successful!")
        else:
            print(f"❌ Simple request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error with simple request: {e}")
    
    print("\n" + "="*50)
    
    # Test 2: Account creation request
    print("TEST 2: Account Creation Request")
    print("-" * 40)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    account_creation_request = {
        "requests": [
            {
                "uri": "/rest/account/v1/accounts",
                "method": "POST",
                "body": {
                    "attributes": {
                        "accountHolderContact": {
                            "firstName": "Test",
                            "lastName": f"DirectAPI_{timestamp}",
                            "emailAddress1": f"directapi_{timestamp}@testcompany.com"
                        },
                        "primaryInsured": f"Direct API Test Company {timestamp}",
                        "segment": "Commercial"
                    }
                }
            }
        ]
    }
    
    try:
        response = session.post(COMPOSITE_URL, json=account_creation_request, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Account creation request processed!")
                print(f"Raw Response: {json.dumps(data, indent=2)}")
                
                # Check for account ID
                if 'responses' in data and len(data['responses']) > 0:
                    account_response = data['responses'][0]
                    if 'body' in account_response and 'id' in account_response['body']:
                        account_id = account_response['body']['id']
                        account_number = account_response['body'].get('accountNumber', 'N/A')
                        print(f"🎉 ACCOUNT CREATED!")
                        print(f"   Account ID: {account_id}")
                        print(f"   Account Number: {account_number}")
                        return account_id
                        
            except Exception as e:
                print(f"Error parsing response: {e}")
        else:
            print(f"❌ Account creation failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error with account creation: {e}")
    
    print("\n" + "="*50)
    
    # Test 3: Job creation (if we have an account)
    print("TEST 3: Job Creation Request")  
    print("-" * 40)
    
    # For now, let's try with a dummy account ID or see what happens
    job_creation_request = {
        "requests": [
            {
                "uri": "/rest/job/v1/jobs",
                "method": "POST",
                "body": {
                    "attributes": {
                        "accountId": "dummy_account_id",  # We'll need a real account ID
                        "productCode": "CyberPolicy",
                        "jobType": "Submission"
                    }
                }
            }
        ]
    }
    
    try:
        response = session.post(COMPOSITE_URL, json=job_creation_request, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Job creation request processed!")
                print(f"Raw Response: {json.dumps(data, indent=2)}")
                
            except Exception as e:
                print(f"Error parsing job response: {e}")
        else:
            print(f"❌ Job creation failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error with job creation: {e}")
    
    print("\n" + "="*50)
    print("DIRECT API TEST COMPLETE")
    print("="*50)

if __name__ == "__main__":
    test_direct_api()