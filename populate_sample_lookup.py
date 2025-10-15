"""
Insert sample Guidewire lookup record based on successful account creation
"""
from database import SessionLocal, GuidewireLookup
from datetime import datetime

def add_sample_lookup():
    """Add the actual account data we created for work item #77"""
    db = SessionLocal()
    
    try:
        # Check if record already exists
        existing = db.query(GuidewireLookup).filter(GuidewireLookup.work_item_id == 77).first()
        if existing:
            print("📋 Sample record already exists!")
            print(f"   Account: {existing.account_number}")
            print(f"   Organization: {existing.organization_name}")
            print(f"   Status: {existing.sync_status}")
            return existing
        
        # Create the lookup record based on our actual success
        sample_lookup = GuidewireLookup(
            work_item_id=77,
            submission_id=59,  # Actual submission ID for work item 77
            account_number="2332505940",  # Actual account created in Guidewire
            organization_name="Test Company Inc 416413",  # Actual organization
            guidewire_account_id="pc:2332505940",  # Guidewire internal ID format
            account_created=True,
            submission_created=False,  # Still pending due to network
            sync_status="partial",  # Account created, submission pending
            coverage_amount="1000000",  # From the original submission data
            industry="Technology",  # Inferred from company name
            contact_email="info@testcompany.com",  # Sample email
            last_error="Network timeout during submission creation",
            retry_count=1,
            account_created_at=datetime.now()
        )
        
        db.add(sample_lookup)
        db.commit()
        db.refresh(sample_lookup)
        
        print("✅ Sample Guidewire lookup record created!")
        print(f"   Work Item: {sample_lookup.work_item_id}")
        print(f"   Account: {sample_lookup.account_number}")
        print(f"   Organization: {sample_lookup.organization_name}")
        print(f"   Status: {sample_lookup.sync_status}")
        print(f"   Account Created: {sample_lookup.account_created}")
        print(f"   Submission Created: {sample_lookup.submission_created}")
        
        return sample_lookup
        
    except Exception as e:
        print(f"❌ Error creating sample record: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Adding sample Guidewire lookup record...")
    add_sample_lookup()