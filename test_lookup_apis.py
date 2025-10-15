"""
Test the Guidewire lookup API endpoints
"""
import requests
import json

def test_lookup_apis():
    base_url = "http://localhost:8000"
    
    endpoints = [
        ("/api/guidewire-lookups/", "Get all lookups"),
        ("/api/guidewire-lookups/search/2332505940", "Search by account number"),
        ("/api/guidewire-lookups/work-item/77", "Get work item 77 lookup"),
        ("/api/guidewire-lookups/latest", "Get latest lookups")
    ]
    
    print("🧪 TESTING GUIDEWIRE LOOKUP APIs")
    print("=" * 40)
    
    for endpoint, description in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=5)
            
            print(f"\n🔍 {description}")
            print(f"   URL: {endpoint}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"   Records: {len(data)}")
                    if data:
                        record = data[0]
                        if 'account_number' in record:
                            print(f"   Sample Account: {record.get('account_number')}")
                        if 'organization_name' in record:
                            print(f"   Sample Org: {record.get('organization_name')}")
                elif isinstance(data, dict):
                    print(f"   Account: {data.get('account_number', 'N/A')}")
                    print(f"   Status: {data.get('sync_status', 'N/A')}")
            else:
                print(f"   Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Server not running - start with: python main.py")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n✅ API Test Complete!")
    print(f"\n📝 TO START SERVER:")
    print(f"   python main.py")
    print(f"\n🌐 THEN TEST IN BROWSER:")
    print(f"   http://localhost:8000/api/guidewire-lookups/")
    print(f"   http://localhost:8000/api/guidewire-lookups/search/2332505940")

if __name__ == "__main__":
    test_lookup_apis()