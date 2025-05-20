import os
from flask import Flask, render_template
from scanner import scan_network
import smtplib
from email.mime.text import MIMEText
from models import init_db, save_device, get_all_devices, get_new_devices
from datetime import datetime, timedelta

app = Flask(__name__)

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

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
    # Scan network
    scanned_devices = scan_network()
    
    # Save all scanned devices to database
    for device in scanned_devices:
        save_device(device)
    
    # Get all devices from database
    all_devices = get_all_devices()
    
    # Get devices seen in the last 5 minutes
    five_mins_ago = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    new_devices = get_new_devices(five_mins_ago)
    
    if new_devices and EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER:
        send_email(new_devices)

    return render_template("index.html", 
                         scanned=all_devices, 
                         new_devices=new_devices)

if __name__ == "__main__":
    init_db()  # Initialize database on startup
    app.run(debug=True)
