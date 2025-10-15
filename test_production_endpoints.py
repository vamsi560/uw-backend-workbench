#!/usr/bin/env python3
"""
Test production backend endpoints to see what's available for UI team
"""

import requests
import json

def test_production_endpoints():
    print('Checking available endpoints on production backend...')
    
    base_url = 'https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net'
    
    # Test root endpoint to see what's available
    try:
        response = requests.get(f'{base_url}/', timeout=10)
        print(f'Root endpoint - Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print('✅ Available endpoints:')
            if 'endpoints' in data:
                for key, endpoint in data['endpoints'].items():
                    print(f'   {key}: {endpoint}')
            print(f'   API Version: {data.get("version", "unknown")}')
            print(f'   Status: {data.get("status", "unknown")}')
        else:
            print(f'Response: {response.text[:300]}')
    except Exception as e:
        print(f'Root error: {e}')
    
    # Check if we can see all work items (this should exist)
    try:
        response = requests.get(f'{base_url}/api/workitems?limit=1', timeout=15)
        print(f'\nWork items API - Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Work items endpoint working - Found {len(data)} items')
        else:
            print(f'Response: {response.text[:200]}')
    except Exception as e:
        print(f'Work items error: {e}')
    
    # Check polling endpoint
    try:
        response = requests.get(f'{base_url}/api/workitems/poll?limit=1', timeout=15)
        print(f'Polling API - Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f'✅ Polling endpoint working - Found {count} items')
            if data.get('items'):
                item = data['items'][0]
                item_id = item.get('id', 'N/A')
                status = item.get('status', 'N/A')
                print(f'   Sample: ID {item_id}, Status: {status}')
        else:
            print(f'Response: {response.text[:200]}')
    except Exception as e:
        print(f'Polling error: {e}')
    
    # Test Guidewire endpoints specifically
    guidewire_endpoints = [
        '/api/guidewire/submissions',
        '/api/guidewire/stats', 
        '/api/guidewire/search',
        '/api/guidewire/submissions/1'
    ]
    
    print(f'\n=== Testing Guidewire Endpoints ===')
    for endpoint in guidewire_endpoints:
        try:
            response = requests.get(f'{base_url}{endpoint}', timeout=10)
            status = response.status_code
            
            if status == 200:
                print(f'✅ {endpoint} - Working (200)')
            elif status == 404:
                print(f'❌ {endpoint} - Not Found (404)')
            elif status == 500:
                print(f'⚠️  {endpoint} - Server Error (500)')
            else:
                print(f'⚠️  {endpoint} - Status {status}')
                
        except Exception as e:
            print(f'❌ {endpoint} - Error: {str(e)[:100]}')
    
    print(f'\n=== Analysis Complete ===')
    print(f'Backend URL: {base_url}')
    print(f'The Guidewire endpoints may not be deployed in the current version.')
    print(f'UI team should use the working endpoints above.')

if __name__ == "__main__":
    test_production_endpoints()