import sqlite3
from datetime import datetime

DB_PATH = "devices.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            mac TEXT UNIQUE,
            first_seen TEXT,
            last_seen TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_known_macs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT mac FROM devices")
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}

def save_or_update_devices(devices):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for d in devices:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO devices (ip, mac, first_seen, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(mac) DO UPDATE SET
                ip=excluded.ip,
                last_seen=excluded.last_seen
        """, (d["ip"], d["mac"], now, now))
    conn.commit()
    conn.close()
