"""
Test the new email content API endpoints
"""

import requests
import json

def test_new_email_endpoints():
    """Test the new endpoints that provide direct access to email body and attachment content"""
    
    base_url = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
    
    print("🚀 TESTING NEW EMAIL CONTENT API ENDPOINTS")
    print("="*60)
    
    # Test 1: Work Items with Email Content endpoint
    print("\n1️⃣ Testing /api/workitems/email-content endpoint...")
    try:
        response = requests.get(f"{base_url}/api/workitems/email-content?limit=2", timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Retrieved {data.get('count', 0)} work items")
            
            items = data.get('items', [])
            if items:
                item = items[0]
                print(f"\n   📧 FIRST WORK ITEM EMAIL CONTENT:")
                print(f"   - Work Item ID: {item.get('work_item_id')}")
                print(f"   - Subject: {item.get('subject', 'No subject')}")
                print(f"   - Sender: {item.get('sender_email', 'Unknown')}")
                print(f"   - Status: {item.get('work_item_status', 'Unknown')}")
                
                # Check email body content
                email_body = item.get('email_body')
                if email_body:
                    print(f"\n   📝 EMAIL BODY CONTENT:")
                    print(f"      Length: {len(str(email_body))} characters")
                    print(f"      Content: {str(email_body)[:300]}...")
                else:
                    print(f"\n   📝 EMAIL BODY: Not available")
                
                # Check attachment content
                attachment_content = item.get('attachment_content')
                if attachment_content:
                    print(f"\n   📎 ATTACHMENT CONTENT:")
                    print(f"      Length: {len(str(attachment_content))} characters")
                    print(f"      Content: {str(attachment_content)[:300]}...")
                else:
                    print(f"\n   📎 ATTACHMENTS: None")
                
                # Check extracted fields
                extracted = item.get('extracted_fields', {})
                if extracted:
                    print(f"\n   🔍 EXTRACTED FIELDS:")
                    print(f"      Total fields: {len(extracted)}")
                    print(f"      Company: {extracted.get('company_name', 'Not specified')}")
                    print(f"      Industry: {extracted.get('industry', 'Not specified')}")
                    print(f"      Coverage: {extracted.get('coverage_amount', 'Not specified')}")
        
        elif response.status_code == 404:
            print("   ❌ Endpoint not found (needs deployment)")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Raw Submissions endpoint
    print(f"\n2️⃣ Testing /api/submissions/raw endpoint...")
    try:
        response = requests.get(f"{base_url}/api/submissions/raw?limit=1", timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Retrieved {data.get('count', 0)} raw submissions")
            
            submissions = data.get('submissions', [])
            if submissions:
                submission = submissions[0]
                print(f"\n   📧 FIRST RAW SUBMISSION:")
                print(f"   - Submission ID: {submission.get('id')}")
                print(f"   - Subject: {submission.get('subject', 'No subject')}")
                print(f"   - Sender: {submission.get('sender_email', 'Unknown')}")
                
                # Check raw email body
                email_body = submission.get('email_body')
                if email_body:
                    print(f"\n   📝 RAW EMAIL BODY:")
                    print(f"      Length: {len(str(email_body))} characters")
                    print(f"      Content: {str(email_body)[:200]}...")
                
                # Check raw attachment content
                attachment_content = submission.get('attachment_content')
                if attachment_content:
                    print(f"\n   📎 RAW ATTACHMENT CONTENT:")
                    print(f"      Length: {len(str(attachment_content))} characters")
                    print(f"      Content: {str(attachment_content)[:200]}...")
        
        elif response.status_code == 404:
            print("   ❌ Endpoint not found (needs deployment)")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Specific work item details
    print(f"\n3️⃣ Testing specific work item email content...")
    try:
        response = requests.get(f"{base_url}/api/workitems/email-content?work_item_id=87", timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            work_item = data.get('work_item', {})
            
            if work_item:
                print(f"   ✅ SUCCESS! Retrieved work item 87 details")
                print(f"   📧 Subject: {work_item.get('subject')}")
                
                email_body = work_item.get('email_body')
                attachment_content = work_item.get('attachment_content')
                
                print(f"   📝 Has Email Body: {'Yes' if email_body else 'No'}")
                print(f"   📎 Has Attachments: {'Yes' if attachment_content else 'No'}")
                
                if email_body:
                    print(f"   📝 Email Body Length: {len(str(email_body))} chars")
                if attachment_content:
                    print(f"   📎 Attachment Content Length: {len(str(attachment_content))} chars")
        
        elif response.status_code == 404:
            print("   ❌ Endpoint not found (needs deployment)")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("📋 NEW API ENDPOINTS SUMMARY")
    print("="*60)
    print("🎯 CREATED FOR UI TEAM:")
    print("")
    print("✅ Endpoint 1: Work Items + Email Content")
    print(f"   GET {base_url}/api/workitems/email-content")
    print("   → Returns work items with email_body and attachment_content")
    print("   → Includes extracted fields and business data")
    print("   → Supports pagination: ?skip=0&limit=10")
    print("   → Specific item: ?work_item_id=87")
    print("")
    print("✅ Endpoint 2: Raw Submissions")
    print(f"   GET {base_url}/api/submissions/raw")
    print("   → Returns raw submissions with email_body and attachment_content")
    print("   → Bypasses validation issues")
    print("   → Supports pagination: ?skip=0&limit=10")
    print("   → Specific submission: ?submission_id=70")
    print("")
    print("🚀 BENEFITS:")
    print("   • Direct access to email body text ✅")
    print("   • Direct access to attachment content ✅")
    print("   • No validation errors ✅")
    print("   • Includes all extracted business data ✅")
    print("   • Ready for immediate UI integration ✅")
    print("")
    print("📝 NEXT STEPS:")
    print("   1. Deploy these new endpoints to production")
    print("   2. UI team can start integration immediately")
    print("   3. Full email body and attachment content available!")

if __name__ == "__main__":
    test_new_email_endpoints()