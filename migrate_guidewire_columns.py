#!/usr/bin/env python3
"""
Manual database migration script to add Guidewire human-readable number columns
"""

from sqlalchemy import create_engine, text
from config import settings

# Create engine
engine = create_engine(settings.database_url)

migration_sql = """
-- Add the new Guidewire human-readable number columns to work_items table
ALTER TABLE work_items 
ADD COLUMN IF NOT EXISTS guidewire_account_number VARCHAR(100),
ADD COLUMN IF NOT EXISTS guidewire_job_number VARCHAR(100);

-- Create index on the new columns for faster lookups
CREATE INDEX IF NOT EXISTS idx_work_items_guidewire_account_number ON work_items(guidewire_account_number);
CREATE INDEX IF NOT EXISTS idx_work_items_guidewire_job_number ON work_items(guidewire_job_number);
"""

print("🔧 Starting manual database migration...")
print("=" * 60)

try:
    with engine.connect() as conn:
        # Execute the migration
        conn.execute(text(migration_sql))
        conn.commit()
        
        print("✅ Migration completed successfully!")
        
        # Verify the new columns exist
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'work_items' 
            AND column_name LIKE '%guidewire%'
            ORDER BY column_name
        """))
        
        cols = list(result)
        print(f"\n📋 Current Guidewire columns ({len(cols)} total):")
        for col_name, data_type in cols:
            print(f"  ✓ {col_name} ({data_type})")
        
        print(f"\n🎯 Migration Summary:")
        print(f"  • Added guidewire_account_number column")
        print(f"  • Added guidewire_job_number column")
        print(f"  • Created indexes for faster lookups")
        print(f"  • Ready to store human-readable numbers!")

except Exception as e:
    print(f"❌ Migration failed: {e}")
    raise