#!/usr/bin/env python3
"""
Debug the exact validation process to see why auto-sync fails
"""

import requests
import json
import sys
import os

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from business_rules import CyberInsuranceValidator
    from llm_service import llm_service
    print("✅ Successfully imported business rules and LLM service")
except ImportError as e:
    print(f"❌ Could not import modules: {e}")
    print("This script should be run from the project directory")
    sys.exit(1)

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_llm_extraction_locally():
    """Test LLM extraction locally to see what data we get"""
    print("🤖 TESTING LLM EXTRACTION LOCALLY")
    print("="*60)
    
    test_email_text = """
    Subject: Cyber Insurance Quote Request
    From: test@company.com
    
    Company: Test Company Inc
    Industry: Technology
    Contact: John Smith
    Email: john@testcompany.com
    
    We need cyber insurance with $2,000,000 coverage.
    Policy Type: Cyber Liability
    Effective Date: 2025-01-01
    
    Our company operates in the software development space.
    """
    
    print(f"📧 Testing with email text:")
    print(f"   Text: {test_email_text[:100]}...")
    
    try:
        extracted = llm_service.extract_insurance_data(test_email_text)
        
        print(f"✅ LLM Extraction Results:")
        key_fields = ["company_name", "insured_name", "industry", "policy_type", "effective_date", "coverage_amount"]
        
        for field in key_fields:
            value = extracted.get(field, "MISSING")
            print(f"   {field}: '{value}'")
        
        print(f"\n🔍 Now testing business validation...")
        validation_result = CyberInsuranceValidator.validate_submission(extracted)
        validation_status, missing_fields, reason = validation_result
        
        print(f"   Validation Status: '{validation_status}'")
        print(f"   Missing Fields: {missing_fields}")
        print(f"   Reason: {reason}")
        
        # Check the auto-sync conditions
        print(f"\n🎯 Auto-sync Condition Check:")
        print(f"   validation_status != 'Rejected': {validation_status != 'Rejected'}")
        print(f"   extracted_data exists: {bool(extracted)}")
        print(f"   extracted_data truthy: {extracted is not None and len(extracted) > 0}")
        
        auto_sync_should_work = (validation_status != "Rejected" and extracted)
        print(f"   🎉 AUTO-SYNC SHOULD WORK: {auto_sync_should_work}")
        
        return extracted, validation_result, auto_sync_should_work
        
    except Exception as e:
        print(f"❌ LLM extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, False

def test_validation_with_different_inputs():
    """Test validation with different input scenarios"""
    print(f"\n🧪 TESTING VALIDATION WITH DIFFERENT SCENARIOS")
    print("="*60)
    
    test_cases = [
        {
            "name": "Complete Valid Case",
            "data": {
                "company_name": "Test Company Inc",
                "insured_name": "Test Company Inc", 
                "industry": "technology",
                "policy_type": "Cyber Liability",
                "effective_date": "2025-01-01",
                "coverage_amount": "2000000"
            }
        },
        {
            "name": "Minimal Valid Case",
            "data": {
                "insured_name": "Test Company",
                "industry": "technology", 
                "policy_type": "cyber",
                "effective_date": "2025-01-01"
            }
        },
        {
            "name": "Missing Required Field",
            "data": {
                "insured_name": "Test Company",
                "policy_type": "cyber",
                "effective_date": "2025-01-01"
                # Missing industry
            }
        },
        {
            "name": "Invalid Policy Type",
            "data": {
                "insured_name": "Test Company",
                "industry": "technology",
                "policy_type": "Auto Insurance", # Wrong type
                "effective_date": "2025-01-01"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        try:
            validation_result = CyberInsuranceValidator.validate_submission(test_case['data'])
            validation_status, missing_fields, reason = validation_result
            
            print(f"   Status: '{validation_status}'")
            print(f"   Missing: {missing_fields}")  
            print(f"   Reason: {reason}")
            
            auto_sync_condition = (validation_status != "Rejected" and test_case['data'])
            print(f"   Auto-sync would work: {auto_sync_condition}")
            
        except Exception as e:
            print(f"   ❌ Validation error: {str(e)}")

def test_real_email_extraction():
    """Send a real email and see what gets extracted vs what we expect"""
    print(f"\n📧 TESTING REAL EMAIL EXTRACTION")
    print("="*60)
    
    test_email = {
        "subject": "DEBUG EXTRACTION - Cyber Insurance Request",
        "sender_email": "debug@testcompany.com",
        "body": """
        Company Name: Debug Test Company Inc
        Industry: Technology
        Business Type: Software Development
        
        Contact Information:
        - Name: Debug Tester
        - Email: debug@testcompany.com
        - Phone: 555-DEBUG-01
        
        Insurance Requirements:
        - Policy Type: Cyber Liability
        - Coverage Amount: $3,000,000
        - Effective Date: January 1, 2025
        
        We develop software applications and need comprehensive cyber insurance.
        
        Please provide a quote.
        """,
        "attachments": []
    }
    
    print(f"📧 Sending debug email to see extraction results...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake",
                               json=test_email,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Email processed:")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            
            # Check if auto-sync happened
            message = data.get('message', '')
            if 'guidewire' in message.lower():
                print(f"   🎉 AUTO-SYNC DETECTED IN RESPONSE!")
            else:
                print(f"   ❌ No auto-sync detected")
            
            return True
            
        else:
            print(f"❌ Email failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Real email test error: {str(e)}")
        return False

def main():
    print("🔬 COMPLETE VALIDATION DEBUG ANALYSIS")
    print("="*80)
    
    print("This script will:")
    print("1. Test LLM extraction locally")
    print("2. Test business validation with different scenarios")  
    print("3. Send a real email to compare")
    print()
    
    # Test 1: Local LLM extraction
    extracted, validation_result, should_work = test_llm_extraction_locally()
    
    # Test 2: Different validation scenarios
    test_validation_with_different_inputs()
    
    # Test 3: Real email
    real_email_worked = test_real_email_extraction()
    
    print(f"\n{'='*80}")
    print("🎯 COMPLETE ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    if should_work:
        print("✅ LOCAL VALIDATION: Auto-sync should work based on local tests")
    else:
        print("❌ LOCAL VALIDATION: Issues found in validation logic")
    
    if real_email_worked:
        print("✅ REAL EMAIL: Successfully processed")
    else:
        print("❌ REAL EMAIL: Processing failed")
    
    if extracted:
        print(f"\n💡 KEY INSIGHTS:")
        validation_status = validation_result[0] if validation_result else "Unknown"
        
        if validation_status == "Rejected":
            print("   - Validation is rejecting submissions")
            print("   - Check business rules for acceptance criteria")
        elif validation_status == "Incomplete":
            print("   - Validation finds missing required fields")
            print("   - Check LLM extraction completeness") 
        elif validation_status == "Complete":
            print("   - Validation passes, issue is elsewhere")
            print("   - Check server-side implementation")
        else:
            print(f"   - Unexpected validation status: {validation_status}")
    
    print(f"\n🔧 NEXT STEPS:")
    if should_work and real_email_worked:
        print("   - Auto-sync should be working - check server logs")
    else:
        print("   - Fix identified validation issues")
        print("   - Ensure LLM extracts all required fields")
        print("   - Verify business rules accept valid cyber insurance")

if __name__ == "__main__":
    main()