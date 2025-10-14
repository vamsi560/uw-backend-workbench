#!/usr/bin/env python3
"""
Test the fixed automatic Guidewire sync in email intake
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_automatic_guidewire_sync():
    """Test if the automatic Guidewire sync now works during email intake"""
    
    print("🚀 TESTING FIXED AUTOMATIC GUIDEWIRE SYNC")
    print("="*60)
    
    # Create a comprehensive email that should definitely pass validation
    timestamp = datetime.now().strftime("%H%M%S")
    
    test_email = {
        "subject": f"AUTO-SYNC TEST {timestamp} - Complete Cyber Insurance Request",
        "sender_email": f"autosync{timestamp}@testcompany.com",
        "body": f"""
        Subject: Cyber Insurance Quote Request
        
        Company Information:
        - Company Name: AutoSync Test Company Inc
        - Industry: Technology
        - Business Type: Corporation
        - Years in Business: 10
        
        Contact Information:
        - Contact Name: John AutoSync
        - Email: autosync{timestamp}@testcompany.com
        - Phone: 555-AUTO-SYNC
        - Address: 123 AutoSync Avenue, Test City, CA 90210
        
        Business Details:
        - Number of Employees: 150
        - Annual Revenue: $8,000,000
        - Primary Business: Software Development
        
        Insurance Requirements:
        - Policy Type: Cyber Liability
        - Coverage Amount: $3,000,000
        - Effective Date: 2025-01-01
        - Data Types: Customer PII, Financial Records, Health Information
        
        This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} to test automatic Guidewire sync.
        
        Please provide a comprehensive cyber insurance quote.
        
        Thank you,
        John AutoSync
        AutoSync Test Company Inc
        """,
        "attachments": []
    }
    
    print(f"📧 Sending comprehensive test email...")
    print(f"   Subject: {test_email['subject']}")
    print(f"   From: {test_email['sender_email']}")
    print(f"   Contains: Company name, industry, coverage amount, policy type, etc.")
    
    try:
        # Send the email
        response = requests.post(f"{BASE_URL}/api/email/intake",
                               json=test_email,
                               timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ EMAIL INTAKE RESPONSE:")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            print(f"   Submission ID: {data.get('submission_id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            # Check if the message indicates Guidewire sync
            message = data.get('message', '')
            if 'guidewire' in message.lower() or 'policycenter' in message.lower():
                print(f"   🎉 SUCCESS: Message mentions Guidewire - auto-sync worked!")
                guidewire_mentioned = True
            else:
                print(f"   ⚠️  Message doesn't mention Guidewire - auto-sync may not have triggered")
                guidewire_mentioned = False
            
            # Wait and check the latest work item
            print(f"\n⏳ Waiting 5 seconds for complete processing...")
            time.sleep(5)
            
            # Get the latest work item to see if it has Guidewire IDs
            print(f"\n🔍 Checking work item for Guidewire integration...")
            db_response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
            
            if db_response.status_code == 200:
                db_data = db_response.json()
                latest_item = db_data.get('latest_work_item')
                
                if latest_item:
                    work_item_id = latest_item['id']
                    title = latest_item['title']
                    
                    print(f"   📧 Latest Work Item: ID {work_item_id}")
                    print(f"   Title: {title}")
                    
                    # Check if this is our work item (by timestamp or title match)
                    if f"AUTO-SYNC TEST {timestamp}" in title or "AutoSync Test Company" in title:
                        print(f"   ✅ This is our test work item!")
                        
                        # Check application logs for our Guidewire sync attempts
                        print(f"\n🔍 Checking for Guidewire sync logs...")
                        
                        # Try to manually sync to see current behavior
                        manual_response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire", timeout=30)
                        
                        if manual_response.status_code == 200:
                            manual_data = manual_response.json()
                            print(f"   📊 Manual Sync Test:")
                            print(f"      Success: {manual_data.get('success', False)}")
                            print(f"      Account Number: {manual_data.get('account_number', 'None')}")
                            print(f"      Message: {manual_data.get('message', 'No message')}")
                            
                            if manual_data.get('account_number'):
                                print(f"   🎉 Manual sync works - Guidewire integration is functioning!")
                                return {
                                    'auto_sync_detected': guidewire_mentioned,
                                    'manual_sync_works': True,
                                    'account_number': manual_data.get('account_number'),
                                    'work_item_id': work_item_id,
                                    'submission_ref': data.get('submission_ref')
                                }
                            else:
                                print(f"   ⚠️  Manual sync has parsing issues but may still create accounts")
                        else:
                            print(f"   ❌ Manual sync failed: HTTP {manual_response.status_code}")
                    else:
                        print(f"   ℹ️  This appears to be a different work item")
                else:
                    print(f"   ❌ No latest work item found")
            
            return {
                'auto_sync_detected': guidewire_mentioned,
                'manual_sync_works': False,
                'work_item_created': True,
                'submission_ref': data.get('submission_ref')
            }
            
        else:
            print(f"❌ Email intake failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
            
            return {'success': False, 'error': f'HTTP {response.status_code}'}
    
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_direct_guidewire_for_comparison():
    """Test direct Guidewire to ensure it's still working"""
    print(f"\n🧪 TESTING DIRECT GUIDEWIRE (FOR COMPARISON)")
    print("="*60)
    
    try:
        test_data = {
            "company_name": "Direct Comparison Test Company",
            "contact_email": "direct@comparison.com",
            "industry": "technology",
            "employee_count": "100",
            "annual_revenue": "5000000",
            "coverage_amount": "2000000"
        }
        
        response = requests.post(f"{BASE_URL}/api/test/guidewire-submission",
                               json=test_data,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            gw_result = data.get('guidewire_result', {})
            
            if gw_result.get('success') and gw_result.get('account_number'):
                print(f"✅ Direct Guidewire still works: Account {gw_result.get('account_number')}")
                return True
            else:
                print(f"❌ Direct Guidewire failed: {gw_result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Direct Guidewire request failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Direct Guidewire test error: {str(e)}")
        return False

def main():
    print("🔧 TESTING AUTOMATIC GUIDEWIRE SYNC FIXES")
    print("After implementing enhanced logging and more permissive sync conditions")
    print("="*80)
    
    # Test 1: Direct Guidewire (baseline)
    direct_works = test_direct_guidewire_for_comparison()
    
    # Test 2: Email with automatic sync
    auto_sync_result = test_automatic_guidewire_sync()
    
    print(f"\n{'='*80}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    
    print(f"🔍 BASELINE TESTS:")
    if direct_works:
        print(f"   ✅ Direct Guidewire API: WORKING")
    else:
        print(f"   ❌ Direct Guidewire API: FAILED")
    
    print(f"\n🎯 AUTOMATIC SYNC TEST:")
    if auto_sync_result.get('auto_sync_detected'):
        print(f"   🎉 Auto-sync DETECTED in email response!")
        print(f"   ✅ The fix appears to be working!")
    elif auto_sync_result.get('work_item_created'):
        print(f"   ⚠️  Work item created but auto-sync not detected in response")
        print(f"   📋 This means the sync condition is still not being met")
    else:
        print(f"   ❌ Email intake failed completely")
    
    if auto_sync_result.get('manual_sync_works'):
        print(f"   ✅ Manual sync confirmed working")
        if auto_sync_result.get('account_number'):
            print(f"   🏢 Account created: {auto_sync_result.get('account_number')}")
    
    print(f"\n💡 NEXT STEPS:")
    if auto_sync_result.get('auto_sync_detected'):
        print(f"   🎉 SUCCESS! Auto-sync is now working!")
        print(f"   📧 You can now send emails and they should auto-create Guidewire accounts")
    else:
        print(f"   🔍 Need to investigate further:")
        print(f"      - Check application logs for LLM extraction results")
        print(f"      - Check business validation logic")
        print(f"      - Verify the enhanced logging output")
    
    return auto_sync_result

if __name__ == "__main__":
    main()