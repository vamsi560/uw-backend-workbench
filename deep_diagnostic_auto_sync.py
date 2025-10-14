#!/usr/bin/env python3
"""
Deep diagnostic for why auto-sync isn't working
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def check_work_item_details(work_item_id):
    """Get detailed information about a work item"""
    print(f"🔍 DETAILED WORK ITEM ANALYSIS: ID {work_item_id}")
    print("="*60)
    
    try:
        # Get work item details via debug endpoint
        response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Find our work item
            recent_items = data.get('recent_work_items', [])
            our_item = None
            
            for item in recent_items:
                if item['id'] == work_item_id:
                    our_item = item
                    break
            
            if our_item:
                print(f"📋 Work Item Found:")
                print(f"   ID: {our_item['id']}")
                print(f"   Title: {our_item['title']}")
                print(f"   Status: {our_item['status']}")
                print(f"   Created: {our_item['created_at']}")
                print(f"   Submission ID: {our_item['submission_id']}")
                
                # Now try to get more details by calling the work item API directly
                print(f"\n📊 Attempting to get full work item data...")
                
                # Try various approaches to get detailed data
                test_manual_sync(work_item_id)
                
                return our_item
            else:
                print(f"❌ Work item {work_item_id} not found in recent items")
                
        else:
            print(f"❌ Failed to get database info: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking work item: {str(e)}")
    
    return None

def test_manual_sync(work_item_id):
    """Test manual sync and analyze the response"""
    print(f"\n🔧 Testing manual Guidewire sync for work item {work_item_id}...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire", 
                               timeout=30)
        
        print(f"   📡 Manual sync response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"   Success: {data.get('success', 'Unknown')}")
            print(f"   Message: {data.get('message', 'No message')}")
            print(f"   Account Number: {data.get('account_number', 'None')}")
            
            if 'error' in data:
                print(f"   Error: {data['error']}")
            
            # The key insight: if manual sync works, then the issue is in the 
            # email intake validation logic, not in the Guidewire integration
            
        else:
            print(f"   ❌ Manual sync failed with HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response text: {response.text}")
        
    except Exception as e:
        print(f"❌ Manual sync test error: {str(e)}")

def analyze_validation_logic():
    """Try to understand what the validation logic expects"""
    print(f"\n🧠 ANALYZING VALIDATION LOGIC")
    print("="*60)
    
    print("From our code analysis, the validation conditions in email intake are:")
    print("1. validation_status must NOT be 'Rejected'")
    print("2. extracted_data must exist and be truthy")
    print("3. LLM extraction must succeed")
    
    print(f"\nThe most likely issue:")
    print("- Either LLM extraction is failing")
    print("- Or the business validation is returning 'Rejected'")
    print("- Or extracted_data is None/empty")
    
    print(f"\n💡 To debug this, we need to:")
    print("1. Check what the LLM extraction actually returns")
    print("2. Check what the business validation returns")
    print("3. Look at the actual validation_status value")

def create_simple_test_email():
    """Create a very simple test email to isolate the issue"""
    print(f"\n🧪 CREATING MINIMAL TEST EMAIL")
    print("="*60)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    minimal_email = {
        "subject": f"MINIMAL TEST {timestamp}",
        "sender_email": f"minimal{timestamp}@test.com", 
        "body": """
        Company: Test Company
        Industry: Technology  
        Employee Count: 50
        Coverage Amount: 1000000
        Policy Type: Cyber Insurance
        
        Please provide quote.
        """,
        "attachments": []
    }
    
    print(f"📧 Sending minimal test email...")
    print(f"   Subject: {minimal_email['subject']}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake",
                               json=minimal_email,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Response received:")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            # Check if Guidewire mentioned
            message = data.get('message', '')
            if 'guidewire' in message.lower() or 'policycenter' in message.lower():
                print(f"   🎉 GUIDEWIRE MENTIONED - Auto-sync worked!")
                return True, data
            else:
                print(f"   ⚠️  No Guidewire mention - auto-sync didn't trigger")
                return False, data
        else:
            print(f"❌ Email failed: HTTP {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Test email error: {str(e)}")
        return False, None

def main():
    print("🔬 DEEP DIAGNOSTIC FOR AUTO-SYNC ISSUE")
    print("="*80)
    
    # First, check our latest work item
    check_work_item_details(59)
    
    # Analyze the validation logic
    analyze_validation_logic()
    
    # Try a minimal test
    print(f"\n" + "="*80)
    sync_worked, email_data = create_simple_test_email()
    
    print(f"\n{'='*80}")
    print("🎯 DIAGNOSTIC SUMMARY")
    print(f"{'='*80}")
    
    if sync_worked:
        print("🎉 SUCCESS: Minimal test triggered auto-sync!")
        print("   The fix is working for simple emails")
    else:
        print("❌ ISSUE CONFIRMED: Auto-sync still not working")
        print("   The validation conditions are still not being met")
        
    print(f"\n💡 NEXT DEBUGGING STEPS:")
    print("1. Check server logs for LLM extraction results")
    print("2. Add debug logging to see exact validation_status values")
    print("3. Verify business rules aren't rejecting valid submissions")
    print("4. Check if extracted_data is being set correctly")
    
    if email_data:
        print(f"\n📊 Latest test created:")
        print(f"   Ref: {email_data.get('submission_ref')}")
        print(f"   Can test manual sync on latest work item")

if __name__ == "__main__":
    main()