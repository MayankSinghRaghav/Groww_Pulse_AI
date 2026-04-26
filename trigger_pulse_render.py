import requests
import time

print("Triggering Weekly Pulse on Render...")
print("="*60)

url = "https://kuvera-pulse.onrender.com/mcp/run-weekly-pulse"
payload = {
    "app_name": "Kuvera",
    "weeks": 8
}

try:
    print("Starting pipeline...")
    print("This will take 2-3 minutes...")
    print()
    
    response = requests.post(url, json=payload, timeout=300)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Weekly Pulse Completed Successfully!")
        print(f"Message: {result.get('message')}")
        print(f"Timestamp: {result.get('timestamp')}")
        print()
        print("PDFs are now generated and ready to download!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("⚠️  Request timed out (this is normal for long operations)")
    print("The pulse is still running on Render.")
    print("Wait 2-3 minutes, then refresh your dashboard.")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*60)
print("Next steps:")
print("1. Wait 2-3 minutes for processing")
print("2. Refresh your Vercel dashboard")
print("3. PDF notes should now be available for download")
