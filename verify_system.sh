#!/bin/bash

# BPC4MSA System Verification Script
# Verifies all components are running correctly

echo "=============================================="
echo "BPC4MSA System Verification"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_docker() {
    echo -n "Checking Docker daemon... "
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

check_containers() {
    echo ""
    echo "Checking Docker containers..."

    services=("zookeeper" "kafka" "postgres" "business-logic" "compliance-service" "audit-service" "socket-service" "frontend")

    for service in "${services[@]}"; do
        echo -n "  - $service: "
        if docker-compose ps | grep -q "bpc4msa-${service}-1.*Up"; then
            echo -e "${GREEN}✓ Running${NC}"
        else
            echo -e "${RED}✗ Not running${NC}"
        fi
    done
}

check_health() {
    echo ""
    echo "Checking service health..."

    echo -n "  - Business Logic API: "
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
    fi

    echo -n "  - Frontend: "
    if curl -s -I http://localhost:3000 | grep -q "200 OK"; then
        echo -e "${GREEN}✓ Accessible${NC}"
    else
        echo -e "${RED}✗ Not accessible${NC}"
    fi

    echo -n "  - WebSocket: "
    # Simple TCP check on port 8765
    if timeout 1 bash -c "</dev/tcp/localhost/8765" 2>/dev/null; then
        echo -e "${GREEN}✓ Listening${NC}"
    else
        echo -e "${RED}✗ Not listening${NC}"
    fi
}

check_database() {
    echo ""
    echo "Checking database..."

    echo -n "  - PostgreSQL connection: "
    if docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Connected${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi

    echo -n "  - Audit log table: "
    if docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db -c "SELECT COUNT(*) FROM audit_log;" > /dev/null 2>&1; then
        count=$(docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db -t -c "SELECT COUNT(*) FROM audit_log;" | tr -d ' ')
        echo -e "${GREEN}✓ Exists ($count events)${NC}"
    else
        echo -e "${RED}✗ Not found${NC}"
    fi
}

check_kafka() {
    echo ""
    echo "Checking Kafka..."

    echo -n "  - Kafka topics: "
    topics=$(docker exec bpc4msa-kafka-1 kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null | grep -E "business-events|violations" | wc -l)
    if [ "$topics" -ge 2 ]; then
        echo -e "${GREEN}✓ Created (business-events, violations)${NC}"
    else
        echo -e "${YELLOW}⚠ Topics may not exist yet${NC}"
    fi
}

send_test_event() {
    echo ""
    echo "Sending test event..."

    response=$(curl -s -X POST http://localhost:8000/api/loans/apply \
        -H "Content-Type: application/json" \
        -d '{"applicant_name":"System Test","loan_amount":5000}')

    if echo "$response" | grep -q "transaction_id"; then
        tx_id=$(echo "$response" | grep -o '"transaction_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "  ${GREEN}✓ Event sent successfully${NC}"
        echo "    Transaction ID: $tx_id"

        echo ""
        echo "Waiting 2 seconds for processing..."
        sleep 2

        echo -n "  - Checking audit log: "
        recent_events=$(docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db -t -c \
            "SELECT COUNT(*) FROM audit_log WHERE created_at > NOW() - INTERVAL '10 seconds';" | tr -d ' ')

        if [ "$recent_events" -gt 0 ]; then
            echo -e "${GREEN}✓ Event logged ($recent_events events in last 10s)${NC}"
        else
            echo -e "${YELLOW}⚠ No recent events found${NC}"
        fi
    else
        echo -e "  ${RED}✗ Failed to send event${NC}"
    fi
}

# Run checks
check_docker || exit 1
check_containers
check_health
check_database
check_kafka
send_test_event

echo ""
echo "=============================================="
echo "Verification Complete"
echo "=============================================="
echo ""
echo "Access Points:"
echo "  - Frontend:     http://localhost:3000"
echo "  - API:          http://localhost:8000"
echo "  - API Docs:     http://localhost:8000/docs"
echo "  - WebSocket:    ws://localhost:8765"
echo ""
echo "Next Steps:"
echo "  1. Open frontend: open http://localhost:3000"
echo "  2. Send test events: python test_events.py"
echo "  3. Run load test: cd load-testing && locust -f locustfile.py"
echo ""
