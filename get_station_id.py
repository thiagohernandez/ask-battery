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

# If plain password is provided instead, hash it with SHA256
if not password_hash:
    password = os.environ.get('DEYE_PASSWORD')  # Optional: fall back to plain password
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"Your SHA256 hashed password: {password_hash}")
    else:
        print("ERROR: No DEYE_PASSWORD_HASH or DEYE_PASSWORD provided in .env file")
        exit(1)

# Get API base URL from environment
api_url = os.environ.get('DEYE_API_URL', 'https://eu1-developer.deyecloud.com/')
api_url = api_url.rstrip('/')  # Remove trailing slash for proper concatenation

# Get token - using the endpoint format with appId as query parameter
token_url = f"{api_url}/v1.0/account/token?appId={app_id}"
headers = {
    'Content-Type': 'application/json'
}
response = requests.post(token_url, headers=headers, json={
    "appSecret": app_secret,
    "email": email,
    "password": password_hash
})
result = response.json()
print("\nToken response:", result)

# Extract token from response - check different possible response structures
token = None
if result.get('code') == 1000000 or result.get('success'):
    # Try different paths where token might be
    if isinstance(result.get('data'), dict):
        token = result['data'].get('access_token')
    elif result.get('accessToken'):
        token = result.get('accessToken')

    if token:
        print(f"\n✅ Token obtained!")
    else:
        print(f"\n❌ Token not found in response: {result}")
        exit(1)
else:
    print(f"\n❌ Login failed: {result}")
    exit(1)

if token:
    print(f"\n🔐 Token obtained successfully!")

    # Try different Authorization header formats
    headers_variants = [
        {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        {'Authorization': token, 'Content-Type': 'application/json'},
        {'X-Access-Token': token, 'Content-Type': 'application/json'},
    ]

    headers = headers_variants[0]  # Start with Bearer

    # Get device list
    device_list_url = f"{api_url}/v1.0/device/list"
    print(f"\n🔍 Fetching devices from: {device_list_url}")

    payload = {
        "page": 1,
        "size": 100
    }

    result = None
    found_valid = False

    # Try each header variant
    for i, h in enumerate(headers_variants, 1):
        try:
            print(f"\n   🔄 Trying header variant {i}...")
            response = requests.post(device_list_url, headers=h, json=payload, timeout=10)
            print(f"   Status: {response.status_code}")
            result = response.json()

            # Check if successful
            if result.get('code') == 1000000 or result.get('success'):
                print(f"   ✅ Success with variant {i}!")
                found_valid = True
                break
            else:
                print(f"   ❌ {result.get('msg', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            print(f"   Request failed: {e}")

    if not found_valid:
        print(f"\n❌ Failed with all header variants")
        print(f"Last response: {result}")
        exit(1)

    print(f"\n📋 Device List Response:")
    print(result)

    # Extract device information
    if result.get('code') == 1000000 or result.get('success'):
        devices = result.get('deviceList', [])
        print(f"\n✅ Found {len(devices)} device(s):")

        for device in devices:
            print(f"\n📱 Device:")
            print(f"   Serial Number: {device.get('deviceSn')}")
            print(f"   Device ID: {device.get('deviceId')}")
            print(f"   Type: {device.get('deviceType')}")
            print(f"   State: {device.get('deviceState')}")
            print(f"   Product ID: {device.get('productId')}")
else:
    print(f"\n❌ Login failed: {result}")
    exit(1)
