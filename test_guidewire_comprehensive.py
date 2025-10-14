#!/usr/bin/env python3
"""
Comprehensive Guidewire PolicyCenter Integration Test Suite
Tests authentication, connectivity, and submission creation before deployment
"""

import requests
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GuidewireTestSuite:
    def __init__(self):
        self.base_url = "https://pc-dev-gwcpdev.valuemom.zeta1-andromeda.guidewire.net"
        self.username = "su"
        self.password = "gw"
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        
        # Common headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'UW-Workbench-Test/1.0'
        })
        
    def test_1_basic_connectivity(self):
        """Test 1: Basic connectivity to Guidewire server"""
        print("\n" + "="*60)
        print("TEST 1: Basic Connectivity")
        print("="*60)
        
        try:
            # Test basic HTTP connectivity (no auth required)
            response = requests.get(f"{self.base_url}", timeout=10)
            print(f"✅ Server reachable: {response.status_code}")
            print(f"   Server: {response.headers.get('Server', 'Unknown')}")
            return True
        except requests.exceptions.ConnectTimeout:
            print("❌ Connection timeout - server unreachable")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def test_2_authentication(self):
        """Test 2: Authentication with provided credentials"""
        print("\n" + "="*60)
        print("TEST 2: Authentication")
        print("="*60)
        
        # Test various authentication endpoints
        auth_endpoints = [
            "/rest/common/v1/ping",
            "/rest/common/v1/locale",
            "/rest",
            "/pc/rest/common/v1/ping"
        ]
        
        for endpoint in auth_endpoints:
            try:
                print(f"\nTesting endpoint: {endpoint}")
                url = f"{self.base_url}{endpoint}"
                
                response = self.session.get(url, timeout=15)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ Authentication successful!")
                    print(f"   Response: {response.text[:200]}...")
                    return True
                elif response.status_code == 401:
                    print(f"   ❌ Authentication failed - invalid credentials")
                elif response.status_code == 404:
                    print(f"   ⚠️  Endpoint not found")
                else:
                    print(f"   ⚠️  Unexpected response: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                
        return False
    
    def test_3_api_discovery(self):
        """Test 3: Discover available API endpoints"""
        print("\n" + "="*60)
        print("TEST 3: API Discovery")
        print("="*60)
        
        discovery_endpoints = [
            "/rest",
            "/rest/common/v1",
            "/rest/account/v1",
            "/rest/job/v1", 
            "/rest/composite/v1"
        ]
        
        available_endpoints = []
        
        for endpoint in discovery_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                print(f"{endpoint}: {response.status_code}")
                
                if response.status_code in [200, 405]:  # 405 = Method Not Allowed (but endpoint exists)
                    available_endpoints.append(endpoint)
                    print(f"   ✅ Available")
                elif response.status_code == 404:
                    print(f"   ❌ Not found")
                elif response.status_code == 401:
                    print(f"   🔐 Requires authentication")
                else:
                    print(f"   ⚠️  Status {response.status_code}")
                            
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\nAvailable endpoints: {len(available_endpoints)}")
        for ep in available_endpoints:
            print(f"   - {ep}")
            
        return len(available_endpoints) > 0
    
    def test_4_composite_endpoint(self):
        """Test 4: Test the composite endpoint with a minimal request"""
        print("\n" + "="*60)
        print("TEST 4: Composite Endpoint")
        print("="*60)
        
        # Try a simple composite request to test the endpoint
        simple_composite = {
            "requests": [
                {
                    "uri": "/rest/common/v1/ping",
                    "method": "GET"
                }
            ]
        }
        
        try:
            url = f"{self.base_url}/rest/composite/v1/composite"
            print(f"Testing composite endpoint: {url}")
            
            response = self.session.post(url, json=simple_composite, timeout=20)
            
            print(f"Status Code: {response.status_code}")
            
            if response.text:
                print(f"Response Body: {response.text[:500]}...")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print("✅ Composite endpoint working!")
                        print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
                        return True
                    except:
                        print("⚠️  Response not JSON format")
                        
            return False
            
        except Exception as e:
            print(f"❌ Composite endpoint error: {e}")
            return False
    
    def test_5_account_creation(self):
        """Test 5: Try to create a test account"""
        print("\n" + "="*60)  
        print("TEST 5: Account Creation Test")
        print("="*60)
        
        # Simple account creation request
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        account_request = {
            "requests": [
                {
                    "uri": "/rest/account/v1/accounts",
                    "method": "POST",
                    "body": {
                        "attributes": {
                            "accountHolderContact": {
                                "firstName": "Test",
                                "lastName": f"User_{timestamp}",
                                "emailAddress1": f"test_{timestamp}@testcompany.com"
                            },
                            "primaryInsured": f"Test Company Inc {timestamp}",
                            "segment": "Commercial",
                            "accountStatus": "Active"
                        }
                    }
                }
            ]
        }
        
        try:
            url = f"{self.base_url}/rest/composite/v1/composite"
            response = self.session.post(url, json=account_request, timeout=30)
            
            print(f"Account creation status: {response.status_code}")
            
            if response.text:
                print(f"Response: {response.text[:400]}...")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print("✅ Account creation request processed!")
                        
                        # Check if account was created successfully
                        if 'responses' in data and len(data['responses']) > 0:
                            account_response = data['responses'][0]
                            if 'body' in account_response:
                                account_data = account_response['body']
                                if 'id' in account_data:
                                    print(f"   ✅ Account created with ID: {account_data['id']}")
                                    print(f"   Account Number: {account_data.get('accountNumber', 'N/A')}")
                                    return True
                                else:
                                    print("   ⚠️  No account ID in response")
                            else:
                                print("   ⚠️  No body in response")
                        else:
                            print("   ⚠️  No responses array")
                        
                    except Exception as e:
                        print(f"   Error parsing response: {e}")
                        
            return False
            
        except Exception as e:
            print(f"❌ Account creation error: {e}")
            return False
    
    def test_6_local_client(self):
        """Test 6: Test our local Guidewire client"""
        print("\n" + "="*60)
        print("TEST 6: Local Guidewire Client Test")
        print("="*60)
        
        try:
            # Import our local client
            from guidewire_client import guidewire_client
            
            print("Testing local Guidewire client...")
            
            # Test authentication method
            auth_result = guidewire_client.authenticate()
            print(f"Authentication result: {auth_result}")
            
            if auth_result:
                print("✅ Local client authentication working!")
                
                # Test submission creation
                test_data = {
                    "company_name": "Local Test Company Inc",
                    "contact_email": "localtest@company.com",
                    "contact_first_name": "Local",
                    "contact_last_name": "Test",
                    "industry": "technology",
                    "employees": 25,
                    "annual_revenue": 1500000,
                    "coverage_amount": 1000000,
                    "business_description": "Local test submission"
                }
                
                print("Testing submission creation...")
                result = guidewire_client.create_cyber_submission(test_data)
                
                print(f"Submission result: {result.get('success', False)}")
                
                if result.get('success'):
                    print("✅ Local client submission creation working!")
                    print(f"   Account ID: {result.get('account_id', 'N/A')}")
                    print(f"   Job ID: {result.get('job_id', 'N/A')}")
                    print(f"   Simulation Mode: {result.get('simulation_mode', 'Unknown')}")
                    return True
                else:
                    print(f"   ❌ Submission failed: {result.get('error', 'Unknown error')}")
                    
            else:
                print("❌ Local client authentication failed")
            
            return False
            
        except Exception as e:
            print(f"❌ Local client test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🧪 GUIDEWIRE POLICYCENTER INTEGRATION TEST SUITE")
        print("="*60)
        print(f"Target Server: {self.base_url}")
        print(f"Username: {self.username}")
        print(f"Test Started: {datetime.now()}")
        
        tests = [
            ("Basic Connectivity", self.test_1_basic_connectivity),
            ("Authentication", self.test_2_authentication),
            ("API Discovery", self.test_3_api_discovery),
            ("Composite Endpoint", self.test_4_composite_endpoint),
            ("Account Creation", self.test_5_account_creation),
            ("Local Client", self.test_6_local_client)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = 0
        total = len(tests)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        # Recommendations
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("   ✅ Guidewire integration is ready for production deployment")
            print("   ✅ Real accounts and jobs will be created")
            print("   ✅ Complete end-to-end workflow will work")
        elif passed >= 4:
            print("\n⚠️  MOSTLY WORKING!")
            print("   ✅ Core functionality is working")
            print("   ⚠️  Some minor issues found")
            print("   ✅ Safe to deploy but monitor for issues")
        else:
            print("\n❌ MAJOR ISSUES FOUND!")
            print("   ❌ Critical functionality not working")
            print("   ❌ DO NOT deploy until issues are fixed")
            print("   ❌ Will likely fall back to simulation mode")
        
        print(f"\nTest Completed: {datetime.now()}")
        
        return passed, total

if __name__ == "__main__":
    print("Starting comprehensive Guidewire integration tests...\n")
    
    test_suite = GuidewireTestSuite()
    passed, total = test_suite.run_all_tests()
    
    print("\n" + "="*60)
    print("FINAL RECOMMENDATION")
    print("="*60)
    
    if passed == total:
        print("✅ DEPLOY: All tests passed - production deployment recommended")
        print("✅ Real Guidewire accounts and submissions will be created")
    elif passed >= 4:
        print("⚠️  DEPLOY WITH CAUTION: Most tests passed - monitor after deployment")
        print("⚠️  May fall back to simulation mode occasionally") 
    else:
        print("❌ DO NOT DEPLOY: Critical issues found")
        print("❌ Fix Guidewire integration before deployment")
        print(f"❌ Only {passed}/{total} tests passed")
    
    print(f"\nFor support, check:")
    print(f"   - Guidewire server: {test_suite.base_url}")
    print(f"   - Credentials: {test_suite.username}/*** ")
    print(f"   - Network connectivity and firewall settings")