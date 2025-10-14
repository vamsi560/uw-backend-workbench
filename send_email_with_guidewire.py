#!/usr/bin/env python3
"""
Send email and then manually sync to Guidewire
This is the workaround until auto-sync is fixed
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def send_email_and_sync():
    """Send email then manually sync to Guidewire"""
    
    # Your email content
    timestamp = datetime.now().strftime("%H%M%S")
    test_email = {
        "subject": f"Fresh Test Email {timestamp} - Insurance Request",
        "sender_email": "test@mycompany.com",
        "body": f"""
        We need cyber insurance for our company.
        
        Company: My Test Company Inc
        Industry: Technology
        Employees: 100
        Annual Revenue: $5,000,000
        Coverage Amount: $2,000,000
        Contact: Test User
        Phone: 555-123-4567
        Address: 123 Test Street, Test City, CA 12345
        
        This email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """,
        "attachments": []
    }
    
    print("📧 SENDING EMAIL...")
    print("="*50)
    
    # Step 1: Send email
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake", 
                               json=test_email, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Email sent successfully!")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            print(f"   Status: {data.get('status')}")
            
            # Wait for processing
            print(f"\n⏳ Waiting 3 seconds for processing...")
            time.sleep(3)
            
            # Step 2: Get the latest work item
            print(f"\n🔍 Finding your new work item...")
            db_response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
            
            if db_response.status_code == 200:
                db_data = db_response.json()
                latest_item = db_data.get('latest_work_item')
                
                if latest_item:
                    work_item_id = latest_item['id']
                    print(f"✅ Work item created: ID {work_item_id}")
                    print(f"   Title: {latest_item['title']}")
                    
                    # Step 3: Create Guidewire account using direct method
                    print(f"\n🚀 Creating Guidewire account...")
                    
                    # Use the direct method that we know works
                    gw_data = {
                        "company_name": "My Test Company Inc",
                        "contact_email": "test@mycompany.com",
                        "contact_name": "Test User",
                        "industry": "technology", 
                        "employee_count": "100",
                        "annual_revenue": "5000000",
                        "coverage_amount": "2000000",
                        "business_address": "123 Test Street",
                        "business_city": "Test City",
                        "business_state": "CA", 
                        "business_zip": "12345",
                        "policy_type": "cyber liability"
                    }
                    
                    gw_response = requests.post(f"{BASE_URL}/api/test/guidewire-submission",
                                              json=gw_data,
                                              timeout=30)
                    
                    if gw_response.status_code == 200:
                        gw_result = gw_response.json().get('guidewire_result', {})
                        
                        if gw_result.get('success'):
                            account_number = gw_result.get('account_number')
                            account_id = gw_result.get('account_id')
                            
                            print(f"🎉 SUCCESS! Guidewire account created!")
                            print(f"   Account Number: {account_number}")
                            print(f"   Account ID: {account_id}")
                            
                            print(f"\n✅ COMPLETE FLOW SUCCESS!")
                            print(f"   📧 Email processed → Work Item {work_item_id}")
                            print(f"   🏢 Guidewire account → {account_number}")
                            print(f"\n🔍 Check Guidewire PolicyCenter for account: {account_number}")
                            
                            return {
                                'work_item_id': work_item_id,
                                'account_number': account_number,
                                'success': True
                            }
                        else:
                            print(f"❌ Guidewire account creation failed: {gw_result.get('error')}")
                    else:
                        print(f"❌ Guidewire request failed: HTTP {gw_response.status_code}")
                else:
                    print(f"❌ No work item found")
            else:
                print(f"❌ Could not check work items: HTTP {db_response.status_code}")
        else:
            print(f"❌ Email failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    return {'success': False}

if __name__ == "__main__":
    print("🚀 EMAIL + GUIDEWIRE WORKAROUND METHOD")
    print("This will send email AND create Guidewire account")
    print("="*60)
    
    result = send_email_and_sync()
    
    if result.get('success'):
        print(f"\n🎯 FINAL RESULT:")
        print(f"✅ Email → Work Item: {result.get('work_item_id')}")
        print(f"✅ Guidewire → Account: {result.get('account_number')}")
        print(f"\n🔍 Go check Guidewire PolicyCenter now!")
    else:
        print(f"\n❌ Something went wrong - check the output above")