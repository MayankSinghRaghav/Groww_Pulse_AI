import requests
import time

print("="*60)
print("TRIGGERING PULSE ON UPDATED RENDER DEPLOYMENT")
print("="*60)

# Step 1: Verify deployment
print("\n1. Checking if Render has the latest code...")
try:
    r = requests.get("https://kuvera-pulse.onrender.com/health")
    if r.status_code == 200:
        print(f"   ✅ Backend is running")
        print(f"   Response: {r.json()}")
    else:
        print(f"   ⚠️  Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Step 2: Trigger weekly pulse
print("\n2. Triggering weekly pulse (this will generate PDFs)...")
print("   This may take 2-3 minutes...")
try:
    r = requests.post(
        "https://kuvera-pulse.onrender.com/mcp/run-weekly-pulse",
        json={"app_name": "Kuvera", "weeks": 8},
        timeout=300
    )
    
    if r.status_code == 200:
        result = r.json()
        print(f"   ✅ Pulse completed successfully!")
        print(f"   Message: {result.get('message')}")
    else:
        print(f"   ❌ Error: {r.status_code}")
        print(f"   Response: {r.text[:300]}")
        exit(1)
except requests.exceptions.Timeout:
    print("   ⚠️  Request timed out (normal for long operations)")
    print("   The pulse is still running on Render...")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Step 3: Wait for files to settle
print("\n3. Waiting 15 seconds for files to be generated...")
time.sleep(15)

# Step 4: Verify PDFs
print("\n4. Verifying PDFs were generated...")
try:
    r = requests.get("https://kuvera-pulse.onrender.com/mcp/latest-results")
    data = r.json()
    
    print(f"   Last updated: {data.get('last_updated')}")
    print(f"   Email drafts: {len(data.get('emails', []))}")
    print()
    
    all_good = True
    for email in data.get('emails', []):
        role = email['role']
        pdf_url = email.get('download_link')
        
        try:
            pdf_r = requests.get(pdf_url, timeout=10, stream=True)
            if pdf_r.status_code == 200:
                content_length = int(pdf_r.headers.get('content-length', 0))
                print(f"   ✅ {role}: PDF exists ({content_length} bytes)")
            else:
                print(f"   ❌ {role}: PDF not found (HTTP {pdf_r.status_code})")
                all_good = False
        except Exception as e:
            print(f"   ❌ {role}: Error - {e}")
            all_good = False
    
    print()
    if all_good:
        print("="*60)
        print("🎉 SUCCESS! All PDFs are generated and ready!")
        print("="*60)
        print("\nYou can now:")
        print("1. Open your Vercel dashboard")
        print("2. Click 'PDF Note' to download")
        print("3. Click 'Compose in Gmail' to send emails")
    else:
        print("="*60)
        print("⚠️  Some PDFs are still missing")
        print("="*60)
        print("\nNext steps:")
        print("1. Check Render logs for errors")
        print("2. Look for 'PDF generation failed' messages")
        print("3. The error will tell us exactly what's wrong")
        
except Exception as e:
    print(f"   ❌ Error checking PDFs: {e}")
