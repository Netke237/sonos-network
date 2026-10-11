"""
Sonos Real-Time Network & Interference Monitor
Queries all Sonos players via UPnP / Atheros Rincon driver status endpoints.
Provides real-time OFDM ANI, Noise Floor, and PHY error rates.
"""

import sys
import time
import re
import argparse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SONOS_DEVICES = {
    'Wohnzimmer_Bookshelf (STP Root)': '192.168.10.230',
    'Wohnzimmer_Esstisch (Play:1)': '192.168.10.160',
    'Wohnzimmer_Buchregal (Play:1)': '192.168.10.101',
    'Keller (Play:3 Leaf)': '192.168.10.217',
    'Kueche (Bookshelf)': '192.168.10.202',
    'Bueroecke (Bookshelf)': '192.168.10.151',
    'Fernsehecke Left Surround': '192.168.10.102',
    'Fernsehecke Beam': '192.168.10.241',
    'Nicolas (Bookshelf)': '192.168.10.165',
    'Noah (Bookshelf)': '192.168.10.229',
    'Noemi (Bookshelf)': '192.168.10.244',
    'Eltern (Bookshelf)': '192.168.10.131',
    'Elternbad (Bookshelf)': '192.168.10.113',
}

previous_phy = {}
previous_time = {}

def get_speaker_status(name, ip, timeout=5.0):
    url = f"http://{ip}:1400/status/proc/ath_rincon/status"
    req = urllib.request.Request(url, headers={'User-Agent': 'SonosMonitor/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode('utf-8', errors='ignore')
            
            ani_m = re.search(r"OFDM ANI level:\s*(\d+)", text)
            ani = int(ani_m.group(1)) if ani_m else None
            
            phy_m = re.search(r"PHY errors since last reading/reset:\s*(\d+)", text)
            phy = int(phy_m.group(1)) if phy_m else None
            
            noise_m = re.findall(r"Noise Floor:\s*(-?\d+)\s*dBm", text)
            noise = f"{noise_m[0]} dBm" if noise_m else "N/A"
            
            ch_m = re.search(r"IEEE channel:\s*(\d+)", text)
            channel = ch_m.group(1) if ch_m else "N/A"
            
            return {
                'name': name,
                'ip': ip,
                'status': 'OK',
                'ani': ani,
                'phy': phy,
                'noise': noise,
                'channel': channel,
                'time': time.time()
            }
    except Exception as e:
        return {
            'name': name,
            'ip': ip,
            'status': 'ERR',
            'error': str(e)
        }

def format_ani(ani):
    if ani is None:
        return "N/A"
    if ani <= 3:
        return f"{ani} (Clean)"
    elif ani <= 6:
        return f"{ani} (Moderate)"
    else:
        return f"{ani} (SEVERE)"

def render_table(results):
    global previous_phy, previous_time
    now = time.time()
    
    header = f"{'Speaker':<36} | {'IP':<14} | {'Ch':<3} | {'OFDM ANI':<12} | {'Noise':<9} | {'PHY Total':<10} | {'Error Rate'}"
    print(header)
    print("-" * len(header))
    
    for r in results:
        name = r['name']
        ip = r['ip']
        if r['status'] != 'OK':
            print(f"{name:<36} | {ip:<14} | {'--':<3} | {'UNREACHABLE':<12} | {'--':<9} | {'--':<10} | {r.get('error', 'Timeout')}")
            continue
        
        ani_str = format_ani(r['ani'])
        phy_total = str(r['phy']) if r['phy'] is not None else "N/A"
        
        # Calculate error rate (errors per second)
        rate_str = "--"
        if r['phy'] is not None and name in previous_phy:
            d_phy = r['phy'] - previous_phy[name]
            d_t = r['time'] - previous_time[name]
            if d_t > 0 and d_phy >= 0:
                rate = d_phy / d_t
                rate_str = f"{rate:6.1f} err/s"
        
        if r['phy'] is not None:
            previous_phy[name] = r['phy']
            previous_time[name] = r['time']
            
        print(f"{name:<36} | {ip:<14} | {r['channel']:<3} | {ani_str:<12} | {r['noise']:<9} | {phy_total:<10} | {rate_str}")
    print()

def main():
    parser = argparse.ArgumentParser(description="Sonos Real-Time Network & Interference Monitor")
    parser.add_argument("--watch", "-w", type=int, default=0, help="Refresh interval in seconds (0 = single run)")
    parser.add_argument("--room", "-r", type=str, default="", help="Filter by room name (e.g. Wohnzimmer)")
    args = parser.parse_args()
    
    devices = SONOS_DEVICES
    if args.room:
        devices = {k: v for k, v in devices.items() if args.room.lower() in k.lower()}
        if not devices:
            print(f"No devices found matching room filter '{args.room}'")
            return

    while True:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(get_speaker_status, name, ip) for name, ip in devices.items()]
            results = [f.result() for f in futures]
            
        # Keep consistent order
        results.sort(key=lambda x: list(devices.keys()).index(x['name']))
        render_table(results)
        
        if args.watch <= 0:
            break
        time.sleep(args.watch)

if __name__ == '__main__':
    main()
