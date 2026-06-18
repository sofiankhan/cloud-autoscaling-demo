"""
Health check script — run this every 5 minutes via cron or Task Scheduler.
L1 uses this as part of the operational runbook before/after deployments.
"""

import subprocess
import platform
import socket
import os
import sys
import logging
from datetime import datetime

logging.basicConfig(
    filename="logs/health_check.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Services and endpoints to check
SERVICES = ["nginx", "python", "node"]         # process names
ENDPOINTS = [("8.8.8.8", 53), ("1.1.1.1", 53)] # (host, port) connectivity checks
DISK_WARN_PCT = 80
MEM_WARN_PCT  = 85

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"


def check_disk_usage() -> bool:
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        pct = (used / total) * 100
        status = PASS if pct < DISK_WARN_PCT else WARN
        print(f"  Disk usage    : {pct:.1f}%  [{status}]")
        logging.info(f"Disk={pct:.1f}%")
        return pct < DISK_WARN_PCT
    except Exception as e:
        print(f"  Disk usage    : ERROR — {e}  [{FAIL}]")
        return False


def check_memory() -> bool:
    try:
        import psutil
        mem = psutil.virtual_memory()
        pct = mem.percent
        status = PASS if pct < MEM_WARN_PCT else WARN
        print(f"  Memory usage  : {pct:.1f}%  [{status}]")
        logging.info(f"Memory={pct:.1f}%")
        return pct < MEM_WARN_PCT
    except ImportError:
        print(f"  Memory usage  : psutil not installed — skipped  [{WARN}]")
        return True


def check_network_connectivity() -> bool:
    all_ok = True
    for host, port in ENDPOINTS:
        try:
            sock = socket.create_connection((host, port), timeout=3)
            sock.close()
            print(f"  Network {host}:{port}: reachable  [{PASS}]")
            logging.info(f"Network {host}:{port} OK")
        except (socket.timeout, OSError) as e:
            print(f"  Network {host}:{port}: UNREACHABLE  [{FAIL}]")
            logging.error(f"Network {host}:{port} FAILED: {e}")
            all_ok = False
    return all_ok


def check_log_directory() -> bool:
    exists = os.path.isdir("logs")
    status = PASS if exists else FAIL
    print(f"  Log directory : {'exists' if exists else 'MISSING'}  [{status}]")
    if not exists:
        logging.error("Log directory missing")
    return exists


def run_health_check() -> bool:
    os.makedirs("logs", exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*50}")
    print(f"  Health Check   {ts}")
    print(f"  Host: {socket.gethostname()}")
    print(f"{'='*50}")

    results = [
        check_disk_usage(),
        check_memory(),
        check_network_connectivity(),
        check_log_directory(),
    ]

    overall = all(results)
    overall_status = PASS if overall else FAIL
    print(f"{'='*50}")
    print(f"  Overall Status : [{overall_status}]")
    print(f"{'='*50}\n")

    logging.info(f"Health check complete — overall={'PASS' if overall else 'FAIL'}")

    if not overall:
        print("  [L1 Action] One or more checks FAILED.")
        print("  Follow runbook.md -> Section 3: Health Check Failures")

    return overall


if __name__ == "__main__":
    ok = run_health_check()
    sys.exit(0 if ok else 1)
