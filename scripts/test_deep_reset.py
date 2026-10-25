import urllib.request
import sys

ip = '192.168.10.151'
url = f'http://{ip}:1400/MediaRenderer/AVTransport/Control'

def call_soap(action, body):
    envelope = f'''<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>{body}</s:Body>
</s:Envelope>'''
    req = urllib.request.Request(url, data=envelope.encode('utf-8'), headers={
        'Content-Type': 'text/xml; charset="utf-8"',
        'SOAPAction': f'"urn:schemas-upnp-org:service:AVTransport:1#{action}"'
    })
    try:
        with urllib.request.urlopen(req, timeout=3.0) as r:
            return 'OK', r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return f'HTTP_{e.code}', e.read().decode('utf-8')
    except Exception as e:
        return 'ERR', str(e)

print('EndDirectControlSession:', call_soap('EndDirectControlSession', '<u:EndDirectControlSession xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:EndDirectControlSession>')[0])
print('Stop:', call_soap('Stop', '<u:Stop xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:Stop>')[0])
print('RemoveAllTracks:', call_soap('RemoveAllTracksFromQueue', '<u:RemoveAllTracksFromQueue xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:RemoveAllTracksFromQueue>')[0])
print('BecomeCoordinator:', call_soap('BecomeCoordinatorOfStandaloneGroup', '<u:BecomeCoordinatorOfStandaloneGroup xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:BecomeCoordinatorOfStandaloneGroup>')[0])
