#!/usr/bin/env python3

import json
import logging
from guidewire_client import guidewire_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_guidewire_result_structure():
    """Test what the Guidewire client returns"""
    
    # Sample data
    extracted_data = {
        "company_name": "Result Test Corp",
        "contact_person": "Test User",
        "email": "test@resulttest.com", 
        "industry": "technology",
        "employees": 25,
        "revenue": 1000000,
        "coverage_amount": 500000
    }
    
    print("🧪 Testing Guidewire result structure...")
    
    guidewire_result = guidewire_client.create_cyber_submission(extracted_data)
    
    print(f"\n📊 Full Guidewire Result:")
    for key, value in guidewire_result.items():
        if key == "parsed_data" and isinstance(value, dict):
            print(f"   {key}: (dict with {len(value)} keys)")
            for subkey in value.keys():
                print(f"      - {subkey}")
        else:
            print(f"   {key}: {value}")
    
    print(f"\n🔍 Key Analysis:")
    print(f"   ✅ success: {guidewire_result.get('success')}")
    print(f"   🏢 account_id: {guidewire_result.get('account_id')}")
    print(f"   📋 job_id: {guidewire_result.get('job_id')}")
    print(f"   📄 account_number: {guidewire_result.get('account_number')}")
    print(f"   🔢 job_number: {guidewire_result.get('job_number')}")
    
    # Test the exact update logic from main.py
    print(f"\n🔧 Testing WorkItem update logic:")
    
    account_id = guidewire_result.get("account_id")
    job_id = guidewire_result.get("job_id")
    
    print(f"   account_id from .get(): {account_id}")
    print(f"   job_id from .get(): {job_id}")
    
    if guidewire_result.get("account_id"):
        print(f"   ✅ Would set account_id: {guidewire_result['account_id']}")
    else:
        print(f"   ❌ Would NOT set account_id")
        
    if guidewire_result.get("job_id"):
        print(f"   ✅ Would set job_id: {guidewire_result['job_id']}")
    else:
        print(f"   ❌ Would NOT set job_id")
    
    print(f"\n✨ Structure test complete!")
    return guidewire_result

if __name__ == "__main__":
    result = test_guidewire_result_structure()
    
    # Also test the condition check
    print(f"\n🧪 Condition Test:")
    print(f"   bool(result.get('account_id')): {bool(result.get('account_id'))}")
    print(f"   bool(result.get('job_id')): {bool(result.get('job_id'))}")