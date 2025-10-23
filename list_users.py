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

# ---- گرفتن همه کاربران ----
def list_all_users():
    cursor.execute("SELECT user_id, full_name FROM users ORDER BY user_id;")
    users = cursor.fetchall()
    if not users:
        print("هیچ کاربری ثبت‌نام نکرده است.")
        return
    print("📋 لیست کاربران ثبت‌نامی:")
    for user in users:
        print(f"- ID: {user['user_id']} | Name: {user['full_name']}")

if __name__ == "__main__":
    list_all_users()
