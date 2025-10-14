#!/usr/bin/env python3
"""
Test what the LLM service is actually extracting from emails
This will help us understand why Guidewire sync isn't triggering
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_llm_extraction():
    """Test LLM data extraction directly"""
    print("🧠 TESTING LLM DATA EXTRACTION")
    print("="*50)
    
    # Test the exact same text that would be sent to LLM during email processing
    test_email_content = """Email Subject: Diagnostic Test - Complete Insurance Request
From: diagnostic@testcompany.com
Email Body:
        
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

Attachment Content:
"""
    
    # We need to test the LLM service directly, but we don't have a direct endpoint
    # Let's check what the latest submission has for extracted_fields
    
    print("🔍 Checking extracted_fields from latest submissions...")
    try:
        # Get recent submissions via debug database endpoint
        response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Also check for recent work items and their extracted fields
            recent_items = data.get("recent_work_items", [])
            
            print(f"📊 Found {len(recent_items)} recent work items")
            
            for i, item in enumerate(recent_items[:3]):  # Check last 3
                work_item_id = item["id"]
                print(f"\n📧 Work Item {work_item_id}:")
                print(f"   Title: {item['title']}")
                print(f"   Status: {item['status']}")
                
                # Try to get the full work item data via polling
                poll_response = requests.get(f"{BASE_URL}/api/workitems/poll", 
                                           params={'work_item_id': work_item_id}, 
                                           timeout=10)
                
                if poll_response.status_code == 200:
                    poll_data = poll_response.json()
                    work_item_detail = poll_data.get('work_item', {})
                    
                    extracted_fields = work_item_detail.get('extracted_fields', {})
                    if extracted_fields:
                        print(f"   ✅ Has extracted_fields: {len(extracted_fields)} fields")
                        print(f"   📋 Extracted Fields:")
                        for key, value in extracted_fields.items():
                            print(f"      {key}: {value}")
                        
                        # Test business validation on this data
                        print(f"\n🔍 Testing Business Validation on this data...")
                        validation_result = test_business_validation(extracted_fields)
                        print(f"   Validation: {validation_result}")
                        
                    else:
                        print(f"   ❌ No extracted_fields found - THIS IS THE PROBLEM!")
                        print(f"      If LLM extraction fails, no Guidewire sync will happen")
                else:
                    print(f"   ⚠️  Could not get detailed work item data: HTTP {poll_response.status_code}")
            
        else:
            print(f"❌ Could not get database info: HTTP {response.status_code}")
    
    except Exception as e:
        print(f"❌ LLM extraction test error: {str(e)}")

def test_business_validation(extracted_fields):
    """Simulate the business validation logic"""
    try:
        # Simulate the validation that happens in email intake
        required_fields = ["insured_name", "policy_type", "effective_date", "industry"]
        
        missing_fields = []
        for field in required_fields:
            if not extracted_fields.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return f"❌ Incomplete - Missing: {missing_fields}"
        
        # Check policy type
        policy_type = str(extracted_fields.get("policy_type", "")).strip()
        accepted_types = ["Cyber Liability", "cyber", "Cyber", "CYBER", "Technology E&O", "Data Breach Response"]
        
        if policy_type not in accepted_types:
            return f"❌ Rejected - Policy type '{policy_type}' not accepted"
        
        return "✅ Complete - Should trigger Guidewire sync"
    
    except Exception as e:
        return f"❌ Validation error: {str(e)}"

def check_guidewire_integration_conditions():
    """Check the specific conditions for Guidewire integration during email intake"""
    print(f"\n🔍 CHECKING GUIDEWIRE INTEGRATION CONDITIONS")
    print("="*60)
    
    print("📋 According to main.py email intake code:")
    print("   Guidewire sync triggers when:")
    print("   1. validation_status in ['Complete', 'Incomplete']")
    print("   2. extracted_data exists and is truthy")
    print("   3. No exception during guidewire_client import")
    print("   4. No exception during create_cyber_submission call")
    
    print(f"\n🔍 Common failure points:")
    print("   ❌ LLM extraction returns empty/None data")
    print("   ❌ Business validation returns 'Rejected' status")  
    print("   ❌ Exception during Guidewire client creation")
    print("   ❌ Network/timeout issues during Guidewire API call")
    
    print(f"\n💡 Based on our tests:")
    print("   ✅ Guidewire API is working (manual sync works)")
    print("   ✅ Email processing creates work items")
    print("   ❓ Need to check: LLM extraction output")
    print("   ❓ Need to check: Business validation results")

def test_manual_guidewire_integration():
    """Test the manual Guidewire integration to compare with auto-sync"""
    print(f"\n🔄 TESTING MANUAL GUIDEWIRE INTEGRATION")
    print("="*50)
    
    # Get the latest work item ID
    try:
        response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
        if response.status_code == 200:
            data = response.json()
            latest_item = data.get("latest_work_item")
            
            if latest_item:
                work_item_id = latest_item["id"]
                print(f"📧 Testing manual sync for Work Item {work_item_id}")
                
                # Try manual sync
                sync_response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire", 
                                            timeout=30)
                
                if sync_response.status_code == 200:
                    sync_data = sync_response.json()
                    
                    print(f"✅ Manual sync response received")
                    print(f"   Success: {sync_data.get('success', False)}")
                    
                    if sync_data.get('success'):
                        print(f"   Account ID: {sync_data.get('guidewire_account_id', 'None')}")
                        print(f"   Account Number: {sync_data.get('account_number', 'None')}")
                        
                        if sync_data.get('account_number'):
                            print(f"   🎉 Manual sync works! Account created: {sync_data.get('account_number')}")
                        else:
                            print(f"   ⚠️  Manual sync 'successful' but no account details")
                    else:
                        print(f"   ❌ Manual sync failed: {sync_data.get('error', 'Unknown error')}")
                        print(f"   Message: {sync_data.get('message', 'No message')}")
                else:
                    print(f"❌ Manual sync request failed: HTTP {sync_response.status_code}")
            else:
                print("❌ No work item to test manual sync")
    except Exception as e:
        print(f"❌ Manual sync test error: {str(e)}")

def main():
    print("🔬 COMPREHENSIVE EMAIL-TO-GUIDEWIRE FLOW ANALYSIS")
    print("="*70)
    
    # Test 1: Check what LLM is extracting
    test_llm_extraction()
    
    # Test 2: Understand Guidewire integration conditions
    check_guidewire_integration_conditions()
    
    # Test 3: Compare with manual integration
    test_manual_guidewire_integration()
    
    print(f"\n{'='*70}")
    print("📊 ANALYSIS SUMMARY")
    print(f"{'='*70}")
    
    print("🔍 INVESTIGATION FINDINGS:")
    print("1. ✅ Email processing works (creates work items)")
    print("2. ✅ Guidewire API works (direct calls successful)")
    print("3. ✅ Manual sync works (can sync existing work items)")
    print("4. ❓ Auto-sync during email intake fails")
    
    print(f"\n🎯 MOST LIKELY CAUSES:")
    print("1. 📊 LLM extraction returning incomplete/empty data")
    print("2. 📋 Business validation marking submissions as 'Rejected'")
    print("3. ⚠️  Exception during Guidewire client creation in email flow")
    
    print(f"\n🛠️  RECOMMENDED FIXES:")
    print("1. Add detailed logging to email intake Guidewire section")
    print("2. Check LLM service configuration and responses")
    print("3. Verify business_rules validation logic")
    print("4. Test with simple, guaranteed-to-pass email content")

if __name__ == "__main__":
    main()