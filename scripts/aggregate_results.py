#!/usr/bin/env python3
"""
Aggregate multiple Locust test runs for statistical analysis
"""

import sys
import glob
import pandas as pd
import numpy as np
from pathlib import Path
import json

def load_stats_files(pattern):
    """Load all _stats.csv files matching pattern"""
    files = glob.glob(pattern)
    if not files:
        # Try adding _stats.csv suffix
        files = glob.glob(f"{pattern}_stats.csv")

    if not files:
        print(f"Error: No files found matching: {pattern}")
        sys.exit(1)

    dfs = []
    for file in sorted(files):
        try:
            df = pd.read_csv(file)
            run_num = Path(file).stem.split('_run')[-1].split('_')[0]
            df['run'] = int(run_num) if run_num.isdigit() else len(dfs) + 1
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Could not load {file}: {e}")

    return pd.concat(dfs, ignore_index=True)

def calculate_statistics(df):
    """Calculate comprehensive statistics"""

    # Group by request type (usually just POST /api/loans/apply)
    stats = []

    for request_type in df['Name'].unique():
        if request_type == 'Aggregated':
            continue

        subset = df[df['Name'] == request_type]

        # Aggregate across runs
        result = {
            'request_type': request_type,
            'num_runs': subset['run'].nunique(),

            # Request counts
            'total_requests_mean': subset['Request Count'].mean(),
            'total_requests_std': subset['Request Count'].std(),

            # Failure rate
            'failure_count_mean': subset['Failure Count'].mean(),
            'failure_rate_mean': (subset['Failure Count'].sum() / subset['Request Count'].sum() * 100),

            # Requests per second
            'rps_mean': subset['Requests/s'].mean(),
            'rps_median': subset['Requests/s'].median(),
            'rps_std': subset['Requests/s'].std(),
            'rps_min': subset['Requests/s'].min(),
            'rps_max': subset['Requests/s'].max(),
            'rps_cv': (subset['Requests/s'].std() / subset['Requests/s'].mean() * 100) if subset['Requests/s'].mean() > 0 else 0,

            # Response times (if available)
            'response_time_mean': subset['Average Response Time'].mean() if 'Average Response Time' in subset else None,
            'response_time_median': subset['Median Response Time'].mean() if 'Median Response Time' in subset else None,
            'response_time_p50': subset['50%'].mean() if '50%' in subset else None,
            'response_time_p95': subset['95%'].mean() if '95%' in subset else None,
            'response_time_p99': subset['99%'].mean() if '99%' in subset else None,
        }

        # Calculate confidence intervals (95%)
        if len(subset) > 1:
            from scipy import stats as sp_stats
            rps_values = subset['Requests/s'].values
            ci = sp_stats.t.interval(0.95, len(rps_values)-1,
                                     loc=np.mean(rps_values),
                                     scale=sp_stats.sem(rps_values))
            result['rps_ci_lower'] = ci[0]
            result['rps_ci_upper'] = ci[1]
        else:
            result['rps_ci_lower'] = result['rps_mean']
            result['rps_ci_upper'] = result['rps_mean']

        stats.append(result)

    return pd.DataFrame(stats)

def print_summary(stats_df):
    """Print formatted summary"""
    print("\n" + "="*70)
    print("AGGREGATED RESULTS SUMMARY")
    print("="*70 + "\n")

    for _, row in stats_df.iterrows():
        print(f"Request Type: {row['request_type']}")
        print(f"Number of Runs: {row['num_runs']}")
        print()

        print("Throughput (Requests/sec):")
        print(f"  Mean:   {row['rps_mean']:.2f}")
        print(f"  Median: {row['rps_median']:.2f}")
        print(f"  Std Dev: {row['rps_std']:.2f}")
        print(f"  Range: [{row['rps_min']:.2f}, {row['rps_max']:.2f}]")
        print(f"  95% CI: [{row['rps_ci_lower']:.2f}, {row['rps_ci_upper']:.2f}]")
        print(f"  CV: {row['rps_cv']:.1f}%")
        print()

        if row['response_time_p95']:
            print("Response Time (ms):")
            print(f"  Mean:   {row['response_time_mean']:.2f}")
            print(f"  Median: {row['response_time_median']:.2f}")
            print(f"  P50:    {row['response_time_p50']:.2f}")
            print(f"  P95:    {row['response_time_p95']:.2f}")
            print(f"  P99:    {row['response_time_p99']:.2f}")
            print()

        if row['failure_count_mean'] > 0:
            print(f"Failures:")
            print(f"  Mean Count: {row['failure_count_mean']:.1f}")
            print(f"  Failure Rate: {row['failure_rate_mean']:.2f}%")
            print()

    print("="*70)

    # Quality indicators
    print("\nQuality Indicators:")
    for _, row in stats_df.iterrows():
        cv = row['rps_cv']
        if cv < 5:
            quality = "Excellent (CV < 5%)"
        elif cv < 10:
            quality = "Good (CV < 10%)"
        elif cv < 15:
            quality = "Acceptable (CV < 15%)"
        else:
            quality = "Poor (CV > 15%) - Consider more runs"

        print(f"  {row['request_type']}: {quality}")

    print()

def save_results(stats_df, output_prefix):
    """Save results to files"""

    # CSV
    csv_file = f"{output_prefix}_aggregated.csv"
    stats_df.to_csv(csv_file, index=False)
    print(f"Saved CSV: {csv_file}")

    # JSON
    json_file = f"{output_prefix}_aggregated.json"
    with open(json_file, 'w') as f:
        json.dump(stats_df.to_dict(orient='records'), f, indent=2)
    print(f"Saved JSON: {json_file}")

    # Markdown summary
    md_file = f"{output_prefix}_summary.md"
    with open(md_file, 'w') as f:
        f.write("# Experiment Results Summary\n\n")

        for _, row in stats_df.iterrows():
            f.write(f"## {row['request_type']}\n\n")
            f.write(f"**Runs:** {row['num_runs']}\n\n")

            f.write("### Throughput\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Mean RPS | {row['rps_mean']:.2f} |\n")
            f.write(f"| Median RPS | {row['rps_median']:.2f} |\n")
            f.write(f"| Std Dev | {row['rps_std']:.2f} |\n")
            f.write(f"| 95% CI | [{row['rps_ci_lower']:.2f}, {row['rps_ci_upper']:.2f}] |\n")
            f.write(f"| CV | {row['rps_cv']:.1f}% |\n\n")

            if row['response_time_p95']:
                f.write("### Latency (ms)\n\n")
                f.write("| Percentile | Value |\n")
                f.write("|------------|-------|\n")
                f.write(f"| P50 | {row['response_time_p50']:.2f} |\n")
                f.write(f"| P95 | {row['response_time_p95']:.2f} |\n")
                f.write(f"| P99 | {row['response_time_p99']:.2f} |\n\n")

    print(f"Saved Markdown: {md_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python aggregate_results.py <pattern>")
        print("")
        print("Examples:")
        print("  python aggregate_results.py results/exp1_run*")
        print("  python aggregate_results.py results/exp1_run*_stats.csv")
        sys.exit(1)

    pattern = sys.argv[1]

    print(f"Loading results from: {pattern}")

    df = load_stats_files(pattern)
    print(f"Loaded {len(df)} records from {df['run'].nunique()} runs")

    stats_df = calculate_statistics(df)

    print_summary(stats_df)

    # Determine output prefix
    if '*' in pattern:
        output_prefix = pattern.split('*')[0].rstrip('_run')
    else:
        output_prefix = Path(pattern).stem

    save_results(stats_df, output_prefix)

    print(f"\n✓ Analysis complete!")

if __name__ == '__main__':
    main()
