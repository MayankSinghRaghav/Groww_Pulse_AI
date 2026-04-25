import requests

# Test the Gmail compose endpoint
url = "http://localhost:8001/mcp/gmail-compose"
params = {
    "role": "Product Team"
}

response = requests.get(url, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
