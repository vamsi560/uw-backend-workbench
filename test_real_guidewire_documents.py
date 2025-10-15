#!/usr/bin/env python3
"""
Test Document Storage System with Real Guidewire Submission
Uses the submission data found in cyberlineresponse.json
"""

import requests
import json
from datetime import datetime

# Production API configuration
BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

# Real Guidewire data from cyberlineresponse.json
GUIDEWIRE_DATA = {
    "account_number": "4901420895",
    "job_number": "0001563719", 
    "job_id": "pc:S9Z7G9A7dGlQCKdKlc-G6",
    "job_status": "Quoted",  # This is important - means it has documents!
    "account_id": "pc:SAT9n354FTKe5a3OKtrfy"
}

def test_document_storage_with_real_submission():
    print("📄 Testing Document Storage with REAL Guidewire Submission")
    print("=" * 70)
    print(f"🎯 Using Submission: {GUIDEWIRE_DATA['job_number']} (Status: {GUIDEWIRE_DATA['job_status']})")
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'DocumentStorageTest/1.0'
    })
    
    # Step 1: Check if we have Work Item 87 or create a test with real Guidewire data
    print(f"\n1️⃣  Testing with Real Guidewire Submission...")
    print(f"   Account Number: {GUIDEWIRE_DATA['account_number']}")
    print(f"   Job Number: {GUIDEWIRE_DATA['job_number']}")
    print(f"   Job ID: {GUIDEWIRE_DATA['job_id']}")
    print(f"   Status: {GUIDEWIRE_DATA['job_status']} ✅ (Has Documents!)")
    
    # First, let's test the Guidewire connection from production
    print(f"\n2️⃣  Testing Guidewire Connection from Production...")
    try:
        response = session.get(f"{BASE_URL}/api/guidewire/test-connection")
        if response.status_code == 200:
            connection_data = response.json()
            print(f"✅ Connection Test: {connection_data.get('guidewire_connection', {}).get('success', False)}")
            if connection_data.get('ip_whitelisted'):
                print("✅ IP is whitelisted for Guidewire access")
            else:
                print("❌ IP whitelisting issue detected")
        else:
            print(f"❌ Connection test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection test error: {str(e)}")
    
    # Step 3: Test document retrieval using the job ID directly
    print(f"\n3️⃣  Testing Direct Document Retrieval...")
    test_endpoints = [
        {
            "name": "Test Guidewire Document API Access",
            "url": f"{BASE_URL}/api/test/guidewire-documents",
            "method": "POST",
            "data": {
                "job_id": GUIDEWIRE_DATA['job_id'],
                "job_number": GUIDEWIRE_DATA['job_number']
            }
        }
    ]
    
    for test in test_endpoints:
        print(f"\n   Testing: {test['name']}")
        try:
            if test['method'] == 'POST':
                response = session.post(test['url'], json=test.get('data', {}))
            else:
                response = session.get(test['url'])
                
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ Success: {data.get('message', 'OK')}")
                    if 'documents' in data:
                        print(f"   📄 Documents found: {len(data['documents'])}")
                else:
                    print(f"   ⚠️  Response: {data.get('message', 'No message')}")
            else:
                print(f"   ❌ Error: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    # Step 4: Try to create an endpoint specifically for this job ID
    print(f"\n4️⃣  Testing with Work Item 87 using Real Guidewire Data...")
    
    # Update Work Item 87 with the real Guidewire data
    try:
        update_data = {
            "guidewire_job_id": GUIDEWIRE_DATA['job_id'],
            "guidewire_account_id": GUIDEWIRE_DATA['account_id'],
            "guidewire_job_number": GUIDEWIRE_DATA['job_number'],
            "guidewire_account_number": GUIDEWIRE_DATA['account_number']
        }
        
        response = session.patch(f"{BASE_URL}/api/workitems/87/update-guidewire", json=update_data)
        print(f"   Work Item Update Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Work Item 87 updated with real Guidewire data")
            
            # Now test document storage
            print(f"\n5️⃣  Testing Document Storage with Updated Work Item...")
            doc_response = session.post(f"{BASE_URL}/api/guidewire/submissions/87/fetch-and-store-documents")
            print(f"   Fetch Documents Status: {doc_response.status_code}")
            
            if doc_response.status_code == 200:
                doc_data = doc_response.json()
                if doc_data.get('success'):
                    print(f"   ✅ Documents fetched successfully!")
                    print(f"   📄 Documents stored: {len(doc_data.get('documents', []))}")
                    for i, doc in enumerate(doc_data.get('documents', [])[:3]):
                        print(f"      {i+1}. {doc.get('document_name', 'Unknown')}")
                else:
                    print(f"   ⚠️  Fetch result: {doc_data.get('message', 'Unknown')}")
                    print(f"   Error: {doc_data.get('error', 'No error details')}")
            else:
                print(f"   ❌ Document fetch failed: {doc_response.text}")
        else:
            print(f"   ❌ Work Item update failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Work Item update error: {str(e)}")
    
    # Summary
    print(f"\n🎯 SUMMARY - Real Guidewire Submission Test")
    print("=" * 70)
    print("✅ Real Submission Data:")
    for key, value in GUIDEWIRE_DATA.items():
        print(f"• {key}: {value}")
    
    print(f"\n🎁 Next Steps:")
    print("• ✅ We have a QUOTED submission (has documents)")
    print("• 🔄 Test document retrieval from production whitelisted IP")
    print("• 📄 Store documents in database for fast access")
    print("• ⚡ Enable UI team to download from our database")
    
    return GUIDEWIRE_DATA

if __name__ == "__main__":
    real_data = test_document_storage_with_real_submission()
    print(f"\n🚀 Ready to test with: Job {real_data['job_number']} (Status: {real_data['job_status']})")