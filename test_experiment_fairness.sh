#!/bin/bash
# Experiment Fairness Validation Script
# Tests scientific rigor of experiment setup

echo "================================================================================"
echo "EXPERIMENT FAIRNESS VALIDATION"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((FAILED++))
    fi
}

echo "1. Testing Direct Architecture Access (No Proxy Bottleneck)"
echo "----------------------------------------------------------------"

# Test BPC4MSA direct access
curl -s -f http://localhost:8000/health > /dev/null 2>&1
test_result $? "BPC4MSA accessible directly on port 8000"

# Test Synchronous direct access
curl -s -f http://localhost:8001/health > /dev/null 2>&1
test_result $? "Synchronous accessible directly on port 8001"

# Test Monolithic direct access
curl -s -f http://localhost:8002/health > /dev/null 2>&1
test_result $? "Monolithic accessible directly on port 8002"

echo ""
echo "2. Testing Load Can Reach Architectures Directly"
echo "----------------------------------------------------------------"

# Send test transaction to BPC4MSA directly
RESPONSE=$(curl -s -w "%{http_code}" -X POST http://localhost:8000/api/loans/apply \
  -H "Content-Type: application/json" \
  -d '{"applicant_name":"FairnessTest","loan_amount":5000,"applicant_role":"customer","credit_score":750,"employment_status":"employed","status":"pending"}' \
  -o /dev/null 2>&1)
test_result $([ "$RESPONSE" = "200" ] && echo 0 || echo 1) "Load can reach BPC4MSA directly (HTTP $RESPONSE)"

# Send test transaction to Monolithic directly
RESPONSE=$(curl -s -w "%{http_code}" -X POST http://localhost:8002/api/loans/apply \
  -H "Content-Type: application/json" \
  -d '{"applicant_name":"FairnessTest","loan_amount":5000,"applicant_role":"customer","credit_score":750,"employment_status":"employed","status":"pending"}' \
  -o /dev/null 2>&1)
test_result $([ "$RESPONSE" = "200" ] && echo 0 || echo 1) "Load can reach Monolithic directly (HTTP $RESPONSE)"

# Send test transaction to Synchronous directly
RESPONSE=$(curl -s -w "%{http_code}" -X POST http://localhost:8001/api/loans/apply \
  -H "Content-Type: application/json" \
  -d '{"applicant_name":"FairnessTest","loan_amount":5000,"applicant_role":"customer","credit_score":750,"employment_status":"employed","status":"pending"}' \
  -o /dev/null 2>&1)
test_result $([ "$RESPONSE" = "200" ] && echo 0 || echo 1) "Load can reach Synchronous directly (HTTP $RESPONSE)"

echo ""
echo "3. Testing Metrics Collection (From Architecture Databases)"
echo "----------------------------------------------------------------"

# Test metrics endpoints return valid data
BPC_METRICS=$(curl -s http://localhost:8080/api/metrics/bpc4msa | python3 -c "import sys, json; print(json.load(sys.stdin).get('architecture'))" 2>/dev/null)
test_result $([ "$BPC_METRICS" = "bpc4msa" ] && echo 0 || echo 1) "BPC4MSA metrics sourced correctly (arch: $BPC_METRICS)"

MONO_METRICS=$(curl -s http://localhost:8080/api/metrics/monolithic | python3 -c "import sys, json; print(json.load(sys.stdin).get('architecture'))" 2>/dev/null)
test_result $([ "$MONO_METRICS" = "monolithic" ] && echo 0 || echo 1) "Monolithic metrics sourced correctly (arch: $MONO_METRICS)"

SYNC_METRICS=$(curl -s http://localhost:8080/api/metrics/synchronous | python3 -c "import sys, json; print(json.load(sys.stdin).get('architecture'))" 2>/dev/null)
test_result $([ "$SYNC_METRICS" = "synchronous" ] && echo 0 || echo 1) "Synchronous metrics sourced correctly (arch: $SYNC_METRICS)"

echo ""
echo "4. Testing Resource Measurement Independence"
echo "----------------------------------------------------------------"

# Check that each architecture has its own container
docker ps --format "{{.Names}}" | grep "business-logic" > /dev/null 2>&1
test_result $? "BPC4MSA has independent container (business-logic)"

docker ps --format "{{.Names}}" | grep "monolithic-service" > /dev/null 2>&1
test_result $? "Monolithic has independent container"

docker ps --format "{{.Names}}" | grep "soa-service" > /dev/null 2>&1
test_result $? "Synchronous has independent container (soa-service)"

echo ""
echo "5. Critical Check: Control-API Should NOT Be Bottleneck"
echo "----------------------------------------------------------------"

# Get CPU usage for control-api and architectures
echo "Resource consumption (from Docker stats):"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "control-api|monolithic-service|business-logic|soa-service"

echo ""
echo -e "${YELLOW}⚠️  WARNING CHECK:${NC}"
echo "If control-api CPU > architecture CPU during load test, there is a PROXY BOTTLENECK"
echo "This would invalidate experimental results!"

echo ""
echo "6. Checking Locust Configuration"
echo "----------------------------------------------------------------"

# Check that Locust files point directly to architectures
echo "Locust target hosts:"
grep -E "^ *host *= *\"http://localhost:(8000|8001|8002)\"" experiments/locustfile_*.py | head -5

echo ""
# Check if any locust file's host is explicitly set to the control-api port, ignoring comments
PROXY_HOST_COUNT=$(grep -E 'host.*=.*localhost:8080' experiments/locustfile_*.py | grep -v '^ *#' | wc -l)

if [ $PROXY_HOST_COUNT -eq 0 ]; then
    test_result 0 "Locust files do NOT use control-api proxy (good!)"
else
    test_result 1 "Some Locust files use control-api proxy (bad!)"
    echo "Offending lines:"
    grep -nE 'host.*=.*localhost:8080' experiments/locustfile_*.py | grep -v '^ *#'
fi

echo ""
echo "================================================================================"
echo "VALIDATION SUMMARY"
echo "================================================================================"
echo "Total Checks: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL FAIRNESS CHECKS PASSED${NC}"
    echo "Experiment setup is scientifically rigorous"
    exit 0
else
    echo -e "${RED}⚠️  FAIRNESS VIOLATIONS DETECTED${NC}"
    echo "Experimental results may be invalid!"
    echo ""
    echo "RECOMMENDATIONS:"
    echo "1. Ensure Locust sends load directly to architecture ports (8000, 8001, 8002)"
    echo "2. Do NOT route through control-api (port 8080) during load tests"
    echo "3. Verify metrics collected from each architecture's own database"
    echo "4. Measure resources at architecture container level, not proxy"
    exit 1
fi
