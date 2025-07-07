import meraki
from influxdb import InfluxDBClient
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_ID = os.getenv("ORG_ID")

if not MERAKI_API_KEY or not ORG_ID:
    raise ValueError("Missing MERAKI_API_KEY or ORG_ID")

dashboard = meraki.DashboardAPI(MERAKI_API_KEY, suppress_logging=True)
client = InfluxDBClient(host="localhost", port=8086, database="meraki")

# Create DB if not exists
if "meraki" not in [db["name"] for db in client.get_list_database()]:
    client.create_database("meraki")

# Time window: last 1 day
now = datetime.now(timezone.utc)
t1 = now.isoformat()
t0 = (now - timedelta(days=1)).isoformat()

try:
    top_devices = dashboard.organizations.getOrganizationSummaryTopDevicesByUsage(
        organizationId=ORG_ID,
        t0=t0,
        t1=t1,
        quantity=10
    )

    json_body = []
    for device in top_devices:
        point = {
            "measurement": "top_device_usage",
            "time": int(datetime.now(timezone.utc).timestamp() * 1e9),
            "tags": {
                "name": device["name"],
                "serial": device["serial"],
                "model": device["model"],
                "network_name": device["network"]["name"],
            },
            "fields": {
                "usage_total_mb": float(device["usage"]["total"]),
                "usage_percentage": float(device["usage"]["percentage"]),
                "client_count": int(device["clients"]["counts"]["total"]),
            }
        }
        json_body.append(point)

    if json_body:
        client.write_points(json_body)
        print(f"Wrote {len(json_body)} top devices to InfluxDB")
    else:
        print("No top device data to write")

except Exception as e:
    print(f"Error fetching/writing top devices: {e}")
