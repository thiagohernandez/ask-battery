import requests
import hashlib
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Your credentials from environment variables
app_id = os.environ.get('DEYE_APP_ID')
app_secret = os.environ.get('DEYE_APP_SECRET')
email = os.environ.get('DEYE_EMAIL')
password_hash = os.environ.get('DEYE_PASSWORD_HASH')
station_id = os.environ.get('DEYE_STATION_ID')

# Get API base URL from environment
api_url = os.environ.get('DEYE_API_URL', 'https://eu1-developer.deyecloud.com/')
api_url = api_url.rstrip('/')

print("=" * 60)
print("🔋 Deye Battery Level Test")
print("=" * 60)
print(f"\n📍 Station ID: {station_id}")
print(f"🌐 API URL: {api_url}")

# Step 1: Get access token
print("\n1️⃣ Getting access token...")
token_url = f"{api_url}/v1.0/account/token?appId={app_id}"
headers = {
    'Content-Type': 'application/json'
}

try:
    response = requests.post(token_url, headers=headers, json={
        "appSecret": app_secret,
        "email": email,
        "password": password_hash
    }, timeout=10)

    result = response.json()

    if result.get('code') == 1000000 or result.get('success'):
        token = result.get('accessToken')
        print(f"   ✅ Token obtained successfully")
        print(f"   Token expires in: {result.get('expiresIn')} seconds")
    else:
        print(f"   ❌ Failed to get token: {result.get('msg')}")
        exit(1)

except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Step 2: Query station latest data for battery level
print("\n2️⃣ Fetching station latest data...")

station_latest_url = f"{api_url}/v1.0/station/latest"
print(f"   🔍 Endpoint: {station_latest_url}")

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

payload = {
    "stationId": int(station_id)
}

try:
    response = requests.post(station_latest_url, headers=headers, json=payload, timeout=10)
    print(f"   Status: {response.status_code}")

    result = response.json()

    if response.status_code == 200 and (result.get('code') == 1000000 or result.get('success')):
        print(f"   ✅ Success!")
        station_data = result

        print("\n" + "=" * 60)
        print("✅ Station Data Retrieved Successfully!")
        print("=" * 60)

        print(f"\n📋 Full Response:")
        print(json.dumps(station_data, indent=2))

        # The response has the data at the top level, not nested in 'data'
        print(f"\n🔋 Battery Information:")
        print("=" * 60)

        # Look for battery percentage
        battery_percent = (
            station_data.get('batterySoc') or
            station_data.get('battery_soc') or
            station_data.get('batterySOC') or
            station_data.get('batteryPercentage') or
            station_data.get('battery_percentage') or
            'N/A'
        )

        if battery_percent != 'N/A':
            print(f"   🔋 Battery Level: {int(battery_percent)}%")
        else:
            print(f"   🔋 Battery Level: {battery_percent}")

        # Look for battery power
        battery_power = (
            station_data.get('batteryPower') or
            station_data.get('battery_power') or
            station_data.get('batterypower')
        )

        if battery_power:
            # chargePower and dischargePower indicate direction
            if battery_power > 50:
                print(f"   ⚡ Battery Charging: {int(battery_power)}W")
            elif battery_power < -50:
                print(f"   🔋 Battery Discharging: {int(abs(battery_power))}W")
            else:
                print(f"   ⏸️ Battery Idle: {int(battery_power)}W")

        # Solar generation
        solar = station_data.get('generationPower')
        if solar:
            print(f"   ☀️ Solar Generation: {int(solar)}W")

        # Home consumption
        consumption = station_data.get('consumptionPower')
        if consumption:
            print(f"   🏠 Home Consumption: {int(consumption)}W")

        # Grid power
        grid = station_data.get('gridPower')
        if grid:
            print(f"   🔌 Grid Power: {int(grid)}W")

        # Update time
        last_update = station_data.get('lastUpdateTime')
        if last_update:
            from datetime import datetime
            update_time = datetime.fromtimestamp(last_update)
            print(f"   🕐 Last Update: {update_time}")

        print("=" * 60)

    else:
        print(f"   ❌ Error: {result.get('msg', 'Unknown error')}")
        print(f"\n   Response: {json.dumps(result, indent=2)}")
        exit(1)

except Exception as e:
    print(f"   ❌ Request failed: {e}")
    exit(1)
