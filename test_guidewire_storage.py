#!/usr/bin/env python3

import json
import logging
from database import SessionLocal, WorkItem, GuidewireResponse
from sqlalchemy import desc
from llm_service import LLMService
from guidewire_client import guidewire_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_guidewire_storage():
    """Test if Guidewire data is being stored in WorkItem correctly"""
    
    # Sample email data
    test_data = {
        "subject": "Cyber Insurance Quote Request - Storage Test",
        "sender_email": "test@storagetest.com",
        "body": """
Company: Storage Test Corp
Contact: Jane Doe
Email: jane@storagetest.com
Phone: 555-9999
Industry: Technology
Employees: 25
Revenue: $2,000,000
Coverage: $500,000 cyber liability
"""
    }
    
    print("🧪 Testing Guidewire data storage...")
    
    # Extract data using LLM
    llm_service = LLMService()
    extracted_data = llm_service.extract_insurance_data(test_data["body"])
    
    print(f"📊 Extracted data: {json.dumps(extracted_data, indent=2)[:300]}...")
    
    # Test Guidewire submission
    print("\n🎯 Testing Guidewire submission...")
    guidewire_result = guidewire_client.create_cyber_submission(extracted_data)
    
    print(f"✅ Guidewire Success: {guidewire_result.get('success')}")
    print(f"🏢 Account ID: {guidewire_result.get('account_id')}")
    print(f"📋 Job ID: {guidewire_result.get('job_id')}")
    print(f"📄 Account Number: {guidewire_result.get('account_number')}")
    print(f"🔢 Job Number: {guidewire_result.get('job_number')}")
    
    # Test storage with database simulation
    db = SessionLocal()
    try:
        # Create a test WorkItem (simulating the email processing)
        from database import Submission
        import uuid
        
        # Create submission first
        submission = Submission(
            submission_id=99999,  # Test ID
            submission_ref=uuid.uuid4(),
            subject=test_data["subject"],
            sender_email=test_data["sender_email"],
            body_text=test_data["body"],
            extracted_fields=extracted_data
        )
        db.add(submission)
        db.commit()
        
        # Create work item
        work_item = WorkItem(
            submission_id=submission.id,
            title="Test Storage Work Item",
            description="Testing Guidewire ID storage"
        )
        db.add(work_item)
        db.commit()
        
        print(f"\n📋 Created test WorkItem {work_item.id}")
        
        # Store Guidewire response
        if guidewire_result.get("success"):
            guidewire_response_id = guidewire_client.store_guidewire_response(
                db=db,
                work_item_id=work_item.id,
                submission_id=submission.id,
                parsed_data=guidewire_result.get("parsed_data", {}),
                raw_response=guidewire_result.get("raw_response", {})
            )
            
            print(f"💾 Stored GuidewireResponse {guidewire_response_id}")
            
            # Test the WorkItem update logic
            print(f"\n🔍 Testing WorkItem update...")
            print(f"Account ID from result: {guidewire_result.get('account_id')}")
            print(f"Job ID from result: {guidewire_result.get('job_id')}")
            
            if guidewire_result.get("account_id"):
                work_item.guidewire_account_id = guidewire_result["account_id"]
                print(f"✅ Set WorkItem account_id: {guidewire_result['account_id']}")
            if guidewire_result.get("job_id"):
                work_item.guidewire_job_id = guidewire_result["job_id"]
                print(f"✅ Set WorkItem job_id: {guidewire_result['job_id']}")
            
            # Fallback test
            if not work_item.guidewire_account_id or not work_item.guidewire_job_id:
                print("🔄 Testing fallback logic...")
                gw_response = db.query(GuidewireResponse).filter(
                    GuidewireResponse.work_item_id == work_item.id
                ).first()
                if gw_response:
                    if not work_item.guidewire_account_id and gw_response.guidewire_account_id:
                        work_item.guidewire_account_id = gw_response.guidewire_account_id
                        print(f"🔄 Fallback: Set account_id from GuidewireResponse: {gw_response.guidewire_account_id}")
                    if not work_item.guidewire_job_id and gw_response.guidewire_job_id:
                        work_item.guidewire_job_id = gw_response.guidewire_job_id
                        print(f"🔄 Fallback: Set job_id from GuidewireResponse: {gw_response.guidewire_job_id}")
            
            db.commit()
            
            # Verify the storage
            print(f"\n✅ Final WorkItem state:")
            print(f"   Account ID: {work_item.guidewire_account_id}")
            print(f"   Job ID: {work_item.guidewire_job_id}")
            
            # Also check the GuidewireResponse
            gw_response = db.query(GuidewireResponse).filter(
                GuidewireResponse.work_item_id == work_item.id
            ).first()
            if gw_response:
                print(f"\n📊 GuidewireResponse state:")
                print(f"   Account ID: {gw_response.guidewire_account_id}")
                print(f"   Account Number: {gw_response.account_number}")
                print(f"   Job ID: {gw_response.guidewire_job_id}")
                print(f"   Job Number: {gw_response.job_number}")
                
            print(f"\n🎉 Storage test complete!")
        
    except Exception as e:
        print(f"❌ Error in storage test: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_guidewire_storage()