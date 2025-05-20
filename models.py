from datetime import datetime
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = 'network_devices.db'

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            mac TEXT NOT NULL,
            device_type TEXT NOT NULL,
            first_seen TIMESTAMP NOT NULL,
            last_seen TIMESTAMP NOT NULL,
            UNIQUE(ip, mac)
        )
        ''')
        conn.commit()

def save_device(device):
    with get_db_connection() as conn:
        # Check if device exists
        cursor = conn.execute(
            'SELECT * FROM devices WHERE ip = ? AND mac = ?',
            (device['ip'], device['mac'])
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update last_seen
            conn.execute(
                'UPDATE devices SET last_seen = ?, device_type = ? WHERE ip = ? AND mac = ?',
                (device['timestamp'], device['type'], device['ip'], device['mac'])
            )
        else:
            # Insert new device
            conn.execute(
                'INSERT INTO devices (ip, mac, device_type, first_seen, last_seen) VALUES (?, ?, ?, ?, ?)',
                (device['ip'], device['mac'], device['type'], device['timestamp'], device['timestamp'])
            )
        conn.commit()

def get_all_devices():
    with get_db_connection() as conn:
        cursor = conn.execute('''
            SELECT ip, mac, device_type, first_seen, last_seen
            FROM devices
            ORDER BY last_seen DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]

def get_new_devices(since_timestamp):
    with get_db_connection() as conn:
        cursor = conn.execute('''
            SELECT ip, mac, device_type, first_seen, last_seen
            FROM devices
            WHERE first_seen >= ?
            ORDER BY first_seen DESC
        ''', (since_timestamp,))
        return [dict(row) for row in cursor.fetchall()] 