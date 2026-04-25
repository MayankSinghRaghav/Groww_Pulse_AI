import requests

try:
    response = requests.post(
        "https://kuvera-pulse.onrender.com/mcp/run-weekly-pulse",
        json={"app_name": "Kuvera", "weeks": 8}
    )
    print("Status Code:", response.status_code)
    print("Headers:", response.headers)
    print("Text:", response.text)
except Exception as e:
    print("Error:", e)
