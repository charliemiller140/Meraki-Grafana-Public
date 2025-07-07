import os
import meraki
from dotenv import load_dotenv

load_dotenv()

MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
NETWORK_ID = os.getenv("NETWORK_ID")

dashboard = meraki.DashboardAPI(MERAKI_API_KEY, suppress_logging=True)

def get_network_traffic(network_id, timespan=7200, device_type='combined'):
    """
    Fetch network traffic analysis data from Meraki API.

    Args:
        network_id (str): Meraki network ID.
        timespan (int): Timespan in seconds (max 2592000 = 30 days).
        device_type (str): 'combined', 'wireless', 'switch', or 'appliance'.
    
    Returns:
        list: Traffic data JSON array.
    """
    try:
        traffic_data = dashboard.networks.getNetworkTraffic(
            network_id,
            timespan=timespan,
            deviceType=device_type
        )
        return traffic_data
    except Exception as e:
        print(f"Error fetching network traffic: {e}")
        return []

if __name__ == "__main__":
    data = get_network_traffic(NETWORK_ID, timespan=7200, device_type='combined')
    for entry in data:
        print(f"App: {entry['application']}, Sent: {entry['sent']} bytes, Recv: {entry['recv']} bytes, Clients: {entry['numClients']}")
