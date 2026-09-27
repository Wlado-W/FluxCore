"""
Deep-link'и для прямого импорта подписки в мобильные приложения —
без копирования ссылки вручную, одним тапом из Telegram-бота/ЛК.
"""
import base64
from urllib.parse import quote


def build_deep_links(subscription_url: str) -> dict:
    """
    subscription_url — полный URL подписки (напр. https://panel/sub/<token>/).
    Возвращает {app_name: deep_link_url} для основных клиентских приложений.
    """
    encoded_url = quote(subscription_url, safe="")

    return {
        "v2rayng": f"v2rayng://install-sub?url={encoded_url}",
        "happ": f"happ://add/{encoded_url}",
        "hiddify": f"hiddify://install-config?url={encoded_url}",
        # Shadowrocket ожидает саму ссылку подписки в base64 после sub://
        "shadowrocket": f"shadowrocket://add/sub://{base64.b64encode(subscription_url.encode()).decode()}",
    }
