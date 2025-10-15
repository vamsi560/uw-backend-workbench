#!/usr/bin/env python3
"""
Quick script to check latest work item and Guidewire integration status
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, WorkItem, Submission, GuidewireResponse
from sqlalchemy import desc
from datetime import datetime

def check_latest_work_item():
    """Check the latest work item and its Guidewire status"""
    
    print("🔍 CHECKING LATEST WORK ITEM AND GUIDEWIRE STATUS")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Get the latest work item
        latest_work_item = db.query(WorkItem).order_by(desc(WorkItem.created_at)).first()
        
        if not latest_work_item:
            print("❌ No work items found in database")
            return
        
        # Get associated submission
        submission = db.query(Submission).filter(Submission.id == latest_work_item.submission_id).first()
        
        print(f"📧 Latest Work Item:")
        print(f"   ID: {latest_work_item.id}")
        print(f"   Title: {latest_work_item.title}")
        print(f"   Status: {latest_work_item.status.value if latest_work_item.status else 'Unknown'}")
        print(f"   Created: {latest_work_item.created_at}")
        print(f"   Assigned To: {latest_work_item.assigned_to or 'Unassigned'}")
        
        if submission:
            print(f"   From: {submission.sender_email}")
            print(f"   Subject: {submission.subject}")
        
        print()
        
        # Check for Guidewire IDs in WorkItem
        print("📋 Guidewire Integration Status:")
        has_guidewire_ids = latest_work_item.guidewire_account_id or latest_work_item.guidewire_job_id
        
        if has_guidewire_ids:
            print(f"   ✅ WorkItem has Guidewire IDs:")
            print(f"      Account ID: {latest_work_item.guidewire_account_id}")
            print(f"      Job ID: {latest_work_item.guidewire_job_id}")
        else:
            print(f"   ⚠️ WorkItem missing Guidewire IDs")
            print(f"      Account ID: {latest_work_item.guidewire_account_id}")
            print(f"      Job ID: {latest_work_item.guidewire_job_id}")
        
        print()
        
        # Check GuidewireResponse table for detailed info
        guidewire_responses = db.query(GuidewireResponse).filter(
            GuidewireResponse.work_item_id == latest_work_item.id
        ).order_by(desc(GuidewireResponse.created_at)).all()
        
        if guidewire_responses:
            print(f"📊 Guidewire Response Records: {len(guidewire_responses)} found")
            for i, response in enumerate(guidewire_responses):
                print(f"   Response {i+1}:")
                print(f"      Account Number: {response.account_number}")
                print(f"      Job Number: {response.job_number}")
                print(f"      Organization: {response.organization_name}")
                print(f"      Success: {response.submission_success}")
                print(f"      Created: {response.created_at}")
                if i == 0:  # Show details for most recent
                    print(f"      Account Status: {response.account_status}")
                    print(f"      Job Status: {response.job_status}")
                print()
        else:
            print("❌ No Guidewire response records found")
            print()
        
        # Summary for PolicyCenter search
        print("🎯 SEARCH IN GUIDEWIRE POLICYCENTER:")
        print("-" * 40)
        
        if guidewire_responses and guidewire_responses[0].account_number:
            latest_response = guidewire_responses[0]
            print(f"✅ Account Number: {latest_response.account_number}")
            print(f"✅ Job Number: {latest_response.job_number}")
            print(f"✅ Organization: {latest_response.organization_name}")
            print()
            print("💡 Use these numbers to search in Guidewire PolicyCenter!")
        else:
            print("❌ No account/submission numbers available")
            print("💡 Try manual sync using the API endpoint")
            
    except Exception as e:
        print(f"💥 Error checking work items: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_manual_sync():
    """Test manual Guidewire sync for latest work item"""
    print()
    print("🔄 TESTING MANUAL GUIDEWIRE SYNC")
    print("=" * 40)
    
    try:
        from guidewire_client_fixed import corrected_guidewire_client
        
        # Sample data for testing
        test_data = {
            "company_name": "Manual Sync Test Company",
            "named_insured": "Manual Sync Test Company",
            "contact_name": "Test User",
            "contact_email": "test@company.com",
            "business_address": "123 Test St",
            "business_city": "San Francisco",
            "business_state": "CA", 
            "business_zip": "94105",
            "industry": "technology",
            "employee_count": "25",
            "annual_revenue": "1000000",
            "coverage_amount": "500000",
            "policy_type": "cyber liability"
        }
        
        print("Testing Guidewire connectivity...")
        result = corrected_guidewire_client.create_cyber_submission_correct_flow(test_data)
        
        if result.get("success"):
            print("✅ Manual sync test successful!")
            print(f"   Account Number: {result.get('account_number')}")
            print(f"   Job Number: {result.get('job_number')}")
        else:
            print("❌ Manual sync test failed")
            print(f"   Error: {result.get('error')}")
            print(f"   Message: {result.get('message')}")
            
    except Exception as e:
        print(f"💥 Error in manual sync test: {str(e)}")

if __name__ == "__main__":
    check_latest_work_item()
    test_manual_sync()