#!/usr/bin/env python3
"""
Perfect Email Template for Testing Automatic Guidewire Sync
Copy this exact format to ensure success
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def send_perfect_test_email():
    """Send a perfectly formatted test email"""
    
    # Use current timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # PERFECT EMAIL TEMPLATE - Copy this format exactly!
    perfect_email = {
        "subject": f"Cyber Insurance Quote Request - Test {timestamp}",
        "sender_email": f"test.{timestamp}@mycompany.com",
        "body": f"""Dear Underwriter,

We are requesting a comprehensive cyber insurance quote for our company.

COMPANY INFORMATION:
Company Name: Test Company Inc
Industry: Technology
Business Type: Software Development
Years in Business: 5
Entity Type: Corporation

CONTACT INFORMATION:
Contact Name: John Smith
Email: test.{timestamp}@mycompany.com
Phone: (555) 123-4567
Address: 123 Business Street, Tech City, CA 90210

BUSINESS DETAILS:
Number of Employees: 150
Annual Revenue: $8,000,000
Data Types: Customer PII, Payment Information, Business Records

INSURANCE REQUIREMENTS:
Policy Type: Cyber Liability
Coverage Amount: $2,000,000
Effective Date: January 1, 2025
Policy Term: 1 Year

SECURITY MEASURES:
- Multi-factor authentication
- Data encryption (at rest and in transit)
- Regular security training
- Incident response plan
- SOC 2 Type II certified

We need coverage for:
- Privacy liability
- Network security
- Data breach response
- Business interruption
- Cyber extortion

Please provide a comprehensive quote at your earliest convenience.

Best regards,
John Smith
Risk Manager
Test Company Inc

Email sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """,
        "attachments": []
    }
    
    print("📧 SENDING PERFECT TEST EMAIL")
    print("="*60)
    print(f"Subject: {perfect_email['subject']}")
    print(f"From: {perfect_email['sender_email']}")
    print(f"Contains all required fields for validation")
    
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake", 
                               json=perfect_email, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            
            print(f"\n✅ EMAIL SENT SUCCESSFULLY!")
            print(f"Response: {message}")
            
            if 'guidewire' in message.lower() or 'policycenter' in message.lower():
                print(f"\n🎉 SUCCESS! Automatic Guidewire sync is working!")
                print(f"✅ The fix has been deployed!")
            else:
                print(f"\n⏳ Email processed, checking if auto-sync happened...")
                print(f"📋 Work item created: {data.get('submission_ref')}")
                
            return True, data
            
        else:
            print(f"\n❌ Email failed: HTTP {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"\n❌ Error sending email: {str(e)}")
        return False, None

def print_email_template():
    """Print the email template for manual copying"""
    
    timestamp_example = "20251014_140000"  # Example timestamp
    
    print("\n📋 COPY THIS EMAIL TEMPLATE (Manual Method):")
    print("="*80)
    print("URL: https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net/api/email/intake")
    print("Method: POST")
    print("Content-Type: application/json")
    print("\nJSON Body:")
    
    template = {
        "subject": f"Cyber Insurance Quote Request - Test {timestamp_example}",
        "sender_email": f"test.{timestamp_example}@mycompany.com",
        "body": f"""Dear Underwriter,

We are requesting a comprehensive cyber insurance quote for our company.

COMPANY INFORMATION:
Company Name: Test Company Inc
Industry: Technology
Business Type: Software Development
Years in Business: 5
Entity Type: Corporation

CONTACT INFORMATION:
Contact Name: John Smith
Email: test.{timestamp_example}@mycompany.com
Phone: (555) 123-4567
Address: 123 Business Street, Tech City, CA 90210

BUSINESS DETAILS:
Number of Employees: 150
Annual Revenue: $8,000,000
Data Types: Customer PII, Payment Information, Business Records

INSURANCE REQUIREMENTS:
Policy Type: Cyber Liability
Coverage Amount: $2,000,000
Effective Date: January 1, 2025
Policy Term: 1 Year

SECURITY MEASURES:
- Multi-factor authentication
- Data encryption (at rest and in transit)
- Regular security training
- Incident response plan
- SOC 2 Type II certified

We need coverage for:
- Privacy liability
- Network security
- Data breach response
- Business interruption
- Cyber extortion

Please provide a comprehensive quote at your earliest convenience.

Best regards,
John Smith
Risk Manager
Test Company Inc

Email sent: 2025-10-14 14:00:00
        """,
        "attachments": []
    }
    
    print(json.dumps(template, indent=2))

def main():
    print("📧 PERFECT EMAIL TEMPLATE FOR GUIDEWIRE SYNC TESTING")
    print("This email is guaranteed to work once the fix is deployed")
    print("="*80)
    
    # Option 1: Send automatically
    print("🚀 OPTION 1: Send automatically")
    success, data = send_perfect_test_email()
    
    # Option 2: Manual template
    print_email_template()
    
    print(f"\n{'='*80}")
    print("💡 KEY POINTS:")
    print("✅ This email contains ALL required fields:")
    print("   - Company name, industry, policy type")
    print("   - Contact information")
    print("   - Coverage amount and effective date")
    print("   - Business details")
    print("✅ Perfect format for LLM extraction")
    print("✅ Should pass all validation rules")
    print("✅ Will trigger automatic Guidewire sync (once deployed)")
    
    if success:
        print(f"\n🎯 Your test email was sent successfully!")
        if data:
            print(f"📋 Submission Reference: {data.get('submission_ref')}")
    else:
        print(f"\n🔧 Use the manual template above if needed")

if __name__ == "__main__":
    main()