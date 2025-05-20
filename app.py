import os
from flask import Flask, render_template
from scanner import scan_network, load_known_devices, save_known_devices, detect_new_devices
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

def send_email(new_devices):
    body = "\n".join(f"{d['ip']} - {d['mac']}" for d in new_devices)
    msg = MIMEText(f"New device(s) detected:\n\n{body}")
    msg["Subject"] = "Network Alert: New Device Detected"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

@app.route("/")
def index():
    scanned = scan_network()
    known = load_known_devices()
    new_devices = detect_new_devices(scanned, known)

    if new_devices:
        send_email(new_devices)
        save_known_devices(known + new_devices)

    return render_template("index.html", scanned=scanned, new_devices=new_devices)

if __name__ == "__main__":
    app.run(debug=True)
