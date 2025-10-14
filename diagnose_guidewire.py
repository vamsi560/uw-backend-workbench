#!/usr/bin/env python3
"""
Test direct Guidewire submission creation to diagnose the issue
"""

import requests
import json

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_direct_guidewire_submission():
    """Test creating a submission directly through Guidewire"""
    print("🧪 TESTING DIRECT GUIDEWIRE SUBMISSION CREATION")
    print("=" * 60)
    
    test_data = {
        "company_name": "Direct Test Company from Corporate Network",
        "contact_email": "directtest@testcompany.com",
        "contact_name": "Direct Test User",
        "contact_phone": "555-123-4567",
        "industry": "technology",
        "employee_count": "100",
        "annual_revenue": "5000000",
        "coverage_amount": "1000000",
        "business_address": "123 Corporate Network St",
        "business_city": "Seattle",
        "business_state": "WA",
        "business_zip": "98101",
        "policy_type": "cyber liability",
        "effective_date": "2025-01-01"
    }
    
    try:
        print("Sending direct Guidewire submission test...")
        response = requests.post(f"{BASE_URL}/api/test/guidewire-submission",
                               json=test_data,
                               timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Direct submission test response received")
            print(f"   Success: {data.get('success', False)}")
            
            # Show the Guidewire result details
            gw_result = data.get('guidewire_result', {})
            print(f"\n📊 Guidewire Result Details:")
            print(f"   Success: {gw_result.get('success', False)}")
            print(f"   Simulation Mode: {gw_result.get('simulation_mode', 'Unknown')}")
            print(f"   Account ID: {gw_result.get('account_id', 'None')}")
            print(f"   Account Number: {gw_result.get('account_number', 'None')}")
            print(f"   Job ID: {gw_result.get('job_id', 'None')}")
            print(f"   Job Number: {gw_result.get('job_number', 'None')}")
            print(f"   Message: {gw_result.get('message', 'No message')}")
            
            if gw_result.get('error'):
                print(f"   Error: {gw_result.get('error')}")
            
            # Show quote info if available
            quote_info = gw_result.get('quote_info', {})
            if quote_info:
                print(f"\n💰 Quote Information:")
                for key, value in quote_info.items():
                    print(f"   {key}: {value}")
            
            # Check parsed data
            parsed_data = gw_result.get('parsed_data', {})
            if parsed_data:
                print(f"\n📋 Parsed Data:")
                for key, value in parsed_data.items():
                    print(f"   {key}: {value}")
            
            return gw_result.get('success', False)
            
        else:
            print(f"❌ Direct submission test failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Direct submission test error: {str(e)}")
        return False

def check_guidewire_parsing_debug():
    """Check the Guidewire parsing debug endpoint"""
    print(f"\n🔍 TESTING GUIDEWIRE PARSING DEBUG")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/debug/test-submission-parsing", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Parsing debug response received")
            print(f"   Debug Type: {data.get('debug_type', 'Unknown')}")
            print(f"   Payload Generated: {data.get('payload_generated', False)}")
            print(f"   API Call Success: {data.get('api_call_success', False)}")
            print(f"   API Response Status: {data.get('api_response_status', 'Unknown')}")
            
            parsing_result = data.get('parsing_result', {})
            if parsing_result:
                print(f"\n📊 Parsing Result:")
                print(f"   Success: {parsing_result.get('success', False)}")
                print(f"   Simulation Mode: {parsing_result.get('simulation_mode', 'Unknown')}")
                print(f"   Account ID: {parsing_result.get('account_id', 'None')}")
                print(f"   Account Number: {parsing_result.get('account_number', 'None')}")
                print(f"   Error: {parsing_result.get('error', 'None')}")
                print(f"   Message: {parsing_result.get('message', 'None')}")
            
            # Show raw response info
            print(f"\n🔍 Raw Response Analysis:")
            print(f"   Response Data Type: {data.get('response_data_type', 'Unknown')}")
            print(f"   Has Responses Array: {data.get('has_responses_array', False)}")
            print(f"   Raw API Response Keys: {data.get('raw_api_response_keys', [])}")
            
            return parsing_result.get('success', False) if parsing_result else False
            
        else:
            print(f"❌ Parsing debug failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Parsing debug error: {str(e)}")
        return False

def main():
    print("🔬 DETAILED GUIDEWIRE SUBMISSION ANALYSIS")
    print("Investigating why Account IDs are None despite successful API calls")
    print("=" * 70)
    
    # Test 1: Direct submission test
    submission_success = test_direct_guidewire_submission()
    
    # Test 2: Parsing debug
    parsing_success = check_guidewire_parsing_debug()
    
    print(f"\n{'='*70}")
    print("📊 DIAGNOSIS RESULTS")
    print(f"{'='*70}")
    
    if submission_success:
        print("✅ Direct Guidewire submission: SUCCESS")
        print("🎉 Real accounts and jobs should be created in Guidewire PolicyCenter")
    else:
        print("❌ Direct Guidewire submission: FAILED")
        print("💡 Check the error details above for troubleshooting")
    
    if parsing_success:
        print("✅ Guidewire response parsing: SUCCESS")
    else:
        print("❌ Guidewire response parsing: FAILED")
        print("💡 There may be an issue with parsing Guidewire's response format")
    
    print(f"\n🔍 Next Steps:")
    if submission_success and parsing_success:
        print("1. ✅ Guidewire integration is working correctly")
        print("2. 🔍 Check Guidewire PolicyCenter UI for the created accounts")
        print("3. 📧 Send a test email - it should create accounts automatically")
    elif submission_success and not parsing_success:
        print("1. ✅ Guidewire is creating accounts but response parsing is broken")
        print("2. 🔧 The accounts are being created but IDs aren't being extracted")
        print("3. 🔍 Check Guidewire PolicyCenter UI - accounts should still be there")
    else:
        print("1. ❌ Guidewire integration has issues")
        print("2. 🔧 Check network connectivity and authentication")
        print("3. 💬 Contact Guidewire support team for API troubleshooting")

if __name__ == "__main__":
    main()