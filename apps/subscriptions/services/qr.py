"""Генерация QR-кода для ссылки подписки."""
import io

import qrcode


def build_subscription_qr_png(subscription_url: str) -> bytes:
    """Возвращает PNG-изображение QR-кода в виде байтов."""
    img = qrcode.make(subscription_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
