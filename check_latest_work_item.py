#!/usr/bin/env python3

from database import SessionLocal, WorkItem

def check_latest_work_item():
    print("🔍 Checking Latest Work Item from Your New Email")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get the most recent work item
        latest = db.query(WorkItem).order_by(WorkItem.created_at.desc()).first()
        
        if not latest:
            print("❌ No work items found")
            return
            
        print(f"📋 Latest Work Item Details:")
        print(f"  • ID: {latest.id}")
        print(f"  • Title: {latest.title}")
        print(f"  • Created: {latest.created_at}")
        print()
        
        print(f"🔗 INTERNAL IDs (for API calls):")
        print(f"  • Account ID: {latest.guidewire_account_id or 'Not set'}")
        print(f"  • Job ID: {latest.guidewire_job_id or 'Not set'}")
        print()
        
        print(f"🎯 HUMAN-READABLE NUMBERS (for Guidewire search):")
        account_num = latest.guidewire_account_number
        job_num = latest.guidewire_job_number
        
        print(f"  • Account Number: {account_num or '❌ Not set'}")
        print(f"  • Job Number: {job_num or '❌ Not set'}")
        print()
        
        if account_num and job_num:
            print("🎉 SUCCESS! Full End-to-End Flow Working!")
            print("=" * 50)
            print(f"✅ Account Number: {account_num}")
            print(f"✅ Job Number: {job_num}")
            print()
            print("🔍 You can now search in Guidewire PolicyCenter using these numbers:")
            print(f"  → Search by Account: {account_num}")
            print(f"  → Search by Job: {job_num}")
            
        elif latest.guidewire_account_id and latest.guidewire_job_id:
            print("⏳ Partial Success - Guidewire sync happened but numbers not extracted")
            print("   This might be from before our fix was deployed.")
            print(f"   Internal IDs are: {latest.guidewire_account_id}, {latest.guidewire_job_id}")
            
        else:
            print("⚠️ No Guidewire sync detected yet")
            print("   The work item was created but may not have synced to Guidewire yet.")
            
    except Exception as e:
        print(f"❌ Error checking work item: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_latest_work_item()