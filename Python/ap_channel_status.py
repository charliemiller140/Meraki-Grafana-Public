import os
from datetime import datetime
import meraki
from influxdb import InfluxDBClient
from dotenv import load_dotenv

load_dotenv()

MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
NETWORK_ID = os.getenv("NETWORK_ID")
dashboard = meraki.DashboardAPI(MERAKI_API_KEY, suppress_logging=True)

influx_client = InfluxDBClient(host='localhost', port=8086, database='meraki')

timestamp = int(datetime.utcnow().timestamp() * 1e9)

try:
    devices = dashboard.networks.getNetworkDevices(NETWORK_ID)
except Exception as e:
    print(f"Error getting devices for network {NETWORK_ID}: {e}")
    devices = []

for device in devices:
    if not device["model"].startswith("MR"):
        continue

    serial = device["serial"]
    model = device["model"]

    try:
        status = dashboard.wireless.getDeviceWirelessStatus(serial)
        bss_list = status.get("basicServiceSets", [])
    except Exception as e:
        print(f"Error getting wireless status for device {serial}: {e}")
        continue

    json_body = []

    for bss in bss_list:
        if bss.get("channel") is None:
            continue

        power_str = bss.get("power")
        if power_str:
            power_val = int(power_str.replace(" dBm", ""))
        else:
            power_val = 0

        point = {
            "measurement": "ap_channel_status",
            "time": timestamp,
            "fields": {
                "channel": int(bss["channel"]),
                "power": power_val
            },
            "tags": {
                "serial": serial,
                "model": model,
                "band": bss.get("band", "unknown"),
                "ssid": bss.get("ssidName", "unknown")
            }
        }
        json_body.append(point)

    if json_body:
        try:
            influx_client.write_points(json_body, time_precision="n")
            print(f"Wrote {len(json_body)} points for device {serial}")
        except Exception as e:
            print(f"Error writing to InfluxDB for device {serial}: {e}")
