import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    'https://kuvera-pulse.onrender.com/mcp/run-weekly-pulse', 
    data=b'{"app_name": "Kuvera", "weeks": 8}', 
    headers={'Content-Type': 'application/json'}
)

try:
    response = urllib.request.urlopen(req, context=ctx)
    print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print("Error body:", e.read().decode())
except Exception as e:
    print(f"Exception: {e}")
