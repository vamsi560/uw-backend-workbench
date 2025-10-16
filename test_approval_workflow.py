#!/usr/bin/env python3
"""
Test Guidewire Approval Workflow
Tests the complete approval process using UW issues API from Postman collection
"""

import json
import requests
from datetime import datetime
from guidewire_integration import guidewire_integration

def test_guidewire_connection():
    """Test basic Guidewire connection"""
    print("🔗 Testing Guidewire connection...")
    result = guidewire_integration.test_connection()
    
    if result["success"]:
        print(f"✅ Connection successful: {result['message']}")
        return True
    else:
        print(f"❌ Connection failed: {result['message']}")
        return False

def test_uw_issues(job_id):
    """Test getting UW issues for a job"""
    print(f"\n📋 Getting UW issues for job: {job_id}")
    result = guidewire_integration.get_uw_issues(job_id)
    
    if result["success"]:
        uw_issues = result["uw_issues"]
        print(f"✅ Found {len(uw_issues)} UW issues")
        
        for i, issue in enumerate(uw_issues):
            print(f"   Issue {i+1}:")
            attrs = issue.get("attributes", {})
            print(f"     ID: {attrs.get('id', 'Unknown')}")
            print(f"     Type: {attrs.get('issueType', {}).get('name', 'Unknown')}")
            print(f"     Status: {attrs.get('status', 'Unknown')}")
            print(f"     Description: {attrs.get('description', 'No description')}")
            
        return result
    else:
        print(f"❌ Failed to get UW issues: {result['message']}")
        return result

def test_approval_workflow(job_id):
    """Test the complete approval workflow"""
    print(f"\n🎯 Testing approval workflow for job: {job_id}")
    
    # First get UW issues to see what needs approval
    uw_result = test_uw_issues(job_id)
    
    if not uw_result["success"]:
        print("❌ Cannot proceed with approval - failed to get UW issues")
        return uw_result
    
    uw_issues = uw_result["uw_issues"]
    if not uw_issues:
        print("ℹ️  No UW issues found - job may already be approved")
        return {"success": True, "message": "No UW issues to approve"}
    
    print(f"\n🔄 Attempting to approve {len(uw_issues)} UW issues...")
    
    # Approve the submission
    approval_result = guidewire_integration.approve_submission(
        job_id=job_id,
        underwriter_notes="Approved via automated testing - meets all underwriting criteria"
    )
    
    if approval_result["success"]:
        status = approval_result.get("status", "approved")
        approved_count = len(approval_result.get("approved_issues", []))
        total_count = approval_result.get("uw_issues_count", 0)
        
        print(f"✅ Approval successful: {status}")
        print(f"   Approved issues: {approved_count}/{total_count}")
        print(f"   Message: {approval_result['message']}")
        
        if "approved_issues" in approval_result:
            print("   Approved issue IDs:", approval_result["approved_issues"])
            
    else:
        print(f"❌ Approval failed: {approval_result['message']}")
        if "failed_approvals" in approval_result:
            print("   Failed approvals:", approval_result["failed_approvals"])
    
    return approval_result

def test_job_status(job_id):
    """Test getting job status to verify approval"""
    print(f"\n📊 Checking job status: {job_id}")
    
    try:
        import requests
        
        job_url = f"https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net/rest/job/v1/jobs/{job_id}"
        
        response = requests.get(
            job_url,
            auth=("su", "gw"),
            headers={'Accept': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            job_data = response.json()
            attrs = job_data.get("data", {}).get("attributes", {})
            
            print(f"✅ Job status retrieved:")
            print(f"   Job Number: {attrs.get('jobNumber', 'Unknown')}")
            print(f"   Status: {attrs.get('status', 'Unknown')}")
            print(f"   State: {attrs.get('state', {}).get('name', 'Unknown')}")
            print(f"   Effective Date: {attrs.get('effectiveDate', 'Unknown')}")
            
            return {
                "success": True,
                "job_status": attrs.get("status"),
                "job_state": attrs.get("state", {}).get("name"),
                "job_number": attrs.get("jobNumber")
            }
        else:
            print(f"❌ Failed to get job status: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "message": response.text
            }
            
    except Exception as e:
        print(f"❌ Error getting job status: {str(e)}")
        return {
            "success": False,
            "error": "Exception", 
            "message": str(e)
        }

def main():
    """Run complete approval workflow test"""
    print("🚀 Guidewire Approval Workflow Test")
    print("=" * 50)
    
    # Test with the real job ID we have
    test_job_id = "pc:S9Z7G9A7dGlQCKdKlc-G6"  # Job 0001563719 from our previous tests
    
    # Step 1: Test connection
    if not test_guidewire_connection():
        print("\n❌ Cannot proceed - connection failed")
        return
    
    # Step 2: Check job status before approval
    print(f"\n📍 BEFORE APPROVAL:")
    status_before = test_job_status(test_job_id)
    
    # Step 3: Test approval workflow
    approval_result = test_approval_workflow(test_job_id)
    
    # Step 4: Check job status after approval
    print(f"\n📍 AFTER APPROVAL:")
    status_after = test_job_status(test_job_id)
    
    # Summary
    print(f"\n📋 APPROVAL TEST SUMMARY")
    print("=" * 30)
    print(f"Job ID: {test_job_id}")
    
    if status_before["success"]:
        print(f"Status Before: {status_before.get('job_status', 'Unknown')}")
        print(f"State Before: {status_before.get('job_state', 'Unknown')}")
    
    print(f"Approval Result: {'✅ Success' if approval_result['success'] else '❌ Failed'}")
    
    if status_after["success"]:
        print(f"Status After: {status_after.get('job_status', 'Unknown')}")
        print(f"State After: {status_after.get('job_state', 'Unknown')}")
    
    if approval_result["success"]:
        print(f"✅ Approval workflow test PASSED")
    else:
        print(f"❌ Approval workflow test FAILED")
        print(f"   Error: {approval_result.get('error', 'Unknown')}")
        print(f"   Message: {approval_result.get('message', 'No message')}")

if __name__ == "__main__":
    main()