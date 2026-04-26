import requests
import json

print("="*60)
print("DEBUGGING RENDER BACKEND")
print("="*60)

BASE_URL = "https://kuvera-pulse.onrender.com"

# 1. Check health
print("\n1. Health Check:")
try:
    r = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
except Exception as e:
    print(f"   ERROR: {e}")

# 2. Get latest results
print("\n2. Latest Results:")
try:
    r = requests.get(f"{BASE_URL}/mcp/latest-results")
    data = r.json()
    print(f"   Last updated: {data.get('last_updated')}")
    print(f"   Has insights: {'local_clusters' in data.get('insights', {})}")
    print(f"   Number of email drafts: {len(data.get('emails', []))}")
    
    if data.get('emails'):
        print("\n   Email Drafts:")
        for i, email in enumerate(data['emails'], 1):
            print(f"\n   Draft {i}:")
            print(f"     Role: {email['role']}")
            print(f"     PDF Filename: {email.get('pdf_filename')}")
            print(f"     Download Link: {email.get('download_link')}")
            
            # Test if PDF exists
            pdf_url = email.get('download_link')
            if pdf_url:
                try:
                    pdf_r = requests.head(pdf_url, allow_redirects=True)
                    print(f"     PDF Status: {pdf_r.status_code}")
                    if pdf_r.status_code == 200:
                        print(f"     PDF Size: {len(requests.get(pdf_url).content)} bytes")
                    else:
                        print(f"     PDF Error: {pdf_r.text[:200]}")
                except Exception as e:
                    print(f"     PDF Check Error: {e}")
except Exception as e:
    print(f"   ERROR: {e}")

# 3. Test Gmail compose endpoint
print("\n3. Gmail Compose Endpoint:")
try:
    r = requests.get(f"{BASE_URL}/mcp/gmail-compose", params={"role": "Product Team"})
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   PDF Exists: {data.get('pdf_exists')}")
        print(f"   PDF Filename: {data.get('pdf_filename')}")
        print(f"   Has Gmail URL: {'gmail_compose_url' in data}")
    else:
        print(f"   Error: {r.text[:300]}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "="*60)
