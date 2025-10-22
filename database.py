# database.py
import sqlite3
import os
from datetime import datetime

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "club.db")

def ensure_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # members: id (pk), tg_id (unique), name, username, role, joined_at, qr_code_path
    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE,
            name TEXT,
            username TEXT,
            role TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            qr_code_path TEXT
        )
    """)
    # attendance: id, member_id, date, time, recorded_by (tg_id of scanner/coach)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            date TEXT,
            time TEXT,
            recorded_by INTEGER,
            FOREIGN KEY(member_id) REFERENCES members(id)
        )
    """)
    conn.commit()
    conn.close()

def add_member(tg_id, name, username, role='member', qr_code_path=None):
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO members (tg_id, name, username, role, qr_code_path)
        VALUES (?, ?, ?, ?, ?)
    """, (tg_id, name, username, role, qr_code_path))
    # If member existed, update name/username/qrpath
    cur.execute("""
        UPDATE members SET name=?, username=?, role=?, qr_code_path=? WHERE tg_id=?
    """, (name, username, role, qr_code_path, tg_id))
    conn.commit()
    # get member id
    cur.execute("SELECT id FROM members WHERE tg_id=?", (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_member_by_tg(tg_id):
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, tg_id, name, username, role, joined_at, qr_code_path FROM members WHERE tg_id=?", (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_member_by_id(member_id):
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, tg_id, name, username, role, joined_at, qr_code_path FROM members WHERE id=?", (member_id,))
    row = cur.fetchone()
    conn.close()
    return row

def add_attendance(member_id, recorded_by=None):
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    cur.execute("INSERT INTO attendance (member_id, date, time, recorded_by) VALUES (?, ?, ?, ?)",
                (member_id, date, time, recorded_by))
    conn.commit()
    conn.close()

def attendance_report(member_id, days=30):
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT date, time FROM attendance
        WHERE member_id=?
        ORDER BY date DESC, time DESC
        LIMIT ?
    """, (member_id, days))
    rows = cur.fetchall()
    conn.close()
    return rows

def list_members():
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, username, role, joined_at FROM members ORDER BY joined_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
