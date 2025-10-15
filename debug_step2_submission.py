#!/usr/bin/env python3
"""
Debug script to test ONLY Step 2 - Submission Creation
Uses the existing account that was successfully created
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from guidewire_client_fixed import corrected_guidewire_client
from database import SessionLocal, WorkItem, Submission
import json

def test_submission_creation_only():
    """Test Step 2 - Submission Creation using existing account"""
    
    print("🔧 TESTING SUBMISSION CREATION (STEP 2 ONLY)")
    print("=" * 60)
    
    # Use the account that was successfully created earlier
    existing_account_id = "pc:SNletr6mHRyeDnhgpuPE-"
    existing_account_number = "2332505940"
    existing_organization = "Test Company Inc 416413"
    
    print(f"📋 Using existing account:")
    print(f"   Account ID: {existing_account_id}")
    print(f"   Account Number: {existing_account_number}")
    print(f"   Organization: {existing_organization}")
    print()
    
    # Get the latest work item to use its extracted data
    db = SessionLocal()
    try:
        latest_work_item = db.query(WorkItem).order_by(WorkItem.created_at.desc()).first()
        if latest_work_item:
            submission = db.query(Submission).filter(Submission.id == latest_work_item.submission_id).first()
            
            # Parse extracted fields
            if submission and submission.extracted_fields:
                if isinstance(submission.extracted_fields, str):
                    import json
                    extracted_data = json.loads(submission.extracted_fields)
                else:
                    extracted_data = submission.extracted_fields
            else:
                extracted_data = {}
            
            print(f"📊 Using extracted data from Work Item {latest_work_item.id}:")
            for key, value in extracted_data.items():
                print(f"   {key}: {value}")
            print()
        else:
            extracted_data = {}
            print("⚠️ No work item found, using default data")
    except Exception as e:
        print(f"❌ Error getting work item data: {e}")
        extracted_data = {}
    finally:
        db.close()
    
    # Add some default values if missing
    test_submission_data = {
        **extracted_data,
        "effective_date": "2025-01-15",
        "business_state": "CA",
        "coverage_amount": extracted_data.get("coverage_amount", "500000"),
        "industry": extracted_data.get("industry", "technology"),
        "employee_count": extracted_data.get("employee_count", "25"),
        "annual_revenue": extracted_data.get("annual_revenue", "2000000")
    }
    
    print("🚀 Testing Step 2 - Submission Creation...")
    print()
    
    try:
        # Test ONLY the submission creation step
        result = corrected_guidewire_client._create_submission_with_account(
            account_id=existing_account_id,
            account_number=existing_account_number,
            organization_name=existing_organization,
            submission_data=test_submission_data
        )
        
        print("📊 STEP 2 RESULTS:")
        print("-" * 40)
        
        if result.get("success"):
            print("✅ SUBMISSION CREATION SUCCESS!")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Job Number: {result.get('job_number')}")
            print(f"   Job Status: {result.get('job_status')}")
            print(f"   Policy Details Updated: {result.get('policy_details_updated', False)}")
            print()
            
            print("🎯 SEARCH IN GUIDEWIRE POLICYCENTER:")
            print(f"   ✅ Account Number: {existing_account_number}")
            print(f"   ✅ Job Number: {result.get('job_number')}")
            print(f"   ✅ Organization: {existing_organization}")
            
        else:
            print("❌ SUBMISSION CREATION FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Message: {result.get('message', 'No message')}")
            
            # Show raw response for debugging
            raw_response = result.get('raw_response', {})
            if raw_response:
                print()
                print("🔍 RAW RESPONSE DEBUG:")
                print(json.dumps(raw_response, indent=2))
        
    except Exception as e:
        print(f"💥 EXCEPTION IN STEP 2:")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_submission_creation_only()