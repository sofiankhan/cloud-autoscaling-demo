"""
Incident logging and tracking.
L1 responsibility: log every alert, include context for L2 escalation.
"""

import json
import os
from datetime import datetime

LOG_FILE = "logs/incidents.log"
JSON_FILE = "logs/incidents.json"


def log_incident(severity: str, description: str, action_taken: str):
    os.makedirs("logs", exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "severity": severity,
        "description": description,
        "action_taken": action_taken,
        "status": "OPEN"
    }

    # Append to human-readable log
    with open(LOG_FILE, "a") as f:
        f.write(
            f"[{entry['timestamp']}] [{severity}] {description} | "
            f"Action: {action_taken}\n"
        )

    # Append to JSON log (machine-readable, useful for dashboards)
    incidents = _load_incidents()
    incidents.append(entry)
    with open(JSON_FILE, "w") as f:
        json.dump(incidents, f, indent=2)

    print(f"  [Incident] Logged: {severity} — {description}")


def list_open_incidents():
    incidents = _load_incidents()
    open_ones = [i for i in incidents if i["status"] == "OPEN"]
    if not open_ones:
        print("No open incidents.")
        return

    print(f"\n{'='*60}")
    print(f"  OPEN INCIDENTS ({len(open_ones)})")
    print(f"{'='*60}")
    for idx, inc in enumerate(open_ones, 1):
        print(f"  {idx}. [{inc['severity']}] {inc['timestamp']}")
        print(f"     {inc['description']}")
        print(f"     Action: {inc['action_taken']}")
    print(f"{'='*60}\n")


def resolve_incident(index: int):
    """Mark incident as RESOLVED during shift handover."""
    incidents = _load_incidents()
    open_ones = [i for i in incidents if i["status"] == "OPEN"]
    if index < 1 or index > len(open_ones):
        print(f"Invalid index {index}")
        return

    target_ts = open_ones[index - 1]["timestamp"]
    for inc in incidents:
        if inc["timestamp"] == target_ts:
            inc["status"] = "RESOLVED"
            inc["resolved_at"] = datetime.now().isoformat()
            break

    with open(JSON_FILE, "w") as f:
        json.dump(incidents, f, indent=2)
    print(f"  [Incident] Resolved: {open_ones[index - 1]['description']}")


def shift_handover_report():
    """Print a handover summary — used at end of every shift."""
    incidents = _load_incidents()
    open_count     = sum(1 for i in incidents if i["status"] == "OPEN")
    resolved_count = sum(1 for i in incidents if i["status"] == "RESOLVED")
    critical_count = sum(1 for i in incidents if i["severity"] == "CRITICAL")

    print(f"\n{'='*60}")
    print("  SHIFT HANDOVER REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"  Total incidents  : {len(incidents)}")
    print(f"  Critical         : {critical_count}")
    print(f"  Open (needs work): {open_count}")
    print(f"  Resolved         : {resolved_count}")
    print(f"{'='*60}")
    print("  [L1 Action] Review open incidents before handover!")
    list_open_incidents()


def _load_incidents() -> list:
    if not os.path.exists(JSON_FILE):
        return []
    with open(JSON_FILE) as f:
        return json.load(f)


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    log_incident("WARNING",  "CPU spiked to 72% on web-01", "Monitoring — no action yet")
    log_incident("CRITICAL", "RPS=1400 exceeded threshold",  "Auto-scaler triggered")
    log_incident("WARNING",  "Memory at 88% on db-02",       "Alerted L2 team")
    shift_handover_report()
