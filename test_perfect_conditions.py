#!/usr/bin/env python3
"""
Test the exact auto-sync condition with perfect data
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_perfect_conditions():
    """Send an email that should definitely trigger auto-sync"""
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Create an email with perfect conditions that match business validation exactly
    perfect_email = {
        "subject": f"PERFECT AUTO-SYNC TEST {timestamp}",
        "sender_email": f"perfect{timestamp}@test.com",
        "body": f"""
Company Name: Perfect Test Company Inc
Industry: technology  
Policy Type: Cyber Liability
Effective Date: 2025-01-01
Coverage Amount: 1000000
Contact Name: Perfect Tester
Contact Email: perfect{timestamp}@test.com

We need comprehensive cyber liability insurance.
        """,
        "attachments": []
    }
    
    print(f"🎯 TESTING PERFECT AUTO-SYNC CONDITIONS")
    print(f"="*60)
    print(f"📧 Email designed to pass all validation:")
    print(f"   Company: Perfect Test Company Inc")  
    print(f"   Industry: technology")
    print(f"   Policy Type: Cyber Liability") 
    print(f"   Coverage: 1000000")
    print(f"   Effective Date: 2025-01-01")
    
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake",
                               json=perfect_email,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ EMAIL RESPONSE:")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            
            # Check for Guidewire mention
            message = data.get('message', '')
            if 'guidewire' in message.lower() or 'policycenter' in message.lower():
                print(f"   🎉 SUCCESS: Auto-sync worked!")
                if 'synced to Guidewire PolicyCenter' in message:
                    print(f"   ✅ Perfect success message detected")
                return True
            else:
                print(f"   ❌ Auto-sync failed - no Guidewire mention")
                print(f"   📋 This confirms the server-side condition isn't met")
                return False
                
        else:
            print(f"❌ Email failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_logic_apps_endpoint():
    """Test the Logic Apps endpoint to see if it behaves differently"""
    timestamp = datetime.now().strftime("%H%M%S")
    
    logic_apps_email = {
        "subject": f"LOGIC APPS AUTO-SYNC TEST {timestamp}",
        "sender_email": f"logicapps{timestamp}@test.com",
        "body": f"""
Company Name: Logic Apps Test Company
Industry: technology
Policy Type: Cyber Liability  
Effective Date: 2025-01-01
Coverage Amount: 2000000
Contact Email: logicapps{timestamp}@test.com

Testing Logic Apps endpoint for auto-sync.
        """,
        "attachments": []
    }
    
    print(f"\n🔄 TESTING LOGIC APPS ENDPOINT")
    print(f"="*60)
    
    try:
        response = requests.post(f"{BASE_URL}/api/logicapps/email/intake",
                               json=logic_apps_email,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ LOGIC APPS RESPONSE:")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            message = data.get('message', '')
            if 'guidewire' in message.lower() or 'policycenter' in message.lower():
                print(f"   🎉 Logic Apps auto-sync worked!")
                return True
            else:
                print(f"   ❌ Logic Apps auto-sync also failed")
                return False
                
        else:
            print(f"❌ Logic Apps failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Logic Apps test error: {str(e)}")
        return False

def main():
    print("🎯 TARGETED AUTO-SYNC TESTING")
    print("Testing with perfect conditions to isolate the exact issue")
    print("="*80)
    
    # Test regular endpoint
    regular_worked = test_perfect_conditions()
    
    # Test Logic Apps endpoint  
    logic_apps_worked = test_logic_apps_endpoint()
    
    print(f"\n{'='*80}")
    print("🎯 TARGETED TEST RESULTS")
    print(f"{'='*80}")
    
    if regular_worked:
        print("🎉 REGULAR ENDPOINT: Auto-sync is working!")
    else:
        print("❌ REGULAR ENDPOINT: Auto-sync still not working")
    
    if logic_apps_worked:
        print("🎉 LOGIC APPS ENDPOINT: Auto-sync is working!")
    else:
        print("❌ LOGIC APPS ENDPOINT: Auto-sync also not working")
    
    if not regular_worked and not logic_apps_worked:
        print(f"\n🔍 DIAGNOSIS:")
        print("   Both endpoints failing suggests:")
        print("   1. Server code hasn't been deployed with our fixes")
        print("   2. Exception happening in Guidewire sync block")
        print("   3. Validation condition still not met on server")
        print("   4. Guidewire client throwing exceptions")
        
        print(f"\n💡 IMMEDIATE ACTIONS NEEDED:")
        print("   1. Check server deployment status")
        print("   2. Review server application logs")
        print("   3. Test manual Guidewire API directly")
        print("   4. Verify business validation on server")
    
    else:
        print(f"\n🎉 SUCCESS: Auto-sync is now working!")
        print("   The fixes have been deployed and are active")

if __name__ == "__main__":
    main()