# Load Testing Scripts for BPC4MSA Framework

This directory contains Locust-based load testing scripts for executing the performance experiments defined in the research manuscript.

## Prerequisites

1. **Python 3.11+** installed
2. **Locust** installed in a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install locust
   ```
3. **Docker** running with all BPC4MSA services up:
   ```bash
   cd ..
   docker-compose up --build -d
   ```

## Quick Start

Test that Locust is working:
```bash
locust -f locustfile.py --headless -u 10 -r 2 --run-time 10s --host=http://localhost:8000
```

## Experiment Commands

### Experiment 1: Baseline Performance (No Compliance Overhead)

**Objective:** Establish baseline performance metrics.

**Setup:**
```bash
# 1. Edit ../docker-compose.yml and comment out compliance-service
# 2. Restart system
cd ..
docker-compose down
docker-compose up --build -d
cd load-testing
```

**Execute:**
```bash
locust -f locustfile.py --headless -u 50 -r 10 --run-time 60s \
       --host=http://localhost:8000 --csv=../results/exp1_baseline
```

**Metrics to Record:**
- Requests/sec (RPS)
- P95 Latency
- P99 Latency
- Failure rate

---

### Experiment 2: Compliance Overhead

**Objective:** Measure the performance cost of compliance monitoring.

**Setup:**
```bash
# 1. Edit ../docker-compose.yml and uncomment compliance-service
# 2. Restart system
cd ..
docker-compose down
docker-compose up --build -d
cd load-testing
```

**Execute:**
```bash
locust -f locustfile.py --headless -u 50 -r 10 --run-time 60s \
       --host=http://localhost:8000 --csv=../results/exp2_overhead
```

**Analysis:**
Compare RPS and latency with Experiment 1 to calculate overhead percentage.

---

### Experiment 3: Scalability Assessment

**Objective:** Test how the system scales under increasing load.

**Execute Test Series:**
```bash
# 10 users
locust -f locustfile.py --headless -u 10 -r 2 --run-time 60s \
       --host=http://localhost:8000 --csv=../results/exp3_10_users

# 25 users
locust -f locustfile.py --headless -u 25 -r 5 --run-time 60s \
       --host=http://localhost:8000 --csv=../results/exp3_25_users

# 50 users
locust -f locustfile.py --headless -u 50 -r 10 --run-time 60s \
       --host=http://localhost:8000 --csv=../results/exp3_50_users

# 75 users
locust -f locustfile.py --headless -u 75 -r 15 --run-time 60s \
       --host=http://localhost:8000 --csv=../results/exp3_75_users

# 100 users
locust -f locustfile.py --headless -u 100 -r 20 --run-time 60s \
       --host=http://localhost:8000 --csv=../results/exp3_100_users
```

**Generate Graphs:**
Use the CSV files to plot:
1. User Count vs. Actual RPS
2. User Count vs. P95 Latency

---

### Experiment 4: Effectiveness Validation

**Objective:** Verify 100% violation detection accuracy.

**Setup:**
```bash
# Clear the audit log
docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db \
  -c "TRUNCATE TABLE audit_log;"
```

**Execute with 10% violation rate:**
```bash
VIOLATION_RATE=0.1 locust -f locustfile.py --headless -u 10 -r 2 \
       --run-time 30s --host=http://localhost:8000
```

The script will print the number of violations sent. Then verify detection:

```bash
docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db \
  -c "SELECT COUNT(*) FROM audit_log WHERE event_type = 'ViolationDetected';"
```

**Expected Result:** Count should match the violations sent (100% detection rate).

---

### Experiment 5: Dynamic Rule Adaptability

**Objective:** Demonstrate runtime rule updates without restart.

**Setup - Initial Rules:**
```bash
# Create initial rules with lower threshold
cat > ../config/rules.json << 'EOF'
[
  {
    "id": "RULE001",
    "type": "field_value",
    "description": "Transaction status must not be 'suspended'",
    "field": "status",
    "forbidden_values": ["suspended", "blocked"]
  },
  {
    "id": "RULE002",
    "type": "field_range",
    "description": "Transaction amount must be between 0 and 5000",
    "field": "amount",
    "min": 0,
    "max": 5000
  }
]
EOF
```

**Execute Continuous Load:**
```bash
# Start 5-minute continuous load test
locust -f locustfile.py --headless -u 25 -r 5 --run-time 300s \
       --host=http://localhost:8000 --csv=../results/exp5_adaptability &
```

**Monitor violations:**
Open http://localhost:3000 in browser to watch live violations.

**After 90 seconds, update the rule** (in a new terminal):
```bash
# Update rule to higher threshold (fewer violations expected)
cat > ../config/rules.json << 'EOF'
[
  {
    "id": "RULE001",
    "type": "field_value",
    "description": "Transaction status must not be 'suspended'",
    "field": "status",
    "forbidden_values": ["suspended", "blocked"]
  },
  {
    "id": "RULE002",
    "type": "field_range",
    "description": "Transaction amount must be between 0 and 15000",
    "field": "amount",
    "min": 0,
    "max": 15000
  }
]
EOF
```

**Observe:** Within 10 seconds, the compliance service will reload rules and violation rates should drop on the live frontend.

**Data Collection:**
- Screenshot the frontend before and after the rule change
- Query violation counts before/after:
  ```bash
  docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db \
    -c "SELECT DATE_TRUNC('second', timestamp) as sec, COUNT(*)
        FROM audit_log
        WHERE event_type = 'ViolationDetected'
        GROUP BY sec
        ORDER BY sec;"
  ```

---

## Configuration Options

### Environment Variables

- `VIOLATION_RATE`: Float 0.0-1.0, percentage of requests that should violate rules (default: 0.0)
- `ENABLE_LOGGING`: Set to `true` for verbose logging (default: false)

### Locust Parameters

- `-u` or `--users`: Total number of concurrent users
- `-r` or `--spawn-rate`: Users spawned per second
- `--run-time`: Test duration (e.g., `60s`, `5m`)
- `--csv`: Output CSV file prefix for results
- `--headless`: Run without web UI

## Results Location

All test results should be saved to `../results/` directory:
- CSV files: `exp1_baseline_stats.csv`, etc.
- Screenshots: For Experiment 5
- Summary: `../results/summary.md`

## Troubleshooting

**Connection Refused:**
- Ensure Docker services are running: `docker-compose ps`
- Check business-logic service: `curl http://localhost:8000/health`

**No Violations Detected:**
- Verify compliance-service is running: `docker-compose logs compliance-service`
- Check rules.json is mounted: `docker-compose logs compliance-service | grep "Loaded.*rules"`

**High Failure Rate:**
- Reduce spawn rate (`-r`)
- Check service logs: `docker-compose logs business-logic`
