"""
Test production API to find the exact fields containing email body and attachment content
"""

import requests
import json

def find_email_body_content():
    """Find where email body and attachment content is stored"""
    
    base_url = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
    
    print("🔍 SEARCHING FOR EMAIL BODY & ATTACHMENT CONTENT")
    print("="*60)
    
    try:
        # Get work items data
        response = requests.get(f"{base_url}/api/workitems/poll?limit=1", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if items:
                item = items[0]
                print(f"📧 Analyzing Work Item ID: {item.get('id')}")
                print(f"📧 Subject: {item.get('title')}")
                
                extracted = item.get('extracted_fields', {})
                
                print(f"\n🔍 SEARCHING ALL {len(extracted)} FIELDS FOR EMAIL CONTENT:")
                print("-" * 60)
                
                # Search for fields that might contain email body
                email_content_keywords = ['email', 'body', 'message', 'content', 'text', 'description']
                attachment_keywords = ['attachment', 'file', 'document', 'upload']
                
                email_content_fields = []
                attachment_fields = []
                
                for field_name, field_value in extracted.items():
                    field_str = str(field_value).strip()
                    
                    # Skip empty or "Not specified" fields
                    if not field_str or field_str.lower() in ['not specified', 'none', 'null', '']:
                        continue
                    
                    # Check if field name suggests email content
                    if any(keyword in field_name.lower() for keyword in email_content_keywords):
                        if len(field_str) > 50:  # Likely to be actual content
                            email_content_fields.append((field_name, field_str))
                    
                    # Check if field name suggests attachment content
                    if any(keyword in field_name.lower() for keyword in attachment_keywords):
                        if len(field_str) > 20:  # Likely to be actual content
                            attachment_fields.append((field_name, field_str))
                
                # Display email content fields
                print(f"\n📧 EMAIL CONTENT FIELDS FOUND:")
                if email_content_fields:
                    for field_name, content in email_content_fields:
                        print(f"\n   📝 Field: {field_name}")
                        print(f"      Length: {len(content)} characters")
                        print(f"      Content: {content[:200]}...")
                        if len(content) > 200:
                            print(f"      [Content continues for {len(content)} total chars]")
                else:
                    print("   ❌ No obvious email content fields found")
                
                # Display attachment content fields
                print(f"\n📎 ATTACHMENT CONTENT FIELDS FOUND:")
                if attachment_fields:
                    for field_name, content in attachment_fields:
                        print(f"\n   📁 Field: {field_name}")
                        print(f"      Length: {len(content)} characters")
                        print(f"      Content: {content[:200]}...")
                        if len(content) > 200:
                            print(f"      [Content continues for {len(content)} total chars]")
                else:
                    print("   ❌ No obvious attachment content fields found")
                
                # Search for any field with substantial text content
                print(f"\n📄 FIELDS WITH SUBSTANTIAL TEXT CONTENT:")
                text_fields = []
                for field_name, field_value in extracted.items():
                    field_str = str(field_value).strip()
                    if len(field_str) > 100 and field_str.lower() not in ['not specified']:
                        text_fields.append((field_name, field_str))
                
                if text_fields:
                    for field_name, content in text_fields[:5]:  # Show first 5
                        print(f"\n   📄 {field_name}:")
                        print(f"      Length: {len(content)} chars")
                        print(f"      Preview: {content[:150]}...")
                else:
                    print("   ❌ No fields with substantial text content found")
                
                # Show all field names for reference
                print(f"\n📋 ALL FIELD NAMES ({len(extracted)} total):")
                field_names = list(extracted.keys())
                for i in range(0, len(field_names), 6):
                    print(f"   {', '.join(field_names[i:i+6])}")
        
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Also check the submissions table directly via debug endpoint
    print(f"\n{'='*60}")
    print("🔍 CHECKING SUBMISSIONS TABLE STRUCTURE")
    print("="*60)
    
    try:
        response = requests.get(f"{base_url}/api/debug/database", timeout=30)
        
        if response.status_code == 200:
            debug_data = response.json()
            latest_submission = debug_data.get('latest_submission', {})
            
            if latest_submission:
                print(f"📧 Latest Submission in Database:")
                print(f"   ID: {latest_submission.get('id')}")
                print(f"   Subject: {latest_submission.get('subject')}")
                print(f"   Sender: {latest_submission.get('sender_email')}")
                print(f"   Created: {latest_submission.get('created_at')}")
                
                print(f"\n💡 The submissions table likely contains:")
                print(f"   - body_text: Email body content")
                print(f"   - attachment_content: Decoded attachment text") 
                print(f"   - extracted_fields: LLM-processed data")
                
                print(f"\n🔗 To access this data, try the fixed /api/submissions endpoint")
                print(f"   (Currently has validation issue, but data is there)")
    
    except Exception as e:
        print(f"❌ Error checking submissions table: {e}")

if __name__ == "__main__":
    find_email_body_content()