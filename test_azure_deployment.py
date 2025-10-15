#!/usr/bin/env python3
"""
Test the Azure-deployed Guidewire number extraction functionality
"""

import requests
import json
import time

# Azure deployment URL
AZURE_BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def test_azure_deployment():
    print("🚀 Testing Azure Deployment - Guidewire Number Extraction")
    print("=" * 70)
    
    # Wait for deployment to complete
    print("⏳ Waiting for deployment to complete...")
    time.sleep(30)  # Give Azure time to deploy
    
    try:
        # Test 1: Health check
        print("\n1. 🏥 Health Check...")
        health_response = requests.get(f"{AZURE_BASE_URL}/health", timeout=30)
        if health_response.status_code == 200:
            print("   ✅ Azure backend is running")
        else:
            print(f"   ❌ Health check failed: {health_response.status_code}")
            return
            
        # Test 2: Test the new Guidewire number extraction endpoint
        print("\n2. 🔍 Testing Guidewire Number Extraction...")
        test_response = requests.post(
            f"{AZURE_BASE_URL}/api/debug/test-guidewire-numbers",
            timeout=60  # Guidewire can be slow
        )
        
        if test_response.status_code == 200:
            result = test_response.json()
            print("   ✅ Guidewire test endpoint responded successfully")
            
            print(f"\n   📋 Test Results:")
            print(f"     • Test Type: {result.get('test_type')}")
            print(f"     • Timestamp: {result.get('timestamp')}")
            print(f"     • Extraction Success: {result.get('extraction_success', False)}")
            
            if result.get('extraction_success'):
                numbers = result.get('extracted_numbers', {})
                print(f"     • 🎯 Account Number: {numbers.get('account_number', 'Not extracted')}")
                print(f"     • 🎯 Job Number: {numbers.get('job_number', 'Not extracted')}")
                
                if result.get('updated_work_item'):
                    updated = result['updated_work_item']
                    print(f"     • ✅ Updated Work Item {updated.get('id')} with human-readable numbers")
            else:
                print(f"     • ❌ Extraction failed: {result.get('error', result.get('message', 'Unknown error'))}")
                
        else:
            print(f"   ❌ Guidewire test failed: {test_response.status_code}")
            print(f"   Response: {test_response.text[:500]}")
            
        # Test 3: Check work items with updated schema
        print("\n3. 📊 Checking Work Items Schema...")
        poll_response = requests.get(f"{AZURE_BASE_URL}/api/debug/poll", timeout=30)
        
        if poll_response.status_code == 200:
            poll_result = poll_response.json()
            work_items = poll_result.get('work_items', [])
            
            print(f"   ✅ Found {len(work_items)} work items")
            
            if work_items:
                latest = work_items[0]
                print(f"   📋 Latest Work Item:")
                print(f"     • ID: {latest.get('id')}")
                print(f"     • Title: {latest.get('title', 'No title')}")
                print(f"     • Internal Account ID: {latest.get('guidewire_account_id', 'Not set')}")
                print(f"     • Internal Job ID: {latest.get('guidewire_job_id', 'Not set')}")
                print(f"     • 🎯 Human Account Number: {latest.get('guidewire_account_number', 'Not set')}")
                print(f"     • 🎯 Human Job Number: {latest.get('guidewire_job_number', 'Not set')}")
                
                # Check if we have human-readable numbers
                has_numbers = latest.get('guidewire_account_number') and latest.get('guidewire_job_number')
                if has_numbers:
                    print(f"   ✅ SUCCESS: Human-readable numbers are populated!")
                    print(f"     🔍 You can now search Guidewire with:")
                    print(f"     • Account Number: {latest.get('guidewire_account_number')}")
                    print(f"     • Job Number: {latest.get('guidewire_job_number')}")
                else:
                    print(f"   ⏳ Human-readable numbers not yet populated (will be set on next email submission)")
        else:
            print(f"   ❌ Work items check failed: {poll_response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_azure_deployment()