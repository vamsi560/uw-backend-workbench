#!/usr/bin/env python3
"""
Database Migration: Add body_html column to submissions table
This migration adds a new column to store original HTML email content
"""

import os
import psycopg2
from urllib.parse import urlparse

def run_migration():
    """Add body_html column to submissions table"""
    
    # Database connection details
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://uwworkbench_user:tI7mZcVLSaJx8WLtvtc9aUGfoJnOGwxK@dpg-cs8dlmij1k6c73ebs2fg-a.oregon-postgres.render.com/uwworkbench')
    
    try:
        # Connect to the database
        print("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if column already exists
        print("Checking if body_html column exists...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='submissions' AND column_name='body_html';
        """)
        
        exists = cur.fetchone()
        
        if exists:
            print("✅ body_html column already exists in submissions table")
        else:
            print("Adding body_html column to submissions table...")
            
            # Add the new column
            cur.execute("""
                ALTER TABLE submissions 
                ADD COLUMN body_html TEXT;
            """)
            
            print("✅ Successfully added body_html column to submissions table")
            
            # Add comment for documentation
            cur.execute("""
                COMMENT ON COLUMN submissions.body_html IS 'Original HTML format email body content';
            """)
            
            print("✅ Added column comment for documentation")
        
        # Verify the column structure
        print("\nVerifying submissions table structure:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='submissions' 
            AND column_name IN ('body_text', 'body_html')
            ORDER BY column_name;
        """)
        
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Check current submissions count
        cur.execute("SELECT COUNT(*) FROM submissions;")
        count = cur.fetchone()[0]
        print(f"\nTotal submissions in database: {count}")
        
        if count > 0:
            # Check how many have HTML content in body_text
            cur.execute("""
                SELECT COUNT(*) FROM submissions 
                WHERE body_text LIKE '%<html>%' OR body_text LIKE '%<body>%';
            """)
            html_count = cur.fetchone()[0]
            print(f"Submissions with HTML content in body_text: {html_count}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Deploy the updated application code")
        print("2. New emails will store both HTML and text versions")
        print("3. API endpoints will provide both formats to UI team")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting database migration: Add body_html column")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        exit(1)