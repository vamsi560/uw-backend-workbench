#!/usr/bin/env python3
"""
Test script for the new Guidewire API endpoints
"""
import requests
import json

def test_guidewire_apis():
    """Test the new Guidewire API endpoints"""
    base_url = 'http://localhost:8000'
    
    print('=== Testing Guidewire API Endpoints ===')
    
    # Test 1: Get Guidewire submissions
    print('\n1. GET /api/guidewire/submissions')
    try:
        response = requests.get(f'{base_url}/api/guidewire/submissions?limit=3')
        if response.status_code == 200:
            data = response.json()
            print(f'✅ SUCCESS: Found {len(data["submissions"])} submissions')
            if data['submissions']:
                sub = data['submissions'][0]
                print(f'   Sample: Work Item {sub["work_item_id"]} - Account: {sub["guidewire_account_number"]}, Job: {sub["guidewire_job_number"]}')
            else:
                print('   No submissions with Guidewire data found')
        else:
            print(f'❌ ERROR: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
    
    # Test 2: Get Guidewire stats
    print('\n2. GET /api/guidewire/stats')
    try:
        response = requests.get(f'{base_url}/api/guidewire/stats')
        if response.status_code == 200:
            data = response.json()
            stats = data['integration_stats']
            print(f'✅ SUCCESS: {stats["complete_guidewire_data"]}/{stats["total_work_items"]} work items have complete Guidewire data ({stats["integration_percentage"]}%)')
        else:
            print(f'❌ ERROR: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
    
    # Test 3: Search Guidewire submissions by account number
    print('\n3. GET /api/guidewire/search?account_number=1296620652')
    try:
        response = requests.get(f'{base_url}/api/guidewire/search?account_number=1296620652')
        if response.status_code == 200:
            data = response.json()
            print(f'✅ SUCCESS: Found {data["total_found"]} matches for account number search')
            if data['matches']:
                match = data['matches'][0]
                print(f'   Match: {match["title"]} - Account: {match["guidewire_account_number"]}')
        else:
            print(f'❌ ERROR: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
    
    # Test 4: Get specific work item detail (Work Item 87)
    print('\n4. GET /api/guidewire/submissions/87')
    try:
        response = requests.get(f'{base_url}/api/guidewire/submissions/87')
        if response.status_code == 200:
            data = response.json()
            gw = data['guidewire']
            print(f'✅ SUCCESS: Work Item 87 details retrieved')
            print(f'   Account Number: {gw["account_number"]}')
            print(f'   Job Number: {gw["job_number"]}')
            print(f'   Search Ready: {gw["has_complete_data"]}')
            print(f'   PolicyCenter URL: {gw["policycenter_search_url"]}')
            print(f'   Instructions: {gw["search_instructions"]["account_search"]}')
        else:
            print(f'❌ ERROR: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
    
    print('\n=== API Endpoint Summary for UI Team ===')
    print('1. GET /api/guidewire/submissions - List all submissions with Guidewire data')
    print('2. GET /api/guidewire/submissions/{work_item_id} - Get detailed submission data')  
    print('3. GET /api/guidewire/search - Search submissions by account/job numbers')
    print('4. GET /api/guidewire/stats - Integration statistics for dashboard')
    print('\nAll endpoints return human-readable numbers for PolicyCenter search!')

if __name__ == '__main__':
    test_guidewire_apis()