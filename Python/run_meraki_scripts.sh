#!/bin/bash

# Activate virtualenv (adjust if your venv is somewhere else)
source /opt/meraki-monitoring/venv/bin/activate

# Run the Python scripts with absolute paths

echo "Running Channel History Script: "
python3 /opt/meraki-monitoring/complete/ap_channel_status.py
echo "Running AP Latency Script: "
python3 /opt/meraki-monitoring/complete/ap_latency.py
echo "Running AP average RSSI and SnR over 6 hours Script: "
python3 /opt/meraki-monitoring/complete/ap_signal.py
echo "Running AP channel Utilisation Script: "
python3 /opt/meraki-monitoring/complete/channelutilisation.py
echo "Running Client Count Script: "
python3 /opt/meraki-monitoring/complete/clientcount.py
echo "Running Top AP data Usage Script: "
python3 /opt/meraki-monitoring/complete/top_ap.py
echo "Running top Network Usage Apps Script: "
python3 /opt/meraki-monitoring/complete/app_usage_db.py
echo "running snmp up/down now: "

# This is a different venv because the SNMP module does not run on the lastest Python verson
source ~/meraki-py311-env/bin/activate 
python /opt/meraki-monitoring/complete/snmp_influx.py
