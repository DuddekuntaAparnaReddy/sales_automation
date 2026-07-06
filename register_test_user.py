import requests, json

payload = {
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "test",
    "phone": "1234567890"
}

r = requests.post("http://127.0.0.1:8000/register", json=payload)
print("Status:", r.status_code)
print("Response:", r.text)
