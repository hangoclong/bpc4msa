#!/opt/homebrew/bin/bash

###############################################################################
# Pilot Test Runner
# Purpose: 2-hour quick validation before full-scale experiment
#
# Protocol: N=3 samples, 2 load levels (50, 200 users)
# Expected trials: 3 architectures × 2 loads × 3 samples = 18 trials
# Expected duration: ~2 hours
###############################################################################

set -e

echo "======================================================================"
echo "PILOT TEST - Quick Validation (2 hours)"
echo "======================================================================"
echo ""
echo "This pilot will:"
echo "  - Test N=3 samples per condition"
echo "  - Test 2 load levels: 50 and 200 users"
echo "  - Run 18 trials total (~2 hours)"
echo "  - Validate if BPC4MSA is faster (Scenario A/B/C)"
echo ""
echo "After completion, analyze results to determine next steps."
echo ""
read -p "Press Enter to start pilot test, or Ctrl+C to cancel..."
echo ""

# Run pilot with revised script
./scripts/execute_publication_run_revised.sh \
    3 \
    experiments/locustfile_steady_state.py \
    "50 200"

echo ""
echo "======================================================================"
echo "PILOT COMPLETE - Next Steps"
echo "======================================================================"
echo ""
echo "Analyze results:"
echo "  python scripts/analyze_results.py results/campaign_results_*.csv"
echo ""
echo "Check which scenario applies:"
echo "  - Scenario A: BPC4MSA faster (>10% higher RPS)"
echo "  - Scenario B: No difference (±5% range)"
echo "  - Scenario C: BPC4MSA slower (>10% lower RPS)"
echo ""
echo "See docs/2-paper-plan/05-Pilot-To-Fullscale-Workflow.md for next actions."
echo ""
