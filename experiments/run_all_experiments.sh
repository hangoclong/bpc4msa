#!/bin/bash
#
# Automated Experiment Runner for BPC4MSA Publication
# Runs all 5 experiments from PRD_Analyst_Experiment.md
#
# Prerequisites:
# - Docker and docker-compose installed
# - Locust installed: pip install locust
# - All services running: docker-compose -f docker-compose.experiment.yml up -d
#
# Output:
# - CSV files in /tmp/experiment_*.csv
# - HTML reports in ./reports/
# - Consolidated results in ./results/
#

set -e  # Exit on error

# Colors for output
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
REPORTS_DIR="./reports"
RESULTS_DIR="./results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create directories
mkdir -p "$REPORTS_DIR"
mkdir -p "$RESULTS_DIR"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}BPC4MSA Experiment Suite${NC}"
echo -e "${GREEN}Publication Version${NC}"
echo -e "${GREEN}Timestamp: $TIMESTAMP${NC}"
echo -e "${GREEN}======================================${NC}"

# Function to wait for services to be healthy
wait_for_services() {
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 10

    # Check BPC4MSA
    until curl -sf http://localhost:8000/health > /dev/null; do
        echo "  Waiting for BPC4MSA (port 8000)..."
        sleep 2
    done
    echo -e "  ${GREEN}✓${NC} BPC4MSA ready"

    # Check Synchronous SOA
    until curl -sf http://localhost:8001/health > /dev/null; do
        echo "  Waiting for Synchronous SOA (port 8001)..."
        sleep 2
    done
    echo -e "  ${GREEN}✓${NC} Synchronous SOA ready"

    # Check Monolithic
    until curl -sf http://localhost:8002/health > /dev/null; do
        echo "  Waiting for Monolithic (port 8002)..."
        sleep 2
    done
    echo -e "  ${GREEN}✓${NC} Monolithic ready"

    echo -e "${GREEN}All services healthy!${NC}\n"
}

# Function to clear database data
clear_data() {
    echo -e "${YELLOW}Clearing database data...${NC}"
    curl -X DELETE http://localhost:8080/api/data/clear 2>/dev/null || true
    sleep 2
    echo -e "${GREEN}✓ Data cleared${NC}\n"
}

# ==================================================
# EXPERIMENT 1: Baseline Performance
# ==================================================
run_experiment_1() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Experiment 1: Baseline Performance${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "Goal: Establish baseline WITHOUT compliance overhead"
    echo "Duration: 5 minutes"
    echo ""

    # Stop compliance service for baseline
    echo -e "${YELLOW}Stopping compliance-service...${NC}"
    docker-compose stop compliance-service
    sleep 5

    clear_data

    echo -e "${YELLOW}Running load test...${NC}"
    locust -f locustfile_experiment1_baseline.py --headless \
        -u 10 -r 2 --run-time 5m \
        --csv "$RESULTS_DIR/experiment1_baseline_$TIMESTAMP" \
        --html "$REPORTS_DIR/experiment1_baseline_$TIMESTAMP.html" \
        --logfile "$RESULTS_DIR/experiment1_baseline_$TIMESTAMP.log"

    # Restart compliance service
    echo -e "${YELLOW}Restarting compliance-service...${NC}"
    docker-compose start compliance-service
    sleep 10

    echo -e "${GREEN}✓ Experiment 1 complete${NC}\n"
}

# ==================================================
# EXPERIMENT 2: Compliance Overhead
# ==================================================
run_experiment_2() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Experiment 2: Compliance Overhead${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "Goal: Measure BPC4MSA compliance overhead"
    echo "Duration: 5 minutes"
    echo ""

    clear_data

    echo -e "${YELLOW}Running load test WITH compliance...${NC}"
    locust -f locustfile_experiment2_overhead.py --headless \
        -u 10 -r 2 --run-time 5m \
        --csv "$RESULTS_DIR/experiment2_overhead_$TIMESTAMP" \
        --html "$REPORTS_DIR/experiment2_overhead_$TIMESTAMP.html" \
        --logfile "$RESULTS_DIR/experiment2_overhead_$TIMESTAMP.log"

    echo -e "${GREEN}✓ Experiment 2 complete${NC}\n"
}

# ==================================================
# EXPERIMENT 3: Scalability Assessment
# ==================================================
run_experiment_3() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Experiment 3: Scalability Assessment${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "Goal: Test all 3 architectures under increasing load"
    echo "Load steps: 10, 25, 50, 75, 100 TPS"
    echo "Duration: ~10 minutes per architecture"
    echo ""

    for arch in "bpc4msa" "synchronous" "monolithic"; do
        echo -e "${YELLOW}Testing $arch architecture...${NC}"

        clear_data

        ARCHITECTURE=$arch locust -f locustfile_experiment3_scalability.py --headless \
            --csv "$RESULTS_DIR/experiment3_scalability_${arch}_$TIMESTAMP" \
            --html "$REPORTS_DIR/experiment3_scalability_${arch}_$TIMESTAMP.html" \
            --logfile "$RESULTS_DIR/experiment3_scalability_${arch}_$TIMESTAMP.log"

        echo -e "${GREEN}✓ $arch complete${NC}\n"
        sleep 30  # Cool-down between tests
    done

    echo -e "${GREEN}✓ Experiment 3 complete (all architectures)${NC}\n"
}

# ==================================================
# EXPERIMENT 4: Effectiveness Validation
# ==================================================
run_experiment_4() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Experiment 4: Effectiveness Validation${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "Goal: Prove 100% violation detection accuracy"
    echo "Duration: 2 minutes per architecture"
    echo ""

    for arch in "bpc4msa" "synchronous" "monolithic"; do
        echo -e "${YELLOW}Testing $arch architecture...${NC}"

        clear_data

        ARCHITECTURE=$arch locust -f locustfile_experiment4_effectiveness.py --headless \
            -u 10 -r 2 --run-time 2m \
            --csv "$RESULTS_DIR/experiment4_effectiveness_${arch}_$TIMESTAMP" \
            --html "$REPORTS_DIR/experiment4_effectiveness_${arch}_$TIMESTAMP.html" \
            --logfile "$RESULTS_DIR/experiment4_effectiveness_${arch}_$TIMESTAMP.log"

        echo -e "${GREEN}✓ $arch complete${NC}\n"
        sleep 10  # Cool-down
    done

    echo -e "${GREEN}✓ Experiment 4 complete (all architectures)${NC}\n"
}

# ==================================================
# EXPERIMENT 5: Dynamic Rule Adaptability
# ==================================================
run_experiment_5() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Experiment 5: Dynamic Rule Adaptability${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "Goal: Demonstrate live rule updates (NQ3)"
    echo "Duration: 2 minutes"
    echo ""

    # Test with Synchronous SOA (easier to verify immediate detection)
    clear_data

    # Reset rules to original
    echo -e "${YELLOW}Resetting rules to original (threshold=10000)...${NC}"
    python update_rules.py --threshold 10000

    echo -e "${YELLOW}Starting load test...${NC}"
    echo "  - 0-60s: threshold=10000"
    echo "  - At 60s: threshold→15000"
    echo "  - 60-120s: threshold=15000"

    # Start load test in background
    ARCHITECTURE=synchronous locust -f locustfile_experiment5_adaptability.py --headless \
        -u 20 -r 4 --run-time 2m \
        --csv "$RESULTS_DIR/experiment5_adaptability_$TIMESTAMP" \
        --html "$REPORTS_DIR/experiment5_adaptability_$TIMESTAMP.html" \
        --logfile "$RESULTS_DIR/experiment5_adaptability_$TIMESTAMP.log" &

    LOCUST_PID=$!

    # Wait 60 seconds then update rules
    sleep 60
    echo -e "${YELLOW}Updating rules (threshold 10000 → 15000)...${NC}"
    python update_rules.py --threshold 15000

    # Wait for test to complete
    wait $LOCUST_PID

    # Reset rules back
    echo -e "${YELLOW}Resetting rules to original...${NC}"
    python update_rules.py --threshold 10000

    echo -e "${GREEN}✓ Experiment 5 complete${NC}\n"
}

# ==================================================
# Main Execution
# ==================================================
main() {
    echo -e "${YELLOW}Starting experiment suite...${NC}\n"

    # Ensure services are running
    wait_for_services

    # Run all experiments
    read -p "Run Experiment 1 (Baseline)? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        run_experiment_1
    fi

    read -p "Run Experiment 2 (Overhead)? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        run_experiment_2
    fi

    read -p "Run Experiment 3 (Scalability)? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        run_experiment_3
    fi

    read -p "Run Experiment 4 (Effectiveness)? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        run_experiment_4
    fi

    read -p "Run Experiment 5 (Adaptability)? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        run_experiment_5
    fi

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}All Experiments Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Results saved to:"
    echo "  - CSV files: $RESULTS_DIR/"
    echo "  - HTML reports: $REPORTS_DIR/"
    echo "  - Raw data: /tmp/experiment_*.csv"
    echo ""
    echo "Next steps:"
    echo "  1. Run analysis scripts: python analyze_results.py"
    echo "  2. Generate publication graphs"
    echo "  3. Verify 100% detection rate (Experiment 4)"
}

# Run main
main
