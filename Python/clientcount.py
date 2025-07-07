import meraki
from influxdb import InfluxDBClient
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# Config
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
NETWORK_ID = os.getenv("NETWORK_ID")

if not MERAKI_API_KEY or not NETWORK_ID:
    raise ValueError("Missing MERAKI_API_KEY or NETWORK_ID")

dashboard = meraki.DashboardAPI(MERAKI_API_KEY, suppress_logging=True)
client = InfluxDBClient(host="localhost", port=8086, database="meraki")

# Create DB if not exists
if "meraki" not in [db["name"] for db in client.get_list_database()]:
    client.create_database("meraki")

# Time window: last 6 hours
now = datetime.now(timezone.utc)
t0 = (now - timedelta(hours=6)).isoformat()
t1 = now.isoformat()

try:
    print("Fetching client count history")
    client_history = dashboard.wireless.getNetworkWirelessClientCountHistory(
        networkId=NETWORK_ID,
        t0=t0,
        t1=t1,
        resolution=600  # 10 minutes
    )

    json_body = []
    for entry in client_history:
        if entry["clientCount"] is None:
            continue

        dt = datetime.fromisoformat(entry["startTs"].replace("Z", "+00:00"))
        timestamp = int(dt.timestamp() * 1e9)

        point = {
            "measurement": "client_count",
            "time": timestamp,
            "fields": {
                "clientCount": int(entry["clientCount"]),
            },
            "tags": {
                "network": NETWORK_ID
            }
        }
        json_body.append(point)

    if json_body:
        client.write_points(json_body)
        print(f"Wrote {len(json_body)} points to InfluxDB")
    else:
        print("No client count data to write")

except Exception as e:
    print(f"Error fetching/writing client count history: {e}")
