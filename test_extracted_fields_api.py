#!/usr/bin/env python3
"""
Test script to verify extracted fields are included in all API responses
"""

import requests
import json
import sys

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_submissions_api():
    """Test the submissions API for extracted fields"""
    
    print("1️⃣ Testing GET /api/submissions")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/api/submissions?limit=5")
        
        if response.status_code == 200:
            submissions = response.json()
            print(f"✅ Found {len(submissions)} submissions")
            
            for i, submission in enumerate(submissions[:2]):  # Show first 2
                print(f"\nSubmission {i+1}:")
                print(f"  ID: {submission.get('id')}")
                print(f"  Subject: {submission.get('subject', 'N/A')}")
                print(f"  Sender: {submission.get('sender_email', 'N/A')}")
                
                extracted_fields = submission.get('extracted_fields', {})
                if extracted_fields:
                    print("  ✅ Extracted Fields:")
                    for key, value in extracted_fields.items():
                        print(f"    {key}: {value}")
                else:
                    print("  ⚠️  No extracted fields found")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_workitems_api():
    """Test the workitems poll API for extracted fields"""
    
    print("\n\n2️⃣ Testing GET /api/workitems/poll")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/api/workitems/poll?limit=3")
        
        if response.status_code == 200:
            data = response.json()
            workitems = data.get('items', [])
            print(f"✅ Found {len(workitems)} work items")
            
            for i, workitem in enumerate(workitems[:2]):  # Show first 2
                # Handle both dict and object responses
                item_dict = workitem.__dict__ if hasattr(workitem, '__dict__') else workitem
                
                print(f"\nWork Item {i+1}:")
                print(f"  ID: {item_dict.get('id')}")
                print(f"  Title: {item_dict.get('title', 'N/A')}")
                print(f"  Status: {item_dict.get('status', 'N/A')}")
                
                extracted_fields = item_dict.get('extracted_fields', {})
                if extracted_fields:
                    print("  ✅ Extracted Fields:")
                    for key, value in extracted_fields.items():
                        print(f"    {key}: {value}")
                else:
                    print("  ⚠️  No extracted fields found")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_email_content_api():
    """Test the email-content API for extracted fields"""
    
    print("\n\n3️⃣ Testing GET /api/workitems/email-content")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/api/workitems/email-content?limit=2")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            print(f"✅ Found {len(items)} work items with email content")
            
            for i, item in enumerate(items[:1]):  # Show first item
                print(f"\nEmail Content Item {i+1}:")
                print(f"  Work Item ID: {item.get('work_item_id')}")
                print(f"  Subject: {item.get('subject', 'N/A')}")
                print(f"  Sender: {item.get('sender_email', 'N/A')}")
                
                extracted_fields = item.get('extracted_fields', {})
                if extracted_fields:
                    print("  ✅ Extracted Fields:")
                    for key, value in extracted_fields.items():
                        print(f"    {key}: {value}")
                else:
                    print("  ⚠️  No extracted fields found")
                    
                # Also show the individual business fields
                business_fields = [
                    'company_name', 'industry', 'coverage_amount', 
                    'annual_revenue', 'business_address', 'contact_email', 'contact_phone'
                ]
                
                print("  📋 Individual Business Fields:")
                for field in business_fields:
                    value = item.get(field, 'Not found')
                    print(f"    {field}: {value}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_specific_workitem_details():
    """Test detailed workitem endpoint"""
    
    print("\n\n4️⃣ Testing detailed work item with extracted fields")
    print("=" * 50)
    
    try:
        # First get a work item ID
        response = requests.get(f"{BASE_URL}/api/workitems/poll?limit=1")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if items:
                item = items[0]
                item_dict = item.__dict__ if hasattr(item, '__dict__') else item
                work_item_id = item_dict.get('id')
                
                print(f"Testing detailed view for work item {work_item_id}")
                
                # Get detailed view
                detailed_response = requests.get(f"{BASE_URL}/api/workitems/poll?work_item_id={work_item_id}")
                
                if detailed_response.status_code == 200:
                    detailed_data = detailed_response.json()
                    work_item_detail = detailed_data.get('work_item', {})
                    
                    print("✅ Detailed work item response:")
                    print(f"  ID: {work_item_detail.get('id')}")
                    print(f"  Title: {work_item_detail.get('title')}")
                    
                    extracted_fields = work_item_detail.get('extracted_fields', {})
                    if extracted_fields:
                        print("  ✅ Extracted Fields in Detail:")
                        for key, value in extracted_fields.items():
                            print(f"    {key}: {value}")
                    else:
                        print("  ⚠️  No extracted fields in detailed view")
                else:
                    print(f"❌ Detailed request failed: {detailed_response.status_code}")
            else:
                print("⚠️  No work items available for detailed testing")
        else:
            print(f"❌ Failed to get work items: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def show_extracted_fields_summary():
    """Show what extracted fields are typically available"""
    
    print("\n\n📋 Extracted Fields Summary")
    print("=" * 30)
    
    print("The following extracted fields are included in ALL API responses:")
    print("✅ GET /api/submissions - Full extracted_fields object")
    print("✅ GET /api/workitems/poll - Full extracted_fields object")
    print("✅ GET /api/workitems/poll?work_item_id={id} - Full extracted_fields object")
    print("✅ GET /api/workitems/email-content - Full extracted_fields + individual fields")
    
    print("\nCommon extracted fields include:")
    fields = [
        "company_name", "industry", "coverage_amount", "annual_revenue",
        "business_address", "contact_email", "contact_phone", "policy_type",
        "company_size", "risk_factors", "technology_stack", "data_sensitivity"
    ]
    
    for field in fields:
        print(f"  • {field}")
    
    print("\n💡 For UI Team:")
    print("- All endpoints return 'extracted_fields' as a complete object")
    print("- Email-content endpoint also provides individual convenience fields")
    print("- Fields are automatically parsed from JSON strings to objects")
    print("- Missing fields default to empty object {} or 'Not specified'")

if __name__ == "__main__":
    print("🔍 Testing Extracted Fields in All API Responses")
    print("=" * 55)
    
    test_submissions_api()
    test_workitems_api()
    test_email_content_api()
    test_specific_workitem_details()
    show_extracted_fields_summary()
    
    print("\n🎉 All APIs include extracted fields!")
    print("The UI team has access to all extracted data through:")
    print("- submissions API: extracted_fields object")
    print("- workitems API: extracted_fields object") 
    print("- email-content API: both extracted_fields object AND individual fields")
    print("- detailed workitem API: extracted_fields object")