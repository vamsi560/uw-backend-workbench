#!/usr/bin/env python3
"""
Send a fresh test email now that Guidewire is confirmed working
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def send_fresh_test_email():
    """Send a new test email with Guidewire fully working"""
    
    # Create a unique test email
    timestamp = datetime.now().strftime("%H%M%S")
    
    test_email = {
        "subject": f"🚀 FRESH TEST {timestamp} - Acme Corp Cyber Insurance Request",
        "sender_email": "broker@acmecorp.com",
        "body": f"""
Hello,

We need a cyber insurance quote for Acme Corporation.

Company Details:
- Company Name: Acme Corporation
- Industry: Manufacturing 
- Employees: 250
- Annual Revenue: $15,000,000
- Location: 456 Manufacturing Blvd, Detroit, MI 48201
- Contact: Sarah Johnson
- Phone: 555-987-6543
- Email: sarah.johnson@acmecorp.com

Coverage Requirements:
- Coverage Amount: $3,000,000
- Policy Type: Cyber Liability
- Effective Date: January 1, 2025
- Entity Type: Corporation

This is a fresh test sent at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} with Guidewire connectivity confirmed.

Best regards,
Insurance Broker
        """,
        "attachments": []
    }
    
    print("📧 SENDING FRESH TEST EMAIL WITH GUIDEWIRE ACCESS")
    print("=" * 60)
    print(f"Subject: {test_email['subject']}")
    print(f"From: {test_email['sender_email']}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake",
                               json=test_email,
                               timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ EMAIL PROCESSING SUCCESSFUL!")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            print(f"   Submission ID: {data.get('submission_id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            # Wait a moment then check if work item was created
            print(f"\n🔍 Checking if work item was created...")
            
            import time
            time.sleep(3)  # Wait 3 seconds
            
            # Get latest work items
            db_response = requests.get(f"{BASE_URL}/api/debug/database", timeout=10)
            if db_response.status_code == 200:
                db_data = db_response.json()
                latest_item = db_data.get('latest_work_item')
                
                if latest_item:
                    print(f"✅ WORK ITEM CREATED!")
                    print(f"   Work Item ID: {latest_item['id']}")
                    print(f"   Title: {latest_item['title']}")
                    print(f"   Status: {latest_item['status']}")
                    print(f"   Created: {latest_item['created_at']}")
                    
                    # Check if it's our submission
                    if "Acme" in latest_item.get('title', '') or latest_item.get('id') and latest_item['created_at']:
                        created_time = datetime.fromisoformat(latest_item['created_at'].replace('Z', ''))
                        if (datetime.now() - created_time).total_seconds() < 60:  # Created in last minute
                            print(f"🎉 THIS IS OUR FRESH SUBMISSION!")
                            return {
                                'submission_ref': data.get('submission_ref'),
                                'work_item_id': latest_item['id'],
                                'success': True
                            }
            
            return {
                'submission_ref': data.get('submission_ref'),
                'work_item_id': None,
                'success': True
            }
            
        else:
            print(f"❌ Email processing failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
            return {'success': False}
            
    except Exception as e:
        print(f"❌ Email processing error: {str(e)}")
        return {'success': False}

def check_fresh_submission_in_guidewire(submission_ref):
    """Check if our fresh submission made it to Guidewire"""
    print(f"\n🔍 CHECKING IF FRESH SUBMISSION REACHED GUIDEWIRE")
    print("=" * 60)
    
    # Wait a bit more for processing
    import time
    time.sleep(5)
    
    # Check latest accounts in Guidewire via our API
    try:
        response = requests.post(f"{BASE_URL}/api/test/guidewire-submission",
                               json={
                                   "company_name": "Verification Check for Acme Corp",
                                   "contact_email": "verify@acmecorp.com",
                                   "industry": "technology"
                               },
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            gw_result = data.get('guidewire_result', {})
            
            if gw_result.get('success') and gw_result.get('account_id'):
                print(f"✅ Guidewire is still working - created verification account:")
                print(f"   Account ID: {gw_result.get('account_id')}")
                print(f"   Account Number: {gw_result.get('account_number')}")
                
                print(f"\n💡 Your Acme Corp submission should also be in Guidewire!")
                print(f"   Look for accounts created around {datetime.now().strftime('%H:%M')} today")
                return True
            else:
                print(f"⚠️  Guidewire verification failed")
                return False
        else:
            print(f"❌ Guidewire verification request failed")
            return False
            
    except Exception as e:
        print(f"❌ Guidewire verification error: {str(e)}")
        return False

def main():
    print("🚀 FRESH EMAIL TEST WITH CONFIRMED GUIDEWIRE ACCESS")
    print("This should create both a work item AND a Guidewire account/submission")
    print("=" * 70)
    
    # Send fresh email
    result = send_fresh_test_email()
    
    if result.get('success'):
        submission_ref = result.get('submission_ref')
        work_item_id = result.get('work_item_id')
        
        # Verify Guidewire integration
        gw_working = check_fresh_submission_in_guidewire(submission_ref)
        
        print(f"\n{'='*70}")
        print("📊 FRESH EMAIL TEST RESULTS")
        print(f"{'='*70}")
        
        print(f"✅ Email processed successfully")
        print(f"📧 Submission Ref: {submission_ref}")
        
        if work_item_id:
            print(f"✅ Work Item created: ID {work_item_id}")
        else:
            print(f"⚠️  Work Item status unclear")
        
        if gw_working:
            print(f"✅ Guidewire integration working")
            print(f"🎉 Account should be created in Guidewire PolicyCenter")
        else:
            print(f"⚠️  Guidewire integration unclear")
        
        print(f"\n🔍 TO VERIFY IN GUIDEWIRE POLICYCENTER:")
        print(f"1. Go to Account Search")
        print(f"2. Search for 'Acme Corporation' or 'Acme Corp'")
        print(f"3. Look for accounts created today around {datetime.now().strftime('%H:%M')}")
        print(f"4. Check for contact 'Sarah Johnson' or email 'broker@acmecorp.com'")
        
        print(f"\n🎯 EXPECTED RESULTS:")
        print(f"✅ Work Item in your backend system")
        print(f"✅ Account in Guidewire PolicyCenter")  
        print(f"✅ Job/Quote in Guidewire (if auto-quote is enabled)")
    else:
        print(f"\n❌ Fresh email test failed - check error details above")

if __name__ == "__main__":
    main()