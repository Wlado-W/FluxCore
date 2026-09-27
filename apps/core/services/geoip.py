import ipaddress
import logging

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TTL = 86400 * 7  # Кэшируем гео-данные IP на 7 дней


def _is_private_or_local(address: str) -> bool:
    """
    Корректно отличает приватные/loopback/link-local адреса от публичных —
    в отличие от строкового startswith("192.168."), учитывает 10.0.0.0/8,
    172.16.0.0/12, IPv6 loopback/link-local и т.п. Если address — доменное
    имя (не IP), ipaddress.ip_address() бросит ValueError, и это НЕ
    приватный адрес — просто резолвим его через ip-api как есть (сервис
    сам умеет резолвить домены).
    """
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved


class GeoIPService:
    @staticmethod
    def resolve_ip(ip_address: str) -> dict:
        """
        Определяет страну, город, координаты и ISP по IP-адресу (или домену).
        Сначала запрашивает данные из кэша, затем обращается к ip-api.com.
        """
        if _is_private_or_local(ip_address):
            return {
                "country": "Локальная сеть",
                "country_code": "",  # country_code — ISO alpha-2 (2 символа), пусто = "неизвестно"
                "city": "",
                "lat": None,
                "lon": None,
                "isp": "Private Network",
            }

        cache_key = f"geoip_data_{ip_address}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        try:
            # ip-api.com: бесплатно до 45 запросов в минуту, только HTTP на
            # бесплатном тарифе (HTTPS — платная опция их стороны). Это не
            # утечка секретов — резолвится только сам IP/домен ноды, без
            # каких-либо токенов/креды в запросе.
            url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,city,lat,lon,isp"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                country_code = (data.get("countryCode") or "")[:2]  # гарантируем помещение в CharField(max_length=2)
                result = {
                    "country": data.get("country", ""),
                    "country_code": country_code,
                    "city": data.get("city", ""),
                    "lat": float(data["lat"]) if data.get("lat") is not None else None,
                    "lon": float(data["lon"]) if data.get("lon") is not None else None,
                    "isp": data.get("isp", ""),
                }
                cache.set(cache_key, result, CACHE_TTL)
                return result

            logger.warning("GeoIP lookup failed for %s: %s", ip_address, data.get("message"))
        except (requests.RequestException, ValueError, KeyError) as exc:
            logger.error("Failed to resolve GeoIP for %s: %s", ip_address, exc)

        # Фолбэк при ошибке — пустые значения, а не выдуманные "Unknown"/(0,0),
        # чтобы (0.0, 0.0) — координаты в Гвинейском заливе — не попадали на карту нод.
        return {
            "country": "",
            "country_code": "",
            "city": "",
            "lat": None,
            "lon": None,
            "isp": "",
        }
