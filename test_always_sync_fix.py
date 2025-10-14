#!/usr/bin/env python3
"""
Test the ALWAYS SYNC fix - no conditions, always create Guidewire accounts
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_always_sync_fix():
    """Test if removing conditions makes auto-sync work"""
    
    print("🚀 TESTING ALWAYS SYNC FIX")
    print("No conditions - should ALWAYS create Guidewire accounts!")
    print("="*80)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Test with perfect email
    test_email = {
        "subject": f"ALWAYS SYNC TEST {timestamp}",
        "sender_email": f"alwayssync{timestamp}@test.com",
        "body": f"""
Company Name: Always Sync Test Company
Industry: Technology  
Policy Type: Cyber Liability
Coverage: 1000000
Effective Date: 2025-01-01

Testing the always sync fix - should work every time now!
        """,
        "attachments": []
    }
    
    print(f"📧 Sending test email...")
    response = requests.post(f"{BASE_URL}/api/email/intake", json=test_email, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        message = data.get('message', '')
        print(f"✅ Response: {message}")
        
        if 'guidewire' in message.lower() or 'policycenter' in message.lower():
            print(f"🎉 SUCCESS! Auto-sync is now working!")
            return True
        else:
            print(f"⚠️  No Guidewire mention - checking if it's still processing...")
            return False
    else:
        print(f"❌ Email failed: HTTP {response.status_code}")
        return False

def main():
    print("🔧 TESTING ALWAYS SYNC FIX")
    print("Removed all validation conditions!")
    print("="*60)
    
    success = test_always_sync_fix()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 SUCCESS! Always sync fix is working!")
        print("📧 Emails now automatically create Guidewire accounts!")
    else:
        print("⚠️  Fix may need deployment time or there are other issues")

if __name__ == "__main__":
    main()