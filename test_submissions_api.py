"""
Test script for submission APIs to retrieve email body and attachments
This script tests the endpoints that the UI team can use to display email content
"""

import requests
import json
from typing import Dict, Any
import time

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your deployed URL when testing production
API_ENDPOINTS = {
    "get_all_submissions": "/api/submissions",
    "get_submission_history": "/api/submissions/{submission_id}/history",
    "health_check": "/health",
    "debug_database": "/api/debug/database"
}

def test_api_endpoint(url: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Test an API endpoint and return the response
    """
    try:
        print(f"\n{'='*60}")
        print(f"Testing: {method} {url}")
        print(f"{'='*60}")
        
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"Response (JSON):")
                print(json.dumps(json_response, indent=2, default=str)[:2000])  # Truncate for readability
                if len(json.dumps(json_response, default=str)) > 2000:
                    print("\n[Response truncated for display...]")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": json_response
                }
            except json.JSONDecodeError:
                print(f"Response (Text): {response.text[:1000]}")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.text
                }
        else:
            print(f"Error Response: {response.text}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def test_submissions_api():
    """
    Test the submissions API endpoints that UI team needs
    """
    print("🧪 Testing Submissions API for UI Team")
    print("=" * 60)
    print("These are the endpoints UI team can use to display email body and attachments")
    
    # Test 1: Health check
    print("\n📋 Test 1: Health Check")
    health_result = test_api_endpoint(f"{BASE_URL}/health")
    
    # Test 2: Database debug info
    print("\n📋 Test 2: Database Debug Info")
    debug_result = test_api_endpoint(f"{BASE_URL}/api/debug/database")
    
    # Test 3: Get all submissions (main endpoint for UI)
    print("\n📋 Test 3: Get All Submissions (MAIN UI ENDPOINT)")
    print("This endpoint returns email body, attachments, and extracted data")
    submissions_result = test_api_endpoint(f"{BASE_URL}/api/submissions")
    
    # Test 4: Test with pagination
    print("\n📋 Test 4: Get Submissions with Pagination")
    paginated_result = test_api_endpoint(f"{BASE_URL}/api/submissions?skip=0&limit=5")
    
    # Test 5: If we have submissions, test getting history for the first one
    if (submissions_result.get("success") and 
        submissions_result.get("data") and 
        len(submissions_result["data"]) > 0):
        
        first_submission = submissions_result["data"][0]
        submission_id = first_submission.get("id")
        
        if submission_id:
            print(f"\n📋 Test 5: Get Submission History (ID: {submission_id})")
            history_result = test_api_endpoint(
                f"{BASE_URL}/api/submissions/{submission_id}/history"
            )
            
            # Show detailed breakdown of first submission for UI reference
            print(f"\n📋 Test 6: Detailed Breakdown of First Submission")
            print("=" * 40)
            print("This shows what data is available for UI display:")
            print("=" * 40)
            
            submission = first_submission
            print(f"🆔 ID: {submission.get('id')}")
            print(f"📧 Subject: {submission.get('subject', 'No subject')}")
            print(f"👤 Sender: {submission.get('sender_email', 'Unknown sender')}")
            print(f"📝 Body Text: {submission.get('body_text', 'No body')[:200]}...")
            print(f"📎 Attachment Content: {submission.get('attachment_content', 'No attachments')[:200] if submission.get('attachment_content') else 'No attachments'}...")
            print(f"🔍 Extracted Fields: {json.dumps(submission.get('extracted_fields', {}), indent=2)[:500] if submission.get('extracted_fields') else 'No extracted data'}...")
            print(f"📅 Created: {submission.get('created_at', 'Unknown')}")
            print(f"📊 Status: {submission.get('task_status', 'Unknown')}")
            print(f"👨‍💼 Assigned To: {submission.get('assigned_to', 'Unassigned')}")

    # Summary for UI team
    print(f"\n{'='*60}")
    print("📝 SUMMARY FOR UI TEAM")
    print(f"{'='*60}")
    print("✅ Main endpoint: GET /api/submissions")
    print("   - Returns email body_text (truncated for DB)")
    print("   - Returns attachment_content (decoded attachment text)")
    print("   - Returns extracted_fields (structured data from LLM)")
    print("   - Returns sender_email, subject, created_at, etc.")
    print("")
    print("✅ Pagination support: ?skip=0&limit=10")
    print("✅ Individual submission history: GET /api/submissions/{id}/history")
    print("")
    print("📋 Response Fields Available:")
    print("   - id: Database ID")
    print("   - submission_id: Human-readable submission ID")
    print("   - subject: Email subject line")
    print("   - sender_email: Email sender address")
    print("   - body_text: Email body content (truncated)")
    print("   - attachment_content: Decoded attachment text")
    print("   - extracted_fields: LLM-extracted structured data")
    print("   - created_at: Timestamp")
    print("   - task_status: Processing status")
    print("   - assigned_to: Assigned underwriter")
    
    return {
        "health_check": health_result,
        "debug_info": debug_result,
        "submissions": submissions_result,
        "paginated": paginated_result
    }

def test_with_sample_data():
    """
    Test creating a sample submission and then retrieving it
    """
    print(f"\n{'='*60}")
    print("🧪 Testing with Sample Data Creation")
    print(f"{'='*60}")
    
    # Sample email data
    sample_email = {
        "subject": "Test Insurance Quote Request - API Test",
        "sender_email": "test@testcompany.com",
        "body": "Please provide a quote for cyber liability insurance for our company. We have 50 employees and need $1M coverage.",
        "attachments": [
            {
                "filename": "company_info.txt",
                "contentBase64": "Q29tcGFueTogVGVzdCBDb21wYW55IEluYy4KRW1wbG95ZWVzOiA1MApJbmR1c3RyeTogVGVjaG5vbG9neQpSZXZlbnVlOiAkNU0="  # "Company: Test Company Inc.\nEmployees: 50\nIndustry: Technology\nRevenue: $5M"
            }
        ]
    }
    
    print("📤 Creating sample submission...")
    create_result = test_api_endpoint(
        f"{BASE_URL}/api/email/intake",
        method="POST",
        data=sample_email
    )
    
    if create_result.get("success"):
        print("✅ Sample submission created successfully!")
        
        # Wait a moment for processing
        print("⏳ Waiting 2 seconds for processing...")
        time.sleep(2)
        
        # Now test retrieving it
        print("📥 Retrieving updated submissions list...")
        updated_submissions = test_api_endpoint(f"{BASE_URL}/api/submissions?limit=1")
        
        if (updated_submissions.get("success") and 
            updated_submissions.get("data") and 
            len(updated_submissions["data"]) > 0):
            
            latest_submission = updated_submissions["data"][0]
            print("\n📋 Latest Submission Details:")
            print("=" * 40)
            print(f"📧 Subject: {latest_submission.get('subject')}")
            print(f"👤 Sender: {latest_submission.get('sender_email')}")
            print(f"📝 Body: {latest_submission.get('body_text')}")
            print(f"📎 Attachments: {latest_submission.get('attachment_content')}")
            print(f"🔍 Extracted Data: {json.dumps(latest_submission.get('extracted_fields', {}), indent=2)}")
    else:
        print("❌ Failed to create sample submission")
        print("This might be because the server is not running or there's a configuration issue")

if __name__ == "__main__":
    print("🚀 Starting API Tests for UI Team")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print("Make sure your server is running with: python run.py")
    print("")
    
    try:
        # Test existing data
        results = test_submissions_api()
        
        # Test with sample data creation
        test_with_sample_data()
        
        print(f"\n{'='*60}")
        print("🎉 API Testing Complete!")
        print(f"{'='*60}")
        print("UI team can now use these endpoints to display email content")
        
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")