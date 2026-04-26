import requests

print("Regenerating PDFs on Render...")
print("="*60)

# First, get the current insights
print("\n1. Fetching current insights...")
try:
    r = requests.get("https://kuvera-pulse.onrender.com/mcp/latest-results")
    data = r.json()
    has_insights = 'local_clusters' in data.get('insights', {})
    print(f"   Has insights: {has_insights}")
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# The issue is that PDFs need to be generated separately
# Let's trigger a fresh pulse which will generate PDFs
print("\n2. Triggering fresh pulse (this will generate PDFs)...")
try:
    r = requests.post(
        "https://kuvera-pulse.onrender.com/mcp/run-weekly-pulse",
        json={"app_name": "Kuvera", "weeks": 8},
        timeout=300
    )
    
    if r.status_code == 200:
        result = r.json()
        print("   ✅ Pulse completed!")
        print(f"   Message: {result.get('message')}")
    else:
        print(f"   ❌ Error: {r.status_code}")
        print(f"   Response: {r.text[:300]}")
except Exception as e:
    print(f"   ⚠️  Request issue: {e}")

print("\n3. Waiting 10 seconds for files to settle...")
import time
time.sleep(10)

# Verify PDFs exist
print("\n4. Verifying PDFs...")
try:
    r = requests.get("https://kuvera-pulse.onrender.com/mcp/latest-results")
    data = r.json()
    
    for email in data.get('emails', []):
        pdf_url = email.get('download_link')
        role = email['role']
        
        try:
            pdf_r = requests.get(pdf_url, timeout=10)
            if pdf_r.status_code == 200:
                print(f"   ✅ {role}: PDF exists ({len(pdf_r.content)} bytes)")
            else:
                print(f"   ❌ {role}: PDF not found (status {pdf_r.status_code})")
        except Exception as e:
            print(f"   ❌ {role}: Error checking PDF - {e}")
            
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "="*60)
print("Done! Try downloading PDFs from your dashboard now.")
