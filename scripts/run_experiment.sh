#!/bin/bash

# Enhanced Experiment Runner
# Runs experiments multiple times for statistical significance

set -e

# Configuration
NUM_RUNS=5
COOLDOWN_SECONDS=60
WARMUP_SECONDS=30

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: $0 <experiment_number> [options]"
    echo ""
    echo "Examples:"
    echo "  $0 1                    # Run Experiment 1 (5 runs)"
    echo "  $0 2 --runs 10          # Run Experiment 2 (10 runs)"
    echo "  $0 3 --users 50         # Run Experiment 3 with 50 users"
    echo ""
    echo "Options:"
    echo "  --runs N                Number of test runs (default: 5)"
    echo "  --users N               Concurrent users (default: varies by experiment)"
    echo "  --duration N            Test duration in seconds (default: 90)"
    echo "  --no-cleanup            Skip cleanup between runs"
    exit 1
}

cleanup_system() {
    echo -e "${BLUE}Cleaning up system...${NC}"

    # Truncate audit log
    docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db \
        -c "TRUNCATE TABLE audit_log;" 2>/dev/null || true

    # Clear Kafka consumer groups
    docker exec bpc4msa-kafka-1 kafka-consumer-groups \
        --bootstrap-server localhost:9092 --all-groups --delete 2>/dev/null || true
}

monitor_resources() {
    local output_file=$1
    local duration=$2

    echo "timestamp,container,cpu_percent,mem_usage,net_io" > "$output_file"

    for i in $(seq 1 $duration); do
        docker stats --no-stream --format \
            "{{.Container}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}}" | \
            while read line; do
                echo "$(date +%s),$line" >> "$output_file"
            done
        sleep 1
    done
}

run_load_test() {
    local exp_num=$1
    local run_num=$2
    local users=$3
    local duration=$4

    local spawn_rate=$((users / 5))
    [ $spawn_rate -lt 1 ] && spawn_rate=1

    local total_duration=$((duration + WARMUP_SECONDS))
    local output_prefix="../results/exp${exp_num}_run${run_num}"

    echo -e "${GREEN}Run $run_num/$NUM_RUNS${NC} - Users: $users, Duration: ${duration}s"

    # Start resource monitoring in background
    monitor_resources "${output_prefix}_resources.csv" $total_duration &
    local monitor_pid=$!

    # Run load test
    cd load-testing
    locust -f locustfile.py --headless \
        -u $users \
        -r $spawn_rate \
        --run-time ${total_duration}s \
        --host=http://localhost:8000 \
        --csv="$output_prefix" \
        --html="${output_prefix}.html" 2>&1 | tee "${output_prefix}.log"
    cd ..

    # Wait for monitoring to complete
    wait $monitor_pid

    # Capture final state
    docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db \
        -c "SELECT COUNT(*) as total_events, event_type FROM audit_log GROUP BY event_type;" \
        > "${output_prefix}_db_summary.txt"
}

# Parse arguments
EXPERIMENT=${1:-}
shift || usage

USERS=50
DURATION=90
DO_CLEANUP=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --runs)
            NUM_RUNS="$2"
            shift 2
            ;;
        --users)
            USERS="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --no-cleanup)
            DO_CLEANUP=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

[ -z "$EXPERIMENT" ] && usage

echo "================================================"
echo "Enhanced Experiment Runner"
echo "================================================"
echo "Experiment: $EXPERIMENT"
echo "Runs: $NUM_RUNS"
echo "Users: $USERS"
echo "Duration: ${DURATION}s (+ ${WARMUP_SECONDS}s warmup)"
echo "Cooldown: ${COOLDOWN_SECONDS}s"
echo "================================================"
echo ""

# Verify system is ready
echo -e "${BLUE}Verifying system...${NC}"
./verify_system.sh > /dev/null 2>&1 || {
    echo -e "${YELLOW}Warning: System verification failed. Continue anyway? (y/n)${NC}"
    read -r response
    [[ "$response" != "y" ]] && exit 1
}

# Create results directory
mkdir -p results

# Run experiment multiple times
for run in $(seq 1 $NUM_RUNS); do
    echo ""
    echo "================================================"
    echo "Run $run of $NUM_RUNS"
    echo "================================================"

    # Cleanup before run
    if [ "$DO_CLEANUP" = true ]; then
        cleanup_system
        sleep 5
    fi

    # Run test
    run_load_test "$EXPERIMENT" "$run" "$USERS" "$DURATION"

    # Cooldown between runs
    if [ $run -lt $NUM_RUNS ]; then
        echo -e "${YELLOW}Cooldown ${COOLDOWN_SECONDS}s...${NC}"
        sleep $COOLDOWN_SECONDS
    fi
done

echo ""
echo "================================================"
echo "All runs complete!"
echo "================================================"
echo ""
echo "Results saved to: results/exp${EXPERIMENT}_run*.csv"
echo ""
echo "Next steps:"
echo "  1. Aggregate results: python scripts/aggregate_results.py results/exp${EXPERIMENT}_run*.csv"
echo "  2. Generate graphs: python scripts/generate_graphs.py results/exp${EXPERIMENT}_run*"
echo ""
