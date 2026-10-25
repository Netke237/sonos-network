import urllib.request
import xml.etree.ElementTree as ET
import sys

def soap_call(endpoint, service, action, body='', ip='192.168.10.151'):
    payload = f'''<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:{action} xmlns:u="urn:schemas-upnp-org:service:{service}">{body}</u:{action}>
</s:Body>
</s:Envelope>'''
    req = urllib.request.Request(
        f'http://{ip}:1400/{endpoint}',
        data=payload.encode('utf-8'),
        headers={
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPAction': f'"urn:schemas-upnp-org:service:{service}#{action}"'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        return f'ERR: {e}'

def get_text(xml_data, tag):
    try:
        root = ET.fromstring(xml_data)
        for elem in root.iter():
            if elem.tag.endswith(tag):
                return elem.text
    except Exception:
        pass
    return None

if __name__ == '__main__':
    ip = sys.argv[1] if len(sys.argv) > 1 else '192.168.10.151'
    print(f'=== DIAGNOSTIC PROBE FOR PLAYER {ip} ===')

    ti = soap_call('MediaRenderer/AVTransport/Control', 'AVTransport:1', 'GetTransportInfo', '<InstanceID>0</InstanceID>', ip=ip)
    print('CurrentTransportState:', get_text(ti, 'CurrentTransportState'))
    print('CurrentTransportStatus:', get_text(ti, 'CurrentTransportStatus'))

    vol = soap_call('MediaRenderer/RenderingControl/Control', 'RenderingControl:1', 'GetVolume', '<InstanceID>0</InstanceID><Channel>Master</Channel>', ip=ip)
    mute = soap_call('MediaRenderer/RenderingControl/Control', 'RenderingControl:1', 'GetMute', '<InstanceID>0</InstanceID><Channel>Master</Channel>', ip=ip)
    print('CurrentVolume (Master):', get_text(vol, 'CurrentVolume'))
    print('CurrentMute (Master):', get_text(mute, 'CurrentMute'))

    mi = soap_call('MediaRenderer/AVTransport/Control', 'AVTransport:1', 'GetMediaInfo', '<InstanceID>0</InstanceID>', ip=ip)
    print('CurrentURI:', get_text(mi, 'CurrentURI'))

    pos = soap_call('MediaRenderer/AVTransport/Control', 'AVTransport:1', 'GetPositionInfo', '<InstanceID>0</InstanceID>', ip=ip)
    print('RelTime:', get_text(pos, 'RelTime'))
    print('TrackDuration:', get_text(pos, 'TrackDuration'))
    print('TrackURI:', get_text(pos, 'TrackURI'))

    try:
        with urllib.request.urlopen(f'http://{ip}:1400/status/showstp', timeout=5) as r:
            stp = r.read().decode('utf-8', errors='replace')
            for line in stp.splitlines():
                if 'root port' in line.lower() or 'designated root' in line.lower():
                    print('STP:', line.strip())
    except Exception as e:
        print('STP check error:', e)

    try:
        with urllib.request.urlopen(f'http://{ip}:1400/status/proc/ath_rincon/status', timeout=5) as r:
            ath = r.read().decode('utf-8', errors='replace')
            for line in ath.splitlines():
                if any(k in line for k in ['OFDM ANI level', 'PHY errors', 'Noise Floor']):
                    print('Radio:', line.strip())
    except Exception as e:
        print('ath_rincon check error:', e)
