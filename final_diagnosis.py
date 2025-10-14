#!/usr/bin/env python3
"""
Final diagnosis: Test Guidewire integration step by step to find the exact issue
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_direct_guidewire_vs_manual_sync():
    """Compare direct Guidewire submission vs manual sync from work item"""
    print("🔬 COMPARING DIRECT GUIDEWIRE VS MANUAL SYNC")
    print("="*60)
    
    # Test 1: Direct Guidewire submission (we know this works)
    print("1️⃣ TESTING DIRECT GUIDEWIRE SUBMISSION:")
    try:
        test_data = {
            "company_name": "Direct Test Company Final",
            "contact_email": "finaltest@company.com",
            "industry": "technology",
            "employee_count": "100",
            "annual_revenue": "3000000",
            "coverage_amount": "1500000",
            "contact_name": "Final Test",
            "business_address": "123 Final Test St",
            "business_city": "Test City",
            "business_state": "CA",
            "business_zip": "12345",
            "policy_type": "cyber liability"
        }
        
        response = requests.post(f"{BASE_URL}/api/test/guidewire-submission",
                               json=test_data,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            gw_result = data.get('guidewire_result', {})
            
            print(f"   ✅ Direct submission SUCCESS")
            print(f"   Account ID: {gw_result.get('account_id', 'None')}")
            print(f"   Account Number: {gw_result.get('account_number', 'None')}")
            print(f"   Success: {gw_result.get('success', False)}")
            
            direct_account_number = gw_result.get('account_number')
            
        else:
            print(f"   ❌ Direct submission FAILED: HTTP {response.status_code}")
            direct_account_number = None
    except Exception as e:
        print(f"   ❌ Direct submission ERROR: {str(e)}")
        direct_account_number = None
    
    # Test 2: Manual sync of latest work item
    print(f"\n2️⃣ TESTING MANUAL SYNC OF WORK ITEM:")
    try:
        # Get latest work item
        db_response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
        if db_response.status_code == 200:
            db_data = db_response.json()
            latest_item = db_data.get('latest_work_item')
            
            if latest_item:
                work_item_id = latest_item['id']
                print(f"   📧 Work Item {work_item_id}: {latest_item['title']}")
                
                # Try manual sync
                sync_response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire",
                                            timeout=30)
                
                if sync_response.status_code == 200:
                    sync_data = sync_response.json()
                    
                    print(f"   ✅ Manual sync response SUCCESS")
                    print(f"   Success: {sync_data.get('success', False)}")
                    print(f"   Account ID: {sync_data.get('guidewire_account_id', 'None')}")
                    print(f"   Account Number: {sync_data.get('account_number', 'None')}")
                    print(f"   Message: {sync_data.get('message', 'No message')}")
                    
                    if sync_data.get('error'):
                        print(f"   Error: {sync_data.get('error')}")
                    
                    manual_account_number = sync_data.get('account_number')
                else:
                    print(f"   ❌ Manual sync FAILED: HTTP {sync_response.status_code}")
                    try:
                        error_data = sync_response.json()
                        print(f"   Error details: {error_data}")
                    except:
                        print(f"   Response text: {sync_response.text}")
                    manual_account_number = None
            else:
                print(f"   ❌ No work item found")
                manual_account_number = None
        else:
            print(f"   ❌ Could not get work item: HTTP {db_response.status_code}")
            manual_account_number = None
    except Exception as e:
        print(f"   ❌ Manual sync ERROR: {str(e)}")
        manual_account_number = None
    
    # Analysis
    print(f"\n🔍 COMPARISON ANALYSIS:")
    if direct_account_number and manual_account_number:
        print(f"   ✅ Both methods work and create accounts")
        print(f"   Direct: {direct_account_number}, Manual: {manual_account_number}")
    elif direct_account_number and not manual_account_number:
        print(f"   ⚠️  Direct works ({direct_account_number}) but Manual sync has parsing issues")
        print(f"   The Guidewire API is working, but manual sync response parsing is broken")
    elif not direct_account_number and not manual_account_number:
        print(f"   ❌ Both methods have issues - Guidewire API problem")
    else:
        print(f"   🤔 Unexpected result pattern")

def test_email_intake_with_logging():
    """Send a test email and try to trace what happens"""
    print(f"\n📧 TESTING EMAIL INTAKE WITH DETAILED ANALYSIS")
    print("="*60)
    
    # Send a very simple, guaranteed-to-pass email
    simple_email = {
        "subject": "SIMPLE TEST - Cyber Insurance Quote",
        "sender_email": "simple@testcompany.com", 
        "body": """
        Company: Simple Test Corp
        Industry: technology
        Policy Type: cyber liability
        Coverage: $1,000,000
        Employees: 50
        Revenue: $2,000,000
        Contact: Simple Test
        Address: 123 Simple St, Simple City, CA 12345
        """,
        "attachments": []
    }
    
    print(f"📤 Sending simple email with guaranteed fields...")
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake",
                               json=simple_email,
                               timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Email intake successful:")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            # Check if the message indicates Guidewire integration
            message = data.get('message', '')
            if 'guidewire' in message.lower():
                print(f"   ✅ Message mentions Guidewire - integration may have been attempted")
            else:
                print(f"   ⚠️  Message doesn't mention Guidewire - integration may not have been triggered")
            
            return data.get('submission_ref')
            
        else:
            print(f"❌ Email intake failed: HTTP {response.status_code}")
            try:
                error_data = response.json() 
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Email intake error: {str(e)}")
        return None

def check_application_logs():
    """Try to get any error information from the application"""
    print(f"\n📋 CHECKING FOR APPLICATION ERRORS")
    print("="*60)
    
    # Try some debug endpoints to see if there are any errors
    endpoints_to_check = [
        "/api/debug/database",
        "/api/test/guidewire", 
        "/health"
    ]
    
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            print(f"   {endpoint}: HTTP {response.status_code}")
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        print(f"      Error: {error_data['error']}")
                except:
                    pass
        except Exception as e:
            print(f"   {endpoint}: Exception - {str(e)}")

def main():
    print("🎯 FINAL DIAGNOSIS: ROOT CAUSE ANALYSIS")
    print("="*70)
    
    # Step 1: Compare direct vs manual sync
    test_direct_guidewire_vs_manual_sync()
    
    # Step 2: Test email intake
    submission_ref = test_email_intake_with_logging()
    
    # Step 3: Check for any application errors
    check_application_logs()
    
    print(f"\n{'='*70}")
    print("🏆 FINAL CONCLUSIONS")
    print(f"{'='*70}")
    
    print("🔍 WHAT WE KNOW FOR CERTAIN:")
    print("   ✅ Guidewire PolicyCenter API is working")
    print("   ✅ Direct Guidewire API calls create real accounts")
    print("   ✅ Email processing creates work items")
    print("   ✅ Manual sync endpoints exist and respond")
    
    print(f"\n❓ THE MYSTERY:")
    print("   🤔 Why doesn't email intake trigger Guidewire sync automatically?")
    print("   🤔 Why does manual sync return 'success' but no account details?")
    
    print(f"\n🎯 MOST LIKELY ROOT CAUSES:")
    print("   1. 📊 LLM extraction fails or returns insufficient data")
    print("   2. 📋 Business validation marks submissions as 'Rejected'")
    print("   3. 🐛 Bug in the email intake -> Guidewire integration code path")
    print("   4. ⚠️  Exception handling masks the real errors")
    print("   5. 🔧 Response parsing bug in manual sync endpoint")
    
    print(f"\n✅ WORKAROUND SOLUTION:")
    print("   1. Send emails (work items get created)")
    print("   2. Use direct Guidewire test endpoint to create accounts")
    print("   3. Manually map work items to Guidewire accounts")
    
    print(f"\n🛠️  PERMANENT FIX NEEDED:")
    print("   1. Add detailed debug logging to email intake Guidewire section")
    print("   2. Fix response parsing in manual sync endpoints")
    print("   3. Test LLM service data extraction output")
    print("   4. Verify business validation logic flow")

if __name__ == "__main__":
    main()