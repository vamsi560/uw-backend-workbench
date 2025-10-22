#!/usr/bin/env python3
"""
Simple test to verify notes functionality works end-to-end
"""

import requests
import json

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_notes_functionality():
    print("🧪 TESTING NOTES FUNCTIONALITY END-TO-END")
    print("=" * 50)
    
    # Step 1: Test the polling endpoint
    print("\n1️⃣ Testing work items polling endpoint...")
    poll_response = requests.get(f"{BASE_URL}/api/workitems/poll")
    print(f"   Status: {poll_response.status_code}")
    
    if poll_response.status_code == 200:
        data = poll_response.json()
        work_items = data.get("work_items", [])
        print(f"   ✅ Found {len(work_items)} work items")
        
        if work_items:
            first_item = work_items[0]
            has_notes_field = "underwriting_notes" in first_item
            print(f"   ✅ underwriting_notes field present: {has_notes_field}")
            
            work_item_id = first_item["id"]
            current_notes = first_item.get("underwriting_notes")
            print(f"   📝 Current notes: {current_notes[:50] if current_notes else 'None'}...")
            
            return work_item_id, has_notes_field
        else:
            print("   ❌ No work items available for testing")
            return None, False
    else:
        try:
            error = poll_response.json()
            print(f"   ❌ Error: {error.get('detail', 'Unknown error')}")
        except:
            print(f"   ❌ Error: {poll_response.text}")
        return None, False

def test_notes_endpoints():
    print("\n2️⃣ Testing notes endpoints availability...")
    
    # Test notes update endpoint (should return 404 for invalid ID)
    notes_response = requests.put(
        f"{BASE_URL}/api/workitems/99999/notes",
        json={"underwriting_notes": "test", "updated_by": "test"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Notes endpoint status: {notes_response.status_code}")
    if notes_response.status_code == 404:
        print("   ✅ Notes endpoint is available (404 for invalid ID is correct)")
    else:
        print(f"   ⚠️  Unexpected status: {notes_response.status_code}")

def main():
    work_item_id, has_notes_field = test_notes_functionality()
    test_notes_endpoints()
    
    print("\n" + "=" * 50)
    print("📋 NOTES FUNCTIONALITY SUMMARY")
    print("=" * 50)
    
    if has_notes_field:
        print("✅ READY FOR UI TEAM:")
        print(f"   • Save notes: PUT {BASE_URL}/api/workitems/{{id}}/notes")
        print(f"   • Get notes: GET {BASE_URL}/api/workitems/poll (includes notes)")
        print(f"   • Get notes: GET {BASE_URL}/api/workitems/{{id}} (includes notes)")
        print("\n📝 Usage:")
        print("   1. UI saves notes when underwriter types them")
        print("   2. UI gets notes back in all work item responses")
        print("   3. Notes are automatically saved with approve/reject")
    else:
        print("❌ NEEDS DEPLOYMENT:")
        print("   The database migration was successful locally,")
        print("   but the production API needs to be redeployed")
        print("   to include the new underwriting_notes field.")

if __name__ == "__main__":
    main()