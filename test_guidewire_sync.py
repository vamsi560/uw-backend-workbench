#!/usr/bin/env python3
"""
Test Guidewire connection and sync existing work items
Now that you're on corporate network with Guidewire access
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_guidewire_connection():
    """Test if Guidewire is now accessible"""
    print("🔍 TESTING GUIDEWIRE CONNECTION")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/test/guidewire", timeout=15)
        if response.status_code == 200:
            data = response.json()
            gw_test = data.get('guidewire_test', {})
            
            print(f"✅ Guidewire Test Response Received")
            print(f"   Success: {gw_test.get('success', False)}")
            print(f"   Message: {gw_test.get('message', 'No message')}")
            
            if gw_test.get('error'):
                print(f"   Error: {gw_test.get('error')}")
            
            # Show connection details
            config = data.get('configuration', {})
            if config:
                print(f"\n📋 Connection Details:")
                print(f"   Base URL: {config.get('base_url', 'Not shown')}")
                print(f"   Auth Method: {config.get('auth_method', 'Unknown')}")
                print(f"   Username: {config.get('username', 'Not shown')}")
            
            return gw_test.get('success', False)
        else:
            print(f"❌ Guidewire test failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Guidewire test error: {str(e)}")
        return False

def test_simple_guidewire_request():
    """Test a simple Guidewire API call"""
    print("\n🔍 TESTING SIMPLE GUIDEWIRE API CALL")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/debug/test-simple-guidewire", timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Simple API Test Response:")
            print(f"   Endpoint: {data.get('endpoint', 'Not shown')}")
            
            results = data.get('results', {})
            
            # Ping test
            ping_test = results.get('ping_test', {})
            if ping_test.get('success'):
                print(f"   ✅ Ping Test: SUCCESS")
            else:
                print(f"   ❌ Ping Test: FAILED - {ping_test.get('error', 'Unknown error')}")
            
            # Account creation test
            account_test = results.get('account_creation', {})
            if account_test.get('success'):
                print(f"   ✅ Account Creation Test: SUCCESS")
                
                # Check if real account was created
                real_account = results.get('real_account_created', {})
                if real_account.get('success'):
                    print(f"   🎉 REAL ACCOUNT CREATED!")
                    print(f"      Account ID: {real_account.get('account_id')}")
                    print(f"      Account Number: {real_account.get('account_number')}")
                else:
                    print(f"   ⚠️  Account test succeeded but no real account created")
            else:
                print(f"   ❌ Account Creation Test: FAILED")
                print(f"      Error: {account_test.get('error', 'Unknown error')}")
            
            return account_test.get('success', False)
        else:
            print(f"❌ Simple Guidewire test failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Simple Guidewire test error: {str(e)}")
        return False

def get_pending_work_items():
    """Get work items that haven't been synced to Guidewire"""
    print("\n🔍 CHECKING PENDING WORK ITEMS")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
        if response.status_code == 200:
            data = response.json()
            recent_items = data.get('recent_work_items', [])
            
            print(f"Found {len(recent_items)} recent work items:")
            
            pending_items = []
            for item in recent_items:
                print(f"\n   📧 Work Item ID: {item['id']}")
                print(f"      Title: {item['title']}")
                print(f"      Status: {item['status']}")
                print(f"      Created: {item['created_at']}")
                
                # Check if created today (your test emails)
                try:
                    created_dt = datetime.fromisoformat(item['created_at'].replace('Z', ''))
                    if created_dt.date() == datetime.now().date():
                        print(f"      🆕 Created TODAY - This is from your email test!")
                        pending_items.append(item)
                except:
                    pass
            
            return pending_items
        else:
            print(f"❌ Failed to get work items: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting work items: {str(e)}")
        return []

def sync_work_item_to_guidewire(work_item_id):
    """Try to sync a specific work item to Guidewire"""
    print(f"\n🔄 SYNCING WORK ITEM {work_item_id} TO GUIDEWIRE")
    print("=" * 50)
    
    try:
        response = requests.post(f"{BASE_URL}/api/workitems/{work_item_id}/submit-to-guidewire", 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print(f"✅ SYNC SUCCESSFUL!")
                print(f"   Work Item ID: {data.get('work_item_id')}")
                print(f"   Guidewire Account ID: {data.get('guidewire_account_id')}")
                print(f"   Account Number: {data.get('account_number')}")
                print(f"   Guidewire Job ID: {data.get('guidewire_job_id')}")
                print(f"   Job Number: {data.get('job_number')}")
                
                quote_info = data.get('quote_info', {})
                if quote_info:
                    print(f"   💰 Quote Info: {quote_info}")
                
                return True
            else:
                print(f"❌ SYNC FAILED")
                print(f"   Error: {data.get('error', 'Unknown error')}")
                print(f"   Message: {data.get('message', 'No message')}")
                return False
        else:
            print(f"❌ Sync request failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response text: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Sync error: {str(e)}")
        return False

def test_new_submission():
    """Test creating a brand new submission now that Guidewire is accessible"""
    print(f"\n🆕 TESTING NEW SUBMISSION WITH GUIDEWIRE ACCESS")
    print("=" * 50)
    
    # Create a test email payload
    test_email = {
        "subject": "NEW TEST - Guidewire Connected - Tech Solutions Inc",
        "sender_email": "test@techsolutions.com",
        "body": "We need cyber insurance for Tech Solutions Inc. We have 75 employees, $8M annual revenue, technology industry, need $2M coverage. This is a test with Guidewire access.",
        "attachments": []
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake", 
                               json=test_email, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ NEW SUBMISSION CREATED!")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            print(f"   Submission ID: {data.get('submission_id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            # This should now include Guidewire integration results
            return data.get('submission_ref')
        else:
            print(f"❌ New submission failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ New submission error: {str(e)}")
        return None

def main():
    """Main test function"""
    print("🚀 GUIDEWIRE CONNECTION & SYNC TEST")
    print("Now that you're on corporate network with Guidewire access")
    print("=" * 60)
    
    # 1. Test basic Guidewire connection
    gw_connected = test_guidewire_connection()
    
    # 2. Test simple Guidewire API calls
    gw_api_working = test_simple_guidewire_request()
    
    # 3. Get your pending work items
    pending_items = get_pending_work_items()
    
    # 4. Try to sync existing work items if Guidewire is working
    if gw_api_working and pending_items:
        print(f"\n🔄 ATTEMPTING TO SYNC {len(pending_items)} PENDING WORK ITEMS")
        print("=" * 50)
        
        sync_results = []
        for item in pending_items[:3]:  # Sync first 3 items
            work_item_id = item['id']
            success = sync_work_item_to_guidewire(work_item_id)
            sync_results.append({'id': work_item_id, 'success': success})
        
        successful_syncs = sum(1 for r in sync_results if r['success'])
        print(f"\n📊 SYNC RESULTS: {successful_syncs}/{len(sync_results)} successful")
    
    # 5. Test a brand new submission (should sync automatically)
    if gw_api_working:
        new_submission_ref = test_new_submission()
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*60}")
    
    if gw_connected:
        print("✅ Guidewire connection: WORKING")
    else:
        print("❌ Guidewire connection: FAILED")
    
    if gw_api_working:
        print("✅ Guidewire API calls: WORKING")
        print("🎉 You should now be able to create accounts and submissions in Guidewire!")
    else:
        print("❌ Guidewire API calls: FAILED")
        print("💡 Check network connectivity and Guidewire server status")
    
    if pending_items:
        print(f"📧 Found {len(pending_items)} pending work items from your earlier tests")
        print("💡 These can be manually synced using the sync endpoints")
    
    print(f"\n🔍 Next Steps:")
    if gw_api_working:
        print("1. Check Guidewire PolicyCenter UI for new accounts/submissions")
        print("2. Send another test email - it should sync automatically now")
        print("3. Use the manual sync endpoints for existing work items if needed")
    else:
        print("1. Verify you're on the corporate network")
        print("2. Check Guidewire server status with IT team")
        print("3. Verify VPN/network connectivity to Guidewire")

if __name__ == "__main__":
    main()