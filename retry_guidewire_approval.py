#!/usr/bin/env python3
"""
Re-sync Guidewire approval for job that's approved in our system but not in Guidewire
"""

import sys
sys.path.append('.')
from guidewire_integration import guidewire_integration
from database import get_db, WorkItem
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from config import settings
import time

def retry_guidewire_approval(job_number):
    """Retry Guidewire approval for a job that's approved locally but not in Guidewire"""
    
    print(f"🔄 Retrying Guidewire approval for job: {job_number}")
    print("=" * 60)
    
    # Get work item from database
    try:
        engine = create_engine(settings.database_url)
        db = Session(engine)
        
        work_item = db.query(WorkItem).filter(
            WorkItem.guidewire_job_number == job_number
        ).first()
        
        if not work_item:
            print(f"❌ Work item not found for job number: {job_number}")
            return
        
        print(f"📋 Work Item Details:")
        print(f"  ID: {work_item.id}")
        print(f"  Status in our system: {work_item.status}")
        print(f"  Guidewire Job ID: {work_item.guidewire_job_id}")
        print(f"  Guidewire Job Number: {work_item.guidewire_job_number}")
        print(f"  Last updated: {work_item.updated_at}")
        
        # Use the internal Guidewire job ID for API calls
        guidewire_job_id = work_item.guidewire_job_id
        
        if not guidewire_job_id:
            print("❌ No Guidewire job ID found - cannot retry approval")
            return
            
        print(f"\n🔧 Attempting to re-approve in Guidewire using job ID: {guidewire_job_id}")
        
        # Try multiple connection attempts
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            print(f"\n📡 Attempt {attempt}/{max_retries}: Testing Guidewire connection...")
            
            try:
                conn_result = guidewire_integration.test_connection()
                
                if conn_result['success']:
                    print("✅ Connection successful!")
                    break
                else:
                    print(f"❌ Connection failed: {conn_result.get('message')}")
                    if attempt < max_retries:
                        print(f"   Retrying in 5 seconds...")
                        time.sleep(5)
                    continue
                    
            except Exception as e:
                print(f"❌ Connection error: {e}")
                if attempt < max_retries:
                    print(f"   Retrying in 5 seconds...")
                    time.sleep(5)
                continue
        else:
            print("❌ Failed to connect to Guidewire after all attempts")
            print("\n💡 MANUAL SOLUTION:")
            print(f"   1. Open Guidewire UI directly")
            print(f"   2. Search for job number: {job_number}")
            print(f"   3. Search for job ID: {guidewire_job_id}")
            print(f"   4. Manually approve any pending UW issues")
            print(f"   5. Check that job moves from 'UW Review' to 'Approved' status")
            return
        
        # If connection successful, try to get UW issues
        print(f"\n📋 Getting UW issues for job ID: {guidewire_job_id}")
        
        try:
            uw_result = guidewire_integration.get_uw_issues(guidewire_job_id)
            
            if uw_result['success']:
                issues_count = uw_result.get('uw_issues_count', 0)
                print(f"✅ Found {issues_count} UW issues")
                
                if issues_count > 0:
                    print("\n📋 UW Issues found - this explains why job is still in 'UW Review'")
                    
                    # Show issue details
                    for i, issue in enumerate(uw_result.get('uw_issues', [])):
                        attrs = issue.get('attributes', {})
                        print(f"  Issue {i+1}: {attrs.get('id')} - {attrs.get('description', 'No description')}")
                    
                    # Try to approve them
                    print(f"\n🚀 Attempting to approve {issues_count} UW issues...")
                    
                    approval_result = guidewire_integration.approve_submission(
                        guidewire_job_id, 
                        "Re-approved via API - syncing with system approval"
                    )
                    
                    if approval_result['success']:
                        print("✅ SUCCESS! UW issues approved in Guidewire")
                        print(f"   Status: {approval_result.get('status')}")
                        print(f"   Message: {approval_result.get('message')}")
                        
                        if approval_result.get('approved_issues'):
                            print(f"   Approved issues: {approval_result['approved_issues']}")
                        
                        print(f"\n🎉 Job {job_number} should now show as 'Approved' in Guidewire!")
                        
                    else:
                        print("❌ Failed to approve UW issues:")
                        print(f"   Error: {approval_result.get('message')}")
                        if approval_result.get('failed_approvals'):
                            for failure in approval_result['failed_approvals']:
                                print(f"   - {failure}")
                        
                        print(f"\n💡 MANUAL ACTION REQUIRED:")
                        print(f"   Log into Guidewire and manually approve job {job_number}")
                        
                else:
                    print("✅ No pending UW issues found")
                    print("   Job should already be approved in Guidewire")
                    print("   Check Guidewire UI - there might be a display delay")
                    
            else:
                print(f"❌ Failed to get UW issues: {uw_result.get('message')}")
                print(f"   This could mean the job ID format is incorrect")
                
        except Exception as e:
            print(f"❌ Error processing UW issues: {e}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    job_number = "0000749253"
    retry_guidewire_approval(job_number)
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print("• Job is approved in our system ✅")
    print("• Guidewire sync may have failed during original approval")  
    print("• Manual verification in Guidewire UI recommended")
    print("• If still showing 'UW Review', approve manually in Guidewire")