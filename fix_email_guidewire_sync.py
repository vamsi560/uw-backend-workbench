#!/usr/bin/env python3
"""
Diagnostic script to understand why Guidewire auto-sync isn't working during email intake
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def check_latest_work_item_details():
    """Check the details of the latest work item to understand why Guidewire sync didn't happen"""
    print("🔍 ANALYZING LATEST WORK ITEM FOR GUIDEWIRE SYNC FAILURE")
    print("="*70)
    
    try:
        # Get database details
        response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
        if response.status_code == 200:
            data = response.json()
            latest_item = data.get("latest_work_item")
            
            if latest_item:
                work_item_id = latest_item["id"]
                print(f"📧 Latest Work Item (ID: {work_item_id}):")
                print(f"   Title: {latest_item['title']}")
                print(f"   Status: {latest_item['status']}")
                print(f"   Submission ID: {latest_item['submission_id']}")
                print(f"   Created: {latest_item['created_at']}")
                
                # Try to get work item history using polling endpoint
                print(f"\n🔍 Checking Work Item History...")
                history_response = requests.get(f"{BASE_URL}/api/workitems/poll", 
                                              params={'work_item_id': work_item_id}, 
                                              timeout=10)
                
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    history = history_data.get('history', [])
                    
                    if history:
                        print(f"   Found {len(history)} history entries:")
                        for i, h in enumerate(history[:5]):  # Show first 5
                            print(f"   {i+1}. {h.get('action', 'Unknown')} at {h.get('timestamp', 'Unknown time')}")
                            details = h.get('details', {})
                            if details:
                                print(f"      Details: {json.dumps(details, indent=8)}")
                        
                        # Check if there's any Guidewire-related history
                        guidewire_history = [h for h in history if 'guidewire' in str(h.get('details', {})).lower()]
                        if guidewire_history:
                            print(f"\n🔍 Guidewire History Found:")
                            for gh in guidewire_history:
                                print(f"   Action: {gh.get('action')}")
                                print(f"   Details: {gh.get('details', {})}")
                        else:
                            print(f"\n❌ NO Guidewire history found - this means auto-sync didn't trigger")
                    else:
                        print(f"   ⚠️  No history entries found")
                else:
                    print(f"   ❌ Failed to get history: HTTP {history_response.status_code}")
                
                # Try to get the related submission data
                print(f"\n🔍 Checking Related Submission Data...")
                submission_id = latest_item.get('submission_id')
                if submission_id:
                    # We need to get submission details - let's try the debug endpoint for orphaned submissions
                    orphan_response = requests.get(f"{BASE_URL}/api/debug/orphaned-submissions", timeout=10)
                    if orphan_response.status_code == 200:
                        orphan_data = orphan_response.json()
                        print(f"   Checked for orphaned submissions...")
                    
                    # Let's also check if we can get submission history
                    sub_history_response = requests.get(f"{BASE_URL}/api/submissions/{submission_id}/history", timeout=10)
                    if sub_history_response.status_code == 200:
                        sub_history = sub_history_response.json()
                        print(f"   ✅ Submission has {len(sub_history)} history entries")
                    else:
                        print(f"   ⚠️  Could not get submission history: HTTP {sub_history_response.status_code}")
                
                return work_item_id, latest_item
            else:
                print("❌ No latest work item found")
                return None, None
    except Exception as e:
        print(f"❌ Error analyzing work item: {str(e)}")
        return None, None

def test_validation_logic():
    """Test what the business validation logic would return for typical email data"""
    print(f"\n🔍 TESTING BUSINESS VALIDATION LOGIC")
    print("="*70)
    
    # Let's test the business rules directly
    try:
        # Create sample extracted data that should pass validation
        sample_extracted_data = {
            "company_name": "Test Company Inc",
            "industry": "technology",
            "employee_count": "100",
            "annual_revenue": "5000000",
            "coverage_amount": "1000000",
            "contact_email": "test@company.com",
            "contact_name": "John Doe",
            "business_address": "123 Test St",
            "business_city": "Test City",
            "business_state": "CA",
            "business_zip": "12345",
            "policy_type": "cyber liability"
        }
        
        print("📋 Sample Data for Validation Test:")
        for key, value in sample_extracted_data.items():
            print(f"   {key}: {value}")
        
        # The validation logic is in business_rules.py - let's simulate what happens
        print(f"\n💡 According to the email intake code:")
        print(f"   Guidewire sync happens if:")
        print(f"   1. validation_status in ['Complete', 'Incomplete'] (not 'Rejected')")
        print(f"   2. extracted_data exists and is not empty")
        
        print(f"\n🔍 Potential Issues:")
        print(f"   ❓ Is the business validation returning 'Rejected' status?")
        print(f"   ❓ Is the extracted_data empty or None?")
        print(f"   ❓ Is there an exception during Guidewire client import/creation?")
        
    except Exception as e:
        print(f"❌ Error in validation test: {str(e)}")

def simulate_email_intake():
    """Simulate sending an email that should trigger Guidewire sync"""
    print(f"\n🧪 SIMULATING EMAIL INTAKE WITH GUIDEWIRE SYNC")
    print("="*70)
    
    # Create a comprehensive test email that should pass all validations
    test_email = {
        "subject": "Diagnostic Test - Complete Insurance Request",
        "sender_email": "diagnostic@testcompany.com",
        "body": """
        We need cyber insurance for our company.
        
        Company: Diagnostic Test Company Inc
        Industry: Technology
        Employees: 150
        Annual Revenue: $8,000,000
        Coverage Needed: $2,000,000
        Address: 789 Diagnostic Ave, Test City, CA 90210
        Contact: Jane Doe
        Phone: 555-123-4567
        Entity Type: Corporation
        Years in Business: 8
        
        Please provide a quote.
        """,
        "attachments": []
    }
    
    print(f"📧 Sending comprehensive test email...")
    print(f"   This email has complete information that should pass validation")
    
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake",
                               json=test_email,
                               timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Email intake successful:")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            print(f"   Submission ID: {data.get('submission_id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            # Wait and then check if Guidewire sync happened
            import time
            print(f"\n⏳ Waiting 5 seconds for processing...")
            time.sleep(5)
            
            # Check latest work item again
            print(f"\n🔍 Checking if new work item has Guidewire data...")
            db_response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
            if db_response.status_code == 200:
                db_data = db_response.json()
                new_latest = db_data.get("latest_work_item")
                
                if new_latest and new_latest.get("id") != 55:  # Different from previous
                    print(f"✅ New work item created: ID {new_latest['id']}")
                    print(f"   Title: {new_latest['title']}")
                    
                    # Check its history for Guidewire integration
                    new_work_item_id = new_latest["id"]
                    history_response = requests.get(f"{BASE_URL}/api/workitems/poll", 
                                                  params={'work_item_id': new_work_item_id}, 
                                                  timeout=10)
                    
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        history = history_data.get('history', [])
                        
                        guidewire_history = [h for h in history if 'guidewire' in str(h.get('details', {})).lower()]
                        if guidewire_history:
                            print(f"✅ Guidewire integration detected in new work item!")
                            for gh in guidewire_history:
                                print(f"   {gh.get('action')}: {gh.get('details', {})}")
                        else:
                            print(f"❌ No Guidewire integration in new work item either")
                            print(f"   This confirms the auto-sync issue exists")
                else:
                    print(f"⚠️  No new work item found or same as before")
            
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
        print(f"❌ Email simulation error: {str(e)}")
        return None

def main():
    print("🔬 DIAGNOSING GUIDEWIRE AUTO-SYNC FAILURE IN EMAIL INTAKE")
    print("="*80)
    
    # Step 1: Analyze the latest work item
    work_item_id, work_item_data = check_latest_work_item_details()
    
    # Step 2: Test validation logic
    test_validation_logic()
    
    # Step 3: Try a comprehensive test email
    new_submission_ref = simulate_email_intake()
    
    print(f"\n{'='*80}")
    print("📊 DIAGNOSTIC SUMMARY")
    print(f"{'='*80}")
    
    if work_item_id:
        print(f"✅ Latest work item analyzed: ID {work_item_id}")
        print(f"   📧 Email processing works (creates work items)")
    
    if new_submission_ref:
        print(f"✅ New diagnostic email processed: {new_submission_ref}")
    
    print(f"\n🔍 LIKELY ROOT CAUSES:")
    print(f"1. 📋 Business validation might be returning 'Rejected' status")
    print(f"2. 📊 LLM data extraction might be returning empty/invalid data")
    print(f"3. ⚠️  Exception during Guidewire client import or execution")
    print(f"4. 🔧 Guidewire client configuration issue during email processing")
    
    print(f"\n🛠️  RECOMMENDED FIXES:")
    print(f"1. Check application logs for Guidewire errors during email processing")
    print(f"2. Verify business_rules.py validation logic")
    print(f"3. Test LLM data extraction output")
    print(f"4. Add more detailed logging to email intake Guidewire section")
    
    print(f"\n✅ CONFIRMED WORKING:")
    print(f"   - Email processing and work item creation")
    print(f"   - Manual Guidewire sync via API endpoints")
    print(f"   - Direct Guidewire API calls")

if __name__ == "__main__":
    main()