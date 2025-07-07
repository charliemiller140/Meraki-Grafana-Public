import meraki
from influxdb import InfluxDBClient
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
NETWORK_ID = os.getenv("NETWORK_ID")
BAND = os.getenv("BAND")  # "2.4", "5", "6" or None

if not MERAKI_API_KEY or not NETWORK_ID:
    raise ValueError("Missing MERAKI_API_KEY or NETWORK_ID")

dashboard = meraki.DashboardAPI(MERAKI_API_KEY, suppress_logging=True, print_console=False)
client = InfluxDBClient(host="localhost", port=8086, database="meraki")

if "meraki" not in [db["name"] for db in client.get_list_database()]:
    client.create_database("meraki")

# Time window: last 6 hours
now = datetime.now(timezone.utc)
t0 = (now - timedelta(hours=6)).isoformat()
t1 = now.isoformat()

print("Fetching AP devices in network...")
ap_devices = dashboard.networks.getNetworkDevices(NETWORK_ID)
ap_devices = [d for d in ap_devices if d["model"].startswith("MR")]
print(f"Found {len(ap_devices)} APs")

for ap in ap_devices:
    serial = ap["serial"]
    model = ap["model"]
    print(f"Fetching latency history for AP {serial} ({model})")

    try:
        params = {
            "networkId": NETWORK_ID,
            "deviceSerial": serial,
            "t0": t0,
            "t1": t1,
            "resolution": 600,
            "autoResolution": False,
        }
        if BAND in ["2.4", "5", "6"]:
            params["band"] = BAND

        latency_history = dashboard.wireless.getNetworkWirelessLatencyHistory(**params)

        json_body = []
        for entry in latency_history:
            start_ts = entry.get("startTs")
            avg_latency_ms = entry.get("avgLatencyMs")

            if start_ts is None or avg_latency_ms is None:
                continue

            dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
            timestamp = int(dt.timestamp() * 1e9)  # nanoseconds for InfluxDB

            point = {
                "measurement": "wireless_latency_history",
                "time": timestamp,
                "fields": {
                    "avg_latency_ms": float(avg_latency_ms),
                },
                "tags": {
                    "serial": serial,
                    "model": model,
                    "band": BAND if BAND in ["2.4", "5", "6"] else "all"
                }
            }
            json_body.append(point)

        if json_body:
            client.write_points(json_body)
            print(f"Wrote {len(json_body)} latency points for AP {serial}")
        else:
            print(f"No latency data to write for AP {serial}")

    except Exception as e:
        print(f"Error fetching/writing latency history for AP {serial}: {e}")
