import io

import qrcode
from qrcode.image.pure import PyPNGImage


def generate_qr_png(data: str) -> bytes:
    """Generate a QR code PNG from a string and return raw bytes."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(image_factory=PyPNGImage)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return buf.read()
