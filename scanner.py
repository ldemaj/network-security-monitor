from scapy.all import ARP, Ether, srp
import datetime
import json
import os

def scan_network(ip_range="192.168.86.1/24"):
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=3, verbose=0)[0]

    devices = []
    for sent, received in result:
        devices.append({
            "ip": received.psrc,
            "mac": received.hwsrc,
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
