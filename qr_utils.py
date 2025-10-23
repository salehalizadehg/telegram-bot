import os
import qrcode

QR_DIR = "data/qrcodes"
os.makedirs(QR_DIR, exist_ok=True)

def generate_qr_for_member(user_id):
    qr_path = f"{QR_DIR}/{user_id}.png"
    if os.path.exists(qr_path):
        return qr_path  # اگر قبلاً وجود داشت، دوباره تولید نکن
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(str(user_id))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_path)
    return qr_path
