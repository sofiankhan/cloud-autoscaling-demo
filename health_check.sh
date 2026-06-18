#!/bin/bash
# ============================================================
# health_check.sh — Bash equivalent of health_check.py
# Run manually or via cron: */5 * * * * /path/to/health_check.sh
# L1 DevOps: execute this at start of every shift
# ============================================================

LOG_DIR="./logs"
LOG_FILE="$LOG_DIR/health_check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
PASS="\e[92mPASS\e[0m"
FAIL="\e[91mFAIL\e[0m"
WARN="\e[93mWARN\e[0m"
OVERALL=0   # 0=pass, 1=fail

mkdir -p "$LOG_DIR"

log() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

print_header() {
    echo ""
    echo "=================================================="
    echo "  Health Check   $TIMESTAMP"
    echo "  Host: $(hostname)"
    echo "=================================================="
}

check_disk() {
    USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
    if [ "$USAGE" -lt 80 ]; then
        echo -e "  Disk usage    : ${USAGE}%  [$PASS]"
        log "Disk=${USAGE}% OK"
    else
        echo -e "  Disk usage    : ${USAGE}%  [$WARN]"
        log "Disk=${USAGE}% WARNING"
        OVERALL=1
    fi
}

check_memory() {
    if command -v free &>/dev/null; then
        TOTAL=$(free | awk '/Mem:/ {print $2}')
        USED=$(free  | awk '/Mem:/ {print $3}')
        PCT=$(( USED * 100 / TOTAL ))
        if [ "$PCT" -lt 85 ]; then
            echo -e "  Memory usage  : ${PCT}%  [$PASS]"
            log "Memory=${PCT}% OK"
        else
            echo -e "  Memory usage  : ${PCT}%  [$WARN]"
            log "Memory=${PCT}% WARNING"
            OVERALL=1
        fi
    else
        echo -e "  Memory usage  : free not available  [$WARN]"
    fi
}

check_network() {
    HOSTS=("8.8.8.8" "1.1.1.1")
    for HOST in "${HOSTS[@]}"; do
        if ping -c 1 -W 2 "$HOST" &>/dev/null; then
            echo -e "  Network $HOST : reachable  [$PASS]"
            log "Network $HOST OK"
        else
            echo -e "  Network $HOST : UNREACHABLE  [$FAIL]"
            log "Network $HOST FAILED"
            OVERALL=1
        fi
    done
}

check_log_dir() {
    if [ -d "$LOG_DIR" ]; then
        echo -e "  Log directory : exists  [$PASS]"
        log "Log dir OK"
    else
        echo -e "  Log directory : MISSING  [$FAIL]"
        log "Log dir MISSING"
        OVERALL=1
    fi
}

check_python() {
    if command -v python3 &>/dev/null; then
        VER=$(python3 --version 2>&1)
        echo -e "  Python        : $VER  [$PASS]"
        log "Python OK: $VER"
    else
        echo -e "  Python        : not found  [$FAIL]"
        log "Python NOT FOUND"
        OVERALL=1
    fi
}

print_footer() {
    echo "=================================================="
    if [ $OVERALL -eq 0 ]; then
        echo -e "  Overall Status : [$PASS]"
    else
        echo -e "  Overall Status : [$FAIL]"
        echo "  [L1 Action] Check failed — see runbook.md Section 3"
    fi
    echo "=================================================="
    echo ""
}

# ---- Main ----
print_header
check_disk
check_memory
check_network
check_log_dir
check_python
print_footer

exit $OVERALL
