#!/usr/bin/env python3
"""
Check Guidewire job status for troubleshooting approval issues
"""

import sys
sys.path.append('.')
from guidewire_integration import guidewire_integration
import json

def check_job_status(job_identifier):
    """Check the status of a Guidewire job"""
    
    print(f"🔍 Checking Guidewire status for job: {job_identifier}")
    print("=" * 60)
    
    # Step 1: Test connection
    print("🧪 Testing Guidewire connection...")
    try:
        conn_result = guidewire_integration.test_connection()
        if conn_result['success']:
            print("✅ Guidewire connection successful")
        else:
            print(f"❌ Connection failed: {conn_result.get('message')}")
            return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Step 2: Get UW issues
    print(f"\n📋 Getting UW issues for job: {job_identifier}")
    try:
        uw_result = guidewire_integration.get_uw_issues(job_identifier)
        
        print(f"Response status: {uw_result.get('success')}")
        
        if uw_result['success']:
            issues_count = uw_result.get('uw_issues_count', 0)
            print(f"✅ Found {issues_count} UW issues")
            
            if uw_result.get('uw_issues') and issues_count > 0:
                print("\n📋 UW Issues Details:")
                for i, issue in enumerate(uw_result['uw_issues']):
                    attrs = issue.get('attributes', {})
                    print(f"  Issue {i+1}:")
                    print(f"    ID: {attrs.get('id', 'N/A')}")
                    print(f"    Status: {attrs.get('status', 'N/A')}")
                    
                    # Check issue type
                    issue_type = attrs.get('issueType', {})
                    if isinstance(issue_type, dict):
                        print(f"    Type: {issue_type.get('name', 'N/A')} ({issue_type.get('code', 'N/A')})")
                    else:
                        print(f"    Type: {issue_type}")
                    
                    print(f"    Description: {attrs.get('description', 'N/A')}")
                    
                    # Check if issue is approved
                    approval_status = attrs.get('approvalStatus')
                    if approval_status:
                        print(f"    Approval Status: {approval_status}")
                    
                    print()
                
                print("🚨 DIAGNOSIS: Job has UW issues that need approval")
                print("   This is why it's still showing 'UW review' status")
                
                # Try to approve the issues
                print("\n🔧 Attempting to approve UW issues...")
                approval_result = guidewire_integration.approve_submission(job_identifier, "Approved via API")
                
                if approval_result['success']:
                    print(f"✅ Approval successful: {approval_result.get('message')}")
                    print(f"   Status: {approval_result.get('status')}")
                    
                    if approval_result.get('approved_issues'):
                        print(f"   Approved issues: {approval_result['approved_issues']}")
                else:
                    print(f"❌ Approval failed: {approval_result.get('message')}")
                    if approval_result.get('failed_approvals'):
                        print("   Failed approvals:")
                        for failure in approval_result['failed_approvals']:
                            print(f"     - {failure}")
                
            else:
                print("✅ No pending UW issues found")
                print("   Job should be approved - check Guidewire directly")
                
        else:
            print(f"❌ Failed to get UW issues: {uw_result.get('message')}")
            print(f"   Error code: {uw_result.get('error')}")
            print(f"   Status code: {uw_result.get('status_code')}")
            
            # If job number format is wrong, suggest alternatives
            if "404" in str(uw_result.get('status_code')) or "not found" in str(uw_result.get('message', '')).lower():
                print("\n💡 Possible issues:")
                print("   1. Job number format might be wrong")
                print("   2. Job might need internal ID format (pc:xxxxx)")
                print("   3. Job might not exist in Guidewire")
                print("   4. Job might be in different environment")
                
    except Exception as e:
        print(f"❌ Error getting UW issues: {e}")
    
    # Step 3: Try to get documents (to check if job exists)
    print(f"\n📄 Checking if documents exist for job: {job_identifier}")
    try:
        docs_result = guidewire_integration.get_quote_documents(job_identifier)
        
        if docs_result['success']:
            docs_count = docs_result.get('documents_count', 0)
            print(f"✅ Found {docs_count} documents")
            
            if docs_count > 0:
                print("   Job exists and has quote documents")
            else:
                print("   Job exists but no quote documents yet")
        else:
            print(f"❌ No documents found: {docs_result.get('message')}")
            
    except Exception as e:
        print(f"❌ Error getting documents: {e}")

if __name__ == "__main__":
    # Check the specific job
    job_number = "0000749253"
    check_job_status(job_number)
    
    print("\n" + "=" * 60)
    print("💡 TROUBLESHOOTING GUIDE:")
    print("1. If UW issues found: Job needs manual approval in Guidewire")
    print("2. If no UW issues: Job should be approved already")  
    print("3. If 404 error: Check job number format or existence")
    print("4. Check Guidewire UI directly for current status")