from scapy.all import ARP, Ether, srp
import datetime
import json
import os
import nmap
import subprocess
import re
import requests

# Common device manufacturers and their device types
DEVICE_TYPES = {
    'Apple': ['iPhone', 'iPad', 'MacBook', 'Apple TV', 'AirPods'],
    'Samsung': ['Galaxy Phone', 'Galaxy Tablet', 'Samsung TV'],
    'Google': ['Pixel Phone', 'Chromebook', 'Nest'],
    'Xiaomi': ['Xiaomi Phone', 'Xiaomi Tablet'],
    'LG': ['LG Phone', 'LG TV'],
    'Sony': ['Sony TV', 'PlayStation'],
    'Microsoft': ['Xbox', 'Surface'],
    'Amazon': ['Fire TV', 'Echo'],
    'Roku': ['Roku TV', 'Roku Stick'],
    'TP-Link': ['Router', 'Extender'],
    'Netgear': ['Router', 'Extender'],
    'ASUS': ['Router', 'Laptop'],
    'Dell': ['Laptop', 'Desktop'],
    'HP': ['Laptop', 'Desktop', 'Printer'],
    'Canon': ['Printer', 'Camera'],
    'Epson': ['Printer'],
    'Brother': ['Printer'],
}

def get_mac_vendor(mac):
    try:
        # Remove any non-hex characters and convert to uppercase
        mac = re.sub(r'[^0-9A-Fa-f]', '', mac).upper()
        # Get the first 6 characters (OUI)
        oui = mac[:6]
        
        # Try to get vendor from macaddress.io API
        try:
            response = requests.get(f'https://api.macaddress.io/v1?apiKey=at_123456789&output=json&search={mac}')
            if response.status_code == 200:
                data = response.json()
                if 'vendorDetails' in data and 'companyName' in data['vendorDetails']:
                    return data['vendorDetails']['companyName']
        except:
            pass

        # Fallback to local MAC vendor database
        for vendor, devices in DEVICE_TYPES.items():
            if vendor.lower() in mac.lower():
                return vendor
    except:
        pass
    return "Unknown Vendor"

def get_device_type(ip, mac):
    try:
        vendor = get_mac_vendor(mac)
        
        # First try a simple ping to check if device is responsive
        ping_result = subprocess.run(['ping', '-n', '1', '-w', '500', ip], 
                                   capture_output=True, text=True)
        
        device_type = "Unknown Device"
        if "TTL=" in ping_result.stdout:
            # Extract TTL value
            ttl_match = re.search(r'TTL=(\d+)', ping_result.stdout)
            if ttl_match:
                ttl = int(ttl_match.group(1))
                # TTL values can help identify OS
                if ttl <= 64:
                    device_type = "Linux/Unix Device"
                elif ttl <= 128:
                    device_type = "Windows Device"
                else:
                    device_type = "Network Device"

        # Try to get more specific device information
        nm = nmap.PortScanner()
        print(f"Scanning {ip} for device type...")
        
        # Try to detect common device types based on open ports
        try:
            nm.scan(ip, arguments='-sV --version-intensity 0')
            if ip in nm.all_hosts():
                # Check for common device signatures
                if 'tcp' in nm[ip]:
                    ports = nm[ip]['tcp']
                    # Check for common device ports
                    if 554 in ports:  # RTSP port
                        return f"{vendor} TV/Camera"
                    elif 8008 in ports:  # Google Cast
                        return f"{vendor} Cast Device"
                    elif 5353 in ports:  # mDNS
                        return f"{vendor} Smart Device"
                    elif 9100 in ports:  # Printer port
                        return f"{vendor} Printer"
                    elif 62078 in ports:  # iOS device port
                        return f"{vendor} iOS Device"
        except:
            pass

        # If we have a vendor but couldn't determine specific type
        if vendor != "Unknown Vendor":
            # Make an educated guess based on vendor
            if vendor in DEVICE_TYPES:
                return f"{vendor} Device"
            return f"{vendor} {device_type}"
        
        return device_type

    except Exception as e:
        print(f"Error detecting device type for {ip}: {str(e)}")
    return "Unknown Device"

def scan_network(ip_range="192.168.86.1/24"):
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=3, verbose=0)[0]

    devices = []
    for sent, received in result:
        device_type = get_device_type(received.psrc, received.hwsrc)
        devices.append({
            "ip": received.psrc,
            "mac": received.hwsrc,
            "type": device_type,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    return devices

def load_known_devices(path="known_devices.json"):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def save_known_devices(devices, path="known_devices.json"):
    with open(path, "w") as f:
        json.dump(devices, f, indent=4)

def detect_new_devices(scanned_devices, known_devices):
    known_macs = {d["mac"] for d in known_devices}
    return [d for d in scanned_devices if d["mac"] not in known_macs]
