#!/usr/bin/env python3
"""
Parse and display the API response
"""

import json

response_json = '{"success":false,"work_item_id":77,"error":"Submission creation failed","message":"Submission creation failed: ","details":{"success":false,"error":"Submission creation failed","message":"Submission creation failed: ","step_failed":"submission_creation","account_id":"pc:SNletr6mHRyeDnhgpuPE-","account_number":"2332505940","organization_name":"Test Company Inc 416413"}}'

try:
    data = json.loads(response_json)
    
    print("🎯 GUIDEWIRE API RESPONSE ANALYSIS")
    print("=" * 50)
    
    print(f"Overall Success: {data.get('success')}")
    print(f"Work Item ID: {data.get('work_item_id')}")
    print(f"Error: {data.get('error')}")
    print()
    
    details = data.get('details', {})
    print("📋 DETAILED RESULTS:")
    print(f"Step Failed: {details.get('step_failed')}")
    print()
    
    print("✅ ACCOUNT CREATION (STEP 1) - SUCCESS!")
    print(f"   Account ID: {details.get('account_id')}")
    print(f"   Account Number: {details.get('account_number')}")
    print(f"   Organization: {details.get('organization_name')}")
    print()
    
    print("❌ SUBMISSION CREATION (STEP 2) - FAILED!")
    print(f"   Error: {details.get('error')}")
    print(f"   Message: {details.get('message')}")
    print()
    
    print("🎯 SEARCH IN GUIDEWIRE POLICYCENTER:")
    print("=" * 40)
    print(f"✅ Account Number: {details.get('account_number')}")
    print(f"✅ Organization: {details.get('organization_name')}")
    print("⚠️  Submission: Not created (Step 2 failed)")
    
except Exception as e:
    print(f"Error parsing: {e}")