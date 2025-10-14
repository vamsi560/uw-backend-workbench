#!/usr/bin/env python3

import requests
import json
import logging
from database import SessionLocal, WorkItem, GuidewireResponse
from sqlalchemy import desc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test email content
test_email = {
    "subject": "Cyber Insurance Quote Request - Debug Test",
    "sender_email": "test@guidewiredebug.com",
    "body": """
Dear Underwriter,

We need a cyber insurance quote for our company:

Company: Debug Test Corp
Contact: John Doe
Email: john@debugtestcorp.com
Phone: 555-0123
Address: 123 Main Street, San Francisco, CA 94105

Business Details:
- Industry: Technology/Software
- Entity Type: Corporation
- Employees: 50
- Annual Revenue: $5,000,000
- Total Assets: $2,500,000
- Total Liabilities: $500,000

Insurance Requirements:
- Coverage Type: Cyber Liability
- Coverage Amount: $1,000,000
- Deductible: $10,000
- Policy Start Date: January 1, 2025
- Coverage Areas: Data Breach, Business Interruption, Cyber Extortion

Please provide a quote at your earliest convenience.

Best regards,
John Doe
""",
    "attachments": []
}

print("📧 Sending test email to trigger Guidewire integration...")

# Send test email
response = requests.post(
    "http://localhost:8000/api/email/intake",
    json=test_email,
    headers={"Content-Type": "application/json"}
)

print(f"📤 Email Response Status: {response.status_code}")
print(f"📤 Email Response: {response.json()}")

if response.status_code == 200:
    result = response.json()
    work_item_id = result.get("submission_id")  # This might be the work_item_id
    
    print(f"\n🔍 Checking database for work_item_id: {work_item_id}")
    
    # Check database
    db = SessionLocal()
    
    # Get latest work item
    work_item = db.query(WorkItem).order_by(desc(WorkItem.created_at)).first()
    if work_item:
        print(f"\n📋 Latest WorkItem {work_item.id}:")
        print(f"   - Account ID: {work_item.guidewire_account_id}")
        print(f"   - Job ID: {work_item.guidewire_job_id}")
        print(f"   - Status: {work_item.status}")
        print(f"   - Created: {work_item.created_at}")
        
        # Check if there's a GuidewireResponse for this work item
        gw_response = db.query(GuidewireResponse).filter(
            GuidewireResponse.work_item_id == work_item.id
        ).first()
        
        if gw_response:
            print(f"\n🎯 GuidewireResponse {gw_response.id}:")
            print(f"   - Account ID: {gw_response.guidewire_account_id}")
            print(f"   - Account Number: {gw_response.account_number}")
            print(f"   - Job ID: {gw_response.guidewire_job_id}")
            print(f"   - Job Number: {gw_response.job_number}")
            print(f"   - Success: {gw_response.submission_success}")
            
            print(f"\n❓ Why isn't WorkItem updated with GuidewireResponse data?")
            print(f"   WorkItem account_id: {work_item.guidewire_account_id}")
            print(f"   GuidewireResponse account_id: {gw_response.guidewire_account_id}")
        else:
            print(f"\n❌ No GuidewireResponse found for WorkItem {work_item.id}")
    
    db.close()

print("\n✨ Debug test complete!")