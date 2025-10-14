#!/usr/bin/env python3
"""
Database migration script to add Guidewire integration columns to work_items table
"""

import sys
from sqlalchemy import create_engine, text
from config import settings

def migrate_database():
    """Add missing Guidewire columns to work_items table"""
    
    print("Starting database migration...")
    
    try:
        # Connect to database
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("Checking current table structure...")
                
                # Check if columns already exist
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'work_items' 
                      AND column_name IN ('guidewire_account_id', 'guidewire_job_id')
                """))
                
                existing_columns = [row[0] for row in result]
                print(f"Existing Guidewire columns: {existing_columns}")
                
                # Add guidewire_account_id column if it doesn't exist
                if 'guidewire_account_id' not in existing_columns:
                    print("Adding guidewire_account_id column...")
                    conn.execute(text("""
                        ALTER TABLE work_items 
                        ADD COLUMN guidewire_account_id VARCHAR(100)
                    """))
                    print("✅ guidewire_account_id column added successfully")
                else:
                    print("✅ guidewire_account_id column already exists")
                
                # Add guidewire_job_id column if it doesn't exist
                if 'guidewire_job_id' not in existing_columns:
                    print("Adding guidewire_job_id column...")
                    conn.execute(text("""
                        ALTER TABLE work_items 
                        ADD COLUMN guidewire_job_id VARCHAR(100)
                    """))
                    print("✅ guidewire_job_id column added successfully")
                else:
                    print("✅ guidewire_job_id column already exists")
                
                # Commit the transaction
                trans.commit()
                print("✅ Database migration completed successfully!")
                
                # Verify the changes
                print("\nVerifying migration...")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'work_items' 
                      AND column_name IN ('guidewire_account_id', 'guidewire_job_id')
                    ORDER BY column_name
                """))
                
                print("New columns:")
                for row in result:
                    print(f"  - {row[0]} ({row[1]}, nullable: {row[2]})")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def verify_database():
    """Verify the database structure after migration"""
    
    print("\n" + "="*50)
    print("VERIFICATION REPORT")
    print("="*50)
    
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check work_items table structure
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'work_items'
                ORDER BY ordinal_position
            """))
            
            print("\nwork_items table structure:")
            for row in result:
                print(f"  {row[0]:<25} {row[1]:<20} (nullable: {row[2]})")
            
            # Count records
            result = conn.execute(text("SELECT COUNT(*) FROM work_items"))
            work_items_count = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM submissions"))
            submissions_count = result.scalar()
            
            print(f"\nRecord counts:")
            print(f"  Submissions: {submissions_count}")
            print(f"  Work items:  {work_items_count}")
            
            if submissions_count == work_items_count:
                print("✅ Record counts match - no orphaned submissions")
            else:
                print(f"⚠️  Mismatch: {submissions_count - work_items_count} submissions without work items")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")


if __name__ == "__main__":
    print("Database Migration Tool")
    print("This will add Guidewire integration columns to the work_items table")
    print(f"Target database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    
    # Confirm before proceeding
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        proceed = True
    else:
        response = input("\nDo you want to proceed? (y/N): ")
        proceed = response.lower() in ['y', 'yes']
    
    if proceed:
        success = migrate_database()
        verify_database()
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print("The API should now work without column errors.")
            sys.exit(0)
        else:
            print("\n💥 Migration failed!")
            sys.exit(1)
    else:
        print("Migration cancelled.")
        sys.exit(0)