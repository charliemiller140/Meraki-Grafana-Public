import meraki
from influxdb import InfluxDBClient
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Meraki config
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
NETWORK_ID = os.getenv("NETWORK_ID")

if not MERAKI_API_KEY or not NETWORK_ID:
    raise ValueError("Missing MERAKI_API_KEY or NETWORK_ID in .env")

# Meraki Dashboard API client
dashboard = meraki.DashboardAPI(MERAKI_API_KEY, suppress_logging=True)

# InfluxDB client
client = InfluxDBClient(host="localhost", port=8086, database="meraki")

# Create DB if it doesn't exist
dbs = [db['name'] for db in client.get_list_database()]
if "meraki" not in dbs:
    client.create_database("meraki")

# Get all devices in the network
devices = dashboard.networks.getNetworkDevices(NETWORK_ID)

for device in devices:
    serial = device.get("serial")
    model = device.get("model")
    name = device.get("name")

    print(f"Fetching channel utilization for device {name} ({serial})")

    for band in ["2.4", "5"]:
        try:
            now = datetime.now(timezone.utc)
            t0 = (now - timedelta(days=1)).isoformat()
            t1 = now.isoformat()

            utilization_history = dashboard.wireless.getNetworkWirelessChannelUtilizationHistory(
                NETWORK_ID,
                deviceSerial=serial,
                band=band,
                t0=t0,
                t1=t1,
                resolution=600  # 10-minute buckets
            )

            print(f"Received {len(utilization_history)} entries for {serial} on {band}GHz")

            json_body = []
            for entry in utilization_history:
                if entry["utilizationTotal"] is None:
                    continue  # skip entries with no data

                dt = datetime.fromisoformat(entry["startTs"].replace("Z", "+00:00"))
                timestamp = int(dt.timestamp() * 1e9)  # nanoseconds

                point = {
                    "measurement": "channel_utilization",
                    "time": timestamp,
                    "fields": {
                        "utilizationTotal": float(entry["utilizationTotal"]),
                        "utilization80211": float(entry["utilization80211"]),
                        "utilizationNon80211": float(entry["utilizationNon80211"]),
                    },
                    "tags": {
                        "serial": serial,
                        "model": model,
                        "band": f"{band}GHz",
                    }
                }
                json_body.append(point)

            if json_body:
                client.write_points(json_body)
                print(f"Wrote {len(json_body)} points for {serial} on {band}GHz")
            else:
                print(f"No data to write for {serial} on {band}GHz")

        except Exception as e:
            print(f"Error fetching/writing data for {serial} on {band}GHz: {e}")
