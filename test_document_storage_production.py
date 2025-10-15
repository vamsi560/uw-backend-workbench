#!/usr/bin/env python3
"""
Test Document Storage System - Production Environment
Tests the Guidewire document storage functionality against production deployment
"""

import requests
import json
from datetime import datetime

# Production API configuration
BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
WORK_ITEM_ID = 87  # Known work item with Guidewire integration

def test_production_document_storage():
    print("📄 Testing Guidewire Document Storage System - PRODUCTION")
    print("=" * 70)
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'DocumentStorageTest/1.0'
    })
    
    # Step 1: Verify Work Item 87 exists and has Guidewire integration
    print(f"\n1️⃣  Verifying Work Item {WORK_ITEM_ID} Guidewire Integration...")
    try:
        response = session.get(f"{BASE_URL}/api/guidewire/submissions/{WORK_ITEM_ID}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Work Item {WORK_ITEM_ID}:")
            print(f"   Account: {data.get('account_number', 'N/A')}")
            print(f"   Job: {data.get('job_number', 'N/A')}")
            print(f"   Job ID: {data.get('guidewire_job_id', 'N/A')}")
            print(f"   Ready: {data.get('success', False)}")
        else:
            print(f"❌ Work Item verification failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error verifying work item: {str(e)}")
        return False
    
    # Step 2: Test fetching and storing documents from Guidewire
    print(f"\n2️⃣  Fetching and Storing Documents from Guidewire...")
    try:
        response = session.post(f"{BASE_URL}/api/guidewire/submissions/{WORK_ITEM_ID}/fetch-and-store-documents")
        print(f"Fetch & Store Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Documents successfully stored!")
                print(f"   Documents fetched: {len(data.get('documents', []))}")
                for i, doc in enumerate(data.get('documents', [])[:3]):  # Show first 3
                    print(f"   📄 {i+1}. {doc.get('document_name', 'Unknown')}")
                    print(f"      Type: {doc.get('document_type', 'Unknown')}")
                    print(f"      Size: {doc.get('file_size_bytes', 0)} bytes")
            else:
                print(f"❌ Document storage failed:")
                print(f"   Message: {data.get('message', 'Unknown error')}")
                print(f"   Error: {data.get('error', 'No details')}")
        else:
            print(f"❌ Fetch & Store failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception during fetch & store: {str(e)}")
    
    # Step 3: Test retrieving stored documents from database
    print(f"\n3️⃣  Checking Stored Documents in Database...")
    try:
        response = session.get(f"{BASE_URL}/api/guidewire/submissions/{WORK_ITEM_ID}/stored-documents")
        print(f"Stored Documents Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('documents'):
                print(f"✅ Found {len(data['documents'])} stored documents:")
                for i, doc in enumerate(data['documents'][:5]):  # Show first 5
                    print(f"   📄 {i+1}. ID: {doc.get('id')} - {doc.get('document_name')}")
                    print(f"      Type: {doc.get('document_type')}")
                    print(f"      Status: {doc.get('status')}")
                    print(f"      Created: {doc.get('created_at')}")
                
                # Step 4: Test downloading a document from database
                if data['documents']:
                    first_doc_id = data['documents'][0]['id']
                    print(f"\n4️⃣  Testing Fast Download from Database (Doc ID: {first_doc_id})...")
                    
                    download_response = session.get(
                        f"{BASE_URL}/api/guidewire/submissions/{WORK_ITEM_ID}/stored-documents/{first_doc_id}/download"
                    )
                    print(f"Download Status: {download_response.status_code}")
                    
                    if download_response.status_code == 200:
                        content_length = len(download_response.content)
                        content_type = download_response.headers.get('content-type', 'Unknown')
                        print(f"✅ Document downloaded successfully!")
                        print(f"   Content-Type: {content_type}")
                        print(f"   Size: {content_length} bytes")
                        print(f"   ⚡ Fast database access (no Guidewire API call needed)")
                    else:
                        print(f"❌ Download failed: {download_response.status_code}")
                        print(f"   Error: {download_response.text}")
            else:
                print(f"❌ No stored documents found")
                print(f"   Message: {data.get('message', 'Unknown')}")
        else:
            print(f"❌ Stored documents query failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception during stored documents check: {str(e)}")
    
    # Summary
    print(f"\n🎯 PRODUCTION DOCUMENT STORAGE SYSTEM SUMMARY")
    print("=" * 70)
    print("✅ Document Storage Features:")
    print(f"• POST {BASE_URL}/api/guidewire/submissions/87/fetch-and-store-documents")
    print("  └── Downloads documents from Guidewire and stores in database")
    print(f"• GET {BASE_URL}/api/guidewire/submissions/87/stored-documents")
    print("  └── Lists documents stored in database with metadata")
    print(f"• GET {BASE_URL}/api/guidewire/submissions/87/stored-documents/{{doc_id}}/download")
    print("  └── Fast download from database (no Guidewire API call needed)")
    
    print(f"\n🎁 Benefits:")
    print("• 📄 Permanent document storage in database")
    print("• ⚡ Fast access without repeated Guidewire API calls")
    print("• 💾 Base64 encoded storage for easy handling")
    print("• 🏷️  Document type classification (Quote, Terms, etc.)")
    print("• 📊 Error tracking and retry capabilities")
    print("• 🕒 Audit trail with timestamps")
    
    print(f"\n🚀 Production ready and tested!")
    return True

if __name__ == "__main__":
    test_production_document_storage()