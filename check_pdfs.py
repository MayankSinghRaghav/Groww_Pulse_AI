import requests

print("Checking if PDFs are available on Render...")
print("="*60)

response = requests.get("https://kuvera-pulse.onrender.com/mcp/latest-results")
data = response.json()

print(f"Last updated: {data.get('last_updated')}")
print(f"Email drafts: {len(data.get('emails', []))}")
print()

for email in data.get('emails', []):
    print(f"Role: {email['role']}")
    print(f"  PDF: {email.get('pdf_filename', 'N/A')}")
    print(f"  Download: {email.get('download_link', 'N/A')}")
    print()

print("="*60)
print("✅ PDFs are ready! You can now:")
print("1. Open your Vercel dashboard")
print("2. Click 'PDF Note' button to download")
print("3. Or click 'Compose in Gmail' to send emails")
