#!/usr/bin/env python3
"""
Test Guidewire approval for job 0000749253 using production setup
"""

import sys
sys.path.append('.')
from guidewire_integration import guidewire_integration
from database import get_db, WorkItem
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from config import settings

def test_guidewire_approval():
    """Test the Guidewire approval for the problematic job"""
    
    print("🔧 Testing Guidewire approval for job 0000749253")
    print("=" * 60)
    
    try:
        # Get work item from database
        engine = create_engine(settings.database_url)
        db = Session(engine)
        
        work_item = db.query(WorkItem).filter(
            WorkItem.guidewire_job_number == '0000749253'
        ).first()
        
        if not work_item:
            print("❌ Work item not found for job 0000749253")
            return
        
        job_id = work_item.guidewire_job_id
        print(f"📋 Work Item Details:")
        print(f"  ID: {work_item.id}")
        print(f"  Status in our system: {work_item.status}")
        print(f"  Guidewire Job ID: {job_id}")
        print(f"  Guidewire Job Number: {work_item.guidewire_job_number}")
        
        # Test Guidewire connection
        print(f"\n🧪 Testing Guidewire connection...")
        conn_result = guidewire_integration.test_connection()
        
        if not conn_result['success']:
            print(f"❌ Connection failed: {conn_result.get('message')}")
            print("💡 This might be why the approval didn't work initially")
            return
        
        print("✅ Guidewire connection successful")
        
        # Get UW issues using the internal job ID  
        print(f"\n📋 Getting UW issues for job ID: {job_id}")
        uw_result = guidewire_integration.get_uw_issues(job_id)
        
        if uw_result['success']:
            issues_count = uw_result.get('uw_issues_count', 0)
            print(f"✅ Found {issues_count} UW issues")
            
            if issues_count > 0:
                print("\n📋 UW Issues Details:")
                for i, issue in enumerate(uw_result.get('uw_issues', [])):
                    attrs = issue.get('attributes', {})
                    print(f"  Issue {i+1}:")
                    print(f"    ID: {attrs.get('id', 'N/A')}")
                    print(f"    Status: {attrs.get('status', 'N/A')}")
                    print(f"    Description: {attrs.get('description', 'N/A')}")
                
                print("\n🚀 Attempting to approve UW issues...")
                approval_result = guidewire_integration.approve_submission(
                    job_id, 
                    "Re-approved via API - syncing with system status"
                )
                
                if approval_result['success']:
                    print("✅ SUCCESS! UW issues approved in Guidewire")
                    print(f"   Status: {approval_result.get('status')}")
                    print(f"   Message: {approval_result.get('message')}")
                    
                    if approval_result.get('approved_issues'):
                        print(f"   Approved issues: {len(approval_result['approved_issues'])}")
                    
                    print(f"\n🎉 Job 0000749253 should now show as 'Approved' in Guidewire!")
                    
                else:
                    print("❌ Approval failed:")
                    print(f"   Error: {approval_result.get('message')}")
                    
                    if approval_result.get('failed_approvals'):
                        print("   Failed approvals:")
                        for failure in approval_result['failed_approvals']:
                            print(f"     - Issue {failure.get('issue_id')}: {failure.get('error')}")
                    
                    print("\n💡 NEXT STEPS:")
                    print("   1. Log into Guidewire UI directly") 
                    print("   2. Search for job number: 0000749253")
                    print("   3. Manually approve any pending UW issues")
                    
            else:
                print("✅ No pending UW issues found")
                print("   Job should already be approved in Guidewire")
                print("   Check Guidewire UI - there might be a display delay")
                
        else:
            print(f"❌ Failed to get UW issues: {uw_result.get('message')}")
            print(f"   Error: {uw_result.get('error')}")
            print(f"   Status code: {uw_result.get('status_code')}")
            
            if "404" in str(uw_result.get('status_code')):
                print("\n💡 Possible causes:")
                print("   - Job ID format might be incorrect")
                print("   - Job might not exist in current Guidewire environment")
                print("   - Wrong Guidewire environment (dev vs prod)")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_guidewire_approval()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print("• Our system shows job as APPROVED ✅")
    print("• Guidewire sync may have failed during original approval")
    print("• This script attempts to re-sync the approval status")
    print("• If still showing 'UW Review', manual approval in Guidewire needed")