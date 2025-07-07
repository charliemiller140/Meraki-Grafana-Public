import meraki
from influxdb import InfluxDBClient
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# Config
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
NETWORK_ID = os.getenv("NETWORK_ID")
BAND = os.getenv("BAND")  # Expected: "2.4", "5", "6" or None/other for all bands

if not MERAKI_API_KEY or not NETWORK_ID:
    raise ValueError("Missing MERAKI_API_KEY or NETWORK_ID")

dashboard = meraki.DashboardAPI(MERAKI_API_KEY, suppress_logging=True, print_console=False)
client = InfluxDBClient(host="localhost", port=8086, database="meraki")

# Create DB if not exists
if "meraki" not in [db["name"] for db in client.get_list_database()]:
    client.create_database("meraki")

# Time window: last 6 hours
now = datetime.now(timezone.utc)
t0 = (now - timedelta(hours=6)).isoformat()
t1 = now.isoformat()

# Get all AP devices in the network
print("Fetching AP devices in network...")
ap_devices = dashboard.networks.getNetworkDevices(NETWORK_ID)
ap_devices = [d for d in ap_devices if d["model"].startswith("MR")]  # Filter APs (Meraki APs start with MR)
print(f"Found {len(ap_devices)} APs")

for ap in ap_devices:
    serial = ap["serial"]
    model = ap["model"]
    print(f"Fetching signal quality history for AP {serial} ({model})")

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

        signal_quality = dashboard.wireless.getNetworkWirelessSignalQualityHistory(**params)

        json_body = []
        for entry in signal_quality:
            start_ts = entry.get("startTs")
            snr = entry.get("snr")
            rssi = entry.get("rssi")

            if start_ts is None or snr is None or rssi is None:
                continue

            dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
            timestamp = int(dt.timestamp() * 1e9)  # nanoseconds

            point = {
                "measurement": "wireless_signal_quality",
                "time": timestamp,
                "fields": {
                    "snr": float(snr),
                    "rssi": float(rssi),
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
            print(f"Wrote {len(json_body)} points for AP {serial}")
        else:
            print(f"No signal quality data to write for AP {serial}")

    except Exception as e:
        print(f"Error fetching/writing signal quality for AP {serial}: {e}")
