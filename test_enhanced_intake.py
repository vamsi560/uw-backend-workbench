#!/usr/bin/env python3
"""
Test script to verify if the enhanced email intake endpoints are working
This will test both email intake endpoints to see if they create work items
"""

import requests
import json
from datetime import datetime

def test_enhanced_email_intake():
    """Test if the enhanced email intake is deployed and working"""
    
    base_url = 'https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net'
    
    print("🧪 Testing Enhanced Email Intake Deployment")
    print("=" * 60)
    
    # Test payload
    test_email = {
        "subject": f"TEST: Enhanced intake verification {datetime.now().strftime('%H:%M:%S')}",
        "sender_email": "test@enhanced-intake.com",
        "received_at": datetime.utcnow().isoformat() + "Z",
        "body": "This is a test email to verify enhanced intake is working. Company: Test Corp, Industry: Technology, Coverage needed: $5M cyber insurance",
        "attachments": []
    }
    
    print(f"📧 Test Email Subject: {test_email['subject']}")
    print(f"📧 Test Email From: {test_email['sender_email']}")
    
    # Test the enhanced email intake endpoint
    print("\n🔍 Testing /api/email/intake...")
    try:
        response = requests.post(f'{base_url}/api/email/intake', json=test_email)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Email intake endpoint responded successfully!")
            print(f"Response keys: {list(data.keys())}")
            
            # Check if it mentions work item creation
            if 'work_item_id' in data:
                print("✅ ENHANCED VERSION: Work item created!")
                print(f"Work Item ID: {data['work_item_id']}")
                print(f"Submission ID: {data.get('submission_id')}")
                return True
            else:
                print("❌ OLD VERSION: No work item created")
                print("This means the enhanced code is not deployed")
                return False
        else:
            print(f"❌ Email intake failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email intake: {e}")
        return False

def check_deployment_verification():
    """Check various indicators of deployment status"""
    
    base_url = 'https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net'
    
    print("\n🔍 Deployment Verification Checks")
    print("=" * 60)
    
    # Check if enhanced endpoints exist
    enhanced_endpoints = [
        '/api/debug/create-missing-work-items',
        '/api/debug/submissions'
    ]
    
    enhanced_count = 0
    for endpoint in enhanced_endpoints:
        try:
            response = requests.get(f'{base_url}{endpoint}')
            if response.status_code != 404:
                enhanced_count += 1
                print(f"✅ {endpoint}: Available ({response.status_code})")
            else:
                print(f"❌ {endpoint}: Not found (404)")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {str(e)[:50]}")
    
    deployment_score = (enhanced_count / len(enhanced_endpoints)) * 100
    print(f"\n📊 Deployment Score: {deployment_score:.0f}% of enhanced endpoints available")
    
    if deployment_score < 50:
        print("❌ Enhanced code appears to be NOT FULLY DEPLOYED")
    elif deployment_score < 100:
        print("⚠️  Enhanced code appears to be PARTIALLY DEPLOYED")
    else:
        print("✅ Enhanced code appears to be FULLY DEPLOYED")
    
    return deployment_score

def main():
    """Main test function"""
    print("Enhanced Email Intake Deployment Test")
    print("This will test if the new code is properly deployed\n")
    
    # Check deployment indicators
    deployment_score = check_deployment_verification()
    
    # Test email intake functionality
    intake_working = test_enhanced_email_intake()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if intake_working:
        print("✅ Enhanced email intake IS WORKING")
        print("   - Work items are being created automatically")
        print("   - Email intake and poll API should be aligned")
    else:
        print("❌ Enhanced email intake NOT WORKING")
        print("   - Submissions created but no work items")
        print("   - This explains the email intake/poll API misalignment")
        print("   - Production deployment may have failed or be incomplete")
    
    print(f"\n🎯 DEPLOYMENT STATUS: {deployment_score:.0f}% Complete")
    
    if deployment_score < 100:
        print("\n💡 NEXT STEPS:")
        print("1. Check Azure App Service deployment logs")
        print("2. Manually trigger deployment if needed")
        print("3. Verify all files were deployed correctly")
        print("4. Check for any deployment conflicts or errors")

if __name__ == "__main__":
    main()