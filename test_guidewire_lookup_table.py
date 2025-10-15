#!/usr/bin/env python3
"""
Test script for the new Guidewire lookup table
Demonstrates quick search functionality for PolicyCenter
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, GuidewireLookup, WorkItem, Submission
from sqlalchemy import desc
from datetime import datetime

def test_guidewire_lookup_table():
    """Test the new Guidewire lookup functionality"""
    
    print("🔍 TESTING GUIDEWIRE LOOKUP TABLE")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Check if lookup table exists and has data
        lookup_count = db.query(GuidewireLookup).count()
        print(f"📊 Guidewire Lookup Records: {lookup_count}")
        
        if lookup_count == 0:
            print("   ℹ️  No lookup records found - they'll be created when Guidewire sync succeeds")
        else:
            # Show existing lookup records
            lookups = db.query(GuidewireLookup).order_by(desc(GuidewireLookup.updated_at)).limit(5).all()
            
            print()
            print("📋 RECENT LOOKUP RECORDS:")
            print("-" * 30)
            
            for lookup in lookups:
                print(f"   Work Item {lookup.work_item_id}:")
                print(f"      Account Number: {lookup.account_number or 'Not created'}")
                print(f"      Job Number: {lookup.job_number or 'Not created'}")
                print(f"      Organization: {lookup.organization_name or 'Unknown'}")
                print(f"      Status: {lookup.sync_status}")
                print(f"      Coverage: ${lookup.coverage_amount:,.0f}" if lookup.coverage_amount else "      Coverage: N/A")
                print(f"      Industry: {lookup.industry or 'Unknown'}")
                print(f"      Updated: {lookup.updated_at}")
                print()
        
        # Show what the API endpoints will provide
        print("🔗 NEW API ENDPOINTS:")
        print("-" * 20)
        print("   GET /api/guidewire-lookups/")
        print("   GET /api/guidewire-lookups/search/{term}")
        print("   GET /api/guidewire-lookups/work-item/{id}")
        print("   GET /api/guidewire-lookups/latest")
        print()
        
        # Simulate what happens when the account is created
        print("✅ EXAMPLE: After Account Creation")
        print("-" * 35)
        print("   Account Number: 2332505940")
        print("   Organization: Test Company Inc 416413")
        print("   Status: partial (account created, submission pending)")
        print()
        
        print("✅ EXAMPLE: After Complete Success")
        print("-" * 35)
        print("   Account Number: 2332505940")
        print("   Job Number: JOB20251015001")
        print("   Organization: Test Company Inc 416413")
        print("   Status: complete")
        print()
        
        print("🎯 GUIDEWIRE POLICYCENTER SEARCH:")
        print("-" * 40)
        print("   1. Search by Account Number: 2332505940")
        print("   2. Search by Job Number: JOB20251015001") 
        print("   3. Search by Organization: Test Company Inc 416413")
        print("   4. API provides instant lookup without database complexity")
        
    except Exception as e:
        print(f"💥 Error testing lookup table: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def demonstrate_lookup_benefits():
    """Show the benefits of the lookup table"""
    
    print()
    print("🎯 BENEFITS OF GUIDEWIRE LOOKUP TABLE")
    print("=" * 45)
    
    print()
    print("✅ QUICK SEARCH:")
    print("   - Instant access to account/job numbers")
    print("   - No need to parse complex GuidewireResponse JSON")
    print("   - Indexed for fast queries")
    print()
    
    print("✅ STATUS TRACKING:")
    print("   - Know which step failed (account vs submission)")
    print("   - Track retry attempts")
    print("   - Monitor sync progress")
    print()
    
    print("✅ BUSINESS CONTEXT:")
    print("   - Coverage amounts for prioritization")
    print("   - Industry for categorization")
    print("   - Contact email for follow-up")
    print()
    
    print("✅ POLICYCENTER INTEGRATION:")
    print("   - Ready-to-search account numbers")
    print("   - Ready-to-search job numbers")
    print("   - Organization names for verification")
    print()
    
    print("🔍 SAMPLE API CALLS:")
    print("-" * 20)
    print("   # Get all lookups with status")
    print("   GET /api/guidewire-lookups/?status=complete")
    print()
    print("   # Search by account number")
    print("   GET /api/guidewire-lookups/search/2332505940")
    print()
    print("   # Get specific work item's Guidewire info")
    print("   GET /api/guidewire-lookups/work-item/77")
    print()
    print("   # Get latest 10 records for dashboard")
    print("   GET /api/guidewire-lookups/latest")

if __name__ == "__main__":
    test_guidewire_lookup_table()
    demonstrate_lookup_benefits()