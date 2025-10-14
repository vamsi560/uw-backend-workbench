#!/usr/bin/env python3

import logging
from database import SessionLocal, WorkItem, GuidewireResponse
from sqlalchemy import desc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🔧 Fixing WorkItem Guidewire ID storage...")

db = SessionLocal()

# Find all GuidewireResponses that have data but corresponding WorkItems don't
gw_responses = db.query(GuidewireResponse).filter(
    GuidewireResponse.guidewire_account_id.isnot(None)
).all()

print(f"📊 Found {len(gw_responses)} GuidewireResponses with account data")

fixed_count = 0
for gw_response in gw_responses:
    # Get the corresponding WorkItem
    work_item = db.query(WorkItem).filter(WorkItem.id == gw_response.work_item_id).first()
    
    if work_item and not work_item.guidewire_account_id:
        print(f"\n🔄 Fixing WorkItem {work_item.id}:")
        print(f"   Setting account_id: {gw_response.guidewire_account_id}")
        print(f"   Setting job_id: {gw_response.guidewire_job_id}")
        
        work_item.guidewire_account_id = gw_response.guidewire_account_id
        work_item.guidewire_job_id = gw_response.guidewire_job_id
        
        db.commit()
        fixed_count += 1
        
        print(f"   ✅ Fixed!")
    elif work_item and work_item.guidewire_account_id:
        print(f"\n✓ WorkItem {work_item.id} already has Guidewire IDs")
    else:
        print(f"\n❌ WorkItem {gw_response.work_item_id} not found")

print(f"\n🎉 Fixed {fixed_count} WorkItems!")

# Show current state
print(f"\n📋 Current WorkItem Guidewire Status:")
work_items = db.query(WorkItem).order_by(desc(WorkItem.created_at)).limit(5).all()
for wi in work_items:
    print(f"   WorkItem {wi.id}: account_id={wi.guidewire_account_id}, job_id={wi.guidewire_job_id}")

db.close()
print("✨ Fix complete!")