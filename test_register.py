import requests, json

payload = {
    "full_name": "Test User",
    "email": "test@example.com",
    "event_name": "Test Event",
    "event_id": 1
}

try:
    r = requests.post("http://127.0.0.1:8000/event/register", json=payload)
    print("Status:", r.status_code)
    print("Response:", r.text)
except Exception as e:
    print("Error:", e)
