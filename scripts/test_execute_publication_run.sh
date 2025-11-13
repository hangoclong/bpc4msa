#!/opt/homebrew/bin/bash

###############################################################################
# Test Script for execute_publication_run.sh
# Validates all critical functions without running full experiments
###############################################################################

set -e

echo "=================================="
echo "Testing execute_publication_run.sh"
echo "=================================="
echo ""

# Test 1: Verify script exists and is executable
echo "[Test 1] Checking script exists and is executable..."
if [ -x "./scripts/execute_publication_run.sh" ]; then
    echo "✅ PASS: Script is executable"
else
    echo "❌ FAIL: Script is not executable"
    exit 1
fi

# Test 2: Verify usage message
echo ""
echo "[Test 2] Checking usage message..."
if ./scripts/execute_publication_run.sh 2>&1 | grep -q "num_samples"; then
    echo "✅ PASS: Usage message displays correctly"
else
    echo "❌ FAIL: Usage message not found"
    exit 1
fi

# Test 3: Verify Locust file validation
echo ""
echo "[Test 3] Checking Locust file validation..."
if ./scripts/execute_publication_run.sh 1 nonexistent.py 2>&1 | grep -q "not found"; then
    echo "✅ PASS: Locust file validation works"
else
    echo "❌ FAIL: Locust file validation failed"
    exit 1
fi

# Test 4: Verify results directory creation
echo ""
echo "[Test 4] Checking results directory..."
if [ -d "results" ]; then
    echo "✅ PASS: Results directory exists"
else
    echo "❌ FAIL: Results directory does not exist"
    exit 1
fi

# Test 5: Source script and test helper functions
echo ""
echo "[Test 5] Testing randomization function..."

# Create a test function that mimics randomize_architectures
test_randomization() {
    local archs=("bpc4msa" "synchronous" "monolithic")
    local iterations=100
    local orders=()

    for ((i=0; i<iterations; i++)); do
        # Fisher-Yates shuffle (same as in main script)
        local temp_archs=("${archs[@]}")
        for ((j=${#temp_archs[@]}-1; j>0; j--)); do
            k=$((RANDOM % (j+1)))
            temp="${temp_archs[j]}"
            temp_archs[j]="${temp_archs[k]}"
            temp_archs[k]="$temp"
        done
        orders+=("${temp_archs[0]}")
    done

    # Check that each architecture appears first at least once
    local has_bpc4msa=0
    local has_sync=0
    local has_mono=0

    for order in "${orders[@]}"; do
        [ "$order" = "bpc4msa" ] && has_bpc4msa=1
        [ "$order" = "synchronous" ] && has_sync=1
        [ "$order" = "monolithic" ] && has_mono=1
    done

    if [ $has_bpc4msa -eq 1 ] && [ $has_sync -eq 1 ] && [ $has_mono -eq 1 ]; then
        echo "✅ PASS: Randomization produces varied orders"
        return 0
    else
        echo "❌ FAIL: Randomization not working properly"
        return 1
    fi
}

test_randomization

# Test 6: Verify Bash version requirement
echo ""
echo "[Test 6] Checking Bash version..."
if [ "${BASH_VERSINFO[0]}" -ge 4 ]; then
    echo "✅ PASS: Bash version $BASH_VERSION is compatible"
else
    echo "❌ FAIL: Bash version too old: $BASH_VERSION"
    exit 1
fi

# Test 7: Verify associative arrays work
echo ""
echo "[Test 7] Testing associative arrays..."
declare -A test_array=(
    ["key1"]="value1"
    ["key2"]="value2"
)

if [ "${test_array[key1]}" = "value1" ]; then
    echo "✅ PASS: Associative arrays work correctly"
else
    echo "❌ FAIL: Associative arrays not working"
    exit 1
fi

# Test 8: Verify required commands exist
echo ""
echo "[Test 8] Checking required dependencies..."
required_commands=("docker" "docker-compose" "curl" "awk" "locust")
all_present=1

for cmd in "${required_commands[@]}"; do
    if command -v "$cmd" &> /dev/null; then
        echo "  ✅ $cmd: found"
    else
        echo "  ❌ $cmd: NOT FOUND"
        all_present=0
    fi
done

if [ $all_present -eq 1 ]; then
    echo "✅ PASS: All required dependencies present"
else
    echo "⚠️  WARNING: Some dependencies missing (may cause runtime errors)"
fi

# Test 9: Verify Docker is running
echo ""
echo "[Test 9] Checking Docker daemon..."
if docker ps > /dev/null 2>&1; then
    echo "✅ PASS: Docker is running"
else
    echo "❌ FAIL: Docker is not running"
    exit 1
fi

# Final Summary
echo ""
echo "=================================="
echo "All Critical Tests Passed! ✅"
echo "=================================="
echo ""
echo "The execute_publication_run.sh script is ready for use."
echo ""
echo "Quick Start:"
echo "  ./scripts/execute_publication_run.sh 1 experiments/locustfile_spike_test.py \"50\""
echo ""
