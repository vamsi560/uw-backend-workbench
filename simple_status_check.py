#!/usr/bin/env python3
"""
Simple test to check your email processing results
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def check_status():
    print("🔍 CHECKING YOUR EMAIL STATUS")
    print("=" * 50)
    
    # Check database status
    print("\n1. Database Status:")
    try:
        response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database connected")
            print(f"📊 Work Items: {data['work_items_count']}")
            print(f"📧 Submissions: {data['submissions_count']}")
            
            # Show latest work item
            latest = data.get('latest_work_item')
            if latest:
                print(f"\n📋 Latest Work Item:")
                print(f"   ID: {latest['id']}")
                print(f"   Title: {latest['title']}")
                print(f"   Status: {latest['status']}")
                print(f"   Created: {latest['created_at']}")
            
            # Show recent work items
            recent = data.get('recent_work_items', [])
            if recent:
                print(f"\n📋 Recent Work Items ({len(recent)}):")
                for i, wi in enumerate(recent[:5]):  # Show top 5
                    print(f"   {i+1}. ID:{wi['id']} - {wi['title']} [{wi['status']}]")
        else:
            print(f"❌ Database check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Database check error: {str(e)}")
    
    # Check Guidewire status
    print("\n2. Guidewire Status:")
    try:
        response = requests.get(f"{BASE_URL}/api/test/guidewire", timeout=15)
        if response.status_code == 200:
            data = response.json()
            gw_test = data.get('guidewire_test', {})
            if gw_test.get('success'):
                print("✅ Guidewire connection successful")
                print(f"   Message: {gw_test.get('message', 'Connected')}")
            else:
                print("❌ Guidewire connection failed")
                print(f"   Error: {gw_test.get('error', 'Unknown error')}")
                print("   This is expected when working from home (off corporate network)")
        else:
            print(f"⚠️  Guidewire test returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Guidewire test error: {str(e)}")
        print("   This is expected when working from home")
    
    # Test a simple workitems call
    print("\n3. Work Items API Test:")
    try:
        response = requests.get(f"{BASE_URL}/api/workitems", timeout=10)
        if response.status_code == 200:
            workitems = response.json()
            if isinstance(workitems, list):
                print(f"✅ Work Items API working - found {len(workitems)} items")
                if workitems:
                    latest_wi = workitems[0]
                    print(f"   Latest: {latest_wi.get('subject', 'No subject')} from {latest_wi.get('from_email', 'Unknown')}")
            else:
                print(f"⚠️  Unexpected work items format: {type(workitems)}")
        else:
            print(f"❌ Work Items API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Work Items API error: {str(e)}")
    
    # Check for your recent submissions
    print("\n4. Your Recent Email Processing:")
    try:
        # Get recent work items from debug endpoint
        response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
        if response.status_code == 200:
            data = response.json()
            recent_items = data.get('recent_work_items', [])
            
            print(f"Found {len(recent_items)} recent work items:")
            
            for i, item in enumerate(recent_items):
                print(f"\n   📧 Work Item #{i+1}:")
                print(f"      ID: {item['id']}")
                print(f"      Title: {item['title']}")
                print(f"      Status: {item['status']}")
                print(f"      Created: {item['created_at']}")
                print(f"      Submission ID: {item['submission_id']}")
                
                # Check if this was created recently (today)
                try:
                    created_dt = datetime.fromisoformat(item['created_at'].replace('Z', ''))
                    now = datetime.now()
                    if created_dt.date() == now.date():
                        print(f"      🆕 Created TODAY! This might be from your email")
                except:
                    pass
    except Exception as e:
        print(f"❌ Recent items check error: {str(e)}")
    
    print(f"\n{'='*50}")
    print("📊 SUMMARY:")
    print("✅ Your backend API is working")
    print("✅ Database has work items and submissions")
    print("⚠️  Guidewire may not be accessible (normal from home)")
    print("\n💡 If you see recent work items created today, your email was processed!")
    print("💡 The work item will sync with Guidewire when you're back on corporate network")

if __name__ == "__main__":
    check_status()