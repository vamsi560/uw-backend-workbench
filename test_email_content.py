"""
Test production API to get actual email body and attachment details
"""

import requests
import json

def test_email_body_and_attachments():
    """Get actual email body and attachment content from production API"""
    
    base_url = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
    
    print("📧 Testing Email Body & Attachment Content")
    print("="*60)
    
    try:
        # Get work items with email data
        print("🔍 Fetching email data from production...")
        response = requests.get(f"{base_url}/api/workitems/poll?limit=3", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            print(f"✅ Found {len(items)} emails with content")
            print("="*60)
            
            for i, item in enumerate(items, 1):
                print(f"\n📧 EMAIL {i}")
                print("-" * 40)
                
                # Basic email info
                print(f"📌 Work Item ID: {item.get('id')}")
                print(f"📧 Subject: {item.get('title', 'No subject')}")
                print(f"📅 Received: {item.get('created_at', 'Unknown')}")
                print(f"📊 Status: {item.get('status', 'Unknown')}")
                
                # Get extracted fields (contains email body and attachments)
                extracted = item.get('extracted_fields', {})
                
                if extracted:
                    print(f"\n📄 EXTRACTED EMAIL CONTENT:")
                    print(f"   Total fields extracted: {len(extracted)}")
                    
                    # Look for email body content
                    email_body_fields = ['email_body', 'body_content', 'message_content', 'email_text']
                    for field in email_body_fields:
                        if field in extracted and extracted[field]:
                            print(f"\n   📝 Email Body ({field}):")
                            body_content = str(extracted[field])[:500]  # First 500 chars
                            print(f"      {body_content}...")
                            if len(str(extracted[field])) > 500:
                                print(f"      [Content truncated - full length: {len(str(extracted[field]))} chars]")
                            break
                    
                    # Look for attachment content
                    attachment_fields = ['attachment_content', 'attachments', 'document_content', 'file_content']
                    for field in attachment_fields:
                        if field in extracted and extracted[field]:
                            print(f"\n   📎 Attachment Content ({field}):")
                            attachment_content = str(extracted[field])[:300]  # First 300 chars
                            print(f"      {attachment_content}...")
                            if len(str(extracted[field])) > 300:
                                print(f"      [Content truncated - full length: {len(str(extracted[field]))} chars]")
                            break
                    
                    # Show business data extracted from email/attachments
                    business_fields = {
                        'company_name': 'Company Name',
                        'industry': 'Industry',
                        'coverage_amount': 'Coverage Amount',
                        'annual_revenue': 'Annual Revenue',
                        'employees': 'Number of Employees',
                        'business_address': 'Business Address',
                        'contact_email': 'Contact Email',
                        'contact_phone': 'Contact Phone'
                    }
                    
                    print(f"\n   🏢 BUSINESS DATA (extracted from email/attachments):")
                    for field, label in business_fields.items():
                        if field in extracted and extracted[field] and str(extracted[field]) != 'Not specified':
                            value = str(extracted[field])[:100]  # Limit length
                            print(f"      {label}: {value}")
                    
                    # Show all available fields for reference
                    print(f"\n   📋 ALL AVAILABLE FIELDS:")
                    field_names = list(extracted.keys())[:15]  # Show first 15 fields
                    print(f"      {', '.join(field_names)}")
                    if len(extracted) > 15:
                        print(f"      ... and {len(extracted) - 15} more fields")
                
                else:
                    print("   ⚠️ No extracted fields found for this email")
                
                if i < len(items):
                    print("\n" + "="*60)
        
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test specific work item for detailed view
    print(f"\n{'='*60}")
    print("🔍 TESTING SPECIFIC WORK ITEM DETAILS")
    print("="*60)
    
    try:
        # Get detailed view of work item 87 (we know this exists)
        print("📋 Fetching detailed view of work item 87...")
        response = requests.get(f"{base_url}/api/workitems/poll?work_item_id=87", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            work_item = data.get('work_item', {})
            
            if work_item:
                print(f"✅ Got detailed work item data")
                print(f"📧 Title: {work_item.get('title')}")
                print(f"📝 Description: {work_item.get('description', 'No description')}")
                
                extracted = work_item.get('extracted_fields', {})
                if extracted:
                    print(f"\n📄 FULL EMAIL CONTENT ANALYSIS:")
                    print(f"   Fields available: {len(extracted)}")
                    
                    # Try to find the original email content
                    content_fields = ['email_body', 'body_text', 'message_content', 'original_content']
                    for field in content_fields:
                        if field in extracted:
                            content = str(extracted[field])
                            print(f"\n   📧 {field.upper()}:")
                            print(f"      Length: {len(content)} characters")
                            print(f"      Preview: {content[:200]}...")
        
        else:
            print(f"❌ Error getting work item details: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting work item details: {e}")

if __name__ == "__main__":
    test_email_body_and_attachments()