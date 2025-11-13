#!/bin/bash
# Quick Test Script for BPC4MSA Frontend APIs
# Usage: ./quick_test.sh

set -e

CONTROL_API="http://localhost:8080"

echo "=========================================="
echo "BPC4MSA Quick API Test"
echo "=========================================="
echo ""

# Test 1: Control API Health
echo "1. Testing Control API Health..."
curl -s ${CONTROL_API}/health | python3 -m json.tool
echo ""

# Test 2: All Architectures Health
echo "2. Testing All Architectures Health..."
curl -s ${CONTROL_API}/api/architectures/health | python3 -m json.tool
echo ""

# Test 3: Send Test Transaction to BPC4MSA
echo "3. Sending Test Transaction to BPC4MSA..."
curl -s -X POST "${CONTROL_API}/api/architectures/bpc4msa/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_name": "Quick Test User",
    "loan_amount": 50000,
    "applicant_role": "customer",
    "credit_score": 750,
    "employment_status": "employed",
    "status": "pending"
  }' | python3 -m json.tool
echo ""

# Test 4: Get BPC4MSA Statistics
echo "4. Getting BPC4MSA Statistics..."
curl -s ${CONTROL_API}/api/architectures/stats/bpc4msa | python3 -m json.tool
echo ""

# Test 5: Architecture Status
echo "5. Getting Architecture Status..."
curl -s ${CONTROL_API}/api/architectures/status | python3 -m json.tool
echo ""

echo "=========================================="
echo "✓ All Quick Tests Completed"
echo "=========================================="
echo ""
echo "Open http://localhost:3000/dashboard-pro to see the frontend"
echo "WebSocket events at ws://localhost:8765"
