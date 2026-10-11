#!/usr/bin/env python3
"""
Sonos Ghost Group Flusher & Topology Sanitizer
Residential Network - 14-Player Sonos Architecture

Diagnoses and cleans corrupted UPnP Group IDs where a player's
Group ID prefix does not match its actual Coordinator UUID.
"""

import urllib.request
import xml.etree.ElementTree as ET
import concurrent.futures
import sys

SONOS_PLAYERS = {
    'Wohnzimmer_Bookshelf (Anchor)': '192.168.10.230',
    'Wohnzimmer_Buchregal': '192.168.10.101',
    'Wohnzimmer_Esstisch': '192.168.10.160',
    'Fernsehecke Beam': '192.168.10.241',
    'Kueche': '192.168.10.202',
    'Keller': '192.168.10.217',
    'Nicolas': '192.168.10.165',
    'Noah': '192.168.10.229',
    'Noemi': '192.168.10.244',
    'Eltern': '192.168.10.131',
    'Elternbad': '192.168.10.113',
    'Bueroecke': '192.168.10.151'
}

SOAP_STANDALONE = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:BecomeCoordinatorOfStandaloneGroup xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
<InstanceID>0</InstanceID>
</u:BecomeCoordinatorOfStandaloneGroup>
</s:Body>
</s:Envelope>"""

SOAP_ATTRIBUTES = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body><u:GetZoneGroupAttributes xmlns:u="urn:schemas-upnp-org:service:ZoneGroupTopology:1" /></s:Body>
</s:Envelope>"""

def check_and_sanitize(name, ip, force_reset=False):
    url_topo = f"http://{ip}:1400/ZoneGroupTopology/Control"
    url_trans = f"http://{ip}:1400/MediaRenderer/AVTransport/Control"
    
    # Check current group attributes
    try:
        req = urllib.request.Request(url_topo, data=SOAP_ATTRIBUTES.encode('utf-8'), headers={
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPAction': '"urn:schemas-upnp-org:service:ZoneGroupTopology:1#GetZoneGroupAttributes"'
        })
        with urllib.request.urlopen(req, timeout=3.0) as r:
            xml = r.read().decode('utf-8')
            root = ET.fromstring(xml)
            grp_id = root.findtext('.//CurrentZoneGroupID', '')
            grp_name = root.findtext('.//CurrentZoneGroupName', '')
            members = root.findtext('.//CurrentZonePlayerUUIDsInGroup', '')
    except Exception as e:
        return (name, ip, 'OFFLINE/ERROR', str(e))
    
    needs_reset = force_reset
    # Detect ghost group mismatch if standalone
    if ':' in grp_id:
        coord_uuid = grp_id.split(':')[0]
        # If player is in a 1-player group but grp_id doesn't match its own UUID, it's a ghost group
        if members and ',' not in members and coord_uuid not in members:
            needs_reset = True
            
    if needs_reset:
        try:
            req_reset = urllib.request.Request(url_trans, data=SOAP_STANDALONE.encode('utf-8'), headers={
                'Content-Type': 'text/xml; charset="utf-8"',
                'SOAPAction': '"urn:schemas-upnp-org:service:AVTransport:1#BecomeCoordinatorOfStandaloneGroup"'
            })
            with urllib.request.urlopen(req_reset, timeout=4.0) as r:
                return (name, ip, 'SANITIZED', f"Flushed ghost ID (was {grp_id})")
        except Exception as e:
            return (name, ip, 'RESET_FAILED', str(e))
            
    return (name, ip, 'CLEAN', f"{grp_name} [{grp_id[:22]}...]")

def main():
    force_all = '--all' in sys.argv or '-a' in sys.argv
    mode_str = "FORCE RESETTING ALL GROUPS" if force_all else "AUDITING & FLUSHING GHOST GROUPS"
    print(f"\n=== SONOS GROUP TOPOLOGY AUDIT ({mode_str}) ===")
    print(f"{'Speaker':<32} | {'IP Address':<15} | {'Status':<12} | Details")
    print("-" * 85)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SONOS_PLAYERS)) as ex:
        results = list(ex.map(lambda item: check_and_sanitize(item[0], item[1], force_all), SONOS_PLAYERS.items()))
        
    for name, ip, status, details in sorted(results, key=lambda x: x[0]):
        print(f"{name:<32} | {ip:<15} | {status:<12} | {details}")
    print("-" * 85)
    print("Done. All active players audited.")

if __name__ == '__main__':
    main()
