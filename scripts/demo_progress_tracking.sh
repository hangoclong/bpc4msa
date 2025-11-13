#!/opt/homebrew/bin/bash

###############################################################################
# Demo Script: Visual Progress Tracking
# Simulates the enhanced progress display without running actual experiments
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Progress bar function
draw_progress_bar() {
    local current=$1
    local total=$2
    local width=50

    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))

    local bar="["
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done
    bar+="]"

    echo -e "${CYAN}${bar}${NC} ${BOLD}${percent}%${NC} (${current}/${total})"
}

# Format time function
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

echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}  Progress Tracking Demo - Publication Experiment System v2.0${NC}"
echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}\n"

# Demo 1: Initial campaign info
echo -e "${BOLD}${BLUE}[Demo 1] Campaign Initialization${NC}\n"

cat <<EOF
${BOLD}Campaign Plan:${NC}
  Total trials: ${CYAN}120${NC}
  Estimated duration: ${YELLOW}2h 20m 00s${NC}
  Started at: ${GREEN}$(date '+%Y-%m-%d %H:%M:%S')${NC}
EOF

sleep 2

# Demo 2: Progress at different stages
echo -e "\n${BOLD}${BLUE}[Demo 2] Progress During Execution${NC}\n"

stages=(
    "5:120:300:75:35.2"     # 5/120, 5min elapsed, 75 RPS, 35.2ms
    "15:120:900:82:42.1"    # 15/120, 15min elapsed, 82 RPS, 42.1ms
    "30:120:1800:95:38.5"   # 30/120, 30min elapsed, 95 RPS, 38.5ms
    "60:120:3600:103:41.8"  # 60/120, 1h elapsed, 103 RPS, 41.8ms
    "90:120:5400:98:39.2"   # 90/120, 1.5h elapsed, 98 RPS, 39.2ms
    "120:120:7200:101:40.5" # 120/120, 2h elapsed, 101 RPS, 40.5ms
)

for stage in "${stages[@]}"; do
    IFS=':' read -r current total elapsed rps latency <<< "$stage"

    avg_trial_time=$((elapsed / current))
    remaining=$((total - current))
    eta=$((remaining * avg_trial_time))

    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║${NC}                    ${BOLD}PROGRESS SUMMARY${NC}                              ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}╠════════════════════════════════════════════════════════════════════╣${NC}"

    printf "${BOLD}${CYAN}║${NC} "
    draw_progress_bar "$current" "$total"
    printf "  ${BOLD}${CYAN}║${NC}\n"

    echo -e "${BOLD}${CYAN}╠════════════════════════════════════════════════════════════════════╣${NC}"

    printf "${BOLD}${CYAN}║${NC} ${BOLD}Time Elapsed:${NC}    %-47s ${BOLD}${CYAN}║${NC}\n" "$(format_time $elapsed)"
    printf "${BOLD}${CYAN}║${NC} ${BOLD}Avg Trial Time:${NC}  %-47s ${BOLD}${CYAN}║${NC}\n" "$(format_time $avg_trial_time)"
    printf "${BOLD}${CYAN}║${NC} ${BOLD}ETA Remaining:${NC}   %-47s ${BOLD}${CYAN}║${NC}\n" "$(format_time $eta)"

    echo -e "${BOLD}${CYAN}╠════════════════════════════════════════════════════════════════════╣${NC}"
    printf "${BOLD}${CYAN}║${NC} ${BOLD}Last Trial Performance:${NC}                                       ${BOLD}${CYAN}║${NC}\n"
    printf "${BOLD}${CYAN}║${NC}   Throughput: %-24s Latency: %-18s ${BOLD}${CYAN}║${NC}\n" "${rps} RPS" "${latency} ms"

    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}\n"

    sleep 1.5
done

# Demo 3: Final summary
echo -e "${BOLD}${BLUE}[Demo 3] Final Campaign Summary${NC}\n"

sleep 1

echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║${NC}                       ${BOLD}FINAL CAMPAIGN SUMMARY${NC}                          ${BOLD}${GREEN}║${NC}"
echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════════════════════════════╣${NC}"
printf "${BOLD}${GREEN}║${NC} ${BOLD}Total Trials Executed:${NC}     %-41s ${BOLD}${GREEN}║${NC}\n" "120 / 120"
printf "${BOLD}${GREEN}║${NC} ${BOLD}Total Duration:${NC}            %-41s ${BOLD}${GREEN}║${NC}\n" "2h 30m 15s"
printf "${BOLD}${GREEN}║${NC} ${BOLD}Average Trial Time:${NC}        %-41s ${BOLD}${GREEN}║${NC}\n" "1m 15s"
printf "${BOLD}${GREEN}║${NC} ${BOLD}Results File:${NC}              %-41s ${BOLD}${GREEN}║${NC}\n" "campaign_results_25-10-10-103045.csv"
printf "${BOLD}${GREEN}║${NC} ${BOLD}Completed At:${NC}              %-41s ${BOLD}${GREEN}║${NC}\n" "$(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════════════════════════════╣${NC}"
printf "${BOLD}${GREEN}║${NC} ${BOLD}Data Integrity:${NC}                                                     ${BOLD}${GREEN}║${NC}\n"
printf "${BOLD}${GREEN}║${NC}   ✅ All trials completed successfully                                 ${BOLD}${GREEN}║${NC}\n"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BOLD}${GREEN}🎊 Congratulations! Your publication-ready data is complete! 🎊${NC}\n"

# Demo 4: Comparison
echo -e "${BOLD}${BLUE}[Demo 4] Before vs After${NC}\n"

echo -e "${BOLD}${RED}Before (v1.0):${NC}"
cat <<EOF
Trial 15 / 120
[SUCCESS] Load test complete
[Long silence...]

Trial 16 / 120
[SUCCESS] Load test complete
[More silence...]
EOF

echo ""
sleep 2

echo -e "${BOLD}${GREEN}After (v2.0):${NC}"
echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║${NC} [███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 12% (15/120)           ${BOLD}${CYAN}║${NC}"
echo -e "${BOLD}${CYAN}║${NC} ${BOLD}ETA Remaining:${NC}   2h 11m 15s                                        ${BOLD}${CYAN}║${NC}"
echo -e "${BOLD}${CYAN}║${NC} ${BOLD}Throughput:${NC} 95.23 RPS    ${BOLD}Latency:${NC} 42.15 ms                      ${BOLD}${CYAN}║${NC}"
echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BOLD}${YELLOW}Key Improvements:${NC}"
echo "  ✅ Visual progress indication"
echo "  ✅ Accurate time estimates"
echo "  ✅ Performance feedback"
echo "  ✅ Reassurance it's working"
echo ""

echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}  Demo Complete - Ready to run real experiments!${NC}"
echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "${BOLD}Try it yourself:${NC}"
echo -e "  ${YELLOW}./scripts/execute_publication_run.sh 1 experiments/locustfile_spike_test.py \"50\"${NC}\n"
