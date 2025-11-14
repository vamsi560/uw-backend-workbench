#!/usr/bin/env python3
"""
Test script to debug Guidewire approval issue for job 0000749253
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
GUIDEWIRE_BASE = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net"

def test_approval_workflow():
    """Debug the approval workflow for job 0000749253"""
    
    print("🔍 Debugging Guidewire Approval Issue")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Target Job: 0000749253")
    print()
    
    try:
        # Step 1: Find the work item with job ID 0000749253
        print("1️⃣ Finding work item with Guidewire job 0000749253...")
        
        workitems_response = requests.get(f"{BASE_URL}/api/workitems/poll?limit=50")
        
        if workitems_response.status_code != 200:
            print(f"❌ Failed to get work items: {workitems_response.status_code}")
            return False
            
        workitems_data = workitems_response.json()
        items = workitems_data.get("items", [])
        
        target_work_item = None
        for item in items:
            if hasattr(item, 'guidewire_job_number') and item.guidewire_job_number == "0000749253":
                target_work_item = item
                break
            # Also check dict access
            if isinstance(item, dict) and item.get('guidewire_job_number') == "0000749253":
                target_work_item = item
                break
        
        if not target_work_item:
            print(f"❌ Could not find work item with job 0000749253")
            print(f"   Found {len(items)} work items. Checking job numbers...")
            
            for item in items[:5]:
                job_num = getattr(item, 'guidewire_job_number', 'N/A') if hasattr(item, 'guidewire_job_number') else item.get('guidewire_job_number', 'N/A')
                print(f"   - Work Item ID: {getattr(item, 'id', item.get('id', 'N/A'))}, Job: {job_num}")
                
            return False
        
        work_item_id = getattr(target_work_item, 'id', target_work_item.get('id'))
        current_status = getattr(target_work_item, 'status', target_work_item.get('status'))
        
        print(f"✅ Found work item ID: {work_item_id}")
        print(f"   Current status: {current_status}")
        print(f"   Guidewire job: 0000749253")
        print()
        
        # Step 2: Check current UW issues for this job
        print("2️⃣ Checking current UW issues in Guidewire...")
        
        try:
            uw_issues_response = requests.get(
                f"{GUIDEWIRE_BASE}/rest/job/v1/jobs/0000749253/uw-issues",
                auth=("su", "gw"),
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            print(f"   UW Issues response: {uw_issues_response.status_code}")
            
            if uw_issues_response.status_code == 200:
                uw_data = uw_issues_response.json()
                print(f"   UW Issues data: {json.dumps(uw_data, indent=2)}")
            else:
                print(f"   UW Issues error: {uw_issues_response.text}")
                
        except Exception as gw_error:
            print(f"   ❌ Guidewire connection failed: {gw_error}")
        
        print()
        
        # Step 3: Try approval via API
        print("3️⃣ Testing approval via API...")
        
        approval_payload = {
            "underwriter_notes": "Test approval from debugging script",
            "approved_by": "Debug Script"
        }
        
        approval_response = requests.post(
            f"{BASE_URL}/api/workitems/{work_item_id}/approve",
            json=approval_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Approval response: {approval_response.status_code}")
        
        if approval_response.status_code == 200:
            approval_data = approval_response.json()
            print(f"   ✅ Approval successful!")
            print(f"   Response: {json.dumps(approval_data, indent=2)}")
        else:
            print(f"   ❌ Approval failed!")
            print(f"   Error: {approval_response.text}")
        
        print()
        
        # Step 4: Check final status
        print("4️⃣ Checking final status...")
        
        final_check = requests.get(f"{BASE_URL}/api/workitems/poll?work_item_id={work_item_id}")
        
        if final_check.status_code == 200:
            final_data = final_check.json()
            work_item_detail = final_data.get('work_item', {})
            final_status = work_item_detail.get('status', 'Unknown')
            
            print(f"   Final status: {final_status}")
            
            if final_status == "APPROVED":
                print("   ✅ Status successfully updated to APPROVED")
            else:
                print(f"   ⚠️  Status is still: {final_status}")
        else:
            print(f"   ❌ Could not check final status: {final_check.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in approval workflow test: {e}")
        return False

def test_direct_guidewire_connection():
    """Test direct connection to Guidewire server"""
    
    print("\n🌐 Testing Direct Guidewire Connection")
    print("=" * 45)
    
    try:
        # Test basic connectivity
        test_response = requests.get(
            f"{GUIDEWIRE_BASE}/rest/job/v1/jobs/0000749253",
            auth=("su", "gw"),
            headers={'Accept': 'application/json'},
            timeout=10
        )
        
        print(f"Job details response: {test_response.status_code}")
        
        if test_response.status_code == 200:
            job_data = test_response.json()
            print("✅ Guidewire connection successful!")
            print(f"Job data preview: {str(job_data)[:200]}...")
        else:
            print(f"❌ Guidewire connection failed: {test_response.text}")
            
    except Exception as e:
        print(f"❌ Direct Guidewire test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Approval Debugging for Job 0000749253")
    
    success = test_approval_workflow()
    
    if success:
        test_direct_guidewire_connection()
    
    print("\n📋 Debugging Summary:")
    print("- Check if work item exists and has correct job ID")
    print("- Verify Guidewire connectivity and UW issues")
    print("- Test approval API endpoint")
    print("- Verify status update after approval")
    
    print("\n🔧 Common Issues:")
    print("- Guidewire server connectivity problems")
    print("- UW issues already resolved/approved")
    print("- Authentication/authorization failures")
    print("- Duplicate API endpoints causing confusion")