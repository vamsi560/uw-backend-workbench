#!/usr/bin/env python3
"""
Migration script to add level and department columns to underwriters table
"""

import sys
sys.path.append('.')
from sqlalchemy import create_engine, text
from config import settings

def migrate_underwriters_table():
    """Add level and department columns to existing underwriters table"""
    
    print("🔄 Migrating underwriters table to add level and department columns")
    print("=" * 70)
    
    try:
        # Create database connection
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if columns already exist
                check_level_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'underwriters' 
                AND column_name = 'level'
                """
                
                level_exists = conn.execute(text(check_level_sql)).fetchone()
                
                if level_exists:
                    print("✅ Level column already exists, skipping migration")
                    trans.rollback()
                    return True
                
                print("📋 Adding level column...")
                
                # Add level column as VARCHAR first, then convert to enum
                conn.execute(text("""
                    ALTER TABLE underwriters 
                    ADD COLUMN level VARCHAR(20) DEFAULT 'JUNIOR'
                """))
                
                print("📋 Adding department column...")
                
                # Add department column
                conn.execute(text("""
                    ALTER TABLE underwriters 
                    ADD COLUMN department VARCHAR(100) DEFAULT 'Cyber Insurance'
                """))
                
                print("📋 Creating UnderwriterLevel enum type...")
                
                # Create enum type
                conn.execute(text("""
                    CREATE TYPE underwriterlevel AS ENUM ('JUNIOR', 'SENIOR', 'PRINCIPAL', 'MANAGER')
                """))
                
                print("📋 Dropping default constraint and converting column to enum type...")
                
                # Remove default constraint first
                conn.execute(text("""
                    ALTER TABLE underwriters 
                    ALTER COLUMN level DROP DEFAULT
                """))
                
                # Convert column to enum type
                conn.execute(text("""
                    ALTER TABLE underwriters 
                    ALTER COLUMN level TYPE underwriterlevel 
                    USING level::underwriterlevel
                """))
                
                # Add default back
                conn.execute(text("""
                    ALTER TABLE underwriters 
                    ALTER COLUMN level SET DEFAULT 'JUNIOR'
                """))
                
                print("📋 Setting default values for existing records...")
                
                # Update existing records with appropriate levels
                conn.execute(text("""
                    UPDATE underwriters 
                    SET level = 'SENIOR', department = 'Cyber Insurance'
                    WHERE level IS NULL OR level = 'JUNIOR'
                """))
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
                # Verify the changes
                print("\n📊 Verifying migration...")
                
                result = conn.execute(text("""
                    SELECT COUNT(*) as total, level, department
                    FROM underwriters 
                    GROUP BY level, department
                """))
                
                rows = result.fetchall()
                for row in rows:
                    print(f"  {row.level}: {row.total} underwriters in {row.department}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    success = migrate_underwriters_table()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Run setup_underwriters.py to populate default data")
        print("2. Test the new underwriter assignment APIs")
    else:
        print("\n❌ Migration failed!")
        exit(1)