#!/usr/bin/env python3

import logging
import json
from guidewire_client import guidewire_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test the enhanced Guidewire integration
test_submission_data = {
    "company_name": "Test Corp",
    "contact_person": "John Doe", 
    "email": "john@testcorp.com",
    "phone": "555-0123",
    "address": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94105",
    "industry": "technology",
    "entity_type": "corporation",
    "employees": 50,
    "revenue": 5000000,
    "assets": 2500000,
    "liabilities": 500000,
    "policy_type": "cyber",
    "coverage_amount": 1000000,
    "deductible": 10000,
    "policy_start": "2025-01-01",
    "coverage_types": ["data_breach", "business_interruption", "cyber_extortion"]
}

print("🔄 Testing Enhanced Guidewire Integration...")
result = guidewire_client.create_cyber_submission(test_submission_data)

print("\n📊 Guidewire Result Structure:")
print(f"✅ Success: {result.get('success')}")
print(f"🏢 Account ID: {result.get('account_id')}")
print(f"📄 Account Number: {result.get('account_number')} ")
print(f"📋 Job ID: {result.get('job_id')}")
print(f"🔢 Job Number: {result.get('job_number')}")
print(f"💰 Quote Info: {result.get('quote_info')}")
print(f"📝 Message: {result.get('message')}")

print("\n🔍 Full Result Keys:")
for key in result.keys():
    print(f"  - {key}")

print("\n📦 Parsed Data Keys:")
if result.get("parsed_data"):
    for key in result.get("parsed_data", {}).keys():
        print(f"  - {key}")
        
print("\n✨ Test Complete!")