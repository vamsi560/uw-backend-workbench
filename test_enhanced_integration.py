#!/usr/bin/env python3
"""
Test the enhanced Guidewire client that creates both Account and Submission
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_enhanced_guidewire_integration():
    """Test the enhanced Guidewire integration with Account + Submission"""
    
    print("🚀 TESTING ENHANCED GUIDEWIRE INTEGRATION")
    print("Now creates both Account AND Submission with full field mapping!")
    print("="*80)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Test with comprehensive data that should create both account and submission
    comprehensive_test_data = {
        "company_name": "Enhanced Test Company Inc",
        "named_insured": "Enhanced Test Company Inc",
        "contact_name": "Enhanced Test Manager",
        "contact_email": f"enhanced{timestamp}@test.com",
        "industry": "technology",
        "business_type": "Software Development",
        "entity_type": "Corporation",
        "years_in_business": "7",
        "company_ein": "12-3456789",
        "employee_count": "180",
        "annual_revenue": "12000000",
        "policy_type": "Cyber Liability",
        "coverage_amount": "3000000",
        "aggregate_limit": "3000000",
        "per_occurrence_limit": "1500000",
        "deductible": "50000",
        "effective_date": "2025-01-01",
        "policy_term": "1 Year",
        "business_address": "789 Enhanced Street",
        "business_city": "Enhanced City", 
        "business_state": "CA",
        "business_zip": "90211",
        "contact_phone": "(555) ENH-ANCED",
        "data_types": "Customer PII, Financial Records, Health Information",
        "security_measures": "Multi-factor authentication, End-to-end encryption, SOC 2 Type II certified, Penetration testing"
    }
    
    print(f"🧪 Testing enhanced direct Guidewire submission...")
    print(f"   Company: {comprehensive_test_data['company_name']}")
    print(f"   Coverage: ${comprehensive_test_data['coverage_amount']}")
    print(f"   Industry: {comprehensive_test_data['industry']}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/test/guidewire-submission", 
                               json=comprehensive_test_data, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            gw_result = data.get('guidewire_result', {})
            
            print(f"\n✅ Enhanced Guidewire test response:")
            print(f"   Success: {gw_result.get('success')}")
            print(f"   Account ID: {gw_result.get('account_id', 'None')}")
            print(f"   Account Number: {gw_result.get('account_number', 'None')}")
            print(f"   Job ID: {gw_result.get('job_id', 'None')}")
            print(f"   Job Number: {gw_result.get('job_number', 'None')}")
            print(f"   Message: {gw_result.get('message', 'No message')}")
            
            if gw_result.get('success'):
                account_number = gw_result.get('account_number')
                job_number = gw_result.get('job_number')
                
                if account_number and account_number != 'None':
                    print(f"\n🏢 ACCOUNT CREATED: {account_number}")
                else:
                    print(f"\n⚠️  Account creation unclear")
                
                if job_number and job_number != 'None':
                    print(f"📋 SUBMISSION CREATED: {job_number}")
                    print(f"🎉 SUCCESS! Both Account AND Submission created!")
                    
                    return {
                        'success': True,
                        'account_number': account_number,
                        'job_number': job_number,
                        'has_both': True
                    }
                else:
                    print(f"⚠️  Submission creation unclear - may be parsing issue")
                    
                    return {
                        'success': True,
                        'account_number': account_number,
                        'job_number': 'Not parsed',
                        'has_both': False
                    }
            else:
                print(f"\n❌ Enhanced Guidewire test failed: {gw_result.get('error', 'Unknown error')}")
                return {'success': False, 'error': gw_result.get('error')}
        else:
            print(f"❌ Request failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response: {response.text[:200]}...")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_enhanced_email_integration():
    """Test if the enhanced integration works with email processing"""
    
    print(f"\n📧 TESTING ENHANCED EMAIL INTEGRATION")
    print("="*60)
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    enhanced_email = {
        "subject": f"ENHANCED TEST {timestamp} - Complete Integration",
        "sender_email": f"enhanced{timestamp}@company.com",
        "body": f"""
COMPANY INFORMATION:
Company Name: Enhanced Email Test Company Inc
Industry: Technology
Business Type: Software Development
Years in Business: 6

CONTACT INFORMATION:
Contact Name: Enhanced Email Manager
Email: enhanced{timestamp}@company.com
Phone: (555) 123-ENHANCED
Address: 101 Enhanced Boulevard, Tech Valley, CA 94102

BUSINESS DETAILS:
Number of Employees: 160
Annual Revenue: $11,000,000
Data Types: Customer PII, Financial Records
Security Measures: Multi-factor authentication, Encryption, SOC 2 certified

INSURANCE REQUIREMENTS:
Policy Type: Cyber Liability
Coverage Amount: $2,500,000
Deductible: $40,000
Effective Date: 2025-01-01

We need comprehensive cyber liability coverage including network security, 
privacy liability, and data breach response.

This email tests the enhanced integration that should create both 
Guidewire account and submission.
        """,
        "attachments": []
    }
    
    print(f"📧 Sending enhanced integration test email...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake", 
                               json=enhanced_email, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            
            print(f"✅ Enhanced email processed:")
            print(f"   Message: {message}")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            
            if 'guidewire' in message.lower():
                if 'success' in message.lower() or 'synced' in message.lower():
                    print(f"   🎉 Auto-sync appears to be working!")
                    return True, data
                else:
                    print(f"   ⚠️  Auto-sync attempted but may have issues")
                    return False, data
            else:
                print(f"   ❌ No Guidewire sync detected")
                return False, data
        else:
            print(f"❌ Enhanced email failed: HTTP {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Enhanced email error: {str(e)}")
        return False, None

def main():
    print("🔧 TESTING ENHANCED GUIDEWIRE INTEGRATION")
    print("Now creates Account + Submission with complete field mapping!")
    print("="*80)
    
    # Test 1: Direct enhanced Guidewire
    direct_result = test_enhanced_guidewire_integration()
    
    # Test 2: Enhanced email integration
    email_success, email_data = test_enhanced_email_integration()
    
    print(f"\n{'='*80}")
    print("🎯 ENHANCED INTEGRATION TEST RESULTS")
    print(f"{'='*80}")
    
    if direct_result.get('success'):
        print(f"✅ DIRECT GUIDEWIRE TEST:")
        print(f"   🏢 Account: {direct_result.get('account_number')}")
        
        if direct_result.get('has_both'):
            print(f"   📋 Submission: {direct_result.get('job_number')}")
            print(f"   🎉 Both Account AND Submission created!")
        else:
            print(f"   ⚠️  Submission: {direct_result.get('job_number', 'Not detected')}")
    else:
        print(f"❌ Direct Guidewire test failed")
        
    if email_success:
        print(f"\n✅ EMAIL INTEGRATION TEST:")
        print(f"   🎉 Enhanced auto-sync working!")
    else:
        print(f"\n⚠️  EMAIL INTEGRATION TEST:")
        print(f"   Still processing or needs more fixes")
    
    print(f"\n💡 EXPECTED BEHAVIOR:")
    print(f"   📧 Email → Work Item + Account + Submission")
    print(f"   🏢 All field mapping preserved")
    print(f"   📋 Complete insurance request details")

if __name__ == "__main__":
    main()