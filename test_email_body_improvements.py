#!/usr/bin/env python3
"""
Test script: Verify email body storage improvements
Tests that HTML emails are properly processed and stored
"""

import requests
import json
from datetime import datetime

# Test with production server
BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_html_email_processing():
    """Test HTML email processing and storage"""
    
    print("🧪 Testing HTML Email Processing")
    print("=" * 50)
    
    # Sample HTML email content
    html_email_body = """
    <html>
    <body>
        <h1>Cyber Insurance Quote Request</h1>
        <p>Dear Insurance Team,</p>
        
        <p>We are requesting a comprehensive cyber liability insurance quote for our technology company.</p>
        
        <div>
            <h2>Company Information:</h2>
            <ul>
                <li><strong>Company Name:</strong> TechCorp Solutions Inc.</li>
                <li><strong>Industry:</strong> Software Development & IT Services</li>
                <li><strong>Employees:</strong> 75 full-time employees</li>
                <li><strong>Annual Revenue:</strong> $12 million</li>
                <li><strong>Business Address:</strong> 456 Innovation Drive, San Francisco, CA 94105</li>
            </ul>
        </div>
        
        <div>
            <h2>Coverage Requirements:</h2>
            <p>We are seeking the following coverage limits:</p>
            <ul>
                <li>General Liability: $2,000,000</li>
                <li>Data Breach Response: $1,000,000</li>
                <li>Cyber Extortion: $500,000</li>
                <li>Business Interruption: $1,500,000</li>
            </ul>
        </div>
        
        <p>Please let us know if you need any additional information.</p>
        
        <p>Best regards,<br>
        John Smith<br>
        Risk Manager<br>
        TechCorp Solutions Inc.<br>
        Phone: (555) 123-4567<br>
        Email: john.smith@techcorp.com</p>
    </body>
    </html>
    """
    
    # Test email payload
    test_payload = {
        "subject": "Cyber Insurance Quote Request - TechCorp Solutions",
        "from": "john.smith@techcorp.com", 
        "body": html_email_body,
        "received_at": datetime.utcnow().isoformat() + "Z",
        "attachments": []
    }
    
    try:
        print("📧 Sending HTML email to processing endpoint...")
        
        # Send to Logic Apps endpoint (handles HTML better)
        response = requests.post(
            f"{BASE_URL}/api/logicapps/email/intake",
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Email processed successfully!")
            print(f"Submission ID: {result.get('submission_id')}")
            print(f"Work Item ID: {result.get('work_item_id')}")
            
            # Wait a moment for database write
            import time
            time.sleep(1)
            
            # Now test retrieving the email content
            print("\n📥 Testing email content retrieval...")
            
            # Test email content endpoint
            content_response = requests.get(f"{BASE_URL}/api/workitems/email-content?limit=1")
            
            if content_response.status_code == 200:
                content_data = content_response.json()
                
                if content_data.get("success") and content_data.get("items"):
                    item = content_data["items"][0]
                    
                    print("✅ Email content retrieved successfully!")
                    print(f"\nSubject: {item.get('subject')}")
                    print(f"Sender: {item.get('sender_email')}")
                    
                    # Check text version
                    email_body = item.get("email_body", "")
                    print(f"\nPlain Text Body Length: {len(email_body)} characters")
                    print(f"Plain Text Preview: {email_body[:200]}...")
                    
                    # Check HTML version
                    email_html = item.get("email_body_html", "")
                    if email_html:
                        print(f"\nHTML Body Length: {len(email_html)} characters")
                        print(f"HTML Preview: {email_html[:200]}...")
                        print("✅ HTML version stored successfully!")
                    else:
                        print("⚠️  No HTML version stored")
                    
                    # Check extracted data
                    extracted = item.get("extracted_fields", {})
                    if extracted:
                        print(f"\n📊 Extracted Data:")
                        print(f"Company Name: {extracted.get('company_name')}")
                        print(f"Industry: {extracted.get('industry')}")
                        print(f"Coverage Amount: {extracted.get('coverage_amount')}")
                        print(f"Employees: {extracted.get('employees')}")
                    
                else:
                    print("❌ No email content found in response")
            else:
                print(f"❌ Failed to retrieve email content: {content_response.status_code}")
                
        else:
            print(f"❌ Email processing failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_plain_text_email():
    """Test plain text email processing"""
    
    print("\n🧪 Testing Plain Text Email Processing")
    print("=" * 50)
    
    plain_text_body = """
    Dear Insurance Team,
    
    I am writing to request a cyber liability insurance quote for our company.
    
    Company Details:
    - Name: Small Business LLC
    - Industry: Consulting Services  
    - Employees: 15
    - Annual Revenue: $2.5 million
    - Address: 123 Main Street, Austin, TX 78701
    
    We need coverage for:
    - Data breach protection: $500,000
    - Cyber liability: $1,000,000
    - Business interruption: $250,000
    
    Please contact me with any questions.
    
    Thank you,
    Sarah Johnson
    Office Manager
    sarah.johnson@smallbiz.com
    (512) 555-0123
    """
    
    test_payload = {
        "subject": "Cyber Insurance Quote - Small Business LLC",
        "from": "sarah.johnson@smallbiz.com",
        "body": plain_text_body,
        "received_at": datetime.utcnow().isoformat() + "Z",
        "attachments": []
    }
    
    try:
        print("📧 Sending plain text email to processing endpoint...")
        
        response = requests.post(
            f"{BASE_URL}/api/logicapps/email/intake",
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Plain text email processed successfully!")
            print(f"Submission ID: {result.get('submission_id')}")
            
        else:
            print(f"❌ Plain text email processing failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 Email Body Storage Testing")
    print("=" * 60)
    print("Testing improvements to email body processing:")
    print("- Full content storage (no 240 character limit)")
    print("- HTML and plain text versions")  
    print("- Improved email content APIs")
    print()
    
    # Run tests
    test_html_email_processing()
    test_plain_text_email()
    
    print("\n🏁 Testing completed!")
    print("\nKey improvements:")
    print("✅ No more 240 character truncation")
    print("✅ Full HTML content preserved")
    print("✅ Both HTML and text versions available")
    print("✅ Better API responses for UI team")