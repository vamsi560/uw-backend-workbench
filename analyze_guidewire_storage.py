#!/usr/bin/env python3

import logging
from database import SessionLocal, WorkItem, GuidewireResponse
from sqlalchemy import desc, and_

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_guidewire_ids_to_workitems():
    """
    Ensure all WorkItems have their Guidewire IDs populated from GuidewireResponse records
    This function fixes the data synchronization between the two tables.
    """
    
    print("🔄 Syncing Guidewire IDs to WorkItems...")
    
    db = SessionLocal()
    
    try:
        # Find all WorkItems that don't have Guidewire IDs but should
        workitems_missing_ids = db.query(WorkItem).filter(
            and_(
                WorkItem.guidewire_account_id.is_(None),
                WorkItem.guidewire_job_id.is_(None)
            )
        ).all()
        
        print(f"📊 Found {len(workitems_missing_ids)} WorkItems missing Guidewire IDs")
        
        updated_count = 0
        for work_item in workitems_missing_ids:
            # Find corresponding GuidewireResponse
            gw_response = db.query(GuidewireResponse).filter(
                GuidewireResponse.work_item_id == work_item.id
            ).first()
            
            if gw_response and gw_response.guidewire_account_id:
                print(f"\n🔄 Updating WorkItem {work_item.id}:")
                print(f"   Account ID: {gw_response.guidewire_account_id}")
                print(f"   Account Number: {gw_response.account_number}")
                print(f"   Job ID: {gw_response.guidewire_job_id}")  
                print(f"   Job Number: {gw_response.job_number}")
                
                work_item.guidewire_account_id = gw_response.guidewire_account_id
                work_item.guidewire_job_id = gw_response.guidewire_job_id
                
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f"\n✅ Updated {updated_count} WorkItems with Guidewire IDs")
        else:
            print(f"\n✓ No WorkItems needed Guidewire ID updates")
            
    except Exception as e:
        logger.error(f"Error syncing Guidewire IDs: {str(e)}")
        db.rollback()
    finally:
        db.close()
    
    return updated_count

def show_guidewire_data_summary():
    """Show a comprehensive summary of Guidewire data storage"""
    
    print("\n" + "="*60)
    print("📊 GUIDEWIRE DATA STORAGE SUMMARY")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Count total records
        total_workitems = db.query(WorkItem).count()
        total_guidewire_responses = db.query(GuidewireResponse).count()
        
        print(f"\n📋 Total Records:")
        print(f"   WorkItems: {total_workitems}")
        print(f"   GuidewireResponses: {total_guidewire_responses}")
        
        # Count WorkItems with Guidewire IDs
        workitems_with_guidewire = db.query(WorkItem).filter(
            WorkItem.guidewire_account_id.isnot(None)
        ).count()
        
        print(f"\n🎯 WorkItems with Guidewire Integration:")
        print(f"   With Guidewire IDs: {workitems_with_guidewire}")
        print(f"   Without Guidewire IDs: {total_workitems - workitems_with_guidewire}")
        
        # Show recent WorkItems
        print(f"\n📋 Recent WorkItems (Last 5):")
        recent_workitems = db.query(WorkItem).order_by(desc(WorkItem.created_at)).limit(5).all()
        
        for wi in recent_workitems:
            gw_response = db.query(GuidewireResponse).filter(
                GuidewireResponse.work_item_id == wi.id
            ).first()
            
            status = "❌ No Guidewire Data"
            if wi.guidewire_account_id:
                status = f"✅ Account: {wi.guidewire_account_id[:20]}..."
            elif gw_response:
                status = f"⚠️ Data in GuidewireResponse only: {gw_response.guidewire_account_id[:20] if gw_response.guidewire_account_id else 'None'}..."
            
            print(f"   WorkItem {wi.id}: {status}")
        
        # Show where data is stored
        print(f"\n💾 Data Storage Locations:")
        print(f"   1. WorkItem table:")
        print(f"      - guidewire_account_id (Guidewire internal ID)")
        print(f"      - guidewire_job_id (Guidewire internal job ID)")
        print(f"   2. GuidewireResponse table:")
        print(f"      - guidewire_account_id (Guidewire internal ID)")
        print(f"      - account_number (Human-readable account number)")
        print(f"      - guidewire_job_id (Guidewire internal job ID)")
        print(f"      - job_number (Human-readable job number)")
        print(f"      - Plus comprehensive policy, pricing, and business data")
        
        # Show recent GuidewireResponses
        print(f"\n📊 Recent Guidewire Integrations:")
        recent_gw = db.query(GuidewireResponse).order_by(desc(GuidewireResponse.created_at)).limit(3).all()
        
        for gw in recent_gw:
            print(f"   GuidewireResponse {gw.id} (WorkItem {gw.work_item_id}):")
            print(f"      Account: {gw.account_number} (ID: {gw.guidewire_account_id})")
            print(f"      Job: {gw.job_number} (ID: {gw.guidewire_job_id})")
            print(f"      Success: {gw.submission_success}")
            print(f"      Created: {gw.created_at}")
            
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
    finally:
        db.close()
    
    print(f"\n" + "="*60)

if __name__ == "__main__":
    # Sync the data
    updated = sync_guidewire_ids_to_workitems()
    
    # Show comprehensive summary
    show_guidewire_data_summary()
    
    print(f"\n💡 To access Guidewire data in your application:")
    print(f"   - For quick lookups: Use WorkItem.guidewire_account_id and WorkItem.guidewire_job_id")
    print(f"   - For detailed data: Query GuidewireResponse table by work_item_id")
    print(f"   - Account Numbers: Use GuidewireResponse.account_number (e.g., 'ACCT20251014180749')")
    print(f"   - Job Numbers: Use GuidewireResponse.job_number (e.g., 'JOB20251014180749')")
    
    print(f"\n✨ Guidewire data analysis complete!")