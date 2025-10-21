#!/usr/bin/env python3
"""
Database Migration: Add underwriting_notes column to work_items table
Run this script to add the underwriting_notes column to existing databases
"""

from sqlalchemy import text, inspect
from database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_add_underwriting_notes():
    """Add underwriting_notes column to work_items table if it doesn't exist"""
    
    try:
        with engine.connect() as connection:
            # Check if column already exists
            inspector = inspect(engine)
            columns = inspector.get_columns('work_items')
            column_names = [col['name'] for col in columns]
            
            if 'underwriting_notes' in column_names:
                logger.info("✅ underwriting_notes column already exists")
                return True
            
            # Add the column
            logger.info("📝 Adding underwriting_notes column to work_items table...")
            
            alter_sql = """
            ALTER TABLE work_items 
            ADD COLUMN underwriting_notes TEXT NULL;
            """
            
            connection.execute(text(alter_sql))
            connection.commit()
            
            logger.info("✅ Successfully added underwriting_notes column")
            
            # Verify the column was added
            inspector = inspect(engine)
            columns = inspector.get_columns('work_items')
            column_names = [col['name'] for col in columns]
            
            if 'underwriting_notes' in column_names:
                logger.info("✅ Migration verified: underwriting_notes column exists")
                return True
            else:
                logger.error("❌ Migration failed: column was not added")
                return False
                
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        return False

def check_database_schema():
    """Check current work_items table schema"""
    
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns('work_items')
        
        logger.info("📋 Current work_items table schema:")
        for col in columns:
            logger.info(f"   - {col['name']}: {col['type']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema check failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 UNDERWRITING NOTES MIGRATION")
    logger.info("=" * 50)
    
    # Check current schema
    logger.info("\n1️⃣ Checking current database schema...")
    check_database_schema()
    
    # Run migration
    logger.info("\n2️⃣ Running migration...")
    success = migrate_add_underwriting_notes()
    
    if success:
        logger.info("\n3️⃣ Verifying final schema...")
        check_database_schema()
        
        logger.info("\n" + "=" * 50)
        logger.info("🎉 MIGRATION COMPLETE!")
        logger.info("\nThe underwriting_notes column has been added.")
        logger.info("The application can now store and retrieve underwriter notes.")
    else:
        logger.error("\n" + "=" * 50)
        logger.error("❌ MIGRATION FAILED!")
        logger.error("Please check the database connection and permissions.")