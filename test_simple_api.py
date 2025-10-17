"""
Simple API test for UI team - Test existing submission data endpoints
"""

import requests
import json

def test_submissions_endpoints():
    """Test the main endpoints that UI team needs"""
    
    base_url = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"  # Production URL
    
    print("🧪 Testing Submission APIs for UI Team")
    print("="*50)
    
    # Test 1: Health check
    try:
        print("\n1️⃣ Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Get all submissions (main endpoint for UI)
    try:
        print("\n2️⃣ Testing submissions endpoint...")
        response = requests.get(f"{base_url}/api/submissions")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data)} submissions")
            
            if len(data) > 0:
                # Show first submission details
                submission = data[0]
                print(f"\n   📋 First Submission Details:")
                print(f"   - ID: {submission.get('id')}")
                print(f"   - Subject: {submission.get('subject', 'No subject')}")
                print(f"   - Sender: {submission.get('sender_email', 'Unknown')}")
                print(f"   - Body: {submission.get('body_text', 'No body')[:100]}...")
                print(f"   - Has Attachments: {'Yes' if submission.get('attachment_content') else 'No'}")
                print(f"   - Has Extracted Data: {'Yes' if submission.get('extracted_fields') else 'No'}")
                
                if submission.get('attachment_content'):
                    print(f"   - Attachment Content: {submission.get('attachment_content')[:100]}...")
                
                if submission.get('extracted_fields'):
                    print(f"   - Extracted Fields: {json.dumps(submission.get('extracted_fields'), indent=4)}")
                
                # Test getting history for this submission
                submission_id = submission.get('id')
                if submission_id:
                    try:
                        print(f"\n3️⃣ Testing submission history endpoint (ID: {submission_id})...")
                        history_response = requests.get(f"{base_url}/api/submissions/{submission_id}/history")
                        print(f"   Status: {history_response.status_code}")
                        if history_response.status_code == 200:
                            history_data = history_response.json()
                            print(f"   Found {len(history_data)} history entries")
                        else:
                            print(f"   Error: {history_response.text}")
                    except Exception as e:
                        print(f"   Error: {e}")
            else:
                print("   No submissions found in database")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Database debug info
    try:
        print("\n4️⃣ Testing database debug endpoint...")
        response = requests.get(f"{base_url}/api/debug/database")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            debug_data = response.json()
            print(f"   Database Status: {debug_data.get('database_status')}")
            print(f"   Total Submissions: {debug_data.get('submissions_count', 0)}")
            print(f"   Total Work Items: {debug_data.get('work_items_count', 0)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print(f"\n{'='*50}")
    print("📝 SUMMARY FOR UI TEAM:")
    print("="*50)
    print("✅ Main API Endpoint: GET /api/submissions")
    print("   Returns array of submissions with:")
    print("   - subject: Email subject line")
    print("   - sender_email: Email sender") 
    print("   - body_text: Email body content")
    print("   - attachment_content: Decoded attachment text")
    print("   - extracted_fields: LLM-extracted structured data")
    print("   - created_at: Timestamp")
    print("   - task_status: Processing status")
    print("")
    print("✅ Individual History: GET /api/submissions/{id}/history")
    print("✅ Pagination Support: ?skip=0&limit=10")
    print("")
    print("🔗 Example URLs:")
    print(f"   {base_url}/api/submissions")
    print(f"   {base_url}/api/submissions?limit=5")
    print(f"   {base_url}/api/submissions/1/history")

if __name__ == "__main__":
    test_submissions_endpoints()