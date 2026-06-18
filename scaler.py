"""
Auto-scaling logic — simulates AWS Auto Scaling Group behavior.
In production this would call boto3 (AWS SDK) or Azure SDK.
L1 engineers run this manually or it's triggered by monitor.py.
"""

import logging
import time
from datetime import datetime

logging.basicConfig(
    filename="logs/scaler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

MAX_INSTANCES = 10
MIN_INSTANCES = 2
SCALE_OUT_STEP = 2   # add 2 instances per trigger
SCALE_IN_STEP  = 1   # remove 1 instance per trigger


def provision_instance(instance_number: int):
    """
    Simulates spinning up a new EC2/VM instance.
    Real version: boto3 ec2.run_instances() or Terraform apply.
    """
    print(f"    [+] Provisioning instance-{instance_number:03d}...")
    time.sleep(0.5)  # simulate boot time
    print(f"    [+] instance-{instance_number:03d} is RUNNING")
    logging.info(f"Provisioned instance-{instance_number:03d}")


def terminate_instance(instance_number: int):
    """
    Simulates terminating an idle EC2/VM to save cost.
    Real version: boto3 ec2.terminate_instances().
    """
    print(f"    [-] Terminating instance-{instance_number:03d}...")
    time.sleep(0.3)
    print(f"    [-] instance-{instance_number:03d} TERMINATED")
    logging.info(f"Terminated instance-{instance_number:03d}")


def scale_out(current_count: int, metrics: dict) -> int:
    """Add instances when load is high."""
    if current_count >= MAX_INSTANCES:
        print(f"  [Scaler] Already at MAX capacity ({MAX_INSTANCES}). Escalate to L2!")
        logging.warning("MAX capacity reached — manual intervention needed")
        return current_count

    add = min(SCALE_OUT_STEP, MAX_INSTANCES - current_count)
    print(f"\n  [Scaler] SCALE OUT: +{add} instance(s)  "
          f"(CPU={metrics['cpu']}%, RPS={metrics['rps']})")
    logging.info(f"Scale-out triggered: +{add} | metrics={metrics}")

    for i in range(add):
        provision_instance(current_count + i + 1)

    new_count = current_count + add
    print(f"  [Scaler] Fleet: {current_count} -> {new_count} instances")
    return new_count


def scale_in(current_count: int) -> int:
    """Remove instances when load drops to save cost."""
    if current_count <= MIN_INSTANCES:
        return current_count

    remove = min(SCALE_IN_STEP, current_count - MIN_INSTANCES)
    print(f"\n  [Scaler] SCALE IN: -{remove} instance(s)  (load is low)")
    logging.info(f"Scale-in triggered: -{remove}")

    for i in range(remove):
        terminate_instance(current_count - i)

    new_count = current_count - remove
    print(f"  [Scaler] Fleet: {current_count} -> {new_count} instances")
    return new_count


def scaling_report(current_count: int, metrics: dict):
    """Print a one-line scaling decision summary — used in runbooks."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] Instances={current_count} | CPU={metrics['cpu']}% | "
          f"RPS={metrics['rps']} | MEM={metrics['memory']}%")


if __name__ == "__main__":
    # Quick manual test of scale-out and scale-in
    import os
    os.makedirs("logs", exist_ok=True)

    sample_metrics = {"cpu": 85.3, "rps": 1350, "memory": 78.1}
    count = 2
    print("=== Scaler Manual Test ===")
    count = scale_out(count, sample_metrics)
    time.sleep(1)
    low_metrics = {"cpu": 25.0, "rps": 200, "memory": 40.0}
    count = scale_in(count)
    scaling_report(count, low_metrics)
