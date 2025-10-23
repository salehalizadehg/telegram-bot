import os
import csv
import smtplib
from email.message import EmailMessage
import ssl
from database import get_all_users, get_attendance_report
import schedule
import time

# ---- ارسال ایمیل با ضمیمه ----
def send_email_with_attachments(to_email, subject, body, files):
    msg = EmailMessage()
    msg['From'] = os.getenv("EMAIL_ADDRESS")
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    for file_path in files:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(f.name)
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)
    print("✅ ایمیل با فایل‌ها ارسال شد.")

# ---- تولید CSV ----
def generate_csv_files():
    # users.csv
    users = get_all_users()
    with open("users.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "full_name"])
        for u in users:
            writer.writerow([u['user_id'], u['full_name']])

    # attendance.csv
    report = get_attendance_report()
    with open("attendance.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "full_name", "timestamp"])
        for r in report:
            writer.writerow([r['user_id'], r['full_name'], r['timestamp']])

    return ["users.csv", "attendance.csv"]

# ---- ترکیب تولید CSV و ارسال ایمیل ----
def generate_csv_files_and_send_email():
    files = generate_csv_files()
    send_email_with_attachments(
        to_email=os.getenv("ADMIN_EMAIL"),
        subject="گزارش هفتگی اعضای باشگاه",
        body="سلام! فایل‌های CSV کاربران و حضورها پیوست شد.",
        files=files
    )

# ---- برنامه‌ریزی خودکار ----
# روزانه ساعت 07:00 اجرا شود
schedule.every().day.at("07:00").do(generate_csv_files_and_send_email)

print("📧 سیستم گزارش خودکار فعال شد.")
while True:
    schedule.run_pending()
    time.sleep(60)
