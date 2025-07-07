import meraki
from influxdb import InfluxDBClient
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
NETWORK_ID = os.getenv("NETWORK_ID")

if not MERAKI_API_KEY or not NETWORK_ID:
    raise ValueError("Missing MERAKI_API_KEY or NETWORK_ID")

dashboard = meraki.DashboardAPI(MERAKI_API_KEY, suppress_logging=True, print_console=False)
client = InfluxDBClient(host="localhost", port=8086, database="meraki")

if "meraki" not in [db["name"] for db in client.get_list_database()]:
    client.create_database("meraki")

# Time window: last 2 hours (minimum display in Grafana)
now = datetime.now(timezone.utc)
t0 = (now - timedelta(hours=2)).isoformat()
t1 = now.isoformat()

print("Fetching network traffic data...")

try:
    traffic_data = dashboard.networks.getNetworkTraffic(
        NETWORK_ID,
        t0=t0,
        t1=t1,
        deviceType='combined'
    )
except Exception as e:
    print(f"Error fetching network traffic: {e}")
    traffic_data = []

if not traffic_data:
    print("No traffic data received.")
else:
    json_body = []
    for entry in traffic_data:
        # Use current time as timestamp, or if you have timestamp data from API, parse it similarly to latency script
        timestamp = int(now.timestamp() * 1e9)  # nanoseconds

        point = {
            "measurement": "network_traffic",
            "time": timestamp,
            "fields": {
                "sent": int(entry.get("sent", 0)),
                "recv": int(entry.get("recv", 0)),
                "numClients": int(entry.get("numClients", 0)),
                "activeTime": int(entry.get("activeTime", 0)),
                "flows": int(entry.get("flows", 0)),
            },
            "tags": {
                "application": entry.get("application", "unknown"),
                "protocol": entry.get("protocol", "unknown"),
                "destination": entry.get("destination", "unknown"),
                "port": str(entry.get("port", "unknown")),
            }
        }
        json_body.append(point)

    if json_body:
        try:
            client.write_points(json_body)
            print(f"Wrote {len(json_body)} traffic points to InfluxDB")
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")
    else:
        print("No points to write to InfluxDB")
