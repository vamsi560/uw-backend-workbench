#!/usr/bin/env python3
"""
Simple test for the direct Guidewire composite API
Test from production Azure environment to debug authentication and API issues
"""

import requests
import json
from datetime import datetime

# Direct API endpoint provided by Guidewire team
COMPOSITE_URL = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/composite/v1/composite"
USERNAME = "su"
PASSWORD = "gw"

def test_simple_composite():
    """Test the simplest possible composite request"""
    print("🧪 Testing Direct Guidewire Composite API")
    print("="*50)
    print(f"Endpoint: {COMPOSITE_URL}")
    print(f"Username: {USERNAME}")
    print()
    
    # Create session with authentication
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    # Test 1: Very simple ping request
    print("TEST 1: Simple Ping via Composite")
    print("-" * 30)
    
    simple_request = {
        "requests": [
            {
                "uri": "/rest/common/v1/ping",
                "method": "GET"
            }
        ]
    }
    
    try:
        print(f"Sending: {json.dumps(simple_request, indent=2)}")
        
        response = session.post(COMPOSITE_URL, json=simple_request, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Composite API is working!")
            try:
                data = response.json()
                print(f"Parsed response: {json.dumps(data, indent=2)}")
            except:
                print("⚠️  Response is not JSON")
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 2: Try to list accounts (simpler than creating)
    print("TEST 2: List Accounts")
    print("-" * 30)
    
    list_request = {
        "requests": [
            {
                "uri": "/rest/account/v1/accounts",
                "method": "GET"
            }
        ]
    }
    
    try:
        print(f"Sending: {json.dumps(list_request, indent=2)}")
        
        response = session.post(COMPOSITE_URL, json=list_request, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ Account listing works!")
        else:
            print(f"❌ Account listing failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 3: Minimal account creation
    print("TEST 3: Minimal Account Creation")
    print("-" * 30)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    create_request = {
        "requests": [
            {
                "uri": "/rest/account/v1/accounts",
                "method": "POST",
                "body": {
                    "data": {
                        "attributes": {
                            "initialAccountHolder": {
                                "contactSubtype": "Company",
                                "companyName": f"API Test Company {timestamp}",
                                "primaryAddress": {
                                    "addressLine1": "123 Test Street",
                                    "city": "San Francisco",
                                    "postalCode": "94105",
                                    "state": {"code": "CA"}
                                }
                            },
                            "organizationType": {"code": "other"}
                        }
                    }
                }
            }
        ]
    }
    
    try:
        print(f"Sending: {json.dumps(create_request, indent=2)}")
        
        response = session.post(COMPOSITE_URL, json=create_request, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Account creation successful!")
                
                # Look for account ID in response
                if 'responses' in data and len(data['responses']) > 0:
                    account_response = data['responses'][0]
                    if 'body' in account_response and 'data' in account_response['body']:
                        account_data = account_response['body']['data']['attributes']
                        account_id = account_data.get('id')
                        account_number = account_data.get('accountNumber')
                        
                        print(f"🎉 REAL ACCOUNT CREATED!")
                        print(f"   Account ID: {account_id}")
                        print(f"   Account Number: {account_number}")
                        
                        return True
                        
            except Exception as e:
                print(f"Error parsing response: {e}")
        else:
            print(f"❌ Account creation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_simple_composite()
    
    if success:
        print("\n🎉 SUCCESS: Direct API is working!")
        print("We can now create real Guidewire accounts/jobs!")
    else:
        print("\n❌ ISSUES: Need to debug further with Guidewire team")