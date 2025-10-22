# qr_utils.py
import qrcode
import os
from PIL import Image
import io

# For decoding QR images we use pyzbar (may need system-level zbar)
try:
    from pyzbar.pyzbar import decode as zbar_decode
except Exception:
    zbar_decode = None  # fallback handled in decode_qr

QR_DIR = "data/qr"
os.makedirs(QR_DIR, exist_ok=True)

def generate_qr_for_member(member_id, name=None):
    """
    Generates a PNG QR with payload "member:{member_id}" and returns path.
    """
    payload = f"member:{member_id}"
    img = qrcode.make(payload)
    path = os.path.join(QR_DIR, f"{member_id}.png")
    img.save(path)
    return path

def decode_qr_from_bytes(file_bytes):
    """
    Accepts bytes (image), returns decoded string or None.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception:
        return None

    if zbar_decode:
        decoded = zbar_decode(image)
        if decoded:
            return decoded[0].data.decode('utf-8')
        return None
    else:
        # fallback: try to read with pillow (no real decode) -> return None
        return None
