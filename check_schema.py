#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from config import settings

# Check current database schema for Guidewire columns
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Check current Guidewire columns
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'work_items' 
        AND column_name LIKE '%guidewire%'
        ORDER BY column_name
    """))
    
    cols = list(result)
    print("CURRENT GUIDEWIRE COLUMNS IN DATABASE:")
    print("=" * 50)
    for col_name, data_type in cols:
        print(f"  {col_name} ({data_type})")
    
    print(f"\nTotal Guidewire columns found: {len(cols)}")
    
    # Also get the latest work item to see what data we have
    result2 = conn.execute(text("""
        SELECT id, guidewire_account_id, guidewire_job_id, created_at
        FROM work_items 
        ORDER BY created_at DESC 
        LIMIT 1
    """))
    
    latest = result2.fetchone()
    if latest:
        print(f"\nLATEST WORK ITEM:")
        print(f"  ID: {latest[0]}")
        print(f"  Account ID: {latest[1]}")
        print(f"  Job ID: {latest[2]}")
        print(f"  Created: {latest[3]}")
    else:
        print("\nNo work items found")