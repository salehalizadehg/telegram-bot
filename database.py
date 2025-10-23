import os
import psycopg2
from psycopg2.extras import RealDictCursor

# ---- کانکشن دیتابیس ----
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASS,
    dbname=DB_NAME
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# ---- ساخت جدول‌ها ----
def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        full_name TEXT NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

# ---- توابع CRUD ----
def save_user(user_id, full_name):
    cursor.execute("""
    INSERT INTO users (user_id, full_name)
    VALUES (%s, %s)
    ON CONFLICT (user_id) DO NOTHING;
    """, (user_id, full_name))
    conn.commit()

def get_user_by_id(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone()

def log_attendance(user_id):
    cursor.execute("INSERT INTO attendance (user_id) VALUES (%s)", (user_id,))
    conn.commit()

def get_all_users():
    cursor.execute("SELECT * FROM users ORDER BY user_id")
    return cursor.fetchall()

def get_attendance_report():
    cursor.execute("""
    SELECT a.user_id, u.full_name, a.timestamp
    FROM attendance a
    JOIN users u ON a.user_id = u.user_id
    ORDER BY a.timestamp DESC
    """)
    return cursor.fetchall()
