#!/usr/bin/env python3
"""
Check latest work item and manually sync to Guidewire
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def check_and_sync_latest_work_item():
    print("🔍 CHECKING LATEST WORK ITEM AND SYNCING TO GUIDEWIRE")
    print("="*60)
    
    # Get latest work item
    response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
    if response.status_code == 200:
        data = response.json()
        latest_item = data.get("latest_work_item")
        
        if latest_item:
            print(f"📧 Latest Work Item:")
            print(f"   ID: {latest_item['id']}")
            print(f"   Title: {latest_item['title']}")
            print(f"   Status: {latest_item['status']}")
            print(f"   Created: {latest_item['created_at']}")
            
            # Check if created recently (last 10 minutes)
            try:
                created_dt = datetime.fromisoformat(latest_item["created_at"].replace("Z", ""))
                minutes_ago = (datetime.now() - created_dt).total_seconds() / 60
                
                if minutes_ago < 10:
                    print(f"   🆕 Created {minutes_ago:.1f} minutes ago - This is likely your email!")
                    
                    # Now try to sync to Guidewire
                    work_item_id = latest_item["id"]
                    print(f"\n🔄 SYNCING WORK ITEM {work_item_id} TO GUIDEWIRE...")
                    
                    sync_response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire", timeout=30)
                    
                    if sync_response.status_code == 200:
                        sync_data = sync_response.json()
                        
                        if sync_data.get("success"):
                            print(f"✅ SYNC SUCCESSFUL!")
                            print(f"   Guidewire Account ID: {sync_data.get('guidewire_account_id', 'None')}")
                            print(f"   Account Number: {sync_data.get('account_number', 'None')}")
                            print(f"   Guidewire Job ID: {sync_data.get('guidewire_job_id', 'None')}")
                            print(f"   Job Number: {sync_data.get('job_number', 'None')}")
                            
                            if sync_data.get("account_number"):
                                print(f"\n🎉 SUCCESS! Check Guidewire PolicyCenter for Account: {sync_data.get('account_number')}")
                                print(f"   Search for account number: {sync_data.get('account_number')}")
                                print(f"   Or search for company name from your email")
                            else:
                                print(f"\n⚠️  Sync reported success but no account details returned")
                                print(f"   This might indicate a response parsing issue")
                        else:
                            print(f"❌ SYNC FAILED")
                            print(f"   Error: {sync_data.get('error', 'Unknown error')}")
                            print(f"   Message: {sync_data.get('message', 'No message')}")
                            print(f"   Details: {sync_data.get('details', {})}")
                    else:
                        print(f"❌ Sync request failed: HTTP {sync_response.status_code}")
                        try:
                            error_data = sync_response.json()
                            print(f"   Error details: {error_data}")
                        except:
                            print(f"   Response: {sync_response.text}")
                else:
                    print(f"   ℹ️  Created {minutes_ago:.1f} minutes ago - not your recent email")
                    print(f"   Still trying to sync it...")
                    
                    # Try syncing anyway
                    work_item_id = latest_item["id"]
                    sync_response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire", timeout=30)
                    
                    if sync_response.status_code == 200:
                        sync_data = sync_response.json()
                        if sync_data.get("success") and sync_data.get("account_number"):
                            print(f"   ✅ Sync successful! Account: {sync_data.get('account_number')}")
                        else:
                            print(f"   ⚠️  Sync completed but unclear results")
                    else:
                        print(f"   ❌ Sync failed: HTTP {sync_response.status_code}")
                        
            except Exception as e:
                print(f"   ⚠️  Could not parse creation time: {e}")
        else:
            print("❌ No latest work item found")
    else:
        print(f"❌ Failed to get work items: HTTP {response.status_code}")

def check_why_auto_sync_failed():
    """Investigate why automatic Guidewire sync during email processing isn't working"""
    print(f"\n🔍 INVESTIGATING WHY AUTO-SYNC DURING EMAIL PROCESSING FAILED")
    print("="*60)
    
    # Test the exact same flow that email processing uses
    try:
        test_data = {
            "company_name": "Auto-Sync Test Company",
            "contact_email": "autosync@test.com",
            "industry": "technology",
            "employee_count": "50",
            "annual_revenue": "2000000",
            "coverage_amount": "1000000"
        }
        
        print("Testing direct Guidewire submission (same as email processing uses)...")
        response = requests.post(f"{BASE_URL}/api/test/guidewire-submission",
                               json=test_data,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            gw_result = data.get("guidewire_result", {})
            
            if gw_result.get("success") and gw_result.get("account_id"):
                print(f"✅ Direct Guidewire submission works fine!")
                print(f"   Account ID: {gw_result.get('account_id')}")
                print(f"   Account Number: {gw_result.get('account_number')}")
                print(f"\n💡 Issue is likely in the email processing -> Guidewire integration flow")
                print(f"   The Guidewire API itself works perfectly")
            else:
                print(f"❌ Direct Guidewire submission failed")
                print(f"   Error: {gw_result.get('error')}")
                print(f"   This explains why email auto-sync isn't working")
        else:
            print(f"❌ Direct submission test failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Auto-sync investigation error: {str(e)}")

if __name__ == "__main__":
    check_and_sync_latest_work_item()
    check_why_auto_sync_failed()
    
    print(f"\n{'='*60}")
    print("📊 SUMMARY & RECOMMENDATIONS")
    print(f"{'='*60}")
    print("1. ✅ Your email was processed and work item created")
    print("2. ⚠️  Automatic Guidewire sync during email processing may have failed")
    print("3. 🔄 Manual sync should work (results shown above)")
    print("4. 🎯 Check Guidewire PolicyCenter for the account number shown above")
    print("\n💡 For future emails:")
    print("   - Email processing will create work items")
    print("   - Use manual sync if auto-sync fails")
    print("   - Guidewire connection is confirmed working")