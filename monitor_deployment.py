#!/usr/bin/env python3
"""
Monitor deployment status by checking for new approval endpoints
"""

import requests
import time
from datetime import datetime

API_BASE_URL = "https://wu-workbench-backend-h3fkfkcpbjgga7hx.centralus-01.azurewebsites.net"

def check_deployment_status():
    """Check if the new approval endpoints are deployed"""
    print(f"🚀 Monitoring deployment status...")
    print(f"Backend URL: {API_BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Test endpoints that should be available after deployment
    test_endpoints = [
        {
            "name": "Work Item UW Issues",
            "method": "GET",
            "url": "/api/workitems/87/uw-issues",
            "description": "Get UW issues for work item"
        },
        {
            "name": "Approval Workflow Test", 
            "method": "POST",
            "url": "/api/test/approval-workflow",
            "data": {"job_id": "pc:S9Z7G9A7dGlQCKdKlc-G6"},
            "description": "Test complete approval workflow"
        },
        {
            "name": "Document Storage (existing)",
            "method": "POST", 
            "url": "/api/fetch-and-store-quote-documents",
            "data": {"job_id": "pc:S9Z7G9A7dGlQCKdKlc-G6"},
            "description": "Existing document endpoint (should work)"
        }
    ]
    
    results = {}
    
    for endpoint in test_endpoints:
        try:
            url = f"{API_BASE_URL}{endpoint['url']}"
            
            if endpoint["method"] == "GET":
                response = requests.get(url, timeout=10)
            elif endpoint["method"] == "POST":
                data = endpoint.get("data", {})
                response = requests.post(url, json=data, timeout=10)
            
            status_code = response.status_code
            
            if status_code == 200:
                status = "✅ Available"
                results[endpoint["name"]] = True
            elif status_code == 404:
                status = "❌ Not Found"
                results[endpoint["name"]] = False
            elif status_code == 422:
                status = "⚠️  Available (validation error)"
                results[endpoint["name"]] = True
            else:
                status = f"⚠️  HTTP {status_code}"
                results[endpoint["name"]] = False
                
            print(f"{status} {endpoint['name']}")
            print(f"   {endpoint['description']}")
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error - {endpoint['name']}")
            print(f"   Backend may be restarting...")
            results[endpoint["name"]] = False
        except Exception as e:
            print(f"❌ Error - {endpoint['name']}: {str(e)[:100]}")
            results[endpoint["name"]] = False
    
    # Calculate deployment status
    new_endpoints = ["Work Item UW Issues", "Approval Workflow Test"]
    new_deployed = sum(1 for name in new_endpoints if results.get(name, False))
    total_new = len(new_endpoints)
    
    existing_working = results.get("Document Storage (existing)", False)
    
    print("\n" + "=" * 50)
    print(f"📊 DEPLOYMENT STATUS")
    print(f"New Endpoints: {new_deployed}/{total_new} deployed")
    print(f"Existing Endpoints: {'✅ Working' if existing_working else '❌ Issues'}")
    
    if new_deployed == total_new and existing_working:
        print(f"🎉 DEPLOYMENT COMPLETE - All endpoints ready!")
        return True
    elif new_deployed > 0:
        print(f"🔄 DEPLOYMENT IN PROGRESS - {new_deployed}/{total_new} new endpoints ready")
        return False
    elif existing_working:
        print(f"⏳ DEPLOYMENT PENDING - New endpoints not yet available")
        return False
    else:
        print(f"❌ DEPLOYMENT ISSUE - Backend may be down")
        return False

def monitor_deployment():
    """Monitor deployment with periodic checks"""
    max_attempts = 20  # Check for up to 10 minutes (30s intervals)
    attempt = 0
    
    print(f"🔍 Starting deployment monitoring...")
    print(f"Will check every 30 seconds for up to {max_attempts * 30 // 60} minutes\n")
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n📡 Check #{attempt}/{max_attempts}")
        
        if check_deployment_status():
            print(f"\n🎯 SUCCESS! Deployment is complete and ready for testing.")
            return True
        
        if attempt < max_attempts:
            print(f"\n⏱️  Waiting 30 seconds before next check...")
            time.sleep(30)
        
    print(f"\n⏰ Monitoring timeout reached. Deployment may still be in progress.")
    print(f"You can manually check: {API_BASE_URL}")
    return False

if __name__ == "__main__":
    if monitor_deployment():
        print(f"\n🚀 Ready to test approval workflow!")
        print(f"Run: python test_approval_api.py")
    else:
        print(f"\n💡 Try checking deployment status manually or wait a bit longer.")