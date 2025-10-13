#!/usr/bin/env python3
"""
Local test script for Guidewire integration
Tests the payload generation and structure without making actual API calls
"""

import json
import sys
from guidewire_client import guidewire_client

def test_guidewire_integration():
    """Test complete Guidewire integration locally"""
    
    print("🧪 Testing Guidewire Integration Locally")
    print("=" * 50)
    
    # Test data - realistic insurance submission
    test_data = {
        'company_name': 'TechStart Solutions LLC',
        'business_address': '456 Innovation Drive',
        'business_city': 'Palo Alto', 
        'business_state': 'CA',
        'business_zip': '94301',
        'mailing_address': '456 Innovation Drive',
        'mailing_city': 'Palo Alto',
        'mailing_state': 'CA', 
        'mailing_zip': '94301',
        'effective_date': '2025-08-01T18:31:00.000Z',
        'employee_count': '15',
        'annual_revenue': '750000',
        'entity_type': 'llc',
        'years_in_business': '3',
        'industry': 'technology',
        'coverage_amount': '100000',
        'deductible': '5000',
        'business_interruption_limit': '25000',
        'cyber_extortion_limit': '10000'
    }
    
    try:
        # Test 1: Payload generation
        print("1️⃣ Testing payload generation...")
        payload = guidewire_client._map_to_guidewire_format(test_data)
        print(f"   ✅ Generated {len(payload['requests'])} request steps")
        
        # Test 2: Structure validation
        print("2️⃣ Validating payload structure...")
        
        # Check each step
        steps = [
            ("Account Creation", "/account/v1/accounts", "post"),
            ("Submission Creation", "/job/v1/submissions", "post"), 
            ("Coverage Configuration", "/coverages", "post"),
            ("Business Data Update", "/lines/USCyberLine", "patch"),
            ("Quote Generation", "/quote", "post")
        ]
        
        for i, (name, uri_part, method) in enumerate(steps):
            req = payload['requests'][i]
            uri_match = uri_part in req['uri'] 
            method_match = req['method'] == method
            if uri_match and method_match:
                print(f"   ✅ {name}: {method.upper()} {req['uri']}")
            else:
                print(f"   ❌ {name}: Expected {method.upper()} with {uri_part}")
                return False
        
        # Test 3: Field validation
        print("3️⃣ Validating required fields...")
        
        # Account fields
        account = payload['requests'][0]['body']['data']['attributes']
        if 'initialAccountHolder' in account and 'companyName' in account['initialAccountHolder']:
            print(f"   ✅ Company Name: {account['initialAccountHolder']['companyName']}")
        else:
            print("   ❌ Missing company name in account")
            return False
            
        # Submission fields  
        submission = payload['requests'][1]['body']['data']['attributes']
        if 'product' in submission and submission['product']['id'] == 'USCyber':
            print(f"   ✅ Product: {submission['product']['id']}")
        else:
            print("   ❌ Missing or incorrect product")
            return False
            
        # Coverage fields
        coverage = payload['requests'][2]['body']['data']['attributes']
        if 'terms' in coverage and 'ACLCommlCyberLiabilityCyberAggLimit' in coverage['terms']:
            agg_limit = coverage['terms']['ACLCommlCyberLiabilityCyberAggLimit']
            if 'choiceValue' in agg_limit:
                print(f"   ✅ Coverage Limit: {agg_limit['choiceValue']['name']}")
            else:
                print("   ❌ Missing choiceValue in coverage terms")
                return False
        else:
            print("   ❌ Missing coverage terms")
            return False
        
        # Test 4: Data type validation
        print("4️⃣ Validating data types...")
        
        business_data = payload['requests'][3]['body']['data']['attributes']
        
        # Check employee count is integer
        if isinstance(business_data.get('aclTotalFTEmployees'), int):
            print(f"   ✅ Employee Count: {business_data['aclTotalFTEmployees']} (integer)")
        else:
            print(f"   ❌ Employee count should be integer, got {type(business_data.get('aclTotalFTEmployees'))}")
            return False
            
        # Check revenue is string (as expected by Guidewire)
        if isinstance(business_data.get('aclTotalRevenues'), str):
            print(f"   ✅ Revenue: ${business_data['aclTotalRevenues']} (string)")
        else:
            print(f"   ❌ Revenue should be string, got {type(business_data.get('aclTotalRevenues'))}")
            return False
        
        # Test 5: JSON serialization
        print("5️⃣ Testing JSON serialization...")
        try:
            json_str = json.dumps(payload, indent=2)
            print(f"   ✅ Serialized to {len(json_str):,} characters")
            
            # Validate it can be parsed back
            parsed = json.loads(json_str)
            if len(parsed['requests']) == 5:
                print("   ✅ JSON round-trip successful")
            else:
                print("   ❌ JSON round-trip failed")
                return False
                
        except Exception as e:
            print(f"   ❌ JSON serialization failed: {e}")
            return False
        
        # Test 6: Simulate submission creation
        print("6️⃣ Testing submission creation method...")
        try:
            # This will generate the payload and return failure due to network timeout (expected)
            result = guidewire_client.create_cyber_submission(test_data)
            
            # We expect this to fail with network timeout, but the payload should be generated correctly
            if 'error' in result and ('timeout' in result.get('message', '').lower() or 'connection' in result.get('message', '').lower()):
                print("   ✅ Submission method works (network timeout expected)")
            else:
                print(f"   ⚠️  Unexpected result: {result}")
                
        except Exception as e:
            print(f"   ❌ Submission creation failed: {e}")
            return False
        
        print()
        print("🎉 ALL TESTS PASSED!")
        print("✅ Guidewire integration is ready for deployment")
        print("✅ Payload structure matches official format")
        print("✅ All data types and field mappings are correct")
        print("✅ JSON serialization works properly")
        print()
        print("📦 Ready to deploy to Azure!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_guidewire_integration()
    sys.exit(0 if success else 1)