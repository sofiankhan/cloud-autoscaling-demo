# Operational Runbook — E-Commerce Auto-Scaling System

**Team:** DevOps L1  
**Last Updated:** 2026-06-18  
**Escalation Contact:** L2 DevOps on-call

---

## 1. Start of Shift Checklist

Run these in order at the beginning of every shift:

```bash
# 1. Run health check
python health_check.py

# 2. Start the monitor (keep running in background)
python monitor.py

# 3. Review open incidents from previous shift
python incident_log.py
```

Check `logs/incidents.json` — resolve any incidents marked OPEN that are no longer active.

---

## 2. Auto-Scaling Triggers

| Condition | Threshold | L1 Action |
|-----------|-----------|-----------|
| CPU > 60% | WARNING | Watch monitor, no action yet |
| CPU > 80% | CRITICAL | Confirm scaler triggered, log incident |
| RPS > 800 | WARNING | Watch monitor |
| RPS > 1200 | CRITICAL | Confirm scaler triggered, log incident |
| Memory > 85% | WARNING | Alert L2 immediately |
| Instances = MAX (10) | CRITICAL | Escalate to L2 + client |

### Auto-Scaler is ON (normal operation)
- `monitor.py` detects threshold breach
- `scaler.py scale_out()` provisions 2 new instances automatically
- When load drops below 40% CPU / 400 RPS, `scale_in()` removes 1 instance

### If auto-scaler fails to trigger
1. Check `logs/scaler.log` for errors
2. Manually run: `python scaler.py`
3. If still failing, escalate to L2 with full log context

---

## 3. Health Check Failures

### Disk > 80%
```bash
# Check what's consuming space
du -sh /var/log/* | sort -h | tail -10
# Archive old logs if safe
gzip logs/*.log.old
```
Escalate to L2 if disk > 90%.

### Memory > 85%
```bash
# Check top memory consumers
ps aux --sort=-%mem | head -10
```
Escalate to L2 if memory > 90% and trending up.

### Network Unreachable
1. Ping internal gateway first: `ping 10.0.0.1`
2. If gateway unreachable — escalate to infrastructure team immediately
3. If only external DNS fails — check AWS/Azure console for outage

---

## 4. Incident Logging (Required for Every Alert)

Every WARNING or CRITICAL alert must be logged before escalation:

```python
from incident_log import log_incident

log_incident(
    severity="CRITICAL",
    description="CPU=92% on web-03 during flash sale",
    action_taken="Scaler triggered, added 2 instances. L2 notified."
)
```

---

## 5. Shift Handover

Before ending your shift:

```python
from incident_log import shift_handover_report
shift_handover_report()
```

Send the output to the incoming L1 engineer and the L2 on-call channel.

---

## 6. Escalation Template

Use this when contacting L2 or the client:

```
[ESCALATION] [SEVERITY] [TIMESTAMP]

System  : E-Commerce Auto-Scale
Alert   : <describe the alert>
Metrics : CPU=__% | RPS=__ | Memory=__%
Action  : <what L1 already did>
Status  : <current state>
Logs    : logs/monitor.log, logs/incidents.json
```

---

## 7. File Reference

| File | Purpose |
|------|---------|
| `monitor.py` | Real-time metrics monitoring loop |
| `scaler.py` | Scale-out / scale-in logic |
| `health_check.py` | Pre/post deployment health check |
| `health_check.sh` | Bash version (cron-friendly) |
| `incident_log.py` | Log and track incidents |
| `logs/monitor.log` | Raw metrics history |
| `logs/scaler.log` | Scale-out/in event history |
| `logs/incidents.log` | Human-readable incident log |
| `logs/incidents.json` | Machine-readable incident store |
