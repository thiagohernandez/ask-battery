import requests
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Your credentials from environment variables
app_id = os.environ.get('DEYE_APP_ID')
app_secret = os.environ.get('DEYE_APP_SECRET')
email = os.environ.get('DEYE_EMAIL')
password_hash = os.environ.get('DEYE_PASSWORD_HASH')  # Use pre-hashed password from env

# If plain password is provided instead, hash it
if not password_hash:
    password = os.environ.get('DEYE_PASSWORD')  # Optional: fall back to plain password
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"Your hashed password: {password_hash}")
    else:
        print("ERROR: No DEYE_PASSWORD_HASH or DEYE_PASSWORD provided in .env file")
        exit(1)

# Get token
token_url = "https://api.deyecloud.com/v1.0/token"
response = requests.post(token_url, json={
    "appId": app_id,
    "appSecret": app_secret,
    "email": email,
    "password": password_hash
})
result = response.json()
print("\nToken response:", result)

if result.get('code') == '0' or result.get('success'):
    token = result['data']['access_token']
    print(f"\n✅ Token obtained!")
    
    # Get stations
    stations_url = "https://api.deyecloud.com/v1.0/device/station/list"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    stations = requests.post(stations_url, headers=headers, json={})
    stations_result = stations.json()
    
    print("\n📍 Your stations:")
    print(stations_result)
    
    # Try to extract station IDs
    if 'data' in stations_result:
        if isinstance(stations_result['data'], list):
            for station in stations_result['data']:
                print(f"\n🏠 Station: {station.get('stationName', 'Unknown')}")
                print(f"   Station ID: {station.get('stationId')}")
        elif 'list' in stations_result['data']:
            for station in stations_result['data']['list']:
                print(f"\n🏠 Station: {station.get('stationName', 'Unknown')}")
                print(f"   Station ID: {station.get('stationId')}")
else:
    print(f"\n❌ Login failed: {result}")