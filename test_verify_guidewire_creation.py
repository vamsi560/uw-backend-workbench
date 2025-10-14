#!/usr/bin/env python3
"""
Test to check if either endpoint is actually creating Guidewire accounts
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_and_verify_guidewire_creation():
    """Test both endpoints and verify if Guidewire accounts are actually created"""
    
    print("🔍 TESTING ACTUAL GUIDEWIRE ACCOUNT CREATION")
    print("="*80)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Test 1: Regular endpoint
    print(f"\n📧 TEST 1: Regular Endpoint")
    print("-" * 40)
    
    regular_email = {
        "subject": f"REGULAR VERIFY TEST {timestamp}",
        "sender_email": f"regular{timestamp}@verify.com",
        "body": f"""
Company Name: Regular Verify Test Company
Industry: technology
Policy Type: Cyber Liability  
Effective Date: 2025-01-01
Coverage Amount: 1500000
Contact Email: regular{timestamp}@verify.com
        """,
        "attachments": []
    }
    
    response1 = requests.post(f"{BASE_URL}/api/email/intake", json=regular_email, timeout=30)
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"✅ Regular response: {data1.get('message')}")
        regular_ref = data1.get('submission_ref')
    else:
        print(f"❌ Regular endpoint failed")
        regular_ref = None
    
    time.sleep(2)
    
    # Test 2: Logic Apps endpoint
    print(f"\n📧 TEST 2: Logic Apps Endpoint")
    print("-" * 40)
    
    logic_email = {
        "subject": f"LOGIC VERIFY TEST {timestamp}",
        "sender_email": f"logic{timestamp}@verify.com",
        "body": f"""
Company Name: Logic Verify Test Company
Industry: technology
Policy Type: Cyber Liability
Effective Date: 2025-01-01  
Coverage Amount: 1800000
Contact Email: logic{timestamp}@verify.com
        """,
        "attachments": []
    }
    
    response2 = requests.post(f"{BASE_URL}/api/logicapps/email/intake", json=logic_email, timeout=30)
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"✅ Logic Apps response: {data2.get('message')}")
        logic_ref = data2.get('submission_ref')
    else:
        print(f"❌ Logic Apps endpoint failed")
        logic_ref = None
    
    # Wait for processing
    print(f"\n⏳ Waiting for processing to complete...")
    time.sleep(5)
    
    # Check database for work items
    print(f"\n🔍 Checking created work items...")
    
    db_response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
    if db_response.status_code == 200:
        db_data = db_response.json()
        recent_items = db_data.get('recent_work_items', [])
        
        print(f"\n📋 Recent work items:")
        for item in recent_items[:3]:
            print(f"   ID {item['id']}: {item['title'][:50]}...")
            
            # Test manual sync for each to see if Guidewire works
            if f"VERIFY TEST {timestamp}" in item['title']:
                print(f"   🔧 Testing manual Guidewire sync for ID {item['id']}...")
                
                manual_response = requests.post(f"{BASE_URL}/api/workitems/{item['id']}/submit-to-guidewire", timeout=30)
                
                if manual_response.status_code == 200:
                    manual_data = manual_response.json()
                    
                    if manual_data.get('success'):
                        account_num = manual_data.get('account_number', 'Unknown')
                        print(f"   ✅ Manual sync worked - Account: {account_num}")
                        
                        if account_num and account_num != 'None':
                            print(f"   🎉 GUIDEWIRE INTEGRATION WORKING!")
                        else:
                            print(f"   ⚠️  Success but no account number (parsing issue)")
                    else:
                        print(f"   ❌ Manual sync failed: {manual_data.get('message', 'Unknown error')}")
                else:
                    print(f"   ❌ Manual sync HTTP error: {manual_response.status_code}")
    
    # Test direct Guidewire to ensure API is working
    print(f"\n🧪 Testing direct Guidewire API (baseline)...")
    
    direct_test = {
        "company_name": f"Direct Test Company {timestamp}",
        "contact_email": f"direct{timestamp}@test.com",
        "industry": "technology",
        "coverage_amount": "2000000"
    }
    
    direct_response = requests.post(f"{BASE_URL}/api/test/guidewire-submission", json=direct_test, timeout=30)
    
    if direct_response.status_code == 200:
        direct_data = direct_response.json()
        gw_result = direct_data.get('guidewire_result', {})
        
        if gw_result.get('success'):
            print(f"✅ Direct Guidewire works: Account {gw_result.get('account_number', 'Unknown')}")
        else:
            print(f"❌ Direct Guidewire failed: {gw_result.get('error', 'Unknown')}")
    else:
        print(f"❌ Direct Guidewire HTTP error: {direct_response.status_code}")

def main():
    print("🔍 VERIFICATION TEST: ACTUAL GUIDEWIRE ACCOUNT CREATION")
    print("This test will determine if either endpoint is successfully creating Guidewire accounts")
    print("="*80)
    
    test_and_verify_guidewire_creation()
    
    print(f"\n{'='*80}")
    print("🎯 VERIFICATION SUMMARY")
    print(f"{'='*80}")
    print("This test shows:")
    print("1. Whether email intake triggers Guidewire sync")
    print("2. Whether manual sync works for created work items") 
    print("3. Whether direct Guidewire API works (baseline)")
    print("4. If auto-sync isn't working, what the exact issue is")

if __name__ == "__main__":
    main()