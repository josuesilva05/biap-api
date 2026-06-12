import requests
import json

try:
    print("Testing GET /atas/monitoring")
    r = requests.get("http://localhost:8000/atas/monitoring")
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Response: {r.text}")
    else:
        print("Success! Got data.")
        print(r.json()[:2])
except Exception as e:
    print(f"Error: {e}")
