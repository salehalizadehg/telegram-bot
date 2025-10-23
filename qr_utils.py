import qrcode, os

def generate_qr_for_member(member_id):
    os.makedirs("data/qrcodes", exist_ok=True)
    img = qrcode.make(f"member:{member_id}")
    file_path = f"data/qrcodes/{member_id}.png"
    img.save(file_path)
    return file_path
