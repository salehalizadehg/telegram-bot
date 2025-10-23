import os
import threading
import telebot
from flask import Flask
from database import init_db, save_user, get_user_by_id, log_attendance, get_all_users, get_attendance_report
from qr_utils import generate_qr_for_member

# ---- Flask برای Render ----
app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Teymouri Club Bot is running!"

# ---- تنظیمات بات ----
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN در Environment Variables پیدا نشد.")
bot = telebot.TeleBot(BOT_TOKEN)

# ---- راه‌اندازی دیتابیس ----
init_db()

# ---- مدیریت کاربران /start ----
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    if user:
        bot.send_message(user_id, f"👋 سلام {user['full_name']}!\nQR اختصاصی شما قبلاً ساخته شده ✅")
        qr_path = f"data/qrcodes/{user_id}.png"
        if os.path.exists(qr_path):
            with open(qr_path, "rb") as qr:
                bot.send_photo(user_id, qr, caption="🎟 QR شما")
        else:
            qr_path = generate_qr_for_member(user_id)
            with open(qr_path, "rb") as qr:
                bot.send_photo(user_id, qr, caption="🎟 QR شما")
    else:
        msg = bot.send_message(user_id, "🎉 به مجموعه ورزشی تیموری خوش آمدید!\nلطفاً نام و نام خانوادگی خود را وارد کنید:")
        bot.register_next_step_handler(msg, process_name_step)

def process_name_step(message):
    user_id = message.from_user.id
    full_name = message.text.strip()
    try:
        save_user(user_id, full_name)
        qr_path = generate_qr_for_member(user_id)
        with open(qr_path, "rb") as qr:
            bot.send_photo(user_id, qr, caption=f"✅ {full_name} عزیز، ثبت‌نام شما انجام شد!")
    except Exception as e:
        bot.send_message(user_id, f"❌ خطا در ثبت‌نام: {e}")

# ---- نمایش QR /myqr ----
@bot.message_handler(commands=['myqr'])
def myqr(message):
    user_id = message.from_user.id
    user = get_user_by_id(user_id)
    if not user:
        bot.reply_to(message, "❌ شما هنوز ثبت‌نام نکرده‌اید. لطفاً /start را ارسال کنید.")
        return
    qr_path = f"data/qrcodes/{user_id}.png"
    if not os.path.exists(qr_path):
        qr_path = generate_qr_for_member(user_id)
    with open(qr_path, "rb") as qr:
        bot.send_photo(user_id, qr, caption="🎟 QR اختصاصی شما")

# ---- ثبت حضور /attendance ----
@bot.message_handler(commands=['attendance'])
def attendance(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ فرمت درست: /attendance <user_id>")
        return
    try:
        member_id = int(parts[1])
        log_attendance(member_id)
        bot.reply_to(message, f"✅ حضور عضو {member_id} ثبت شد.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا در ثبت حضور: {e}")

# ---- دستورات مدیریتی ----
ADMIN_IDS = [123456789]  # آی‌دی مدیر یا مربی‌ها

@bot.message_handler(commands=['list_users'])
def list_users(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ شما اجازه دسترسی ندارید.")
        return
    users = get_all_users()
    if not users:
        bot.send_message(message.chat.id, "هیچ کاربری ثبت‌نام نکرده است.")
        return
    text = "📋 لیست کاربران:\n"
    for u in users:
        text += f"- {u['user_id']}: {u['full_name']}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['attendance_report'])
def attendance_report(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ شما اجازه دسترسی ندارید.")
        return
    report = get_attendance_report()
    if not report:
        bot.send_message(message.chat.id, "هیچ حضوری ثبت نشده است.")
        return
    text = "📝 گزارش حضور:\n"
    for r in report:
        text += f"- {r['user_id']} | {r['full_name']} | {r['timestamp']}\n"
    bot.send_message(message.chat.id, text)

# ---- اجرای Flask و Bot همزمان ----
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

print("🤖 Teymouri Club Bot is running...")
bot.infinity_polling()
