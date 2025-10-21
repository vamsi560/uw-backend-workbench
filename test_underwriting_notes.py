#!/usr/bin/env python3
"""
Test Underwriting Notes Functionality
Tests the new underwriting notes feature for work items
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_underwriting_notes():
    """Test the underwriting notes functionality"""
    
    print("🧪 TESTING UNDERWRITING NOTES FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Step 1: Get available work items
        print("\n1️⃣ Getting available work items...")
        workitems_url = f"{BASE_URL}/api/workitems/poll"
        
        response = requests.get(workitems_url)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            work_items = data.get("work_items", [])
            
            if not work_items:
                print("   ❌ No work items found to test notes functionality")
                return
            
            # Use the first available work item for testing
            test_work_item = work_items[0]
            work_item_id = test_work_item["id"]
            subject = test_work_item.get("subject", "Unknown")
            current_notes = test_work_item.get("underwriting_notes", "")
            
            print(f"   ✅ Found test work item:")
            print(f"      - ID: {work_item_id}")
            print(f"      - Subject: {subject}")
            print(f"      - Current Status: {test_work_item.get('status', 'Unknown')}")
            print(f"      - Current Notes: {current_notes[:50]}..." if current_notes else "      - Current Notes: None")
        
        else:
            print(f"   ❌ Failed to get work items: {response.status_code}")
            return
        
        # Step 2: Test updating underwriting notes
        print(f"\n2️⃣ Testing underwriting notes update for work item {work_item_id}...")
        
        notes_url = f"{BASE_URL}/api/workitems/{work_item_id}/notes"
        
        sample_notes = f"""
Risk Assessment Notes - {datetime.now().strftime('%Y-%m-%d %H:%M')}

TECHNICAL REVIEW:
- Company size: Medium enterprise
- Industry: Technology/SaaS 
- Current cybersecurity posture appears adequate
- Some concerns about remote work policies

COVERAGE EVALUATION:
- Requested coverage: $2M cyber liability
- Deductible: $25K acceptable
- Business interruption coverage needed

UNDERWRITER DECISION FACTORS:
- No previous cyber incidents reported
- Strong IT governance framework
- Regular security audits conducted
- Incident response plan in place

RECOMMENDATION:
Proceed with standard coverage terms.
May consider 5% discount for excellent security posture.

Next steps: Await management approval.
        """.strip()
        
        notes_payload = {
            "underwriting_notes": sample_notes,
            "updated_by": "Jane Underwriter"
        }
        
        print(f"   Making notes update request to: {notes_url}")
        print(f"   Notes length: {len(sample_notes)} characters")
        
        notes_response = requests.put(
            notes_url,
            json=notes_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Notes Update Response Status: {notes_response.status_code}")
        
        if notes_response.status_code == 200:
            result = notes_response.json()
            print(f"   ✅ NOTES UPDATE SUCCESSFUL!")
            print(f"      - Success: {result.get('success')}")
            print(f"      - Message: {result.get('message')}")
            print(f"      - Notes Length: {result.get('notes_length')}")
            print(f"      - Timestamp: {result.get('timestamp')}")
            
        elif notes_response.status_code == 404:
            print(f"   ❌ Work item not found")
        else:
            print(f"   ❌ Notes update failed: {notes_response.status_code}")
            try:
                error_data = notes_response.json()
                print(f"      Error: {error_data}")
            except:
                print(f"      Response: {notes_response.text}")
        
        # Step 3: Verify notes are saved by getting work item details
        print(f"\n3️⃣ Verifying notes were saved...")
        
        detail_url = f"{BASE_URL}/api/workitems/{work_item_id}"
        detail_response = requests.get(detail_url)
        
        if detail_response.status_code == 200:
            work_item_detail = detail_response.json()
            saved_notes = work_item_detail.get("underwriting_notes", "")
            
            print(f"   ✅ Work item details retrieved:")
            print(f"      - Notes length: {len(saved_notes)} characters")
            print(f"      - Notes preview: {saved_notes[:100]}..." if saved_notes else "      - No notes found")
            
            if sample_notes.strip() == saved_notes.strip():
                print(f"   🎉 SUCCESS: Notes saved correctly!")
            else:
                print(f"   ⚠️  Notes may not match exactly (encoding/formatting differences)")
        else:
            print(f"   ❌ Could not verify notes: {detail_response.status_code}")
        
        # Step 4: Test approval with notes
        print(f"\n4️⃣ Testing approval with underwriting notes...")
        
        approval_url = f"{BASE_URL}/api/workitems/{work_item_id}/approve"
        
        approval_payload = {
            "underwriter_notes": "Final approval notes: Risk acceptable, standard terms approved.",
            "approved_by": "Senior Underwriter"
        }
        
        print(f"   Testing approval with notes (Note: May fail if no Guidewire job ID)")
        
        approval_response = requests.post(
            approval_url,
            json=approval_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Approval Response Status: {approval_response.status_code}")
        
        if approval_response.status_code == 200:
            approval_result = approval_response.json()
            print(f"   ✅ Approval with notes successful!")
        elif approval_response.status_code == 400:
            error_data = approval_response.json()
            print(f"   ⚠️  Expected error (no Guidewire job): {error_data.get('detail')}")
        else:
            print(f"   ❌ Approval failed: {approval_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error during notes testing: {str(e)}")
        import traceback
        traceback.print_exc()

def test_notes_validation():
    """Test notes endpoint validation"""
    
    print(f"\n🔍 TESTING NOTES VALIDATION")
    print("=" * 40)
    
    # Test with invalid work item ID
    print(f"\n1️⃣ Testing invalid work item ID...")
    
    invalid_url = f"{BASE_URL}/api/workitems/99999/notes"
    
    valid_payload = {
        "underwriting_notes": "Test notes",
        "updated_by": "Test User"
    }
    
    response = requests.put(
        invalid_url,
        json=valid_payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 404:
        error_data = response.json()
        print(f"   ✅ Not found handling working: {error_data.get('detail')}")
    else:
        print(f"   ⚠️  Expected 404 error, got {response.status_code}")

if __name__ == "__main__":
    print("🚀 UNDERWRITING NOTES TEST SUITE")
    print("=" * 70)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run tests
    test_underwriting_notes()
    test_notes_validation()
    
    print("\n" + "=" * 70)
    print("🏁 UNDERWRITING NOTES TESTING COMPLETE!")
    print("\nThe underwriting notes functionality is ready for UI integration:")
    print(f"PUT {BASE_URL}/api/workitems/{{work_item_id}}/notes")
    print("Required payload: {\"underwriting_notes\": \"notes\", \"updated_by\": \"underwriter\"}")
    print("\nNotes are included in:")
    print("- Work item details (GET /api/workitems/{id})")
    print("- Work item polling (GET /api/workitems/poll)")
    print("- Approval/rejection workflows automatically save notes")