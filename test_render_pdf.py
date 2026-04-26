import requests

# Test Render backend
print("Testing Render backend health...")
try:
    response = requests.get("https://kuvera-pulse.onrender.com/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test PDF download
print("\nTesting PDF download...")
pdf_url = "https://kuvera-pulse.onrender.com/mcp/download-note/Kuvera_Pulse_Product_Team_20260426.pdf"
try:
    response = requests.get(pdf_url)
    print(f"PDF Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {len(response.content)} bytes")
    if response.status_code == 200:
        print("✅ PDF downloaded successfully!")
    else:
        print(f"❌ PDF error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Check latest results
print("\nChecking latest results...")
try:
    response = requests.get("https://kuvera-pulse.onrender.com/mcp/latest-results")
    data = response.json()
    print(f"Last updated: {data.get('last_updated', 'Never')}")
    print(f"Has insights: {'local_clusters' in data.get('insights', {})}")
    print(f"Has emails: {len(data.get('emails', []))} drafts")
except Exception as e:
    print(f"Error: {e}")
