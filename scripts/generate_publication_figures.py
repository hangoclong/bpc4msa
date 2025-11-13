#!/usr/bin/env python3
"""
Publication-Grade Figure Generation Script
Generates publication-quality visualizations from experiment results

Usage: python scripts/generate_publication_figures.py results/campaign_results_*.csv
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set publication-quality defaults
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'

# Color palette
COLORS = {
    'bpc4msa': '#2E86AB',      # Blue
    'synchronous': '#A23B72',  # Purple
    'monolithic': '#F18F01'    # Orange
}

LABELS = {
    'bpc4msa': 'BPC4MSA (Event-Driven)',
    'synchronous': 'Synchronous SOA',
    'monolithic': 'Monolithic BPMS'
}


def ensure_figures_dir():
    """Create figures directory if it doesn't exist"""
    Path('figures').mkdir(exist_ok=True)


def plot_scalability_curve(df, output_dir='figures'):
    """Generate scalability curve: Throughput vs Load"""
    fig, ax = plt.subplots(figsize=(8, 5))

    for arch in sorted(df['architecture'].unique()):
        arch_data = df[df['architecture'] == arch]
        grouped = arch_data.groupby('load_level')['requests_per_second']

        means = grouped.mean()
        stds = grouped.std()
        sems = grouped.apply(lambda x: np.std(x) / np.sqrt(len(x)))

        ax.errorbar(
            means.index, means.values,
            yerr=1.96 * sems.values,  # 95% CI
            marker='o', markersize=8,
            linewidth=2, capsize=5, capthick=2,
            label=LABELS[arch],
            color=COLORS[arch]
        )

    ax.set_xlabel('Load Level (Concurrent Users)', fontweight='bold')
    ax.set_ylabel('Throughput (Requests/Second)', fontweight='bold')
    ax.set_title('Scalability Comparison: Throughput vs Load', fontweight='bold')
    ax.legend(frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    filepath = f'{output_dir}/fig1_scalability_curve.pdf'
    plt.savefig(filepath)
    plt.savefig(filepath.replace('.pdf', '.png'))
    print(f"✅ Saved: {filepath}")
    plt.close()


def plot_latency_comparison(df, output_dir='figures'):
    """Generate latency comparison: Average and P95"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Average latency
    for arch in sorted(df['architecture'].unique()):
        arch_data = df[df['architecture'] == arch]
        grouped = arch_data.groupby('load_level')['avg_latency_ms']

        means = grouped.mean()
        sems = grouped.apply(lambda x: np.std(x) / np.sqrt(len(x)))

        ax1.errorbar(
            means.index, means.values,
            yerr=1.96 * sems.values,
            marker='s', markersize=8,
            linewidth=2, capsize=5, capthick=2,
            label=LABELS[arch],
            color=COLORS[arch]
        )

    ax1.set_xlabel('Load Level (Concurrent Users)', fontweight='bold')
    ax1.set_ylabel('Average Latency (ms)', fontweight='bold')
    ax1.set_title('Average Response Latency', fontweight='bold')
    ax1.legend(frameon=True, shadow=True)
    ax1.grid(True, alpha=0.3, linestyle='--')

    # P95 latency
    for arch in sorted(df['architecture'].unique()):
        arch_data = df[df['architecture'] == arch]
        grouped = arch_data.groupby('load_level')['p95_latency_ms']

        means = grouped.mean()
        sems = grouped.apply(lambda x: np.std(x) / np.sqrt(len(x)))

        ax2.errorbar(
            means.index, means.values,
            yerr=1.96 * sems.values,
            marker='s', markersize=8,
            linewidth=2, capsize=5, capthick=2,
            label=LABELS[arch],
            color=COLORS[arch]
        )

    ax2.set_xlabel('Load Level (Concurrent Users)', fontweight='bold')
    ax2.set_ylabel('P95 Latency (ms)', fontweight='bold')
    ax2.set_title('95th Percentile Latency', fontweight='bold')
    ax2.legend(frameon=True, shadow=True)
    ax2.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    filepath = f'{output_dir}/fig2_latency_comparison.pdf'
    plt.savefig(filepath)
    plt.savefig(filepath.replace('.pdf', '.png'))
    print(f"✅ Saved: {filepath}")
    plt.close()


def plot_resource_utilization(df, output_dir='figures'):
    """Generate resource utilization charts: CPU and Memory"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # CPU utilization
    for arch in sorted(df['architecture'].unique()):
        arch_data = df[df['architecture'] == arch]
        grouped = arch_data.groupby('load_level')['avg_cpu_percent']

        means = grouped.mean()
        sems = grouped.apply(lambda x: np.std(x) / np.sqrt(len(x)))

        ax1.errorbar(
            means.index, means.values,
            yerr=1.96 * sems.values,
            marker='^', markersize=8,
            linewidth=2, capsize=5, capthick=2,
            label=LABELS[arch],
            color=COLORS[arch]
        )

    ax1.set_xlabel('Load Level (Concurrent Users)', fontweight='bold')
    ax1.set_ylabel('CPU Utilization (%)', fontweight='bold')
    ax1.set_title('CPU Resource Consumption', fontweight='bold')
    ax1.legend(frameon=True, shadow=True)
    ax1.grid(True, alpha=0.3, linestyle='--')

    # Memory utilization
    for arch in sorted(df['architecture'].unique()):
        arch_data = df[df['architecture'] == arch]
        grouped = arch_data.groupby('load_level')['avg_memory_mb']

        means = grouped.mean()
        sems = grouped.apply(lambda x: np.std(x) / np.sqrt(len(x)))

        ax2.errorbar(
            means.index, means.values,
            yerr=1.96 * sems.values,
            marker='^', markersize=8,
            linewidth=2, capsize=5, capthick=2,
            label=LABELS[arch],
            color=COLORS[arch]
        )

    ax2.set_xlabel('Load Level (Concurrent Users)', fontweight='bold')
    ax2.set_ylabel('Memory Usage (MB)', fontweight='bold')
    ax2.set_title('Memory Resource Consumption', fontweight='bold')
    ax2.legend(frameon=True, shadow=True)
    ax2.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    filepath = f'{output_dir}/fig3_resource_utilization.pdf'
    plt.savefig(filepath)
    plt.savefig(filepath.replace('.pdf', '.png'))
    print(f"✅ Saved: {filepath}")
    plt.close()


def plot_efficiency_metrics(df, output_dir='figures'):
    """Generate performance-cost efficiency chart"""
    fig, ax = plt.subplots(figsize=(8, 5))

    for arch in sorted(df['architecture'].unique()):
        arch_data = df[df['architecture'] == arch]

        # Calculate efficiency: RPS per CPU%
        grouped = arch_data.groupby('load_level').apply(
            lambda x: x['requests_per_second'].mean() / x['avg_cpu_percent'].mean()
        )

        ax.plot(
            grouped.index, grouped.values,
            marker='D', markersize=8,
            linewidth=2,
            label=LABELS[arch],
            color=COLORS[arch]
        )

    ax.set_xlabel('Load Level (Concurrent Users)', fontweight='bold')
    ax.set_ylabel('Efficiency (RPS per CPU%)', fontweight='bold')
    ax.set_title('Performance-Cost Efficiency', fontweight='bold')
    ax.legend(frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    filepath = f'{output_dir}/fig4_efficiency_metrics.pdf'
    plt.savefig(filepath)
    plt.savefig(filepath.replace('.pdf', '.png'))
    print(f"✅ Saved: {filepath}")
    plt.close()


def plot_box_plots(df, output_dir='figures'):
    """Generate box plots for variance visualization"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    metrics = [
        ('requests_per_second', 'Throughput (RPS)', axes[0, 0]),
        ('avg_latency_ms', 'Average Latency (ms)', axes[0, 1]),
        ('avg_cpu_percent', 'CPU Utilization (%)', axes[1, 0]),
        ('avg_memory_mb', 'Memory Usage (MB)', axes[1, 1])
    ]

    for metric_col, ylabel, ax in metrics:
        # Select highest load level for comparison
        max_load = df['load_level'].max()
        subset = df[df['load_level'] == max_load]

        # Create box plot
        positions = range(len(subset['architecture'].unique()))
        box_data = [
            subset[subset['architecture'] == arch][metric_col].values
            for arch in sorted(subset['architecture'].unique())
        ]

        bp = ax.boxplot(
            box_data,
            positions=positions,
            labels=[LABELS[arch] for arch in sorted(subset['architecture'].unique())],
            patch_artist=True,
            widths=0.6
        )

        # Color boxes
        for patch, arch in zip(bp['boxes'], sorted(subset['architecture'].unique())):
            patch.set_facecolor(COLORS[arch])
            patch.set_alpha(0.7)

        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_title(f'{ylabel} at Load={max_load} users', fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.tick_params(axis='x', rotation=15)

    plt.tight_layout()
    filepath = f'{output_dir}/fig5_variance_boxplots.pdf'
    plt.savefig(filepath)
    plt.savefig(filepath.replace('.pdf', '.png'))
    print(f"✅ Saved: {filepath}")
    plt.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_publication_figures.py results/campaign_results_*.csv")
        sys.exit(1)

    filepath = sys.argv[1]

    print("📊 Generating publication-quality figures...")
    print(f"📂 Loading data from: {filepath}\n")

    # Load results
    df = pd.read_csv(filepath)

    # Create figures directory
    ensure_figures_dir()

    # Generate all figures
    plot_scalability_curve(df)
    plot_latency_comparison(df)
    plot_resource_utilization(df)
    plot_efficiency_metrics(df)
    plot_box_plots(df)

    print("\n" + "="*80)
    print("✅ ALL FIGURES GENERATED")
    print("="*80)
    print("\nOutput directory: figures/")
    print("Files generated:")
    print("  - fig1_scalability_curve.pdf/.png")
    print("  - fig2_latency_comparison.pdf/.png")
    print("  - fig3_resource_utilization.pdf/.png")
    print("  - fig4_efficiency_metrics.pdf/.png")
    print("  - fig5_variance_boxplots.pdf/.png")
    print("\nThese figures are publication-ready (300 DPI, vector PDF format)")
    print()


if __name__ == '__main__':
    main()
