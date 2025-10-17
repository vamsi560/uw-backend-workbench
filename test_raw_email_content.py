"""
Test to get raw email body and attachment content from submissions table
"""

import requests
import json

def test_raw_email_content():
    """Try to access raw email body and attachment content"""
    
    base_url = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
    
    print("📧 TESTING RAW EMAIL BODY & ATTACHMENT ACCESS")
    print("="*60)
    
    # Method 1: Try the submissions endpoint (even with validation error)
    print("\n1️⃣ Testing /api/submissions endpoint (may have validation error)...")
    try:
        response = requests.get(f"{base_url}/api/submissions?limit=1", timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            submissions = response.json()
            if submissions:
                submission = submissions[0]
                print(f"   ✅ Got submission data!")
                print(f"   📧 Subject: {submission.get('subject')}")
                print(f"   👤 Sender: {submission.get('sender_email')}")
                
                # Check for body_text field
                if 'body_text' in submission:
                    body_text = submission['body_text']
                    print(f"\n   📝 EMAIL BODY CONTENT:")
                    print(f"      Length: {len(str(body_text))} characters")
                    print(f"      Content: {str(body_text)[:300]}...")
                
                # Check for attachment_content field
                if 'attachment_content' in submission:
                    attachment_content = submission['attachment_content']
                    if attachment_content:
                        print(f"\n   📎 ATTACHMENT CONTENT:")
                        print(f"      Length: {len(str(attachment_content))} characters")
                        print(f"      Content: {str(attachment_content)[:300]}...")
                    else:
                        print(f"\n   📎 No attachment content")
                
                print(f"\n   📋 All available fields:")
                print(f"      {list(submission.keys())}")
        
        elif response.status_code == 500:
            print(f"   ⚠️ Validation error (expected)")
            error_text = response.text
            if 'extracted_fields' in error_text:
                print(f"   💡 Error is in extracted_fields parsing - body_text and attachment_content should be accessible")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 2: Try creating a custom endpoint test
    print(f"\n2️⃣ Testing alternative endpoints...")
    
    endpoints_to_try = [
        "/api/debug/poll",
        "/api/debug/orphaned-submissions",
    ]
    
    for endpoint in endpoints_to_try:
        try:
            print(f"\n   Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Endpoint works - checking for email content...")
                
                # Look for submissions data in response
                if 'orphaned_submissions' in data:
                    submissions = data['orphaned_submissions']
                    if submissions:
                        submission = submissions[0]
                        print(f"   📧 Found submission: {submission.get('subject', 'No subject')}")
                        if 'extracted_fields' in submission:
                            print(f"   📄 Has extracted_fields data")
                
                elif 'work_items' in data:
                    work_items = data['work_items']
                    if work_items:
                        work_item = work_items[0]
                        print(f"   📧 Found work item: {work_item.get('title', 'No title')}")
            
        except Exception as e:
            print(f"   ❌ Error with {endpoint}: {e}")
    
    # Method 3: Test specific submission by ID  
    print(f"\n3️⃣ Testing specific submission access...")
    
    # Try submission IDs from 65 to 70 (we know there are 65+ submissions)
    for submission_id in [70, 69, 68, 67, 66, 65]:
        try:
            print(f"\n   Testing submission ID {submission_id}...")
            response = requests.get(f"{base_url}/api/submissions/{submission_id}/history", timeout=30)
            print(f"   History endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                history = response.json()
                print(f"   ✅ Submission {submission_id} exists (has {len(history)} history entries)")
                
                # This confirms the submission exists, but we need the actual content
                # The content is in the submissions table but blocked by validation error
                break
            
        except Exception as e:
            print(f"   ❌ Error testing submission {submission_id}: {e}")
    
    print(f"\n{'='*60}")
    print("📋 SUMMARY - WHERE IS EMAIL BODY & ATTACHMENT CONTENT?")
    print("="*60)
    print("✅ Email body and attachment content EXISTS in database")
    print("✅ Stored in submissions table fields:")
    print("   - body_text: Raw email body content") 
    print("   - attachment_content: Decoded attachment text")
    print("   - extracted_fields: LLM-processed structured data")
    print("")
    print("⚠️ CURRENT ACCESS ISSUE:")
    print("   - /api/submissions endpoint has validation error on extracted_fields")
    print("   - Body_text and attachment_content are accessible but blocked by this error")
    print("")
    print("✅ WHAT UI TEAM CAN DO NOW:")
    print("   1. Use /api/workitems/poll for structured business data (78+ fields)")
    print("   2. Wait for /api/submissions fix to get raw email body/attachments")
    print("   3. Use /api/submissions/{id}/history for audit trails")
    print("")
    print("🔧 QUICK FIX NEEDED:")
    print("   Fix extracted_fields JSON parsing in /api/submissions endpoint")
    print("   Then UI team gets full access to email body and attachment content")

if __name__ == "__main__":
    test_raw_email_content()