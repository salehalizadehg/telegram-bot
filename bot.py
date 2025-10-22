# bot.py
import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from database import (
    ensure_db, add_member, get_member_by_tg, generate_qr_for_member, get_member_by_id,
    add_attendance, attendance_report, list_members, get_member_by_id as db_get_member_by_id
)
from database import ensure_db as db_ensure
import qr_utils
import traceback

# load .env if exists (locally)
load_dotenv()

BOT_TOKEN = os.getenv("7899936164:AAHc-cKh_LbF-y5m535Opuwy_KVhLuPVHTg")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # optional admin id for /members and reports

if not BOT_TOKEN:
    print("❌ BOT_TOKEN not set. Set the BOT_TOKEN environment variable.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Ensure DB exists
db_ensure()

# --- Helpers ---
def safe_send_photo(chat_id, path, caption=None):
    try:
        with open(path, "rb") as f:
            bot.send_photo(chat_id, f, caption=caption)
    except Exception as e:
        bot.send_message(chat_id, f"خطا در ارسال عکس: {e}")

# --- Start / registration flow ---
@bot.message_handler(commands=['start'])
def cmd_start(message):
    tg_id = message.from_user.id
    member = get_member_by_tg(tg_id)
    if member:
        bot.reply_to(message, f"👋 خوش آمدی {member[2]}! تو قبلاً ثبت‌نام کردی. از /myqr برای مشاهدهٔ QR خودت استفاده کن.")
        return

    msg = bot.reply_to(message, "خوش آمدی به باشگاه تیموری 🌿\nلطفاً <b>نام و نام خانوادگی</b> خود را وارد کن:")
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    try:
        name = message.text.strip()
        tg_id = message.from_user.id
        username = message.from_user.username or ""
        # Create member entry (qr_path will be updated)
        member_id = add_member(tg_id, name, username, role='member', qr_code_path=None)
        # generate qr and update db
        qr_path = qr_utils.generate_qr_for_member(member_id, name)
        add_member(tg_id, name, username, role='member', qr_code_path=qr_path)  # updates qr path
        bot.send_message(message.chat.id, f"✅ ثبت‌نام شما با موفقیت انجام شد، {name}!\nQR اختصاصی شما ارسال شد.")
        safe_send_photo(message.chat.id, qr_path, caption="این QR کد اختصاصی شماست — آن را نگه دارید.")
    except Exception as e:
        traceback.print_exc()
        bot.reply_to(message, f"متاسفانه خطایی رخ داد: {e}")

# --- /myqr command ---
@bot.message_handler(commands=['myqr'])
def cmd_myqr(message):
    tg_id = message.from_user.id
    member = get_member_by_tg(tg_id)
    if not member:
        bot.reply_to(message, "شما هنوز ثبت‌نام نکرده‌اید. لطفاً /start را بفرستید و نام خود را وارد کنید.")
        return
    qr_path = member[6]  # qr_code_path
    if qr_path and os.path.exists(qr_path):
        safe_send_photo(message.chat.id, qr_path, caption="QR اختصاصی شما 📱")
    else:
        # regenerate
        member_id = member[0]
        qr_path = qr_utils.generate_qr_for_member(member_id, member[2])
        add_member(tg_id, member[2], member[3], role=member[4], qr_code_path=qr_path)
        safe_send_photo(message.chat.id, qr_path, caption="QR اختصاصی شما (تولید مجدد) 📱")

# --- Handle incoming photos/documents (assume a coach scans member's QR and sends photo to bot) ---
@bot.message_handler(content_types=['photo', 'document'])
def handle_incoming_file(message):
    try:
        # download the file bytes
        file_info = None
        file_bytes = None
        if message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
            file_bytes = bot.download_file(file_info.file_path)
        elif message.content_type == 'document':
            file_info = bot.get_file(message.document.file_id)
            file_bytes = bot.download_file(file_info.file_path)
        else:
            bot.reply_to(message, "لطفاً عکس QR را ارسال کنید.")
            return

        decoded = qr_utils.decode_qr_from_bytes(file_bytes)
        if not decoded:
            bot.reply_to(message, "QR خوانده نشد. لطفاً تصویر واضح‌تری ارسال کنید یا از /myqr استفاده کنید.")
            return

        # expected payload: member:{id}
        if decoded.startswith("member:"):
            try:
                member_id = int(decoded.split(":", 1)[1])
            except:
                bot.reply_to(message, "QR نامعتبر است.")
                return

            member = db_get_member_by_id(member_id)
            if not member:
                bot.reply_to(message, "این عضو در سیستم ثبت نشده است.")
                return

            # record attendance; recorded_by is message.from_user.id (coach who scanned)
            add_attendance(member_id, recorded_by=message.from_user.id)
            bot.reply_to(message, f"✅ حضور برای {member[2]} ثبت شد ({member[2]}).")
        else:
            bot.reply_to(message, "QR نامعتبر یا متعلق به این سیستم نیست.")
    except Exception as e:
        traceback.print_exc()
        bot.reply_to(message, f"خطا در پردازش عکس: {e}")

# --- Admin: list members (optional, protected by ADMIN_ID) ---
@bot.message_handler(commands=['members'])
def cmd_members(message):
    if ADMIN_ID and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔️ این دستور فقط برای ادمین در دسترس است.")
        return
    rows = list_members()
    if not rows:
        bot.reply_to(message, "هیچ عضوی ثبت نشده است.")
        return
    text = "<b>لیست اعضا:</b>\n\n" + "\n".join([f"{r[0]} • {r[1]} (@{r[2] or '-'}) • {r[3]} • {r[4]}" for r in rows])
    bot.send_message(message.chat.id, text)

# --- Admin: get attendance for a member: /report <member_id> ---
@bot.message_handler(commands=['report'])
def cmd_report(message):
    if ADMIN_ID and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔️ این دستور فقط برای ادمین در دسترس است.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "استفاده: /report MEMBER_ID\nمثال: /report 3")
        return
    try:
        member_id = int(parts[1])
    except:
        bot.reply_to(message, "Member ID نامعتبر است.")
        return
    member = db_get_member_by_id(member_id)
    if not member:
        bot.reply_to(message, "عضو پیدا نشد.")
        return
    rows = attendance_report(member_id, days=3650)
    if not rows:
        bot.reply_to(message, f"هیچ حضوری برای {member[2]} ثبت نشده.")
        return
    text = f"<b>گزارش حضور برای {member[2]}:</b>\n" + "\n".join([f"{r[0]} — {r[1]}" for r in rows])
    bot.send_message(message.chat.id, text)

# --- default handler ---
@bot.message_handler(func=lambda m: True)
def fallback(m):
    bot.reply_to(m, "دستور شناخته‌شده نیست. از /start برای ثبت‌نام یا /myqr برای دریافت QR استفاده کن.")

# --- Run ---
if __name__ == "__main__":
    print("🤖 Teymouri Club Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=5)
