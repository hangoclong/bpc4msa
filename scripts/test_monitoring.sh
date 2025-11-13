#!/opt/homebrew/bin/bash

###############################################################################
# Monitoring Validation Test Script
# Purpose: Verify CPU/memory monitoring returns realistic values
# Phase 2 Mandate: "Validate Instrumentation" before data collection
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================================================"
echo "MONITORING VALIDATION TEST"
echo "======================================================================"
echo ""

# Step 1: Ensure services are running
echo -e "${YELLOW}Step 1: Checking if services are running...${NC}"

if ! docker ps | grep -q "bpc4msa-business-logic"; then
    echo -e "${RED}ERROR: business-logic container not running${NC}"
    echo "Please start services: docker-compose up -d"
    exit 1
fi

echo -e "${GREEN}✓ Services are running${NC}"
echo ""

# Step 2: Test docker stats collection
echo -e "${YELLOW}Step 2: Testing docker stats collection (10 seconds)...${NC}"

TEMP_FILE="/tmp/monitoring_test_$$.log"

# Collect stats for 10 seconds
for i in {1..5}; do
    docker stats bpc4msa-business-logic-1 --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" >> "$TEMP_FILE"
    sleep 2
done

echo -e "${GREEN}✓ Collected 5 samples${NC}"
echo ""

# Step 3: Parse and validate results
echo -e "${YELLOW}Step 3: Parsing results...${NC}"
echo ""

# Show raw data
echo "Raw monitoring data:"
cat "$TEMP_FILE"
echo ""

# Parse averages
RESULT=$(awk -F',' '{
    gsub(/%/, "", $1);
    cpu_sum += $1;

    # Extract memory (handle both MiB and GiB)
    split($2, mem_parts, " ");
    mem_value = mem_parts[1];
    mem_unit = mem_parts[2];

    # Convert to MiB if needed
    if (index(mem_unit, "GiB") > 0) {
        gsub(/GiB/, "", mem_unit);
        mem_value = mem_value * 1024;
    } else {
        gsub(/MiB/, "", mem_value);
    }

    mem_sum += mem_value;
    count++;
}
END {
    if (count > 0) {
        printf "%.2f,%.2f", cpu_sum/count, mem_sum/count
    } else {
        print "0.0,0.0"
    }
}' "$TEMP_FILE")

AVG_CPU=$(echo "$RESULT" | cut -d',' -f1)
AVG_MEM=$(echo "$RESULT" | cut -d',' -f2)

echo "Parsed averages:"
echo "  Average CPU: ${AVG_CPU}%"
echo "  Average Memory: ${AVG_MEM} MiB"
echo ""

# Step 4: Validation checks
echo -e "${YELLOW}Step 4: Validation checks...${NC}"
echo ""

PASS=true

# Check 1: CPU should be between 0.1 and 100%
CPU_CHECK=$(awk -v cpu="$AVG_CPU" 'BEGIN {
    if (cpu >= 0.1 && cpu <= 100) print "PASS"
    else print "FAIL"
}')

if [ "$CPU_CHECK" = "PASS" ]; then
    echo -e "${GREEN}✓ CPU range valid (0.1-100%)${NC}"
else
    echo -e "${RED}✗ CPU range INVALID: ${AVG_CPU}% (expected 0.1-100%)${NC}"
    PASS=false
fi

# Check 2: Memory should be > 0 and < 10GB (reasonable for container)
MEM_CHECK=$(awk -v mem="$AVG_MEM" 'BEGIN {
    if (mem > 0 && mem < 10240) print "PASS"
    else print "FAIL"
}')

if [ "$MEM_CHECK" = "PASS" ]; then
    echo -e "${GREEN}✓ Memory range valid (>0, <10GB)${NC}"
else
    echo -e "${RED}✗ Memory range INVALID: ${AVG_MEM} MiB (expected >0, <10GB)${NC}"
    PASS=false
fi

# Check 3: Should have collected 5 samples
SAMPLE_COUNT=$(wc -l < "$TEMP_FILE")

if [ "$SAMPLE_COUNT" -eq 5 ]; then
    echo -e "${GREEN}✓ Sample count correct (5)${NC}"
else
    echo -e "${RED}✗ Sample count INVALID: ${SAMPLE_COUNT} (expected 5)${NC}"
    PASS=false
fi

echo ""

# Cleanup
rm -f "$TEMP_FILE"

# Final result
echo "======================================================================"
if [ "$PASS" = true ]; then
    echo -e "${GREEN}✓ MONITORING VALIDATION PASSED${NC}"
    echo ""
    echo "Monitoring is working correctly. You can proceed with experiments."
    exit 0
else
    echo -e "${RED}✗ MONITORING VALIDATION FAILED${NC}"
    echo ""
    echo "Please fix monitoring issues before running experiments."
    echo "See docs/2-paper-plan/05-Pilot-To-Fullscale-Workflow.md for fixes."
    exit 1
fi
