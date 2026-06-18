"""
CloudWatch-style metrics monitor for e-commerce auto-scaling.
Simulates real-time CPU and traffic monitoring with threshold alerts.
L1 DevOps responsibility: watch this dashboard, escalate if CRITICAL.
"""

import time
import random
import logging
from datetime import datetime
from incident_log import log_incident

logging.basicConfig(
    filename="logs/monitor.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Thresholds (mirrors CloudWatch alarm config)
CPU_WARN_THRESHOLD    = 60   # %
CPU_CRITICAL_THRESHOLD = 80  # %
RPS_WARN_THRESHOLD    = 800  # requests/sec
RPS_CRITICAL_THRESHOLD = 1200

def get_metrics():
    """Simulate fetching metrics from CloudWatch / server agents."""
    cpu    = random.uniform(10, 100)
    rps    = random.uniform(100, 1500)
    memory = random.uniform(30, 95)
    return {"cpu": round(cpu, 1), "rps": round(rps, 1), "memory": round(memory, 1)}

def evaluate_metrics(metrics: dict) -> str:
    """Return severity: OK / WARNING / CRITICAL."""
    if metrics["cpu"] >= CPU_CRITICAL_THRESHOLD or metrics["rps"] >= RPS_CRITICAL_THRESHOLD:
        return "CRITICAL"
    if metrics["cpu"] >= CPU_WARN_THRESHOLD or metrics["rps"] >= RPS_WARN_THRESHOLD:
        return "WARNING"
    return "OK"

def print_dashboard(metrics: dict, severity: str, instance_count: int):
    colors = {"OK": "\033[92m", "WARNING": "\033[93m", "CRITICAL": "\033[91m"}
    reset  = "\033[0m"
    color  = colors.get(severity, "")
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*55}")
    print(f"  E-Commerce Auto-Scale Monitor   {ts}")
    print(f"{'='*55}")
    print(f"  CPU Usage   : {metrics['cpu']:>6}%")
    print(f"  Requests/s  : {metrics['rps']:>6}")
    print(f"  Memory      : {metrics['memory']:>6}%")
    print(f"  Instances   : {instance_count}")
    print(f"  Status      : {color}{severity}{reset}")
    print(f"{'='*55}")

def monitor_loop(iterations=10, interval=3):
    """
    Main monitoring loop — runs continuously in production.
    L1 action guide:
      OK       → no action needed
      WARNING  → watch closely, prepare to escalate
      CRITICAL → trigger scaler.py, log incident, notify on-call
    """
    import os
    os.makedirs("logs", exist_ok=True)

    instance_count = 2  # baseline

    for i in range(iterations):
        metrics  = get_metrics()
        severity = evaluate_metrics(metrics)

        logging.info(f"CPU={metrics['cpu']}% RPS={metrics['rps']} MEM={metrics['memory']}% Status={severity}")
        print_dashboard(metrics, severity, instance_count)

        if severity == "CRITICAL":
            print("  [ACTION] Triggering auto-scaler...")
            from scaler import scale_out
            instance_count = scale_out(instance_count, metrics)
            log_incident(
                severity="CRITICAL",
                description=f"CPU={metrics['cpu']}% RPS={metrics['rps']} exceeded threshold",
                action_taken="Auto-scaler triggered (scale-out)"
            )

        elif severity == "WARNING":
            print("  [NOTICE] Elevated load — monitoring closely")
            logging.warning(f"Elevated load: {metrics}")

        else:
            # Try to scale in if load is low and we have extra capacity
            if instance_count > 2 and metrics["cpu"] < 40 and metrics["rps"] < 400:
                from scaler import scale_in
                instance_count = scale_in(instance_count)

        time.sleep(interval)

    print("\n[Monitor] Session complete. Check logs/monitor.log and logs/incidents.log")

if __name__ == "__main__":
    print("Starting CloudWatch-style monitor (Ctrl+C to stop)...")
    try:
        monitor_loop(iterations=20, interval=2)
    except KeyboardInterrupt:
        print("\n[Monitor] Stopped by operator.")
