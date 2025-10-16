#!/usr/bin/env python3
"""
Test Approval Workflow via FastAPI
Tests the approval endpoints through the web API
"""

import json
import requests
from datetime import datetime

# Configuration
API_BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
TEST_JOB_ID = "pc:S9Z7G9A7dGlQCKdKlc-G6"  # Job 0001563719
TEST_WORK_ITEM_ID = 87  # Work item with real Guidewire data

def test_api_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"🌐 {method} {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success")
            return result
        else:
            print(f"   ❌ Failed: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}", "message": response.text}
    
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - is the server running on {API_BASE_URL}?")
        return {"success": False, "error": "ConnectionError", "message": "Cannot connect to API server"}
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return {"success": False, "error": "Exception", "message": str(e)}

def main():
    """Test approval workflow via API"""
    print("🚀 Guidewire Approval Workflow API Test")
    print("=" * 50)
    
    # Test 1: Direct approval workflow test
    print(f"\n1️⃣  Testing approval workflow directly")
    workflow_result = test_api_endpoint(
        "/api/test/approval-workflow", 
        method="POST", 
        data={"job_id": TEST_JOB_ID}
    )
    
    if workflow_result.get("success"):
        summary = workflow_result.get("summary", {})
        print(f"   Connection: {'✅' if summary.get('connection_success') else '❌'}")
        print(f"   UW Issues Found: {summary.get('uw_issues_found', 0)}")
        print(f"   Approval Attempted: {'Yes' if summary.get('approval_attempted') else 'No'}")
        if summary.get('approval_success') is not None:
            print(f"   Approval Success: {'✅' if summary.get('approval_success') else '❌'}")
    
    # Test 2: Get UW issues for work item
    print(f"\n2️⃣  Getting UW issues for work item {TEST_WORK_ITEM_ID}")
    uw_issues_result = test_api_endpoint(f"/api/workitems/{TEST_WORK_ITEM_ID}/uw-issues")
    
    if uw_issues_result.get("success"):
        uw_count = uw_issues_result.get("uw_issues_count", 0)
        print(f"   Found {uw_count} UW issues")
        
        if uw_count > 0:
            # Test 3: Approve the submission
            print(f"\n3️⃣  Approving submission for work item {TEST_WORK_ITEM_ID}")
            approval_result = test_api_endpoint(
                f"/api/workitems/{TEST_WORK_ITEM_ID}/approve",
                method="POST",
                data={
                    "underwriter_notes": "Approved via API testing - meets underwriting criteria",
                    "approved_by": "Test Underwriter"
                }
            )
            
            if approval_result.get("success"):
                print(f"   ✅ Approval successful!")
                print(f"   Status: {approval_result.get('status', 'approved')}")
                print(f"   Approved Issues: {len(approval_result.get('approved_issues', []))}")
                print(f"   Total Issues: {approval_result.get('uw_issues_count', 0)}")
            else:
                print(f"   ❌ Approval failed: {approval_result.get('message', 'Unknown error')}")
        else:
            print(f"   ℹ️  No UW issues to approve - submission may already be approved")
    
    # Test 4: Test document retrieval for the job
    print(f"\n4️⃣  Testing document retrieval for job")
    doc_result = test_api_endpoint(
        "/api/test/guidewire-documents",
        method="POST",
        data={"job_id": TEST_JOB_ID, "job_number": "0001563719"}
    )
    
    if doc_result.get("success"):
        docs_count = len(doc_result.get("documents", []))
        print(f"   Found {docs_count} documents")
    
    # Summary
    print(f"\n📋 API TEST SUMMARY")
    print("=" * 25)
    print(f"Job ID: {TEST_JOB_ID}")
    print(f"Work Item ID: {TEST_WORK_ITEM_ID}")
    
    if workflow_result.get("success"):
        summary = workflow_result.get("summary", {})
        print(f"Connection: {'✅' if summary.get('connection_success') else '❌'}")
        print(f"UW Issues: {summary.get('uw_issues_found', 0)} found")
        
        if summary.get('approval_attempted'):
            approval_status = '✅ Success' if summary.get('approval_success') else '❌ Failed'
            print(f"Approval: {approval_status}")
        else:
            print(f"Approval: Not attempted")
    else:
        print(f"Workflow Test: ❌ Failed")
    
    print(f"\n🎯 Approval workflow API integration {'✅ READY' if workflow_result.get('success') else '❌ NEEDS ATTENTION'}")

if __name__ == "__main__":
    main()