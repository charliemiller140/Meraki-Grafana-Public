from pysnmp.hlapi import *
from influxdb import InfluxDBClient
from datetime import datetime

# InfluxDB v1 config
INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
INFLUX_DB = "meraki"

# SNMPv3 config
host = ''
user = ''
auth_key = ''
priv_key = ''
port = 161

client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)

def write_down_status_for_all_ports():
    # You can optionally list expected ports here if known
    # Or just write a generic entry indicating device down
    json_body = [{
        "measurement": "mx_port_status",
        "tags": {
            "device": host,
            "port": "all"  # meaning all ports or unknown ports
        },
        "time": datetime.utcnow().isoformat(),
        "fields": {
            "status": 2  # down
        }
    }]
    client.write_points(json_body)
    print(f"[{datetime.utcnow()}] SNMP timeout - wrote device down status to InfluxDB")

def get_port_status_snmpv3():
    usm_user = UsmUserData(
        user,
        authKey=auth_key,
        authProtocol=usmHMACSHAAuthProtocol,
        privKey=priv_key,
        privProtocol=usmDESPrivProtocol
    )

    errorIndicationOccurred = False

    for (errorIndication,
         errorStatus,
         errorIndex,
         varBinds) in nextCmd(
            SnmpEngine(),
            usm_user,
            UdpTransportTarget((host, port)),
            ContextData(),
            ObjectType(ObjectIdentity('IF-MIB', 'ifDescr')),
            lexicographicMode=False):

        if errorIndication:
            print(f'Error: {errorIndication}')
            errorIndicationOccurred = True
            break  # Stop iteration on timeout or error
        elif errorStatus:
            print(f'Error: {errorStatus.prettyPrint()} at {errorIndex}')
            errorIndicationOccurred = True
            break
        else:
            for varBind in varBinds:
                oid, interface_name = varBind
                ifIndex = int(oid.prettyPrint().split('.')[-1])

                errorIndication2, errorStatus2, errorIndex2, varBinds2 = next(
                    getCmd(
                        SnmpEngine(),
                        usm_user,
                        UdpTransportTarget((host, port)),
                        ContextData(),
                        ObjectType(ObjectIdentity('IF-MIB', 'ifOperStatus', ifIndex))
                    )
                )

                if errorIndication2:
                    print(f'Error: {errorIndication2}')
                    continue
                elif errorStatus2:
                    print(f'Error: {errorStatus2.prettyPrint()} at {errorIndex2}')
                    continue

                for varBind2 in varBinds2:
                    oid2, port_status = varBind2
                    status_map = {1: 'up', 2: 'down', 3: 'testing'}
                    status_val = int(port_status)
                    interface_str = interface_name.prettyPrint()
                    status_str = status_map.get(status_val, 'unknown')
                    print(f'Interface {interface_str} is {status_str}')

                    json_body = [{
                        "measurement": "mx_port_status",
                        "tags": {
                            "device": host,
                            "port": interface_str
                        },
                        "time": datetime.utcnow().isoformat(),
                        "fields": {
                            "status": status_val
                        }
                    }]

                    client.write_points(json_body)

    if errorIndicationOccurred:
        # Write down status for all ports or device if we had an SNMP error/timeout
        write_down_status_for_all_ports()

if __name__ == '__main__':
    get_port_status_snmpv3()
    client.close()
