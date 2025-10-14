#!/usr/bin/env python3
"""
Debug the field mapping issue between email extraction and Guidewire submission
"""

import requests
import json

BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def debug_field_mapping_issue():
    """Debug what's happening with field mapping"""
    
    print("🔍 DEBUGGING FIELD MAPPING ISSUE")
    print("="*60)
    
    print("❌ PROBLEM IDENTIFIED:")
    print("1. Email extraction may not populate all required fields")
    print("2. Guidewire client only creates ACCOUNT, not SUBMISSION")
    print("3. Field mapping from LLM extraction to Guidewire is incomplete")
    
    print(f"\n🧠 WHAT SHOULD HAPPEN:")
    print("✅ Email → LLM extracts ALL fields → Guidewire creates Account + Submission")
    
    print(f"\n❌ WHAT'S ACTUALLY HAPPENING:")
    print("📧 Email → LLM extracts SOME fields → Guidewire creates Account only")
    
    # Test with a comprehensive email to see what gets extracted
    timestamp = "20251014_180000"
    
    comprehensive_email = {
        "subject": f"DEBUG FIELD MAPPING - {timestamp}",
        "sender_email": f"debug{timestamp}@test.com",
        "body": f"""
COMPANY INFORMATION:
Company Name: Debug Field Mapping Company Inc
Named Insured: Debug Field Mapping Company Inc
Industry: Technology
Business Type: Software Development
Entity Type: Corporation
Years in Business: 8
Tax ID: 12-3456789

CONTACT INFORMATION:
Contact Name: Debug Manager
Contact Title: Risk Manager  
Contact Email: debug{timestamp}@test.com
Contact Phone: (555) DEBUG-01
Mailing Address: 456 Debug Street
Mailing City: Debug City
Mailing State: CA
Mailing ZIP: 90210
Business Address: 456 Debug Street
Business City: Debug City
Business State: CA
Business ZIP: 90210

BUSINESS DETAILS:
Number of Employees: 200
Annual Revenue: $15,000,000
Company Size: Medium
Data Types: Customer PII, Financial Records, Health Information
Security Measures: MFA, Encryption, SOC2 Certified

INSURANCE REQUIREMENTS:
Policy Type: Cyber Liability
Coverage Amount: $5,000,000
Aggregate Limit: $5,000,000
Per Occurrence Limit: $1,000,000
Deductible: $25,000
Effective Date: 2025-01-01
Policy Term: 1 Year

COVERAGE DETAILS:
Privacy Liability Limit: $2,000,000
Network Security Limit: $2,000,000
Data Breach Response Limit: $1,000,000
Business Interruption Limit: $500,000
Cyber Extortion Limit: $250,000

This is a comprehensive test to debug field mapping.
        """,
        "attachments": []
    }
    
    print(f"\n📧 Sending comprehensive debug email...")
    print(f"   This email contains ALL possible fields")
    print(f"   Subject: {comprehensive_email['subject']}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/email/intake", 
                               json=comprehensive_email, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            
            print(f"✅ Debug email processed:")
            print(f"   Message: {message}")
            print(f"   Submission Ref: {data.get('submission_ref')}")
            
            if 'guidewire' in message.lower():
                print(f"   🎯 Auto-sync attempted!")
            else:
                print(f"   ⚠️  Auto-sync not attempted")
            
            return True, data
        else:
            print(f"❌ Debug email failed: HTTP {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

def explain_guidewire_submission_vs_account():
    """Explain the difference between Account and Submission in Guidewire"""
    
    print(f"\n🏢 GUIDEWIRE ACCOUNT vs SUBMISSION EXPLAINED")
    print("="*60)
    
    print("🏢 ACCOUNT (Customer Record):")
    print("   - Basic company information")
    print("   - Contact details, address")
    print("   - Tax ID, organization type")
    print("   - Think: Customer database entry")
    
    print(f"\n📋 SUBMISSION (Insurance Request):")
    print("   - Specific insurance request")
    print("   - Coverage amounts, policy type")
    print("   - Risk information, business details")
    print("   - Think: Quote request")
    
    print(f"\n🎯 PROPER FLOW SHOULD BE:")
    print("1. ✅ Create Account (company info)")
    print("2. ✅ Create Submission (insurance request)")  
    print("3. ✅ Link Submission to Account")
    print("4. ✅ Generate Quote")
    
    print(f"\n❌ CURRENT ISSUE:")
    print("1. ✅ Account created (basic info)")
    print("2. ❌ No Submission created")
    print("3. ❌ No insurance request details")
    print("4. ❌ No quote generation")

def provide_solution_steps():
    """Provide steps to fix the issue"""
    
    print(f"\n🔧 SOLUTION STEPS")
    print("="*60)
    
    print("1. 🧠 Fix LLM Extraction:")
    print("   - Ensure all required fields are extracted")
    print("   - Map email content to proper field names")
    
    print(f"\n2. 🏢 Fix Guidewire Client:")
    print("   - Create both Account AND Submission")
    print("   - Map all extracted fields properly")
    print("   - Include coverage details in submission")
    
    print(f"\n3. 🔄 Fix Auto-Sync:")
    print("   - Pass complete extracted data")
    print("   - Ensure proper field mapping")
    print("   - Verify both account and submission creation")
    
    print(f"\n💡 EXPECTED RESULT:")
    print("📧 Email → Account (2529555097) + Submission (with all details)")

def main():
    print("🚨 FIELD MAPPING AND SUBMISSION CREATION DEBUG")
    print("Investigating why fields don't match and submissions aren't created")
    print("="*80)
    
    success, data = debug_field_mapping_issue()
    explain_guidewire_submission_vs_account()
    provide_solution_steps()
    
    print(f"\n{'='*80}")
    print("🎯 DEBUG SUMMARY")
    print(f"{'='*80}")
    
    print("✅ IDENTIFIED ISSUES:")
    print("1. ❌ Guidewire client only creates Account, not Submission")
    print("2. ❌ Field mapping incomplete between LLM and Guidewire")
    print("3. ❌ No insurance request details being passed")
    
    print(f"\n🔧 FIXES NEEDED:")
    print("1. Update guidewire_client.py to create submissions")
    print("2. Improve field mapping from email to Guidewire")
    print("3. Ensure all extracted data reaches Guidewire")
    
    if success:
        print(f"\n📧 Debug email sent successfully")
        print("   Use this to test field extraction improvements")

if __name__ == "__main__":
    main()