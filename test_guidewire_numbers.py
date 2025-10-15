#!/usr/bin/env python3
"""
Test script to extract human-readable numbers from existing Guidewire work items
"""

import json
from database import SessionLocal, WorkItem
from guidewire_integration import guidewire_integration

def test_guidewire_number_extraction():
    """Test our ability to extract human-readable numbers from Guidewire"""
    
    print("🔍 Testing Guidewire Human-Readable Number Extraction")
    print("=" * 60)
    
    # Get the latest work item with Guidewire IDs
    db = SessionLocal()
    try:
        work_item = db.query(WorkItem).filter(
            WorkItem.guidewire_account_id.isnot(None),
            WorkItem.guidewire_job_id.isnot(None)
        ).order_by(WorkItem.created_at.desc()).first()
        
        if not work_item:
            print("❌ No work items found with Guidewire IDs")
            return
            
        print(f"📋 Found Work Item:")
        print(f"  • ID: {work_item.id}")
        print(f"  • Title: {work_item.title}")
        print(f"  • Created: {work_item.created_at}")
        print(f"  • Account ID: {work_item.guidewire_account_id}")
        print(f"  • Job ID: {work_item.guidewire_job_id}")
        
        print(f"\n🔍 Current Human-Readable Numbers:")
        print(f"  • Account Number: {work_item.guidewire_account_number or 'NOT SET'}")
        print(f"  • Job Number: {work_item.guidewire_job_number or 'NOT SET'}")
        
        # Test 1: Test connection to Guidewire
        print(f"\n🌐 Testing Guidewire Connection...")
        connection_result = guidewire_integration.test_connection()
        print(f"  Connection: {'✅ Success' if connection_result.get('success') else '❌ Failed'}")
        if not connection_result.get('success'):
            print(f"  Error: {connection_result.get('error', 'Unknown error')}")
            return
            
        # Test 2: Try to create a new test submission to see if we can extract numbers
        print(f"\n🧪 Creating Test Submission to Extract Numbers...")
        test_data = {
            "company_name": f"Number Test Company",
            "business_address": "123 Test Street", 
            "business_city": "San Francisco",
            "business_state": "CA",
            "business_zip": "94105"
        }
        
        result = guidewire_integration.create_account_and_submission(test_data)
        
        if result.get("success"):
            print(f"✅ Test submission successful!")
            print(f"  • Internal Account ID: {result.get('account_id')}")
            print(f"  • Internal Job ID: {result.get('job_id')}")
            print(f"  • Human Account Number: {result.get('account_number', 'NOT EXTRACTED')}")
            print(f"  • Human Job Number: {result.get('job_number', 'NOT EXTRACTED')}")
            
            # Check if we got human-readable numbers
            if result.get('account_number') and result.get('job_number'):
                print(f"\n🎯 SUCCESS: Human-readable numbers extracted!")
                print(f"  ✅ Account Number: {result.get('account_number')}")
                print(f"  ✅ Job Number: {result.get('job_number')}")
                
                # Update the existing work item with these numbers as a test
                print(f"\n📝 Updating existing work item with test numbers...")
                work_item.guidewire_account_number = result.get('account_number')
                work_item.guidewire_job_number = result.get('job_number')
                db.commit()
                print(f"  ✅ Work item {work_item.id} updated with human-readable numbers!")
                
            else:
                print(f"\n⚠️  Human-readable numbers not extracted from response")
                print(f"  Response structure: {json.dumps(result, indent=2)}")
                
        else:
            print(f"❌ Test submission failed:")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            print(f"  Message: {result.get('message', 'No message')}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_guidewire_number_extraction()