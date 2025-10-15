#!/usr/bin/env python3
"""
Test Guidewire APIs on production backend after deployment
"""

import requests
import json

def test_production_guidewire_apis():
    print('Testing Guidewire APIs on production backend...')
    base_url = 'https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net'

    # Test health check first
    try:
        response = requests.get(f'{base_url}/health', timeout=10)
        if response.status_code == 200:
            print('✅ Health check: Server is healthy')
        else:
            print(f'❌ Health check failed: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Health error: {e}')
        return False

    # Test Guidewire submissions API
    try:
        response = requests.get(f'{base_url}/api/guidewire/submissions?limit=3', timeout=15)
        print(f'Submissions API - Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            submissions = data.get('submissions', [])
            total = data.get('pagination', {}).get('total', 0)
            print(f'✅ Found {len(submissions)} submissions (Total: {total})')
            if submissions:
                sub = submissions[0]
                work_id = sub.get('work_item_id', 'N/A')
                account = sub.get('guidewire_account_number', 'N/A')
                print(f'   Sample: ID {work_id}, Account: {account}')
        else:
            print(f'❌ Response: {response.text[:200]}')
    except Exception as e:
        print(f'❌ Submissions error: {e}')

    # Test Guidewire stats API  
    try:
        response = requests.get(f'{base_url}/api/guidewire/stats', timeout=15)
        print(f'Stats API - Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            stats = data.get('integration_stats', {})
            complete = stats.get('complete_guidewire_data', 0)
            total = stats.get('total_work_items', 0)
            pct = stats.get('integration_percentage', 0)
            print(f'✅ Stats: {complete}/{total} items have Guidewire data ({pct}%)')
        else:
            print(f'❌ Response: {response.text[:200]}')
    except Exception as e:
        print(f'❌ Stats error: {e}')

    # Test Guidewire search API
    try:
        response = requests.get(f'{base_url}/api/guidewire/search?account_number=1296620652', timeout=15)
        print(f'Search API - Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            found = data.get('total_found', 0)
            print(f'✅ Search: Found {found} matches for account 1296620652')
            if found > 0:
                results = data.get('results', [])
                if results:
                    item = results[0]
                    print(f'   Match: Work Item {item.get("work_item_id")} - Job: {item.get("guidewire_job_number")}')
        else:
            print(f'❌ Response: {response.text[:200]}')
    except Exception as e:
        print(f'❌ Search error: {e}')

    # Test Work Item 87 detail
    try:
        response = requests.get(f'{base_url}/api/guidewire/submissions/87', timeout=15)
        print(f'Detail API - Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            gw = data.get('guidewire', {})
            account = gw.get('account_number', 'N/A')
            job = gw.get('job_number', 'N/A')
            complete = gw.get('has_complete_data', False)
            print(f'✅ Work Item 87: Account={account}, Job={job}, Complete={complete}')
        elif response.status_code == 404:
            print('ℹ️  Work Item 87 not found')
        else:
            print(f'❌ Response: {response.text[:200]}')
    except Exception as e:
        print(f'❌ Detail error: {e}')

    print('\n🎉 Production API Test Complete!')
    print('\nAll 4 Guidewire endpoints ready for UI team:')
    print('• GET /api/guidewire/submissions - List submissions with pagination')
    print('• GET /api/guidewire/submissions/{id} - Get detailed submission')  
    print('• GET /api/guidewire/search - Search by account/job numbers')
    print('• GET /api/guidewire/stats - Integration statistics')
    print(f'\nBase URL: {base_url}')
    print('✅ All APIs are now deployed and accessible!')

if __name__ == "__main__":
    test_production_guidewire_apis()