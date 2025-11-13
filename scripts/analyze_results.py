#!/usr/bin/env python3
"""
Publication-Grade Statistical Analysis Script
Analyzes results from execute_publication_run.sh

Usage: python scripts/analyze_results.py results/campaign_results_*.csv
"""

import sys
import pandas as pd
import numpy as np
from scipy import stats
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore')


def load_results(filepath):
    """Load experiment results from CSV"""
    print(f"📂 Loading results from: {filepath}")
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {len(df)} data points")
    return df


def print_summary_statistics(df):
    """Print descriptive statistics for each architecture x load level"""
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    for arch in df['architecture'].unique():
        print(f"\n{'─'*80}")
        print(f"Architecture: {arch.upper()}")
        print(f"{'─'*80}")

        arch_data = df[df['architecture'] == arch]

        for load in sorted(arch_data['load_level'].unique()):
            load_data = arch_data[arch_data['load_level'] == load]

            print(f"\n  Load Level: {load} users (N={len(load_data)} samples)")

            metrics = {
                'Throughput (RPS)': 'requests_per_second',
                'Avg Latency (ms)': 'avg_latency_ms',
                'P95 Latency (ms)': 'p95_latency_ms',
                'CPU Usage (%)': 'avg_cpu_percent',
                'Memory (MB)': 'avg_memory_mb',
                'Error Rate (%)': 'error_rate_percent'
            }

            for label, col in metrics.items():
                if col in load_data.columns:
                    mean = load_data[col].mean()
                    std = load_data[col].std()
                    sem = stats.sem(load_data[col])
                    ci_95 = stats.t.interval(0.95, len(load_data)-1, loc=mean, scale=sem)

                    print(f"    {label:20s}: {mean:8.2f} ± {std:6.2f} (95% CI: [{ci_95[0]:8.2f}, {ci_95[1]:8.2f}])")


def test_statistical_significance(df):
    """Perform ANOVA and post-hoc tests"""
    print("\n" + "="*80)
    print("STATISTICAL SIGNIFICANCE TESTS")
    print("="*80)

    architectures = df['architecture'].unique()

    for load in sorted(df['load_level'].unique()):
        print(f"\n{'─'*80}")
        print(f"Load Level: {load} users")
        print(f"{'─'*80}")

        load_data = df[df['load_level'] == load]

        # Prepare data for ANOVA
        groups = [
            load_data[load_data['architecture'] == arch]['requests_per_second'].values
            for arch in architectures
        ]

        # ANOVA
        f_stat, p_value = stats.f_oneway(*groups)

        print(f"\n  ANOVA (Throughput):")
        print(f"    F-statistic: {f_stat:.4f}")
        print(f"    p-value: {p_value:.6f}")

        if p_value < 0.05:
            print(f"    ✅ SIGNIFICANT: Architectures differ (p < 0.05)")

            # Post-hoc pairwise t-tests
            print(f"\n  Post-hoc Pairwise Comparisons (Bonferroni corrected):")

            num_comparisons = len(architectures) * (len(architectures) - 1) / 2
            alpha_corrected = 0.05 / num_comparisons

            for i, arch1 in enumerate(architectures):
                for arch2 in architectures[i+1:]:
                    data1 = load_data[load_data['architecture'] == arch1]['requests_per_second']
                    data2 = load_data[load_data['architecture'] == arch2]['requests_per_second']

                    t_stat, p_val = stats.ttest_ind(data1, data2)

                    # Cohen's d (effect size)
                    pooled_std = np.sqrt((data1.std()**2 + data2.std()**2) / 2)
                    cohens_d = (data1.mean() - data2.mean()) / pooled_std

                    sig_marker = "✅" if p_val < alpha_corrected else "❌"

                    print(f"    {arch1:15s} vs {arch2:15s}: t={t_stat:7.3f}, p={p_val:.6f}, d={cohens_d:6.3f} {sig_marker}")

        else:
            print(f"    ❌ NOT SIGNIFICANT: No difference detected (p >= 0.05)")


def performance_cost_analysis(df):
    """Calculate performance-cost efficiency"""
    print("\n" + "="*80)
    print("PERFORMANCE-COST EFFICIENCY")
    print("="*80)

    for arch in df['architecture'].unique():
        print(f"\n{'─'*80}")
        print(f"Architecture: {arch.upper()}")
        print(f"{'─'*80}")

        arch_data = df[df['architecture'] == arch]

        for load in sorted(arch_data['load_level'].unique()):
            load_data = arch_data[arch_data['load_level'] == load]

            rps_mean = load_data['requests_per_second'].mean()
            cpu_mean = load_data['avg_cpu_percent'].mean()
            mem_mean = load_data['avg_memory_mb'].mean()

            # Efficiency metrics
            rps_per_cpu = rps_mean / cpu_mean if cpu_mean > 0 else 0
            rps_per_gb = rps_mean / (mem_mean / 1024) if mem_mean > 0 else 0

            print(f"\n  Load Level: {load} users")
            print(f"    Throughput/CPU%:  {rps_per_cpu:8.2f} RPS per CPU%")
            print(f"    Throughput/GB:    {rps_per_gb:8.2f} RPS per GB")


def generate_latex_table(df):
    """Generate LaTeX table for publication"""
    print("\n" + "="*80)
    print("LATEX TABLE (Ready for Publication)")
    print("="*80)

    print("\n\\begin{table}[h]")
    print("\\centering")
    print("\\caption{Performance Comparison of Architectures}")
    print("\\label{tab:performance}")
    print("\\begin{tabular}{l|l|r|r|r|r}")
    print("\\hline")
    print("\\textbf{Architecture} & \\textbf{Load} & \\textbf{Throughput} & \\textbf{Latency} & \\textbf{CPU} & \\textbf{Memory} \\\\")
    print("& \\textbf{(users)} & \\textbf{(RPS)} & \\textbf{(ms)} & \\textbf{(\\%)} & \\textbf{(MB)} \\\\")
    print("\\hline")

    for arch in sorted(df['architecture'].unique()):
        arch_data = df[df['architecture'] == arch]

        for load in sorted(arch_data['load_level'].unique()):
            load_data = arch_data[arch_data['load_level'] == load]

            rps = load_data['requests_per_second'].mean()
            rps_std = load_data['requests_per_second'].std()
            lat = load_data['avg_latency_ms'].mean()
            lat_std = load_data['avg_latency_ms'].std()
            cpu = load_data['avg_cpu_percent'].mean()
            cpu_std = load_data['avg_cpu_percent'].std()
            mem = load_data['avg_memory_mb'].mean()
            mem_std = load_data['avg_memory_mb'].std()

            print(f"{arch.upper():15s} & {load:3d} & ${rps:6.1f} \\pm {rps_std:5.1f}$ & ${lat:5.1f} \\pm {lat_std:4.1f}$ & ${cpu:4.1f} \\pm {cpu_std:4.1f}$ & ${mem:6.1f} \\pm {mem_std:5.1f}$ \\\\")

        print("\\hline")

    print("\\end{tabular}")
    print("\\end{table}")


def write_latex_output(df, output_path):
    """Write complete LaTeX analysis to file"""
    with open(output_path, 'w') as f:
        f.write("% Statistical Analysis Report\n")
        f.write(f"% Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary Statistics Section
        f.write("\\section{Summary Statistics}\n\n")
        for arch in df['architecture'].unique():
            f.write(f"\\subsection*{{Architecture: {arch.upper()}}}\n\n")
            arch_data = df[df['architecture'] == arch]

            for load in sorted(arch_data['load_level'].unique()):
                load_data = arch_data[arch_data['load_level'] == load]
                f.write(f"\\textbf{{Load Level: {load} users}} (N={len(load_data)} samples)\n\n")

                f.write("\\begin{itemize}\n")
                metrics = {
                    'Throughput (RPS)': 'requests_per_second',
                    'Avg Latency (ms)': 'avg_latency_ms',
                    'P95 Latency (ms)': 'p95_latency_ms',
                    'CPU Usage (\\%)': 'avg_cpu_percent',
                    'Memory (MB)': 'avg_memory_mb',
                    'Error Rate (\\%)': 'error_rate_percent'
                }

                for label, col in metrics.items():
                    if col in load_data.columns:
                        mean = load_data[col].mean()
                        std = load_data[col].std()
                        sem = stats.sem(load_data[col])
                        ci_95 = stats.t.interval(0.95, len(load_data)-1, loc=mean, scale=sem)
                        f.write(f"  \\item {label}: ${mean:.2f} \\pm {std:.2f}$ (95\\% CI: $[{ci_95[0]:.2f}, {ci_95[1]:.2f}]$)\n")

                f.write("\\end{itemize}\n\n")

        # Statistical Tests Section
        f.write("\\section{Statistical Significance Tests}\n\n")
        architectures = df['architecture'].unique()

        for load in sorted(df['load_level'].unique()):
            f.write(f"\\subsection*{{Load Level: {load} users}}\n\n")
            load_data = df[df['load_level'] == load]

            groups = [
                load_data[load_data['architecture'] == arch]['requests_per_second'].values
                for arch in architectures
            ]

            f_stat, p_value = stats.f_oneway(*groups)
            f.write(f"ANOVA (Throughput): F-statistic = {f_stat:.4f}, p-value = {p_value:.6f}\n\n")

            if p_value < 0.05:
                f.write("\\textbf{SIGNIFICANT}: Architectures differ (p < 0.05)\n\n")
                f.write("\\textbf{Post-hoc Pairwise Comparisons:}\n\n")
                f.write("\\begin{tabular}{l|c|c|c}\n")
                f.write("\\hline\n")
                f.write("Comparison & t-statistic & p-value & Cohen's d \\\\\n")
                f.write("\\hline\n")

                num_comparisons = len(architectures) * (len(architectures) - 1) / 2
                alpha_corrected = 0.05 / num_comparisons

                for i, arch1 in enumerate(architectures):
                    for arch2 in architectures[i+1:]:
                        data1 = load_data[load_data['architecture'] == arch1]['requests_per_second']
                        data2 = load_data[load_data['architecture'] == arch2]['requests_per_second']

                        t_stat, p_val = stats.ttest_ind(data1, data2)
                        pooled_std = np.sqrt((data1.std()**2 + data2.std()**2) / 2)
                        cohens_d = (data1.mean() - data2.mean()) / pooled_std

                        sig = "*" if p_val < alpha_corrected else ""
                        f.write(f"{arch1.upper()} vs {arch2.upper()} & {t_stat:.3f} & {p_val:.6f}{sig} & {cohens_d:.3f} \\\\\n")

                f.write("\\hline\n")
                f.write("\\end{tabular}\n\n")
            else:
                f.write("NOT SIGNIFICANT: No difference detected (p $\\geq$ 0.05)\n\n")

        # Performance Table
        f.write("\\section{Performance Comparison Table}\n\n")
        f.write("\\begin{table}[h]\n")
        f.write("\\centering\n")
        f.write("\\caption{Performance Comparison of Architectures}\n")
        f.write("\\label{tab:performance}\n")
        f.write("\\begin{tabular}{l|l|r|r|r|r}\n")
        f.write("\\hline\n")
        f.write("\\textbf{Architecture} & \\textbf{Load} & \\textbf{Throughput} & \\textbf{Latency} & \\textbf{CPU} & \\textbf{Memory} \\\\\n")
        f.write("& \\textbf{(users)} & \\textbf{(RPS)} & \\textbf{(ms)} & \\textbf{(\\%)} & \\textbf{(MB)} \\\\\n")
        f.write("\\hline\n")

        for arch in sorted(df['architecture'].unique()):
            arch_data = df[df['architecture'] == arch]

            for load in sorted(arch_data['load_level'].unique()):
                load_data = arch_data[arch_data['load_level'] == load]

                rps = load_data['requests_per_second'].mean()
                rps_std = load_data['requests_per_second'].std()
                lat = load_data['avg_latency_ms'].mean()
                lat_std = load_data['avg_latency_ms'].std()
                cpu = load_data['avg_cpu_percent'].mean()
                cpu_std = load_data['avg_cpu_percent'].std()
                mem = load_data['avg_memory_mb'].mean()
                mem_std = load_data['avg_memory_mb'].std()

                f.write(f"{arch.upper():15s} & {load:3d} & ${rps:6.1f} \\pm {rps_std:5.1f}$ & ${lat:5.1f} \\pm {lat_std:4.1f}$ & ${cpu:4.1f} \\pm {cpu_std:4.1f}$ & ${mem:6.1f} \\pm {mem_std:5.1f}$ \\\\\n")

            f.write("\\hline\n")

        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")


def write_markdown_output(df, output_path):
    """Write complete Markdown analysis to file"""
    with open(output_path, 'w') as f:
        f.write("# Statistical Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary Statistics
        f.write("## Summary Statistics\n\n")
        for arch in df['architecture'].unique():
            f.write(f"### Architecture: {arch.upper()}\n\n")
            arch_data = df[df['architecture'] == arch]

            for load in sorted(arch_data['load_level'].unique()):
                load_data = arch_data[arch_data['load_level'] == load]
                f.write(f"#### Load Level: {load} users (N={len(load_data)} samples)\n\n")

                metrics = {
                    'Throughput (RPS)': 'requests_per_second',
                    'Avg Latency (ms)': 'avg_latency_ms',
                    'P95 Latency (ms)': 'p95_latency_ms',
                    'CPU Usage (%)': 'avg_cpu_percent',
                    'Memory (MB)': 'avg_memory_mb',
                    'Error Rate (%)': 'error_rate_percent'
                }

                for label, col in metrics.items():
                    if col in load_data.columns:
                        mean = load_data[col].mean()
                        std = load_data[col].std()
                        sem = stats.sem(load_data[col])
                        ci_95 = stats.t.interval(0.95, len(load_data)-1, loc=mean, scale=sem)
                        f.write(f"- **{label}**: {mean:.2f} ± {std:.2f} (95% CI: [{ci_95[0]:.2f}, {ci_95[1]:.2f}])\n")

                f.write("\n")

        # Statistical Tests
        f.write("## Statistical Significance Tests\n\n")
        architectures = df['architecture'].unique()

        for load in sorted(df['load_level'].unique()):
            f.write(f"### Load Level: {load} users\n\n")
            load_data = df[df['load_level'] == load]

            groups = [
                load_data[load_data['architecture'] == arch]['requests_per_second'].values
                for arch in architectures
            ]

            f_stat, p_value = stats.f_oneway(*groups)
            f.write(f"**ANOVA (Throughput):**\n")
            f.write(f"- F-statistic: {f_stat:.4f}\n")
            f.write(f"- p-value: {p_value:.6f}\n\n")

            if p_value < 0.05:
                f.write("✅ **SIGNIFICANT**: Architectures differ (p < 0.05)\n\n")
                f.write("**Post-hoc Pairwise Comparisons:**\n\n")
                f.write("| Comparison | t-statistic | p-value | Cohen's d | Significant |\n")
                f.write("|------------|-------------|---------|-----------|-------------|\n")

                num_comparisons = len(architectures) * (len(architectures) - 1) / 2
                alpha_corrected = 0.05 / num_comparisons

                for i, arch1 in enumerate(architectures):
                    for arch2 in architectures[i+1:]:
                        data1 = load_data[load_data['architecture'] == arch1]['requests_per_second']
                        data2 = load_data[load_data['architecture'] == arch2]['requests_per_second']

                        t_stat, p_val = stats.ttest_ind(data1, data2)
                        pooled_std = np.sqrt((data1.std()**2 + data2.std()**2) / 2)
                        cohens_d = (data1.mean() - data2.mean()) / pooled_std

                        sig = "✅" if p_val < alpha_corrected else "❌"
                        f.write(f"| {arch1.upper()} vs {arch2.upper()} | {t_stat:.3f} | {p_val:.6f} | {cohens_d:.3f} | {sig} |\n")

                f.write("\n")
            else:
                f.write("❌ **NOT SIGNIFICANT**: No difference detected (p ≥ 0.05)\n\n")

        # Performance Efficiency
        f.write("## Performance-Cost Efficiency\n\n")
        for arch in df['architecture'].unique():
            f.write(f"### Architecture: {arch.upper()}\n\n")
            arch_data = df[df['architecture'] == arch]

            for load in sorted(arch_data['load_level'].unique()):
                load_data = arch_data[arch_data['load_level'] == load]

                rps_mean = load_data['requests_per_second'].mean()
                cpu_mean = load_data['avg_cpu_percent'].mean()
                mem_mean = load_data['avg_memory_mb'].mean()

                rps_per_cpu = rps_mean / cpu_mean if cpu_mean > 0 else 0
                rps_per_gb = rps_mean / (mem_mean / 1024) if mem_mean > 0 else 0

                f.write(f"**Load Level: {load} users**\n")
                f.write(f"- Throughput/CPU%: {rps_per_cpu:.2f} RPS per CPU%\n")
                f.write(f"- Throughput/GB: {rps_per_gb:.2f} RPS per GB\n\n")

        # Performance Table
        f.write("## Performance Comparison Table\n\n")
        f.write("| Architecture | Load (users) | Throughput (RPS) | Latency (ms) | CPU (%) | Memory (MB) |\n")
        f.write("|--------------|--------------|------------------|--------------|---------|-------------|\n")

        for arch in sorted(df['architecture'].unique()):
            arch_data = df[df['architecture'] == arch]

            for load in sorted(arch_data['load_level'].unique()):
                load_data = arch_data[arch_data['load_level'] == load]

                rps = load_data['requests_per_second'].mean()
                rps_std = load_data['requests_per_second'].std()
                lat = load_data['avg_latency_ms'].mean()
                lat_std = load_data['avg_latency_ms'].std()
                cpu = load_data['avg_cpu_percent'].mean()
                cpu_std = load_data['avg_cpu_percent'].std()
                mem = load_data['avg_memory_mb'].mean()
                mem_std = load_data['avg_memory_mb'].std()

                f.write(f"| {arch.upper()} | {load} | {rps:.1f} ± {rps_std:.1f} | {lat:.1f} ± {lat_std:.1f} | {cpu:.1f} ± {cpu_std:.1f} | {mem:.1f} ± {mem_std:.1f} |\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_results.py results/campaign_results_*.csv")
        sys.exit(1)

    filepath = sys.argv[1]

    # Load results
    df = load_results(filepath)

    # Verify data integrity
    expected_rows = len(df['architecture'].unique()) * len(df['load_level'].unique()) * df['sample_num'].max()
    print(f"📊 Data integrity: {len(df)} rows (expected: ~{expected_rows})")

    # Run analyses (console output)
    print_summary_statistics(df)
    test_statistical_significance(df)
    performance_cost_analysis(df)
    generate_latex_table(df)

    # Create output directory
    output_dir = Path("results/stats-output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filenames
    timestamp = datetime.now().strftime("%y-%m-%d-%H%M%S")
    latex_path = output_dir / f"analysis_{timestamp}.tex"
    markdown_path = output_dir / f"analysis_{timestamp}.md"

    # Write output files
    write_latex_output(df, latex_path)
    write_markdown_output(df, markdown_path)

    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    print(f"\n📄 Output files:")
    print(f"   LaTeX:    {latex_path}")
    print(f"   Markdown: {markdown_path}")
    print("\nNext steps:")
    print("  1. Review statistical significance results")
    print("  2. Generate visualizations: python scripts/generate_publication_figures.py " + filepath)
    print("  3. Copy LaTeX table to your manuscript")
    print()


if __name__ == '__main__':
    main()
