import os
import telebot
from database import init_db, save_user, get_user_by_id, log_attendance
from qr_utils import generate_qr_for_member
from flask import Flask

# ---- Flask برای باز کردن پورت Render ----
app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Teymouri Club Bot is running!"

# ---- تنظیمات بات تلگرام ----
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN در Environment Variables پیدا نشد.")
bot = telebot.TeleBot(BOT_TOKEN)

# ---- راه‌اندازی دیتابیس ----
init_db()

# 🧾 /start - شروع و ثبت‌نام اولیه
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user = get_user_by_id(user_id)

    if user:
        bot.send_message(user_id, f"👋 سلام {user[1]}!\nQR کد اختصاصی‌ت قبلاً ساخته شده ✅")
        with open(f"data/qrcodes/{user_id}.png", "rb") as qr:
            bot.send_photo(user_id, qr, caption="این QR مخصوص شماست 🎟")
    else:
        msg = bot.send_message(user_id, "🎉 به مجموعه ورزشی تیموری خوش اومدی!\nلطفاً نام و نام خانوادگی‌ات رو وارد کن:")
        bot.register_next_step_handler(msg, process_name_step)

# 🧍 ثبت نام کاربر جدید
def process_name_step(message):
    user_id = message.from_user.id
    full_name = message.text.strip()

    save_user(user_id, full_name)
    qr_path = generate_qr_for_member(user_id)

    with open(qr_path, "rb") as qr:
        bot.send_photo(user_id, qr, caption=f"✅ {full_name} عزیز، ثبت‌نامت با موفقیت انجام شد!\nاین QR مخصوص شماست.")

# 📸 /myqr - نمایش QR
@bot.message_handler(commands=['myqr'])
def myqr(message):
    user_id = message.from_user.id
    user = get_user_by_id(user_id)

    if not user:
        bot.reply_to(message, "❌ شما هنوز ثبت‌نام نکردید. لطفاً /start رو بفرستید.")
        return

    qr_path = f"data/qrcodes/{user_id}.png"
    if os.path.exists(qr_path):
        with open(qr_path, "rb") as qr:
            bot.send_photo(user_id, qr, caption="QR اختصاصی شما 🎟")
    else:
        qr_path = generate_qr_for_member(user_id)
        with open(qr_path, "rb") as qr:
            bot.send_photo(user_id, qr, caption="QR اختصاصی شما 🎟")

# 🕓 /attendance - ثبت حضور (مربی یا مدیر)
@bot.message_handler(commands=['attendance'])
def attendance(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ فرمت درست: `/attendance <user_id>`")
        return

    try:
        member_id = int(parts[1])
        log_attendance(member_id)
        bot.reply_to(message, f"✅ حضور عضو {member_id} با موفقیت ثبت شد.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا در ثبت حضور: {e}")

# ---- اجرای همزمان بات و وب‌سرور ----
import threading

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

print("🤖 Teymouri Club Bot is running...")
bot.infinity_polling()
