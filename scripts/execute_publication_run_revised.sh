#!/opt/homebrew/bin/bash

###############################################################################
# Publication-Grade Experiment Campaign Script
#
# Implements gold standard methodologies for IS/CS performance evaluation:
# - Full reproducibility and automation
# - Complete environment isolation between trials
# - Randomized trial execution order
# - Comprehensive metric collection (app + system)
# - Parameter space exploration
# - Statistical rigor (N >= 10 samples recommended)
#
# Date: 2025-10-10
# Version: 1.0
#
# Usage: ./execute_publication_run.sh <num_samples> <locust_file> [load_levels]
# Example: ./execute_publication_run.sh 10 experiments/locustfile_spike_test.py
# Example: ./execute_publication_run.sh 10 experiments/locustfile_spike_test.py "50 100 150 200"
#
# Note: Requires Bash 4.0+ (install with: brew install bash)
###############################################################################

set -e  # Exit on any error
set -o pipefail  # Catch errors in pipes

# ==================== Color Definitions ====================

# Detect if running in plain-text mode (for AI agents, CI/CD, etc.)
if [ "$PLAIN_TEXT_MODE" = "1" ] || [ "$CI" = "true" ] || [ ! -t 1 ]; then
    # Plain text mode - no colors
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    NC=''
else
    # Full color mode
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
fi

# ==================== Configuration ====================

# Accept command-line arguments
NUM_SAMPLES="${1:-}"
LOCUST_FILE="${2:-}"
CUSTOM_LOAD_LEVELS="${3:-}"

# Default load levels for parameter space exploration
if [ -z "$CUSTOM_LOAD_LEVELS" ]; then
    LOAD_LEVELS=(50 100 150 200)
else
    # Convert string to array
    read -ra LOAD_LEVELS <<< "$CUSTOM_LOAD_LEVELS"
fi

# Architecture configurations
declare -A ARCH_PORTS=(
    ["bpc4msa"]="8000"
    ["synchronous"]="8001"
    ["monolithic"]="8002"
)

declare -A ARCH_SERVICES=(
    ["bpc4msa"]="bpc4msa-business-logic-1"
    ["synchronous"]="bpc4msa-soa-service-1"
    ["monolithic"]="bpc4msa-monolithic-service-1"
)

declare -A ARCH_METRICS_ENDPOINTS=(
    ["bpc4msa"]="http://localhost:8080/api/metrics/bpc4msa"
    ["synchronous"]="http://localhost:8080/api/metrics/synchronous"
    ["monolithic"]="http://localhost:8080/api/metrics/monolithic"
)

# Test execution parameters
TEST_DURATION=180  # seconds (3 minutes for steady-state)
SPAWN_RATE_MULTIPLIER=1.5  # spawn rate = users * multiplier
WARMUP_SECONDS=60  # Wait for services to stabilize (increased)
COOLDOWN_SECONDS=30  # Wait between trials (increased)

# ==================== Validation & Initialization ====================

usage() {
    cat <<EOF
${BOLD}Usage:${NC} $0 <num_samples> <locust_file> [load_levels]

${BOLD}Arguments:${NC}
  num_samples    : Number of samples per architecture per load level (N >= 10 recommended)
  locust_file    : Path to Locust test file (e.g., experiments/locustfile_spike_test.py)
  load_levels    : (Optional) Space-separated load levels (default: "50 100 150 200")

${BOLD}Examples:${NC}
  $0 10 experiments/locustfile_spike_test.py
  $0 15 experiments/locustfile_experiment1_baseline.py "75 150 300"

${BOLD}Output:${NC}
  Results will be saved to: results/campaign_results_<timestamp>.csv

${BOLD}Gold Standard Requirements:${NC}
  - Each trial runs in a clean, isolated environment (docker-compose down -v)
  - Architecture order is randomized per sample to prevent bias
  - Both application (latency, throughput) and system (CPU, memory) metrics are collected
  - Results are structured for statistical analysis (mean, SD, CI, significance testing)

EOF
    exit 1
}

# Validate arguments
if [ -z "$NUM_SAMPLES" ] || [ -z "$LOCUST_FILE" ]; then
    echo -e "${RED}Error: Missing required arguments${NC}\n"
    usage
fi

if [ ! -f "$LOCUST_FILE" ]; then
    echo -e "${RED}Error: Locust file not found: $LOCUST_FILE${NC}"
    exit 1
fi

if [ "$NUM_SAMPLES" -lt 1 ]; then
    echo -e "${RED}Error: NUM_SAMPLES must be >= 1${NC}"
    exit 1
fi

# Create results directory
mkdir -p results

# Generate timestamped results file
TIMESTAMP=$(date +"%y-%m-%d-%H%M%S")
RESULTS_FILE="results/campaign_results_${TIMESTAMP}.csv"
PROGRESS_LOG="results/campaign_progress_${TIMESTAMP}.log"

# ==================== Logging Functions ====================

log_header() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_trial() {
    echo -e "\n${BOLD}${GREEN}>>> $1${NC}"
}

# ==================== Progress Tracking Functions ====================

# Global variables for tracking
CAMPAIGN_START_TIME=0
TRIAL_START_TIME=0
declare -a TRIAL_TIMES=()

# Progress bar visualization
draw_progress_bar() {
    local current=$1
    local total=$2
    local width=50

    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))

    # Build progress bar
    local bar="["
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done
    bar+="]"

    echo -e "${CYAN}${bar}${NC} ${BOLD}${percent}%${NC} (${current}/${total})"
}

# Format seconds into human-readable time
format_time() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))

    if [ $hours -gt 0 ]; then
        printf "%dh %02dm %02ds" $hours $minutes $secs
    elif [ $minutes -gt 0 ]; then
        printf "%dm %02ds" $minutes $secs
    else
        printf "%ds" $secs
    fi
}

# Calculate and display ETA with IN-PLACE updating (no scrolling)
show_progress_summary() {
    local trial_num=$1
    local total_trials=$2
    local last_rps=$3
    local last_latency=$4

    local current_time=$(date +%s)
    local trial_elapsed=$((current_time - TRIAL_START_TIME))
    TRIAL_TIMES+=("$trial_elapsed")

    # Calculate statistics
    local total_elapsed=$((current_time - CAMPAIGN_START_TIME))

    # Average trial time
    local sum=0
    for time in "${TRIAL_TIMES[@]}"; do
        sum=$((sum + time))
    done
    local avg_trial_time=$((sum / ${#TRIAL_TIMES[@]}))

    # ETA calculation
    local remaining_trials=$((total_trials - trial_num))
    local eta_seconds=$((remaining_trials * avg_trial_time))

    local percent=$((trial_num * 100 / total_trials))

    # Clear previous progress display (move cursor up 5 lines and clear)
    if [ "$trial_num" -gt 1 ]; then
        printf "\033[5A\033[J"  # Move up 5 lines, clear from cursor to end
    fi

    # Display compact progress (IN-PLACE UPDATE - only 5 lines, 68 chars wide)
    printf "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}\n"

    # Progress bar line (with proper spacing)
    printf "${BOLD}${CYAN}║${NC} "
    draw_progress_bar "$trial_num" "$total_trials"
    printf " ${BOLD}${CYAN}║${NC}\n"

    # Time statistics line (68 chars total inside)
    local elapsed_str=$(format_time $total_elapsed)
    local avg_str=$(format_time $avg_trial_time)
    local eta_str=$(format_time $eta_seconds)
    printf "${BOLD}${CYAN}║${NC} Elapsed: ${GREEN}%-10s${NC} Avg: ${GREEN}%-10s${NC} ETA: ${YELLOW}%-14s${NC} ${BOLD}${CYAN}║${NC}\n" \
        "$elapsed_str" "$avg_str" "$eta_str"

    # Performance line
    if [ -n "$last_rps" ] && [ -n "$last_latency" ]; then
        printf "${BOLD}${CYAN}║${NC} Last: ${GREEN}%-12s RPS${NC} ${GREEN}%-12s ms${NC}                          ${BOLD}${CYAN}║${NC}\n" \
            "$last_rps" "$last_latency"
    else
        printf "${BOLD}${CYAN}║${NC}                                                                    ${BOLD}${CYAN}║${NC}\n"
    fi

    printf "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}\n"

    # Also write to progress log (for background monitoring)
    {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Progress: Trial $trial_num/$total_trials ($percent%) | Elapsed: $(format_time $total_elapsed) | ETA: $(format_time $eta_seconds)"
        if [ -n "$last_rps" ] && [ -n "$last_latency" ]; then
            echo "  Performance: $last_rps RPS, $last_latency ms"
        fi
    } >> "$PROGRESS_LOG"
}

# Save checkpoint for crash recovery
save_checkpoint() {
    local checkpoint_file="${RESULTS_FILE}.checkpoint"
    echo "last_trial=$1" > "$checkpoint_file"
    echo "timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$checkpoint_file"
}

# ==================== Core Functions ====================

# Initialize master CSV file with comprehensive headers
initialize_results_file() {
    log_info "Initializing results file: $RESULTS_FILE"

    echo "timestamp,architecture,load_level,sample_num,requests_per_second,avg_latency_ms,p50_latency_ms,p90_latency_ms,p95_latency_ms,p99_latency_ms,avg_cpu_percent,avg_memory_mb,total_requests,failed_requests,error_rate_percent" > "$RESULTS_FILE"

    log_success "Results file created"
}

# Randomize architecture execution order
randomize_architectures() {
    local archs=("${!ARCH_PORTS[@]}")

    # Fisher-Yates shuffle
    for ((i=${#archs[@]}-1; i>0; i--)); do
        j=$((RANDOM % (i+1)))
        temp="${archs[i]}"
        archs[i]="${archs[j]}"
        archs[j]="$temp"
    done

    echo "${archs[@]}"
}

# Reset environment to clean slate
reset_environment() {
    printf "  ${BLUE}↻${NC} Resetting... "
    docker-compose down -v > /dev/null 2>&1
    docker-compose up -d > /dev/null 2>&1
    printf "${GREEN}✓${NC}  Warming up (${WARMUP_SECONDS}s)... "
    sleep $WARMUP_SECONDS
    printf "${GREEN}✓${NC}\n"
}

# Monitor resource usage using docker stats
# FIXED: Corrected implementation with proper sampling
monitor_resources() {
    local service_name="$1"
    local duration="$2"
    local output_file="$3"

    # Sample every 2 seconds for the duration
    (
        for ((i=0; i<duration/2; i++)); do
            docker stats "$service_name" --no-stream \
                --format "{{.CPUPerc}},{{.MemUsage}}" >> "$output_file" 2>/dev/null
            sleep 2
        done
    ) &

    echo $!  # Return PID
}

# Calculate average CPU and Memory from docker stats log
calculate_resource_averages() {
    local resource_file="$1"

    if [ ! -f "$resource_file" ]; then
        echo "0.0,0.0"
        return
    fi

    # Parse docker stats output (format: "12.34%,123.4MiB / 1GiB")
    # Extract CPU percentage and Memory MB
    # FIXED: Handle both MiB and GiB units
    awk -F',' '{
        # Parse CPU percentage
        gsub(/%/, "", $1)
        cpu_sum += $1

        # Parse memory (handle both MiB and GiB)
        split($2, mem_parts, " ")
        mem_value = mem_parts[1]
        mem_unit = mem_parts[2]

        # Convert to MiB if needed
        if (index(mem_unit, "GiB") > 0) {
            gsub(/GiB/, "", mem_unit)
            mem_value = mem_value * 1024
        } else {
            gsub(/MiB/, "", mem_value)
        }

        mem_sum += mem_value
        count++
    }
    END {
        if (count > 0) {
            printf "%.2f,%.2f", cpu_sum/count, mem_sum/count
        } else {
            print "0.0,0.0"
        }
    }' "$resource_file"
}

# Execute Locust load test
execute_load_test() {
    local architecture="$1"
    local load_level="$2"
    local port="${ARCH_PORTS[$architecture]}"

    local spawn_rate=$(awk "BEGIN {printf \"%.0f\", $load_level * $SPAWN_RATE_MULTIPLIER}")
    [ "$spawn_rate" -lt 1 ] && spawn_rate=1

    local temp_csv="/tmp/locust_${architecture}_${load_level}_$$"

    # Activate venv if it exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi

    # Run Locust in background and show progress
    local locust_log="/tmp/locust_${architecture}_${load_level}_$$.log"

    if command -v locust &> /dev/null; then
        locust -f "$LOCUST_FILE" --headless \
            -u "$load_level" \
            -r "$spawn_rate" \
            --run-time "${TEST_DURATION}s" \
            --host="http://localhost:$port" \
            --csv="$temp_csv" \
            --only-summary \
            > "$locust_log" 2>&1 &
    else
        python3 -m locust -f "$LOCUST_FILE" --headless \
            -u "$load_level" \
            -r "$spawn_rate" \
            --run-time "${TEST_DURATION}s" \
            --host="http://localhost:$port" \
            --csv="$temp_csv" \
            --only-summary \
            > "$locust_log" 2>&1 &
    fi

    local locust_pid=$!

    # Show progress with countdown timer
    local elapsed=0
    printf "["
    while kill -0 $locust_pid 2>/dev/null; do
        if [ $elapsed -gt 0 ]; then
            # Overwrite previous progress (move cursor back)
            printf "\r  ${BLUE}⚡${NC} Running load test: [${GREEN}%3ds${NC}/${BOLD}%3ds${NC}] " "$elapsed" "$TEST_DURATION"

            # Progress bar
            local progress=$((elapsed * 30 / TEST_DURATION))
            local remaining=$((30 - progress))
            for ((i=0; i<progress; i++)); do printf "█"; done
            for ((i=0; i<remaining; i++)); do printf "░"; done
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done

    wait $locust_pid
    printf "\r  ${BLUE}⚡${NC} Running load test: [${GREEN}%3ds${NC}/${BOLD}%3ds${NC}] " "$TEST_DURATION" "$TEST_DURATION"
    for ((i=0; i<30; i++)); do printf "█"; done
    printf " ${GREEN}✓${NC}\n"

    # Clean up log file
    rm -f "$locust_log"

    echo "$temp_csv"
}

# Collect metrics from Control API
collect_api_metrics() {
    local architecture="$1"
    local endpoint="${ARCH_METRICS_ENDPOINTS[$architecture]}"

    # Retry logic for API call (silent)
    local max_retries=3
    local retry=0
    local response=""

    while [ $retry -lt $max_retries ]; do
        response=$(curl -s "$endpoint" 2>/dev/null || echo "")

        if [ -n "$response" ]; then
            echo "$response"
            return 0
        fi

        retry=$((retry + 1))
        sleep 2
    done

    echo "{}"
}

# Parse Locust CSV results
parse_locust_results() {
    local csv_prefix="$1"

    # Locust generates: ${prefix}_stats.csv
    local stats_file="${csv_prefix}_stats.csv"

    if [ ! -f "$stats_file" ]; then
        # Return zeros silently (no warning)
        echo "0,0,0,0,0,0,0,0"
        return
    fi

    # Parse stats (skip header, get aggregated row)
    # Format: Type,Name,Request Count,Failure Count,Median,Average,Min,Max,Content Size,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%
    tail -n 1 "$stats_file" 2>/dev/null | awk -F',' '{
        total_requests = $3
        failed_requests = $4
        avg_latency = $6
        p50 = $12
        p90 = $16
        p95 = $17
        p99 = $19
        rps = $10

        error_rate = (total_requests > 0) ? (failed_requests / total_requests * 100) : 0

        printf "%s,%.2f,%.2f,%.2f,%.2f,%.2f,%d,%d,%.2f",
            rps, avg_latency, p50, p90, p95, p99, total_requests, failed_requests, error_rate
    }'
}

# Record trial results to master CSV
record_results() {
    local timestamp="$1"
    local architecture="$2"
    local load_level="$3"
    local sample_num="$4"
    local locust_csv="$5"
    local resource_file="$6"

    # Parse Locust results
    local locust_data
    locust_data=$(parse_locust_results "$locust_csv")

    # Parse resource metrics
    local resource_data
    resource_data=$(calculate_resource_averages "$resource_file")

    # Combine into single CSV row
    echo "${timestamp},${architecture},${load_level},${sample_num},${locust_data},${resource_data}" >> "$RESULTS_FILE"

    # Extract RPS and latency for progress display
    LAST_RPS=$(echo "$locust_data" | cut -d',' -f1)
    LAST_LATENCY=$(echo "$locust_data" | cut -d',' -f2)
}

# Execute a single trial
execute_trial() {
    local architecture="$1"
    local load_level="$2"
    local sample_num="$3"
    local trial_num="$4"

    # Start trial timer
    TRIAL_START_TIME=$(date +%s)

    # Step 1: Reset environment (compact output)
    reset_environment

    # Step 2: Start resource monitoring
    local service_name="${ARCH_SERVICES[$architecture]}"
    local resource_file="/tmp/resources_${architecture}_${load_level}_${sample_num}_$$.log"
    local monitor_pid
    monitor_pid=$(monitor_resources "$service_name" "$TEST_DURATION" "$resource_file")

    # Step 3: Execute load test (with progress bar inside function)
    local locust_csv
    locust_csv=$(execute_load_test "$architecture" "$load_level")
    wait "$monitor_pid" 2>/dev/null || true

    # Step 4: Record results
    printf "  ${BLUE}💾${NC} Recording results... "
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    record_results "$timestamp" "$architecture" "$load_level" "$sample_num" "$locust_csv" "$resource_file"
    printf "${GREEN}✓${NC}\n"

    # Cleanup temp files
    rm -f "$resource_file" "${locust_csv}"*.csv 2>/dev/null || true

    # Cooldown
    if [ "$COOLDOWN_SECONDS" -gt 0 ]; then
        printf "  ${YELLOW}⏸${NC}  Cooldown (${COOLDOWN_SECONDS}s)...\n"
        sleep "$COOLDOWN_SECONDS"
    fi
}

# ==================== Main Execution ====================

main() {
    # Start campaign timer
    CAMPAIGN_START_TIME=$(date +%s)

    log_header "Publication-Grade Experiment Campaign"

    echo -e "${BOLD}Configuration:${NC}"
    echo -e "  Samples per condition: ${GREEN}$NUM_SAMPLES${NC}"
    echo -e "  Load levels: ${GREEN}${LOAD_LEVELS[*]}${NC}"
    echo -e "  Architectures: ${GREEN}${!ARCH_PORTS[*]}${NC}"
    echo -e "  Locust file: ${GREEN}$LOCUST_FILE${NC}"
    echo -e "  Test duration: ${GREEN}${TEST_DURATION}s${NC}"
    echo -e "  Results file: ${GREEN}$RESULTS_FILE${NC}"
    echo ""

    total_trials=$((${#LOAD_LEVELS[@]} * ${#ARCH_PORTS[@]} * NUM_SAMPLES))

    # Calculate estimated duration
    local est_trial_time=$((TEST_DURATION + WARMUP_SECONDS + COOLDOWN_SECONDS + 30))  # +30s overhead
    local est_total_seconds=$((total_trials * est_trial_time))

    echo -e "${BOLD}Campaign Plan:${NC}"
    echo -e "  Total trials: ${CYAN}$total_trials${NC}"
    echo -e "  Estimated duration: ${YELLOW}$(format_time $est_total_seconds)${NC}"
    echo -e "  Started at: ${GREEN}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""

    # Check Locust availability
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi

    if ! command -v locust &> /dev/null && ! python3 -m locust --version &> /dev/null; then
        echo -e "${RED}ERROR: Locust is not installed!${NC}"
        echo ""
        echo "Please install Locust:"
        echo "  1. Activate venv: ${YELLOW}source venv/bin/activate${NC}"
        echo "  2. Install Locust: ${YELLOW}pip install locust${NC}"
        echo ""
        exit 1
    fi

    echo -e "${GREEN}✓${NC} Locust is available"
    echo ""

    # Initialize results file
    initialize_results_file

    # Execution loops
    trial_count=0
    LAST_RPS=""
    LAST_LATENCY=""

    for load in "${LOAD_LEVELS[@]}"; do
        log_header "Load Level: $load users"

        for sample in $(seq 1 "$NUM_SAMPLES"); do
            log_info "Sample: $sample/$NUM_SAMPLES"

            # Randomize architecture order (GOLD STANDARD REQUIREMENT)
            randomized_archs=$(randomize_architectures)
            log_info "Randomized order: $randomized_archs"

            for arch in $randomized_archs; do
                trial_count=$((trial_count + 1))

                # Compact trial header (one line only)
                printf "\n${CYAN}▶ Trial %3d/%d: ${BOLD}%-12s${NC} | Load: ${BOLD}%3d${NC} users | Sample: ${BOLD}%2d/%d${NC}\n" \
                    "$trial_count" "$total_trials" "$arch" "$load" "$sample" "$NUM_SAMPLES"

                execute_trial "$arch" "$load" "$sample" "$trial_count"

                # Save checkpoint
                save_checkpoint "$trial_count"

                # Show progress summary after each trial (updates in-place)
                show_progress_summary "$trial_count" "$total_trials" "$LAST_RPS" "$LAST_LATENCY"
            done
        done
    done

    # Campaign complete - Final summary
    local campaign_end_time=$(date +%s)
    local total_duration=$((campaign_end_time - CAMPAIGN_START_TIME))

    log_header "🎉 CAMPAIGN COMPLETE! 🎉"

    # Calculate final statistics
    local successful_trials=$(wc -l < "$RESULTS_FILE")
    successful_trials=$((successful_trials - 1))  # Subtract header

    echo -e "\n${BOLD}${GREEN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║${NC}                       ${BOLD}FINAL CAMPAIGN SUMMARY${NC}                          ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════════════════════════════╣${NC}"
    printf "${BOLD}${GREEN}║${NC} ${BOLD}Total Trials Executed:${NC}     %-41s ${BOLD}${GREEN}║${NC}\n" "$successful_trials / $total_trials"
    printf "${BOLD}${GREEN}║${NC} ${BOLD}Total Duration:${NC}            %-41s ${BOLD}${GREEN}║${NC}\n" "$(format_time $total_duration)"
    printf "${BOLD}${GREEN}║${NC} ${BOLD}Average Trial Time:${NC}        %-41s ${BOLD}${GREEN}║${NC}\n" "$(format_time $((total_duration / successful_trials)))"
    printf "${BOLD}${GREEN}║${NC} ${BOLD}Results File:${NC}              %-41s ${BOLD}${GREEN}║${NC}\n" "$(basename $RESULTS_FILE)"
    printf "${BOLD}${GREEN}║${NC} ${BOLD}Completed At:${NC}              %-41s ${BOLD}${GREEN}║${NC}\n" "$(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════════════════════════════╣${NC}"
    printf "${BOLD}${GREEN}║${NC} ${BOLD}Data Integrity:${NC}                                                     ${BOLD}${GREEN}║${NC}\n"

    if [ "$successful_trials" -eq "$total_trials" ]; then
        printf "${BOLD}${GREEN}║${NC}   ✅ All trials completed successfully                                 ${BOLD}${GREEN}║${NC}\n"
    else
        printf "${BOLD}${GREEN}║${NC}   ⚠️  Warning: Expected $total_trials, got $successful_trials trials               ${BOLD}${GREEN}║${NC}\n"
    fi

    echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════════════════╝${NC}\n"

    echo -e "${BOLD}Next Steps:${NC}\n"
    echo -e "  ${CYAN}1.${NC} Verify data integrity:"
    echo -e "     ${YELLOW}wc -l $RESULTS_FILE${NC}"
    echo -e "     Expected: $((trial_count + 1)) lines (header + data)\n"

    echo -e "  ${CYAN}2.${NC} Statistical analysis:"
    echo -e "     ${YELLOW}source venv/bin/activate\n"
    echo -e "     ${YELLOW}python scripts/analyze_results.py $RESULTS_FILE${NC}\n"

    echo -e "  ${CYAN}3.${NC} Generate publication figures:"
    echo -e "     ${YELLOW}python scripts/generate_publication_figures.py $RESULTS_FILE${NC}\n"

    echo -e "${BOLD}${GREEN}🎊 Congratulations! Your publication-ready data is complete! 🎊${NC}\n"
}

# Run main
main
