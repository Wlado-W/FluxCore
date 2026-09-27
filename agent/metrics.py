"""Сбор системных метрик ноды (CPU/RAM/диск/аптайм) через psutil."""
import time

import psutil

_BOOT_TIME = psutil.boot_time()


def collect_metrics() -> dict:
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": disk.percent,
        "traffic_up_bytes": net.bytes_sent,
        "traffic_down_bytes": net.bytes_recv,
        "uptime_seconds": int(time.time() - _BOOT_TIME),
    }
