#!/usr/bin/env python3
"""
Test Freshservice API connection and show available data
"""
import os
import requests
import json
from typing import Dict, Any

# Get credentials from environment
API_KEY = os.getenv("FRESHSERVICE_API_KEY", "")
DOMAIN = os.getenv("FRESHSERVICE_DOMAIN", "ttnmssupport")

if not API_KEY:
    print("❌ Error: FRESHSERVICE_API_KEY not set in environment")
    print("Set it with: export FRESHSERVICE_API_KEY=your_key")
    exit(1)

BASE_URL = f"https://{DOMAIN}.freshservice.com/api/v2"

def test_connection():
    """Test basic API connection"""
    print(f"\n🔍 Testing Freshservice Connection")
    print(f"{'='*60}")
    print(f"Domain: {DOMAIN}")
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:10]}...")
    
    # Test connection
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, auth=(API_KEY, "X"), timeout=5)
        if response.status_code == 200:
            print(f"✅ Connection: SUCCESS")
            return True
        else:
            print(f"❌ Connection: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection: ERROR - {e}")
        return False

def fetch_data(endpoint: str, limit: int = 5) -> Dict[str, Any]:
    """Fetch data from Freshservice endpoint"""
    url = f"{BASE_URL}/{endpoint}"
    params = {"per_page": limit}
    
    try:
        response = requests.get(url, auth=(API_KEY, "X"), params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return {}

def show_endpoint_data(endpoint: str, data_key: str, limit: int = 3):
    """Show sample data from endpoint"""
    print(f"\n📊 {endpoint.upper()}")
    print(f"{'-'*60}")
    
    data = fetch_data(endpoint, limit=limit)
    
    if not data:
        print(f"   ❌ No data returned")
        return
    
    if data_key not in data:
        print(f"   ⚠️  Key '{data_key}' not found in response")
        print(f"   Available keys: {list(data.keys())}")
        return
    
    items = data[data_key]
    
    if not items:
        print(f"   ⚠️  No items found")
        return
    
    # Show count
    total_count = data.get("total_count", len(items))
    print(f"✅ Found {len(items)} items (Total: {total_count})")
    
    # Show columns
    if isinstance(items, list) and len(items) > 0:
        first_item = items[0]
        print(f"\n📋 Column Names:")
        for i, col in enumerate(sorted(first_item.keys()), 1):
            print(f"   {i:2d}. {col}")
        
        # Show sample data
        print(f"\n📝 Sample Data (First item):")
        for key, value in sorted(first_item.items()):
            value_str = str(value)[:50]  # Truncate long values
            print(f"   {key}: {value_str}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 FRESHSERVICE API TEST TOOL")
    print("="*60)
    
    # Test connection
    if not test_connection():
        print("\n❌ Cannot connect to Freshservice API")
        print("\n💡 Troubleshooting:")
        print("   1. Check API key is correct: pRZTtmEWbZvE2K68kOND")
        print("   2. Check domain is correct: ttnmssupport")
        print("   3. Check API key hasn't been revoked")
        print("   4. Check if Freshservice account has API access")
        exit(1)
    
    # Test endpoints
    print(f"\n\n🔍 SCANNING ENDPOINTS")
    print(f"{'='*60}")
    
    endpoints = [
        ("tickets", "tickets"),
        ("incidents", "incidents"),
        ("problems", "problems"),
        ("changes", "changes"),
        ("requesters", "requesters"),
        ("agents", "agents"),
    ]
    
    results = {}
    for endpoint, key in endpoints:
        data = fetch_data(endpoint, limit=1)
        if key in data:
            results[endpoint] = {
                "available": True,
                "count": data.get("total_count", 0),
                "columns": list(data[key][0].keys()) if data[key] else []
            }
            print(f"✅ /{endpoint:<15} - {data.get('total_count', 0):>5} items")
        else:
            results[endpoint] = {"available": False}
            print(f"❌ /{endpoint:<15} - Not available")
    
    # Show detailed data
    print(f"\n\n📊 DETAILED DATA PREVIEW")
    print(f"{'='*60}")
    
    for endpoint, key in endpoints:
        if results.get(endpoint, {}).get("available"):
            show_endpoint_data(endpoint, key)
    
    # Summary
    print(f"\n\n📈 SUMMARY")
    print(f"{'='*60}")
    
    available_count = sum(1 for r in results.values() if r.get("available"))
    print(f"✅ Available Endpoints: {available_count}/{len(endpoints)}")
    
    total_items = sum(r.get("count", 0) for r in results.values() if r.get("available"))
    print(f"📦 Total Items Available: {total_items}")
    
    # Recommendations
    print(f"\n\n💡 RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if results.get("tickets", {}).get("available"):
        print(f"✅ Tickets: {results['tickets']['count']} items")
        print(f"   Columns: {', '.join(results['tickets']['columns'][:5])}...")
        print(f"   → Ready to sync to database")
    
    if results.get("incidents", {}).get("available"):
        print(f"✅ Incidents: {results['incidents']['count']} items")
        print(f"   → Ready to sync to database")
    
    if results.get("problems", {}).get("available"):
        print(f"✅ Problems: {results['problems']['count']} items")
        print(f"   → Ready to sync to database")
    
    if results.get("changes", {}).get("available"):
        print(f"✅ Changes: {results['changes']['count']} items")
        print(f"   → Ready to sync to database")
    
    # Next steps
    print(f"\n\n🚀 NEXT STEPS")
    print(f"{'='*60}")
    print("1. Enable Freshservice sync in .env:")
    print("   LOAD_FRESHSERVICE_DATA=true")
    print("\n2. Restart pipeline:")
    print("   docker-compose restart pipeline")
    print("\n3. Query Freshservice data in Grafana:")
    print("   SELECT * FROM public.freshservice_data;")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()
