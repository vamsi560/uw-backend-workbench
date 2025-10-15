#!/usr/bin/env python3
"""
Test the Guidewire API endpoints to diagnose issues
"""
import requests
import sys
import time
import json

def test_guidewire_apis():
    """Test all Guidewire API endpoints"""
    print('=== Testing Guidewire APIs ===')
    
    base_url = 'http://localhost:8000'
    
    # Test 1: Health check first
    print('\n1. Testing Health Check...')
    try:
        response = requests.get(f'{base_url}/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Health check passed - Status: {data.get("status", "unknown")}')
        else:
            print(f'❌ Health check failed: {response.status_code}')
            print(f'   Response: {response.text[:200]}')
            return False
    except Exception as e:
        print(f'❌ Health check error: {str(e)}')
        print('   Server might not be running')
        return False
    
    # Test 2: Guidewire submissions endpoint  
    print('\n2. Testing /api/guidewire/submissions...')
    try:
        response = requests.get(f'{base_url}/api/guidewire/submissions?limit=3', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Guidewire submissions API working')
            print(f'   Found {len(data.get("submissions", []))} submissions')
            print(f'   Total in DB: {data.get("pagination", {}).get("total", 0)}')
            if data.get('submissions'):
                sub = data['submissions'][0]
                print(f'   Sample: Work Item {sub.get("work_item_id")} - Account: {sub.get("guidewire_account_number")}')
        else:
            print(f'❌ Guidewire submissions failed: {response.status_code}')
            print(f'   Response: {response.text[:500]}')
    except Exception as e:
        print(f'❌ Guidewire submissions error: {str(e)}')
    
    # Test 3: Guidewire stats endpoint
    print('\n3. Testing /api/guidewire/stats...')
    try:  
        response = requests.get(f'{base_url}/api/guidewire/stats', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Guidewire stats API working')
            stats = data.get('integration_stats', {})
            print(f'   Total work items: {stats.get("total_work_items", 0)}')
            print(f'   Complete Guidewire data: {stats.get("complete_guidewire_data", 0)}')
            print(f'   Integration percentage: {stats.get("integration_percentage", 0)}%')
        else:
            print(f'❌ Guidewire stats failed: {response.status_code}')
            print(f'   Response: {response.text[:500]}')
    except Exception as e:
        print(f'❌ Guidewire stats error: {str(e)}')
    
    # Test 4: Guidewire search endpoint
    print('\n4. Testing /api/guidewire/search...')
    try:
        response = requests.get(f'{base_url}/api/guidewire/search?account_number=1296620652', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Guidewire search API working')  
            print(f'   Found {data.get("total_found", 0)} search results')
            if data.get('matches'):
                match = data['matches'][0]
                print(f'   Match: {match.get("title")} - Account: {match.get("guidewire_account_number")}')
        else:
            print(f'❌ Guidewire search failed: {response.status_code}')
            print(f'   Response: {response.text[:500]}')
    except Exception as e:
        print(f'❌ Guidewire search error: {str(e)}')
    
    # Test 5: Specific work item detail
    print('\n5. Testing /api/guidewire/submissions/87...')
    try:
        response = requests.get(f'{base_url}/api/guidewire/submissions/87', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Work item detail API working')
            gw = data.get('guidewire', {})
            print(f'   Account Number: {gw.get("account_number")}')
            print(f'   Job Number: {gw.get("job_number")}') 
            print(f'   Search Ready: {gw.get("has_complete_data")}')
        elif response.status_code == 404:
            print(f'⚠️  Work item 87 not found (this is OK if it doesn\'t exist)')
        else:
            print(f'❌ Work item detail failed: {response.status_code}')
            print(f'   Response: {response.text[:500]}')
    except Exception as e:
        print(f'❌ Work item detail error: {str(e)}')
    
    print('\n=== Test Summary ===')
    print('If you see ✅ marks above, the APIs are working correctly.')
    print('If you see ❌ marks, there are issues that need to be fixed.')
    print('\nAll endpoints for UI team:')
    print('• GET /api/guidewire/submissions - List submissions with Guidewire data')
    print('• GET /api/guidewire/submissions/{id} - Get detailed submission data')
    print('• GET /api/guidewire/search - Search by account/job numbers')
    print('• GET /api/guidewire/stats - Integration statistics')
    
    return True

if __name__ == '__main__':
    test_guidewire_apis()