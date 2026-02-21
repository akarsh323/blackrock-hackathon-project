import time
import threading
import psutil
import os
from datetime import timedelta


_start_time = time.time()


def get_uptime_str() -> str:
    """Returns formatted uptime since the app started: HH:MM:SS.mmm"""
    elapsed = time.time() - _start_time
    td = timedelta(seconds=elapsed)
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    millis = int((elapsed % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"


def get_memory_usage_mb() -> str:
    """Returns current process memory usage in MB as a string."""
    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss
    mem_mb = mem_bytes / (1024 * 1024)
    return f"{mem_mb:.2f} MB"


def get_thread_count() -> int:
    """Returns number of active threads in the current process."""
    return threading.active_count()


def get_performance_metrics() -> dict:
    """
    Aggregates all performance metrics into a single dict.

    Returns:
        {
            "time":    "00:00:05.243",
            "memory":  "25.11 MB",
            "threads": 16
        }
    """
    return {
        "time":    get_uptime_str(),
        "memory":  get_memory_usage_mb(),
        "threads": get_thread_count(),
    }
