#!/bin/bash

# Manual Experiment Runner
# Usage: ./run_experiment.sh <architecture> <num_transactions> <violation_rate>

ARCH=${1:-bpc4msa}
NUM_TRANS=${2:-50}
VIOLATION_RATE=${3:-0.3}

# Architecture ports
case $ARCH in
  bpc4msa) PORT=8000 ;;
  synchronous) PORT=8001 ;;
  monolithic) PORT=8002 ;;
  *) echo "Invalid architecture. Use: bpc4msa, synchronous, or monolithic"; exit 1 ;;
esac

echo "Running experiment on $ARCH (port $PORT)"
echo "Transactions: $NUM_TRANS, Violation Rate: $VIOLATION_RATE"
echo "----------------------------------------"

for i in $(seq 1 $NUM_TRANS); do
  # Determine if this should be a violation
  if (( $(echo "$RANDOM / 32767 < $VIOLATION_RATE" | bc -l) )); then
    # Send violating transaction
    curl -s -X POST "http://localhost:$PORT/api/loans/apply" \
      -H "Content-Type: application/json" \
      -d '{
        "applicant_name": "Violator '$i'",
        "loan_amount": 2000000,
        "applicant_role": "invalid_role",
        "credit_score": 400,
        "employment_status": "unemployed",
        "status": "pending"
      }' > /dev/null
    echo "[$i/$NUM_TRANS] Sent VIOLATING transaction"
  else
    # Send valid transaction
    curl -s -X POST "http://localhost:$PORT/api/loans/apply" \
      -H "Content-Type: application/json" \
      -d '{
        "applicant_name": "Customer '$i'",
        "loan_amount": 50000,
        "applicant_role": "customer",
        "credit_score": 750,
        "employment_status": "employed",
        "status": "pending"
      }' > /dev/null
    echo "[$i/$NUM_TRANS] Sent VALID transaction"
  fi
  
  # Small delay between requests
  sleep 0.1
done

echo "----------------------------------------"
echo "✅ Experiment completed!"
echo "View results at: http://localhost:3000/dashboard-pro (Compare Results tab)"
