#!/usr/bin/env python3
"""
Test Document Storage System
Fetch and store quote documents from Guidewire into database
"""

import requests
import json
import time

def test_document_storage():
    print("🗂️  Testing Guidewire Document Storage System")
    print("=" * 60)
    
    # Production URL and known work item with Guidewire integration
    base_url = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
    work_item_id = 87  # Known work item with Guidewire data
    
    # Step 1: Verify work item has Guidewire integration
    print(f"\n1️⃣  Verifying Work Item {work_item_id} Guidewire Integration...")
    try:
        response = requests.get(f"{base_url}/api/guidewire/submissions/{work_item_id}", timeout=15)
        if response.status_code == 200:
            data = response.json()
            gw_data = data.get('guidewire', {})
            print(f"✅ Work Item {work_item_id}:")
            print(f"   Account: {gw_data.get('account_number')}")
            print(f"   Job: {gw_data.get('job_number')}")
            print(f"   Job ID: {gw_data.get('job_id')}")
            print(f"   Ready: {gw_data.get('has_complete_data')}")
        else:
            print(f"❌ Work Item verification failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Work Item verification error: {e}")
        return False
    
    # Step 2: Fetch and store documents
    print(f"\n2️⃣  Fetching and Storing Documents from Guidewire...")
    try:
        response = requests.post(
            f"{base_url}/api/guidewire/submissions/{work_item_id}/fetch-and-store-documents", 
            timeout=60  # Longer timeout for document downloads
        )
        
        print(f"Fetch & Store Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print(f"✅ Document Storage Success:")
                print(f"   Documents Processed: {data.get('documents_processed')}")
                print(f"   Documents Stored: {data.get('documents_stored')}")
                print(f"   Errors: {data.get('errors_count')}")
                print(f"   Message: {data.get('message')}")
                
                # Show stored documents
                stored_docs = data.get('stored_documents', [])
                if stored_docs:
                    print(f"\n   📄 Stored Documents:")
                    for i, doc in enumerate(stored_docs[:3]):  # Show first 3
                        print(f"      {i+1}. {doc.get('document_name')}")
                        print(f"         Type: {doc.get('document_type')}")
                        print(f"         Size: {doc.get('file_size')} bytes")
                        print(f"         Status: {doc.get('status')}")
                        print(f"         DB ID: {doc.get('database_id')}")
                
                # Show any errors
                errors = data.get('errors', [])
                if errors:
                    print(f"\n   ❌ Errors encountered:")
                    for error in errors:
                        print(f"      Doc ID {error.get('document_id')}: {error.get('error')}")
                
            else:
                print(f"⚠️  Document storage failed:")
                print(f"   Error: {data.get('error')}")
                print(f"   Message: {data.get('message')}")
        else:
            print(f"❌ Fetch & Store failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Fetch & Store error: {e}")
    
    # Step 3: Check stored documents
    print(f"\n3️⃣  Checking Stored Documents in Database...")
    try:
        response = requests.get(f"{base_url}/api/guidewire/submissions/{work_item_id}/stored-documents", timeout=15)
        
        print(f"Stored Documents Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            docs_count = data.get('documents_count', 0)
            stored_count = data.get('stored_count', 0)
            error_count = data.get('error_count', 0)
            
            print(f"✅ Database Query Success:")
            print(f"   Total Documents: {docs_count}")
            print(f"   Successfully Stored: {stored_count}")
            print(f"   Errors: {error_count}")
            
            documents = data.get('documents', [])
            if documents:
                print(f"\n   📋 Document List:")
                for i, doc in enumerate(documents):
                    print(f"      {i+1}. {doc.get('document_name')}")
                    print(f"         Type: {doc.get('document_type')}")
                    print(f"         Size: {doc.get('file_size')} bytes")
                    print(f"         Status: {doc.get('status')}")
                    print(f"         Download: {doc.get('download_url')}")
                    print(f"         Has Content: {doc.get('has_content')}")
                
                # Test downloading first document
                if documents and documents[0].get('has_content'):
                    print(f"\n4️⃣  Testing Document Download from Database...")
                    first_doc = documents[0]
                    download_url = first_doc.get('download_url')
                    
                    try:
                        response = requests.head(f"{base_url}{download_url}", timeout=10)
                        print(f"Download Test Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', 'unknown')
                            content_length = response.headers.get('content-length', 'unknown')
                            print(f"✅ Document download ready:")
                            print(f"   Content-Type: {content_type}")
                            print(f"   Content-Length: {content_length} bytes")
                        else:
                            print(f"⚠️  Download test status: {response.status_code}")
                            
                    except Exception as e:
                        print(f"❌ Download test error: {e}")
            else:
                print(f"   No documents found in database")
                
        else:
            print(f"❌ Stored documents query failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Stored documents query error: {e}")
    
    # Summary
    print(f"\n🎯 DOCUMENT STORAGE SYSTEM SUMMARY")
    print("=" * 60)
    print(f"✅ Document Storage Features:")
    print(f"• POST /api/guidewire/submissions/{work_item_id}/fetch-and-store-documents")
    print(f"  └── Downloads documents from Guidewire and stores in database")
    print(f"• GET /api/guidewire/submissions/{work_item_id}/stored-documents") 
    print(f"  └── Lists documents stored in database with metadata")
    print(f"• GET /api/guidewire/submissions/{work_item_id}/stored-documents/{{doc_id}}/download")
    print(f"  └── Fast download from database (no Guidewire API call needed)")
    
    print(f"\n🎁 Benefits:")
    print(f"• 📄 Permanent document storage in database")
    print(f"• ⚡ Fast access without repeated Guidewire API calls") 
    print(f"• 💾 Base64 encoded storage for easy handling")
    print(f"• 🏷️  Document type classification (Quote, Terms, etc.)")
    print(f"• 📊 Error tracking and retry capabilities")
    print(f"• 🕒 Audit trail with timestamps")
    
    print(f"\n🚀 Ready for UI integration!")

if __name__ == "__main__":
    test_document_storage()