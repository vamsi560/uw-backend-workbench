#!/usr/bin/env python3
"""
Demonstrate the difference between automatic vs manual Guidewire sync
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def demonstrate_current_manual_flow():
    """Show the current 2-step manual process"""
    
    print("🔧 CURRENT MANUAL FLOW (What You Have Now)")
    print("="*60)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Step 1: Send email (automatic work item creation)
    print("📧 STEP 1: Send Email (Automatic)")
    print("-" * 30)
    
    test_email = {
        "subject": f"MANUAL DEMO {timestamp} - Insurance Request", 
        "sender_email": f"demo{timestamp}@company.com",
        "body": """
        Company: Manual Demo Company
        Industry: Technology
        Policy Type: Cyber Liability
        Coverage Amount: $2,000,000
        Effective Date: 2025-01-01
        Contact: demo@company.com
        """,
        "attachments": []
    }
    
    print(f"   Sending email...")
    response = requests.post(f"{BASE_URL}/api/email/intake", json=test_email, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Email processed: {data.get('message')}")
        print(f"   📧 Work item created, but NO Guidewire account yet")
        submission_ref = data.get('submission_ref')
    else:
        print(f"   ❌ Email failed")
        return
    
    # Wait and get work item ID
    time.sleep(3)
    
    print(f"\n🔍 Finding the created work item...")
    db_response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
    
    if db_response.status_code == 200:
        db_data = db_response.json()
        latest_item = db_data.get('latest_work_item')
        
        if latest_item and f"MANUAL DEMO {timestamp}" in latest_item['title']:
            work_item_id = latest_item['id']
            print(f"   ✅ Found work item ID: {work_item_id}")
            print(f"   📋 Title: {latest_item['title']}")
        else:
            print(f"   ❌ Could not find our work item")
            return
    else:
        print(f"   ❌ Could not check database")
        return
    
    # Step 2: Manual Guidewire sync (you have to do this)
    print(f"\n🔧 STEP 2: Manual Guidewire Sync (You Must Do This)")
    print("-" * 50)
    print(f"   Now you need to make a separate API call to create the Guidewire account...")
    
    manual_response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire", timeout=30)
    
    if manual_response.status_code == 200:
        manual_data = manual_response.json()
        
        if manual_data.get('success'):
            print(f"   ✅ Manual sync worked!")
            print(f"   🏢 Guidewire account created")
            print(f"   📋 Message: {manual_data.get('message')}")
        else:
            print(f"   ❌ Manual sync failed: {manual_data.get('message')}")
    else:
        print(f"   ❌ Manual sync HTTP error: {manual_response.status_code}")
    
    print(f"\n💡 SUMMARY OF MANUAL FLOW:")
    print(f"   1. You send email → Work item created")
    print(f"   2. You call /submit-to-guidewire → Guidewire account created")
    print(f"   3. Two separate steps required!")

def show_what_automatic_should_look_like():
    """Show what the automatic flow should look like when fixed"""
    
    print(f"\n🎯 WHAT AUTOMATIC FLOW SHOULD LOOK LIKE (Goal)")
    print("="*60)
    
    print("📧 SINGLE STEP: Send Email")
    print("-" * 30)
    print("   When you send email, it should:")
    print("   1. ✅ Create work item")
    print("   2. ✅ Automatically create Guidewire account") 
    print("   3. ✅ Return message: 'Email processed and synced to Guidewire'")
    print()
    print("   🎉 ONE step instead of TWO!")
    print("   🎉 No manual API calls needed!")
    print("   🎉 Complete automation!")

def show_workaround_script():
    """Show a script that automates the manual process"""
    
    print(f"\n🤖 WORKAROUND: AUTOMATED SCRIPT FOR MANUAL PROCESS")
    print("="*60)
    
    script_content = '''#!/usr/bin/env python3
"""
Workaround script that automates the manual Guidewire sync
"""

import requests
import time

def send_email_and_auto_sync(subject, sender_email, body):
    """Send email and automatically trigger Guidewire sync"""
    
    BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
    
    # Step 1: Send email
    email_data = {
        "subject": subject,
        "sender_email": sender_email,
        "body": body,
        "attachments": []
    }
    
    print(f"📧 Sending email...")
    response = requests.post(f"{BASE_URL}/api/email/intake", json=email_data, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Email failed")
        return False
    
    data = response.json()
    print(f"✅ Work item created: {data.get('message')}")
    
    # Wait for processing
    time.sleep(3)
    
    # Step 2: Find work item and auto-sync
    db_response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
    if db_response.status_code == 200:
        db_data = db_response.json()
        latest_item = db_data.get('latest_work_item')
        
        if latest_item:
            work_item_id = latest_item['id']
            print(f"🔧 Auto-triggering Guidewire sync for work item {work_item_id}...")
            
            sync_response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire", timeout=30)
            
            if sync_response.status_code == 200:
                sync_data = sync_response.json()
                if sync_data.get('success'):
                    print(f"🎉 Complete! Guidewire account created automatically")
                    return True
            
            print(f"❌ Auto-sync failed")
            return False
    
    print(f"❌ Could not find work item")
    return False

# Usage example:
if __name__ == "__main__":
    send_email_and_auto_sync(
        subject="Automated Test Insurance Request",
        sender_email="auto@test.com", 
        body="Company: Auto Test\\nIndustry: Technology\\nPolicy: Cyber Liability"
    )
'''
    
    print("   This script combines both steps into one function:")
    print("   📧 send_email_and_auto_sync() does everything automatically")
    print(f"   💾 Would you like me to create this workaround script?")

def main():
    print("🎯 UNDERSTANDING MANUAL vs AUTOMATIC GUIDEWIRE SYNC")
    print("="*80)
    
    demonstrate_current_manual_flow()
    show_what_automatic_should_look_like()
    show_workaround_script()
    
    print(f"\n{'='*80}")
    print("📋 SUMMARY")
    print(f"{'='*80}")
    print("❓ WHAT YOU ASKED:")
    print("   'Should I do something or does something happen in backend?'")
    print()
    print("✅ ANSWER:")
    print("   CURRENTLY: You need to do TWO steps manually")
    print("   GOAL: Should be ONE automatic step")
    print()
    print("🔧 OPTIONS:")
    print("   1. Use current 2-step manual process")
    print("   2. Use workaround script (automates the 2 steps)")  
    print("   3. Fix the auto-sync (requires server-side changes)")
    print()
    print("💡 RECOMMENDATION:")
    print("   Use the workaround script for now - it gives you the automatic behavior you want!")

if __name__ == "__main__":
    main()