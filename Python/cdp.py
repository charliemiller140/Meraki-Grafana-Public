from pysnmp.hlapi import *
from datetime import datetime

# SNMPv3 config
host = '
user = ''
auth_key = ''
priv_key = ''
port = 161

def get_lldp_remote_sys_names_snmpv3():
    usm_user = UsmUserData(
        user,
        authKey=auth_key,
        authProtocol=usmHMACSHAAuthProtocol,
        privKey=priv_key,
        privProtocol=usmDESPrivProtocol
    )

    iterator = nextCmd(
    	SnmpEngine(),
    	usm_user,
    	UdpTransportTarget((host, port)),
    	ContextData(),
    	ObjectType(ObjectIdentity('1.3.6.1.4.1.29671.1.3.4')),  # <-- Meraki devLldpCdpTable
    	lexicographicMode=False
    )

    print(f"[{datetime.utcnow()}] LLDP Remote System Names for device {host}:")
    errorOccurred = False

    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
        if errorIndication:
            print(f"Error: {errorIndication}")
            errorOccurred = True
            break
        elif errorStatus:
            print(f"SNMP error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex)-1][0] or '?'}")
            errorOccurred = True
            break
        else:
            for varBind in varBinds:
                oid, value = varBind
                print(f"{oid.prettyPrint()} = {value.prettyPrint()}")

    if errorOccurred:
        print(f"[{datetime.utcnow()}] SNMP walk failed or incomplete")

if __name__ == '__main__':
    get_lldp_remote_sys_names_snmpv3()
