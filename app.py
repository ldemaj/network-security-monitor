import os
from flask import Flask, render_template, request, redirect, url_for, flash
from scanner import scan_network
import smtplib
from email.mime.text import MIMEText
from models import init_db, save_device, get_all_devices, get_new_devices
from datetime import datetime, timedelta
import ipaddress
import re
import socket
import psutil
import platform

app = Flask(__name__)

# Configuration
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
IP_RANGE = os.getenv("IP_RANGE")

def get_network_info(ip_range):
    try:
        network = ipaddress.IPv4Network(ip_range, strict=False)
        return {
            'network_address': str(network.network_address),
            'broadcast_address': str(network.broadcast_address),
            'netmask': str(network.netmask),
            'total_ips': network.num_addresses,
            'usable_ips': network.num_addresses - 2,  # Excluding network and broadcast
            'is_private': network.is_private,
            'prefixlen': network.prefixlen
        }
    except:
        return None

def get_system_network_info():
    try:
        # Get hostname
        hostname = socket.gethostname()
        
        # Get local IP
        local_ip = socket.gethostbyname(hostname)
        
        # Get network interfaces
        interfaces = []
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4 only
                    interfaces.append({
                        'name': interface,
                        'ip': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
        
        return {
            'hostname': hostname,
            'local_ip': local_ip,
            'interfaces': interfaces,
            'platform': platform.system(),
            'platform_release': platform.release()
        }
    except:
        return None

def get_device_statistics(devices):
    if not devices:
        return {}
    
    # Count devices by type
    device_types = {}
    for device in devices:
        device_type = device['device_type']
        device_types[device_type] = device_types.get(device_type, 0) + 1
    
    # Get most recent scan time
    most_recent = max(device['last_seen'] for device in devices)
    
    # Count new devices in last 5 minutes
    five_mins_ago = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    new_devices_count = len([d for d in devices if d['first_seen'] >= five_mins_ago])
    
    return {
        'total_devices': len(devices),
        'device_types': device_types,
        'most_recent_scan': most_recent,
        'new_devices_count': new_devices_count
    }

def validate_ip_range(ip_range):
    try:
        # Check if the format is correct (e.g., 192.168.1.1/24)
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$', ip_range):
            return False, "Invalid IP range format. Use format: xxx.xxx.xxx.xxx/xx"
        
        # Try to create an IPv4Network object
        network = ipaddress.IPv4Network(ip_range, strict=False)
        
        # Check if the network is private
        if not network.is_private:
            return False, "Please use a private IP range (e.g., 192.168.x.x, 10.x.x.x, 172.16.x.x)"
        
        return True, network
    except ValueError as e:
        return False, f"Invalid IP range: {str(e)}"

def send_email(new_devices):
    body = "\n".join(f"{d['ip']} - {d['mac']} - {d['device_type']}" for d in new_devices)
    msg = MIMEText(f"New device(s) detected:\n\n{body}")
    msg["Subject"] = "Network Alert: New Device Detected"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

@app.route("/")
def index():
    # Get all devices from database
    all_devices = get_all_devices()
    
    # Get devices seen in the last 5 minutes
    five_mins_ago = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    new_devices = get_new_devices(five_mins_ago)
    
    if new_devices and EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER:
        send_email(new_devices)

    # Get network information
    network_info = get_network_info(IP_RANGE) if IP_RANGE else None
    system_info = get_system_network_info()
    device_stats = get_device_statistics(all_devices)

    return render_template("index.html", 
                         scanned=all_devices, 
                         new_devices=new_devices,
                         ip_range=IP_RANGE,
                         network_info=network_info,
                         system_info=system_info,
                         device_stats=device_stats)

@app.route("/scan", methods=["POST"])
def scan():
    ip_range = request.form.get("ip_range", "").strip()
    
    # Validate IP range
    is_valid, result = validate_ip_range(ip_range)
    if not is_valid:
        return render_template("index.html",
                             scanned=get_all_devices(),
                             new_devices=[],
                             ip_range=IP_RANGE,
                             error=result)
    
    try:
        # Scan network with the provided IP range
        scanned_devices = scan_network(ip_range=ip_range)
        
        # Save all scanned devices to database
        for device in scanned_devices:
            save_device(device)
        
        # Get updated device list
        all_devices = get_all_devices()
        five_mins_ago = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        new_devices = get_new_devices(five_mins_ago)
        
        if new_devices and EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER:
            send_email(new_devices)
        
        # Get network information
        network_info = get_network_info(ip_range)
        system_info = get_system_network_info()
        device_stats = get_device_statistics(all_devices)
        
        return render_template("index.html",
                             scanned=all_devices,
                             new_devices=new_devices,
                             ip_range=ip_range,
                             network_info=network_info,
                             system_info=system_info,
                             device_stats=device_stats,
                             success=f"Successfully scanned {len(scanned_devices)} devices")
    
    except Exception as e:
        return render_template("index.html",
                             scanned=get_all_devices(),
                             new_devices=[],
                             ip_range=IP_RANGE,
                             error=f"Error scanning network: {str(e)}")

if __name__ == "__main__":
    init_db()  # Initialize database on startup
    app.run(debug=True)
