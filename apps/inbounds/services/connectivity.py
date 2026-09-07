"""
One-click проверка соединения с inbound'ом прямо из панели: TCP-подключение
к порту ноды + (если включён TLS) проверка успешности TLS-handshake.

Это проверка сетевой доступности порта, а не полной работоспособности
VPN-протокола (для этого потребовался бы настоящий клиент протокола)
— но она быстро ловит частые проблемы: закрытый порт, файрвол, неверный
сертификат.
"""
import socket
import ssl
import time


def test_inbound_connection(inbound, timeout: float = 5.0) -> dict:
    """Возвращает {"success": bool, "latency_ms": float|None, "error": str|None}."""
    host = inbound.node.address
    port = inbound.port

    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            if inbound.security == "tls":
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE  # самоподписанные сертификаты — обычное дело для VPN
                server_name = (inbound.security_settings or {}).get("serverName")
                with context.wrap_socket(sock, server_hostname=server_name) as tls_sock:
                    tls_sock.do_handshake()

            latency_ms = round((time.monotonic() - start) * 1000, 1)
            return {"success": True, "latency_ms": latency_ms, "error": None}

    except (socket.timeout, TimeoutError):
        return {"success": False, "latency_ms": None, "error": "Таймаут подключения."}
    except ConnectionRefusedError:
        return {"success": False, "latency_ms": None, "error": "Соединение отклонено (порт закрыт?)."}
    except ssl.SSLError as exc:
        return {"success": False, "latency_ms": None, "error": f"Ошибка TLS-handshake: {exc}"}
    except OSError as exc:
        return {"success": False, "latency_ms": None, "error": str(exc)}
