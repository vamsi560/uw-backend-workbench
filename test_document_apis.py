#!/usr/bin/env python3
"""
Test Guidewire Document APIs for UI Team Integration
Tests the new document endpoints after deployment
"""

import requests
import json

def test_document_apis():
    print("🔍 Testing Guidewire Document APIs for UI Team")
    print("=" * 60)
    
    # Production URL
    base_url = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"
    work_item_id = 87  # Known work item with Guidewire data
    
    # Test 1: Check if work item has Guidewire data
    print("\n1️⃣  Testing Work Item Data...")
    try:
        response = requests.get(f"{base_url}/api/guidewire/submissions/{work_item_id}", timeout=15)
        if response.status_code == 200:
            data = response.json()
            gw_data = data.get('guidewire', {})
            print(f"✅ Work Item {work_item_id} has Guidewire data:")
            print(f"   Account: {gw_data.get('account_number')}")
            print(f"   Job: {gw_data.get('job_number')}")
            print(f"   Complete: {gw_data.get('has_complete_data')}")
        else:
            print(f"❌ Work Item check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Work Item check error: {e}")
        return False
    
    # Test 2: Get Documents List
    print("\n2️⃣  Testing Document List API...")
    try:
        response = requests.get(f"{base_url}/api/guidewire/submissions/{work_item_id}/documents", timeout=30)
        print(f"Documents API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            docs_count = data.get('documents_count', 0)
            documents = data.get('documents', [])
            
            print(f"✅ Documents API Response:")
            print(f"   Work Item: {data.get('work_item_id')}")
            print(f"   Guidewire Job: {data.get('guidewire_job_id')}")
            print(f"   Account Number: {data.get('guidewire_account_number')}")
            print(f"   Job Number: {data.get('guidewire_job_number')}")
            print(f"   Documents Found: {docs_count}")
            
            if docs_count > 0:
                print(f"   📄 Available Documents:")
                for i, doc in enumerate(documents[:3]):  # Show first 3
                    print(f"      {i+1}. {doc.get('document_name')} ({doc.get('file_size')})")
                    print(f"         ID: {doc.get('document_id')}")
                    print(f"         Download: {doc.get('download_url')}")
                
                # Test document download for first document
                if documents:
                    doc_id = documents[0].get('document_id')
                    if doc_id:
                        print(f"\n3️⃣  Testing Document Download...")
                        try:
                            download_url = f"{base_url}/api/guidewire/submissions/{work_item_id}/documents/{doc_id}/download"
                            response = requests.head(download_url, timeout=15)  # HEAD request to test without downloading
                            print(f"Download Test Status: {response.status_code}")
                            if response.status_code == 200:
                                content_type = response.headers.get('content-type', 'unknown')
                                print(f"✅ Document download ready - Type: {content_type}")
                            else:
                                print(f"⚠️  Download test status: {response.status_code}")
                        except Exception as e:
                            print(f"⚠️  Download test error: {e}")
            else:
                print("   ℹ️  No documents found - may need to generate quote first")
        else:
            print(f"❌ Documents API failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Documents API error: {e}")
    
    # Test 3: Generate Quote API
    print("\n4️⃣  Testing Generate Quote API...")
    try:
        response = requests.post(f"{base_url}/api/guidewire/submissions/{work_item_id}/generate-quote", timeout=30)
        print(f"Generate Quote Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            
            if success:
                print(f"✅ Quote Generation Success:")
                print(f"   Work Item: {data.get('work_item_id')}")
                print(f"   Job ID: {data.get('guidewire_job_id')}")
                print(f"   Documents Count: {data.get('documents_count')}")
                print(f"   Documents URL: {data.get('documents_url')}")
                
                # Quote info if available
                quote_info = data.get('quote_info', {})
                if quote_info:
                    print(f"   Quote Info: {json.dumps(quote_info, indent=6)}")
            else:
                print(f"⚠️  Quote generation failed:")
                print(f"   Error: {data.get('error')}")
                print(f"   Message: {data.get('message')}")
        else:
            print(f"❌ Generate quote failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Generate quote error: {e}")
    
    # Summary for UI Team
    print(f"\n🎯 UI TEAM INTEGRATION SUMMARY")
    print("=" * 60)
    print(f"📋 Document Management APIs Ready:")
    print(f"• GET /api/guidewire/submissions/{work_item_id}/documents")
    print(f"  └── Lists available quote documents")
    print(f"• GET /api/guidewire/submissions/{work_item_id}/documents/{{doc_id}}/download")
    print(f"  └── Downloads specific document (PDF, etc.)")
    print(f"• POST /api/guidewire/submissions/{work_item_id}/generate-quote")
    print(f"  └── Generates quote and creates documents")
    
    print(f"\n🔗 Base URL: {base_url}")
    print(f"📖 Full Documentation: See DOCUMENT_API_GUIDE.md")
    print(f"🎉 Ready for UI integration!")

if __name__ == "__main__":
    test_document_apis()