import urllib.request
import xml.etree.ElementTree as ET

soap_body = '''<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:GetZoneGroupState xmlns:u="urn:schemas-upnp-org:service:ZoneGroupTopology:1"></u:GetZoneGroupState>
</s:Body>
</s:Envelope>'''

req = urllib.request.Request(
    'http://192.168.10.151:1400/ZoneGroupTopology/Control',
    data=soap_body.encode('utf-8'),
    headers={
        'Content-Type': 'text/xml; charset="utf-8"',
        'SOAPAction': '"urn:schemas-upnp-org:service:ZoneGroupTopology:1#GetZoneGroupState"'
    }
)

with urllib.request.urlopen(req, timeout=5) as resp:
    xml_resp = resp.read().decode('utf-8')

root = ET.fromstring(xml_resp)
state_str = None
for elem in root.iter():
    if elem.tag.endswith('ZoneGroupState'):
        state_str = elem.text
        break

if state_str:
    state_xml = ET.fromstring(state_str)
    for zg in state_xml.findall('.//ZoneGroup'):
        gid = zg.attrib.get('ID')
        coord = zg.attrib.get('Coordinator')
        for m in zg.findall('.//ZoneGroupMember'):
            name = m.attrib.get('ZoneName')
            uuid = m.attrib.get('UUID')
            if 'B' in name or 'b' in name:
                print(f"Room: {name}")
                print(f"UUID: {uuid}")
                print(f"Coordinator: {coord}")
                print(f"GroupID: {gid}")
                print(f"Coordinator matches Group prefix: {gid.startswith(coord)}")
                print(f"ChannelMapSet: {m.attrib.get('ChannelMapSet')}")
                print(f"Invisible: {m.attrib.get('Invisible')}")
