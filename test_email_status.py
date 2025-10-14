#!/usr/bin/env python3
"""
Test script to check email processing status and Guidewire integration
Run this after sending an email to see what happened
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Your deployed API URL
BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def check_api_health():
    """Check if the API is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is accessible")
            return True
        else:
            print(f"⚠️  API responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API is not accessible: {str(e)}")
        return False

def get_recent_work_items(limit: int = 10):
    """Get recent work items using the correct polling endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/workitems/poll", 
                              params={'limit': limit, 'include_details': True}, 
                              timeout=10)
        if response.status_code == 200:
            data = response.json()
            # The polling endpoint returns {items: [...], count: n, timestamp: ...}
            if isinstance(data, dict) and 'items' in data:
                return data['items']
            return data
        else:
            print(f"Failed to get work items: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting work items: {str(e)}")
        return None

def get_recent_submissions(limit: int = 10):
    """Get recent submissions using workitems endpoint (they contain submission data)"""
    try:
        # Use the workitems endpoint since it contains submission information
        response = requests.get(f"{BASE_URL}/api/workitems", 
                              params={'limit': limit}, 
                              timeout=10)
        if response.status_code == 200:
            workitems = response.json()
            if isinstance(workitems, list):
                # Extract submission info from workitems
                submissions = []
                for wi in workitems:
                    submissions.append({
                        'id': wi.get('id'),
                        'subject': wi.get('subject'),
                        'from_email': wi.get('from_email'),
                        'created_at': wi.get('created_at'),
                        'status': wi.get('status')
                    })
                return submissions
            return workitems
        else:
            print(f"Failed to get submissions: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting submissions: {str(e)}")
        return None

def get_work_item_history(work_item_id: int):
    """Get work item history - try to get detailed view"""
    try:
        # Try to get detailed work item info (includes history in enhanced poll)
        response = requests.get(f"{BASE_URL}/api/workitems/poll", 
                              params={'work_item_id': work_item_id}, 
                              timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('history', []) if isinstance(data, dict) else []
        else:
            print(f"Failed to get work item history: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting work item history: {str(e)}")
        return None

def check_guidewire_status():
    """Check Guidewire connectivity status"""
    try:
        # Try to access a Guidewire test endpoint 
        response = requests.get(f"{BASE_URL}/api/test/guidewire", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Extract guidewire_test info from the response
            gw_test = data.get("guidewire_test", {})
            return {
                "guidewire_accessible": gw_test.get("success", False),
                "error": gw_test.get("error") if not gw_test.get("success") else None,
                "message": gw_test.get("message", "")
            }
        else:
            print(f"Guidewire status check failed: {response.status_code}")
            return {"guidewire_accessible": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"guidewire_accessible": False, "error": str(e)}

def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    try:
        if dt_str:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        pass
    return dt_str or "Not set"

def display_work_item(item: Dict[str, Any], index: int):
    """Display work item information"""
    print(f"\n{'='*60}")
    print(f"WORK ITEM #{index + 1} (ID: {item.get('id', 'Unknown')})")
    print(f"{'='*60}")
    
    print(f"📧 Subject: {item.get('subject', 'No subject')}")
    print(f"👤 Assigned To: {item.get('assigned_to', 'Unassigned')}")
    print(f"📊 Status: {item.get('status', 'Unknown')}")
    print(f"⚡ Priority: {item.get('priority', 'Unknown')}")
    print(f"📅 Created: {format_datetime(item.get('created_at'))}")
    print(f"🔄 Updated: {format_datetime(item.get('updated_at'))}")
    
    # Guidewire integration status
    guidewire_job_id = item.get('guidewire_job_id')
    if guidewire_job_id:
        print(f"✅ Guidewire Job ID: {guidewire_job_id}")
    else:
        print("❌ Guidewire Job ID: Not created (likely network/connectivity issue)")
    
    # Additional details
    if item.get('description'):
        print(f"📝 Description: {item.get('description')[:100]}...")
    
    if item.get('metadata'):
        print(f"🏷️  Metadata: {json.dumps(item.get('metadata'), indent=2)}")

def display_submission(submission: Dict[str, Any], index: int):
    """Display submission information"""
    print(f"\n{'='*60}")
    print(f"SUBMISSION #{index + 1} (ID: {submission.get('id', 'Unknown')})")
    print(f"{'='*60}")
    
    print(f"🏢 Account Name: {submission.get('account_name', 'Unknown')}")
    print(f"📧 Broker Email: {submission.get('broker_email', 'Unknown')}")
    print(f"🏭 Industry: {submission.get('industry', 'Unknown')}")
    print(f"👥 Employee Count: {submission.get('employee_count', 'Unknown')}")
    print(f"💰 Annual Revenue: ${submission.get('annual_revenue', 'Unknown'):,}" if submission.get('annual_revenue') else "💰 Annual Revenue: Unknown")
    print(f"🛡️  Coverage Amount: ${submission.get('coverage_amount', 'Unknown'):,}" if submission.get('coverage_amount') else "🛡️  Coverage Amount: Unknown")
    print(f"📅 Created: {format_datetime(submission.get('created_at'))}")
    
    # Guidewire integration
    guidewire_account_id = submission.get('guidewire_account_id')
    if guidewire_account_id:
        print(f"✅ Guidewire Account ID: {guidewire_account_id}")
    else:
        print("❌ Guidewire Account ID: Not created")

def main():
    """Main test function"""
    print("🔍 CHECKING EMAIL PROCESSING STATUS")
    print("=" * 60)
    
    # Check API health
    print("\n1. API Health Check:")
    if not check_api_health():
        print("Cannot proceed - API is not accessible")
        return
    
    # Check Guidewire status
    print("\n2. Guidewire Connectivity:")
    gw_status = check_guidewire_status()
    if gw_status.get('guidewire_accessible'):
        print("✅ Guidewire is accessible")
    else:
        print(f"❌ Guidewire is not accessible: {gw_status.get('error', 'Unknown error')}")
        print("   This is expected when working from home - Guidewire requires corporate network")
    
    # Get recent work items
    print("\n3. Recent Work Items:")
    work_items = get_recent_work_items(5)
    if work_items:
        if isinstance(work_items, list) and len(work_items) > 0:
            print(f"Found {len(work_items)} recent work items:")
            
            for i, item in enumerate(work_items):
                display_work_item(item, i)
                
                # Get work item history
                work_item_id = item.get('id')
                if work_item_id:
                    print(f"\n📋 Work Item History:")
                    history = get_work_item_history(work_item_id)
                    if history and isinstance(history, list):
                        for j, h_item in enumerate(history[-3:]):  # Last 3 history items
                            print(f"   {j+1}. {h_item.get('action', 'Unknown')} - {format_datetime(h_item.get('timestamp'))}")
                            if h_item.get('details'):
                                print(f"      Details: {h_item.get('details')}")
                    else:
                        print("   No history available")
        else:
            print("No work items found")
    else:
        print("Could not retrieve work items")
    
    # Get recent submissions
    print("\n4. Recent Submissions:")
    submissions = get_recent_submissions(5)
    if submissions:
        if isinstance(submissions, list) and len(submissions) > 0:
            print(f"Found {len(submissions)} recent submissions:")
            
            for i, submission in enumerate(submissions):
                display_submission(submission, i)
        else:
            print("No submissions found")
    else:
        print("Could not retrieve submissions")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    if work_items and isinstance(work_items, list) and len(work_items) > 0:
        latest_item = work_items[0]
        has_guidewire_job = bool(latest_item.get('guidewire_job_id'))
        
        print(f"✅ Latest work item created: {format_datetime(latest_item.get('created_at'))}")
        print(f"📧 Email processing: SUCCESS")
        
        if has_guidewire_job:
            print(f"✅ Guidewire integration: SUCCESS")
        else:
            print(f"⚠️  Guidewire integration: FAILED (expected from home network)")
            print(f"   The work item was created successfully in the local system")
            print(f"   Guidewire sync will happen when you're back on corporate network")
    else:
        print("❓ No recent work items found - email may not have been processed")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. If work items exist but no Guidewire sync: Normal when off corporate network")
    print(f"   2. If no work items exist: Check email intake logs or try sending another test email")
    print(f"   3. When back on corporate network: Re-run this test to verify Guidewire sync")

if __name__ == "__main__":
    main()