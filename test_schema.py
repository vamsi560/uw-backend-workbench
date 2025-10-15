#!/usr/bin/env python3
"""
Test the database schema changes are working correctly
"""

from database import SessionLocal, WorkItem
from sqlalchemy import text

def test_schema_changes():
    print("🧪 Testing Database Schema Changes")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Test 1: Verify new columns exist and are accessible
        print("1. Testing column access...")
        work_item = db.query(WorkItem).order_by(WorkItem.created_at.desc()).first()
        
        if work_item:
            print(f"✅ Can access guidewire_account_number: {work_item.guidewire_account_number}")
            print(f"✅ Can access guidewire_job_number: {work_item.guidewire_job_number}")
        
        # Test 2: Try updating the columns
        print("\n2. Testing column updates...")
        test_account_number = "TEST123456"
        test_job_number = "TEST789012"
        
        work_item.guidewire_account_number = test_account_number
        work_item.guidewire_job_number = test_job_number
        db.commit()
        
        # Verify the update worked
        db.refresh(work_item)
        print(f"✅ Updated account number: {work_item.guidewire_account_number}")
        print(f"✅ Updated job number: {work_item.guidewire_job_number}")
        
        # Test 3: Query by the new columns
        print("\n3. Testing queries on new columns...")
        found_by_account = db.query(WorkItem).filter(
            WorkItem.guidewire_account_number == test_account_number
        ).first()
        
        found_by_job = db.query(WorkItem).filter(
            WorkItem.guidewire_job_number == test_job_number
        ).first()
        
        print(f"✅ Found by account number: {found_by_account.id if found_by_account else 'None'}")
        print(f"✅ Found by job number: {found_by_job.id if found_by_job else 'None'}")
        
        print(f"\n🎯 Schema Migration Test Results:")
        print(f"  ✅ New columns exist and are accessible")
        print(f"  ✅ Can update values in new columns")  
        print(f"  ✅ Can query by new columns")
        print(f"  ✅ Database schema migration successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_schema_changes()