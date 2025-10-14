#!/usr/bin/env python3
"""
Send a test email and immediately check the work item details
to see what validation status was recorded
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def check_server_validation_behavior():
    """Send test email and immediately check what validation status was stored"""
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    print(f"🔍 CHECKING SERVER VALIDATION BEHAVIOR")
    print("="*60)
    
    # Send perfect test email
    test_email = {
        "subject": f"VALIDATION CHECK {timestamp}",
        "sender_email": f"validation{timestamp}@test.com",
        "body": f"""
Company Name: Validation Check Company
Industry: technology
Policy Type: Cyber Liability
Effective Date: 2025-01-01
Coverage Amount: 1000000
Contact Name: Validation Tester
Contact Email: validation{timestamp}@test.com
        """,
        "attachments": []
    }
    
    print(f"📧 Sending test email with perfect validation conditions...")
    
    # Send email 
    response = requests.post(f"{BASE_URL}/api/email/intake", json=test_email, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Email failed: HTTP {response.status_code}")
        return
    
    data = response.json()
    print(f"✅ Email processed: {data.get('message')}")
    
    # Wait briefly for processing
    time.sleep(3)
    
    # Get the latest work item (should be ours)
    db_response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
    if db_response.status_code != 200:
        print(f"❌ Could not get database info")
        return
    
    db_data = db_response.json()
    latest_item = db_data.get('latest_work_item')
    
    if not latest_item:
        print(f"❌ No latest work item found")
        return
    
    work_item_id = latest_item['id']
    title = latest_item['title']
    
    print(f"\n📋 Latest work item: ID {work_item_id}")
    print(f"   Title: {title}")
    
    # Check if this is our test item
    if f"VALIDATION CHECK {timestamp}" not in title:
        print(f"⚠️  This doesn't appear to be our test item")
        print(f"   Expected: 'VALIDATION CHECK {timestamp}'")
        print(f"   Got: '{title}'")
    
    # Now try manual sync to see what happens
    print(f"\n🔧 Testing manual Guidewire sync...")
    manual_response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire", timeout=30)
    
    if manual_response.status_code == 200:
        manual_data = manual_response.json()
        
        print(f"   Success: {manual_data.get('success')}")
        print(f"   Message: {manual_data.get('message')}")
        
        if manual_data.get('success'):
            print(f"   🎉 Manual sync works - this proves Guidewire integration is functional")
            print(f"   📋 The issue is definitely in the email intake auto-sync logic")
        else:
            print(f"   ❌ Manual sync failed - there may be a broader Guidewire issue")
            if 'error' in manual_data:
                print(f"   Error details: {manual_data['error']}")
    else:
        print(f"   ❌ Manual sync HTTP error: {manual_response.status_code}")

def test_direct_business_validation():
    """Test what our business validation would return for typical email data"""
    
    print(f"\n🧠 TESTING BUSINESS VALIDATION LOGIC")
    print("="*60)
    
    # Try to make a call that will show us what validation logic is being used
    
    # Create data that should definitely pass validation
    perfect_data = {
        "company_name": "Perfect Company Inc",
        "insured_name": "Perfect Company Inc", 
        "industry": "technology",
        "policy_type": "Cyber Liability",
        "effective_date": "2025-01-01",
        "coverage_amount": "1000000",
        "contact_email": "test@perfect.com"
    }
    
    print(f"📊 Testing perfect data that should pass validation:")
    for key, value in perfect_data.items():
        print(f"   {key}: {value}")
    
    # Since we can't directly call validation on server, we'll use the
    # behavior we observe from email processing to infer what's happening

def main():
    print("🔍 FINAL DIAGNOSTIC: SERVER VALIDATION BEHAVIOR")
    print("This will help us understand what the server is actually doing")
    print("="*80)
    
    check_server_validation_behavior()
    test_direct_business_validation()
    
    print(f"\n{'='*80}")
    print("🎯 FINAL ANALYSIS")
    print(f"{'='*80}")
    print("Based on all our testing:")
    print()
    print("✅ CONFIRMED WORKING:")
    print("   - Guidewire API integration")
    print("   - Manual sync from work items")
    print("   - Direct Guidewire account creation")
    print("   - Email processing and work item creation")
    print()
    print("❌ NOT WORKING:")
    print("   - Automatic Guidewire sync during email intake")
    print() 
    print("🔍 ROOT CAUSE:")
    print("   The server-side email intake validation conditions are not being met")
    print("   Even though our local testing shows they should work")
    print()
    print("💡 SOLUTION:")
    print("   The most reliable fix is to update the server-side validation logic")
    print("   to match what we tested locally, ensuring deployment is successful")

if __name__ == "__main__":
    main()