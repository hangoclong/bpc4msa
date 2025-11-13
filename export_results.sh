#!/bin/bash
# Export Experiment Data for Publication
# Generates CSV, LaTeX, and Markdown tables

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "================================================================================"
echo "EXPERIMENT DATA EXPORTER"
echo "================================================================================"
echo "Fetching data from control-api..."
echo ""

# Fetch data
DATA=$(curl -s http://localhost:8080/api/compare/metrics)

# Extract metrics using python
BPC_TRANS=$(echo "$DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['bpc4msa']['total_transactions'])")
BPC_LAT=$(echo "$DATA" | python3 -c "import sys, json; print(round(json.load(sys.stdin)['bpc4msa']['avg_latency_ms'], 2))")
BPC_VIOL=$(echo "$DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['bpc4msa']['total_violations'])")
BPC_THRU=$(echo "$DATA" | python3 -c "import sys, json; print(round(json.load(sys.stdin)['bpc4msa']['throughput_per_min'], 2))")
BPC_VRATE=$(echo "$DATA" | python3 -c "import sys, json; print(round(json.load(sys.stdin)['bpc4msa']['violation_rate'], 2))")

SYNC_TRANS=$(echo "$DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['synchronous']['total_transactions'])")
SYNC_LAT=$(echo "$DATA" | python3 -c "import sys, json; print(round(json.load(sys.stdin)['synchronous']['avg_latency_ms'], 2))")
SYNC_VIOL=$(echo "$DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['synchronous']['total_violations'])")
SYNC_THRU=$(echo "$DATA" | python3 -c "import sys, json; print(round(json.load(sys.stdin)['synchronous']['throughput_per_min'], 2))")
SYNC_VRATE=$(echo "$DATA" | python3 -c "import sys, json; print(round(json.load(sys.stdin)['synchronous']['violation_rate'], 2))")

MONO_TRANS=$(echo "$DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['monolithic']['total_transactions'])")
MONO_LAT=$(echo "$DATA" | python3 -c "import sys, json; print(round(json.load(sys.stdin)['monolithic']['avg_latency_ms'], 2))")
MONO_VIOL=$(echo "$DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['monolithic']['total_violations'])")
MONO_THRU=$(echo "$DATA" | python3 -c "import sys, json; print(round(json.load(sys.stdin)['monolithic']['throughput_per_min'], 2))")
MONO_VRATE=$(echo "$DATA" | python3 -c "import sys, json; print(round(json.load(sys.stdin)['monolithic']['violation_rate'], 2))")

# 1. CSV Export
CSV_FILE="experiment_results_${TIMESTAMP}.csv"
cat > "$CSV_FILE" << EOF
Architecture,Total_Transactions,Avg_Latency_ms,Total_Violations,Throughput_per_min,Violation_Rate_%
BPC4MSA,$BPC_TRANS,$BPC_LAT,$BPC_VIOL,$BPC_THRU,$BPC_VRATE
Synchronous,$SYNC_TRANS,$SYNC_LAT,$SYNC_VIOL,$SYNC_THRU,$SYNC_VRATE
Monolithic,$MONO_TRANS,$MONO_LAT,$MONO_VIOL,$MONO_THRU,$MONO_VRATE
EOF

echo "✅ CSV exported: $CSV_FILE"

# 2. LaTeX Table Export
LATEX_FILE="experiment_table_${TIMESTAMP}.tex"
cat > "$LATEX_FILE" << 'EOF'
\begin{table}[htbp]
\centering
\caption{Architectural Performance Comparison}
\label{tab:arch_comparison}
\begin{tabular}{lrrrrr}
\toprule
\textbf{Architecture} & \textbf{Trans.} & \textbf{Latency (ms)} & \textbf{Violations} & \textbf{Throughput} & \textbf{Viol. Rate (\%)} \\
\midrule
EOF

echo "BPC4MSA & $BPC_TRANS & $BPC_LAT & $BPC_VIOL & $BPC_THRU & $BPC_VRATE \\\\" >> "$LATEX_FILE"
echo "Synchronous & $SYNC_TRANS & $SYNC_LAT & $SYNC_VIOL & $SYNC_THRU & $SYNC_VRATE \\\\" >> "$LATEX_FILE"
echo "Monolithic & $MONO_TRANS & $MONO_LAT & $MONO_VIOL & $MONO_THRU & $MONO_VRATE \\\\" >> "$LATEX_FILE"

cat >> "$LATEX_FILE" << 'EOF'
\bottomrule
\end{tabular}
\end{table}
EOF

echo "✅ LaTeX table exported: $LATEX_FILE"

# 3. Markdown Table Export
MD_FILE="experiment_table_${TIMESTAMP}.md"
cat > "$MD_FILE" << EOF
# Experiment Results

**Date:** $(date '+%Y-%m-%d %H:%M:%S')

## Comparative Performance

| Architecture | Transactions | Avg Latency (ms) | Violations | Throughput (req/min) | Violation Rate (%) |
|--------------|--------------|------------------|------------|----------------------|--------------------|
| BPC4MSA | $BPC_TRANS | $BPC_LAT | $BPC_VIOL | $BPC_THRU | $BPC_VRATE |
| Synchronous | $SYNC_TRANS | $SYNC_LAT | $SYNC_VIOL | $SYNC_THRU | $SYNC_VRATE |
| Monolithic | $MONO_TRANS | $MONO_LAT | $MONO_VIOL | $MONO_THRU | $MONO_VRATE |

## Key Findings

### Latency Analysis
- **BPC4MSA:** $BPC_LAT ms (async event-driven)
- **Synchronous:** $SYNC_LAT ms (direct HTTP calls)
- **Monolithic:** $MONO_LAT ms (all-in-one)

### Throughput Analysis
- **BPC4MSA:** $BPC_THRU req/min
- **Synchronous:** $SYNC_THRU req/min
- **Monolithic:** $MONO_THRU req/min

### Compliance (Violation Rate)
- **BPC4MSA:** $BPC_VRATE%
- **Synchronous:** $SYNC_VRATE%
- **Monolithic:** $MONO_VRATE%
EOF

echo "✅ Markdown table exported: $MD_FILE"

# 4. Statistical Summary
STATS_FILE="experiment_stats_${TIMESTAMP}.txt"
cat > "$STATS_FILE" << EOF
================================================================================
EXPERIMENT STATISTICAL SUMMARY
================================================================================
Generated: $(date '+%Y-%m-%d %H:%M:%S')

BPC4MSA Architecture:
----------------------------------------
  Total Transactions:    $BPC_TRANS
  Avg Latency:           $BPC_LAT ms
  Total Violations:      $BPC_VIOL
  Throughput:            $BPC_THRU req/min
  Violation Rate:        $BPC_VRATE%

Synchronous Architecture:
----------------------------------------
  Total Transactions:    $SYNC_TRANS
  Avg Latency:           $SYNC_LAT ms
  Total Violations:      $SYNC_VIOL
  Throughput:            $SYNC_THRU req/min
  Violation Rate:        $SYNC_VRATE%

Monolithic Architecture:
----------------------------------------
  Total Transactions:    $MONO_TRANS
  Avg Latency:           $MONO_LAT ms
  Total Violations:      $MONO_VIOL
  Throughput:            $MONO_THRU req/min
  Violation Rate:        $MONO_VRATE%

================================================================================
COMPARATIVE ANALYSIS
================================================================================

Performance Ranking (Latency - lower is better):
EOF

# Sort by latency
(
echo "BPC4MSA $BPC_LAT"
echo "Synchronous $SYNC_LAT"
echo "Monolithic $MONO_LAT"
) | sort -k2 -n | awk '{printf "  %-15s: %10s ms\\n", $1, $2}' >> "$STATS_FILE"

cat >> "$STATS_FILE" << EOF

Performance Ranking (Throughput - higher is better):
EOF

# Sort by throughput (reverse)
(
echo "BPC4MSA $BPC_THRU"
echo "Synchronous $SYNC_THRU"
echo "Monolithic $MONO_THRU"
) | sort -k2 -rn | awk '{printf "  %-15s: %10s req/min\\n", $1, $2}' >> "$STATS_FILE"

cat >> "$STATS_FILE" << EOF

Compliance Ranking (Violation Rate - lower is better):
EOF

# Sort by violation rate
(
echo "BPC4MSA $BPC_VRATE"
echo "Synchronous $SYNC_VRATE"
echo "Monolithic $MONO_VRATE"
) | sort -k2 -n | awk '{printf "  %-15s: %10s%%\\n", $1, $2}' >> "$STATS_FILE"

echo "✅ Statistical summary exported: $STATS_FILE"

# 5. Raw JSON
JSON_FILE="experiment_raw_${TIMESTAMP}.json"
echo "$DATA" | python3 -m json.tool > "$JSON_FILE"
echo "✅ Raw JSON exported: $JSON_FILE"

echo ""
echo "================================================================================"
echo "EXPORT COMPLETE"
echo "================================================================================"
echo ""
echo "Generated files:"
echo "  📊 CSV (Excel/R/Python):  $CSV_FILE"
echo "  📄 LaTeX (Paper):         $LATEX_FILE"
echo "  📝 Markdown (Docs):       $MD_FILE"
echo "  📈 Statistics (Analysis): $STATS_FILE"
echo "  🔧 Raw JSON (Custom):     $JSON_FILE"
echo ""
echo "Preview of statistical summary:"
echo "================================================================================"
cat "$STATS_FILE"
