# SOC Log Triage Pipeline
#
# Processes a batch of security events and produces a structured triage report.
#
# For each event the pipeline:
#   1. Classifies severity (critical / high / medium / low)
#   2. Validates source IPs
#   3. Extracts attacker IPs from log messages via regex
#   4. Computes a numeric risk score
#   5. Aggregates counts and top-risk events
#   6. Renders a human-readable triage summary
#
# Run:
#   poetry run cy run examples/basics/soc_log_triage.cy

# ── sample event batch ──────────────────────────────────────────────────────

events = [
    {
        "id": "EVT-001",
        "type": "auth_failure",
        "message": "Failed SSH login from 203.0.113.42 user=root attempts=47",
        "source_ip": "203.0.113.42",
        "dest_port": 22,
        "score_base": 7
    },
    {
        "id": "EVT-002",
        "type": "port_scan",
        "message": "Port scan detected from 198.51.100.77 probing 1024 ports",
        "source_ip": "198.51.100.77",
        "dest_port": 0,
        "score_base": 5
    },
    {
        "id": "EVT-003",
        "type": "data_exfil",
        "message": "Large outbound transfer 450MB to 93.184.216.34 over port 443",
        "source_ip": "93.184.216.34",
        "dest_port": 443,
        "score_base": 9
    },
    {
        "id": "EVT-004",
        "type": "malware_beacon",
        "message": "Beacon traffic from internal host to 185.220.101.5 every 60s",
        "source_ip": "185.220.101.5",
        "dest_port": 8080,
        "score_base": 10
    },
    {
        "id": "EVT-005",
        "type": "config_change",
        "message": "Firewall rule deleted by admin@192.168.1.10 outside change window",
        "source_ip": "192.168.1.10",
        "dest_port": 0,
        "score_base": 6
    },
    {
        "id": "EVT-006",
        "type": "auth_failure",
        "message": "Failed RDP login from 45.33.32.156 user=administrator attempts=12",
        "source_ip": "45.33.32.156",
        "dest_port": 3389,
        "score_base": 6
    },
    {
        "id": "EVT-007",
        "type": "dns_tunnel",
        "message": "Suspicious DNS queries to evil.example.com from 10.0.0.55",
        "source_ip": "10.0.0.55",
        "dest_port": 53,
        "score_base": 8
    },
    {
        "id": "EVT-008",
        "type": "info",
        "message": "Scheduled backup completed successfully on 10.0.0.1",
        "source_ip": "10.0.0.1",
        "dest_port": 0,
        "score_base": 1
    }
]

# ── scoring constants ────────────────────────────────────────────────────────
# Port multipliers: privileged ports get a small bump
PRIV_PORT_BONUS    = 2
# Type weights
WEIGHT_MALWARE     = 4
WEIGHT_EXFIL       = 3
WEIGHT_AUTH        = 2
WEIGHT_SCAN        = 1
WEIGHT_DNS         = 3
WEIGHT_CONFIG      = 2
WEIGHT_DEFAULT     = 1

# ── per-event enrichment and scoring ────────────────────────────────────────

scored = []
i = 0
while (i < list::len(events)) {
    evt = events[i]

    # Extract typed fields with safe defaults
    evt_id        = evt.id ?? ""
    evt_type      = evt.type ?? ""
    evt_message   = evt.message ?? ""
    evt_source_ip = evt.source_ip ?? ""
    evt_dest_port = evt.dest_port ?? 0
    evt_score_base = evt.score_base ?? 1

    # Enrich: IP validation + regex extraction
    ip_valid     = ip::is_v4(evt_source_ip)
    extracted_ip = regex::extract(evt_message, "(\\d+\\.\\d+\\.\\d+\\.\\d+)")

    # Type weight
    weight = WEIGHT_DEFAULT
    if (evt_type == "malware_beacon") {
        weight = WEIGHT_MALWARE
    } elif (evt_type == "data_exfil") {
        weight = WEIGHT_EXFIL
    } elif (evt_type == "auth_failure") {
        weight = WEIGHT_AUTH
    } elif (evt_type == "port_scan") {
        weight = WEIGHT_SCAN
    } elif (evt_type == "dns_tunnel") {
        weight = WEIGHT_DNS
    } elif (evt_type == "config_change") {
        weight = WEIGHT_CONFIG
    }

    # Port bonus for privileged destination ports (1–1023)
    port_bonus = 0
    if (evt_dest_port > 0 and evt_dest_port < 1024) {
        port_bonus = PRIV_PORT_BONUS
    }

    risk_score = evt_score_base * weight + port_bonus

    # Severity label
    severity = "low"
    if (risk_score >= 35) {
        severity = "critical"
    } elif (risk_score >= 20) {
        severity = "high"
    } elif (risk_score >= 10) {
        severity = "medium"
    }

    scored = scored + [{
        "id":           evt_id,
        "type":         evt_type,
        "message":      evt_message,
        "source_ip":    evt_source_ip,
        "ip_valid":     ip_valid,
        "extracted_ip": extracted_ip,
        "risk_score":   risk_score,
        "severity":     severity
    }]

    i = i + 1
}

# ── aggregate statistics ─────────────────────────────────────────────────────

total_events = list::len(scored)

critical_events = [e for(e in scored) if(e.severity == "critical")]
high_events     = [e for(e in scored) if(e.severity == "high")]
medium_events   = [e for(e in scored) if(e.severity == "medium")]
low_events      = [e for(e in scored) if(e.severity == "low")]

n_critical = list::len(critical_events)
n_high     = list::len(high_events)
n_medium   = list::len(medium_events)
n_low      = list::len(low_events)

# Collect all risk scores for average calculation
all_scores    = [e.risk_score for(e in scored)]
total_score   = list::sum(all_scores)
avg_score     = math::round(total_score / total_events, 1)
max_score     = list::max(all_scores)

# Invalid IPs (spoof / malformed)
invalid_ip_events = [e for(e in scored) if(e.ip_valid == False)]
n_invalid_ips = list::len(invalid_ip_events)

# ── sort by risk score descending (manual selection sort on small list) ───────

sorted_events = []
remaining = scored
j = 0
while (j < total_events) {
    best_idx   = 0
    first_rem  = remaining[0]
    best_score = first_rem.risk_score
    k = 1
    while (k < list::len(remaining)) {
        candidate = remaining[k]
        if (candidate.risk_score > best_score) {
            best_score = candidate.risk_score
            best_idx   = k
        }
        k = k + 1
    }
    sorted_events = sorted_events + [remaining[best_idx]]

    # Remove best_idx from remaining (rebuild without it)
    new_remaining = []
    m = 0
    while (m < list::len(remaining)) {
        if (m != best_idx) {
            new_remaining = new_remaining + [remaining[m]]
        }
        m = m + 1
    }
    remaining = new_remaining
    j = j + 1
}

# Top 3 events
top1 = sorted_events[0]
top2 = sorted_events[1]
top3 = sorted_events[2]

top1_id       = top1.id
top1_type     = top1.type
top1_sev      = str::uppercase(top1.severity ?? "unknown")
top1_score    = top1.risk_score
top1_ip       = top1.source_ip
top1_msg      = top1.message

top2_id       = top2.id
top2_type     = top2.type
top2_sev      = str::uppercase(top2.severity ?? "unknown")
top2_score    = top2.risk_score
top2_ip       = top2.source_ip

top3_id       = top3.id
top3_type     = top3.type
top3_sev      = str::uppercase(top3.severity ?? "unknown")
top3_score    = top3.risk_score
top3_ip       = top3.source_ip

# ── build structured result ─────────────────────────────────────────────────

report = {
    "summary": {
        "total_events":   total_events,
        "critical":       n_critical,
        "high":           n_high,
        "medium":         n_medium,
        "low":            n_low,
        "avg_risk_score": avg_score,
        "max_risk_score": max_score,
        "invalid_ips":    n_invalid_ips
    },
    "top_events": [top1, top2, top3],
    "all_events_by_risk": sorted_events
}

triage_text = """
======================================================
  SOC TRIAGE REPORT
======================================================

SUMMARY
-------
  Total events     : ${total_events}
  Critical         : ${n_critical}
  High             : ${n_high}
  Medium           : ${n_medium}
  Low              : ${n_low}
  Avg risk score   : ${avg_score}
  Max risk score   : ${max_score}
  Invalid-IP events: ${n_invalid_ips}

TOP 3 EVENTS BY RISK
--------------------
  #1  [${top1_sev}]  ${top1_id} (${top1_type})
      Risk: ${top1_score}  |  IP: ${top1_ip}
      ${top1_msg}

  #2  [${top2_sev}]  ${top2_id} (${top2_type})
      Risk: ${top2_score}  |  IP: ${top2_ip}

  #3  [${top3_sev}]  ${top3_id} (${top3_type})
      Risk: ${top3_score}  |  IP: ${top3_ip}

======================================================
"""

return {
    "report": report,
    "triage_text": triage_text
}
