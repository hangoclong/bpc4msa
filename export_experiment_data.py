#!/usr/bin/env python3
"""
Experiment Data Exporter for Publication
Extracts raw data and generates publication-ready formats

Usage:
    python3 export_experiment_data.py --format csv
    python3 export_experiment_data.py --format latex
    python3 export_experiment_data.py --format json
    python3 export_experiment_data.py --format all
"""

import requests
import json
import csv
import sys
from datetime import datetime
from typing import Dict, List, Any
import argparse


class ExperimentDataExporter:
    """Export experiment data for academic publication"""

    ARCHITECTURES = ['bpc4msa', 'synchronous', 'monolithic']
    CONTROL_API = "http://localhost:8080"

    def __init__(self, output_dir: str = "experiment_results"):
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def fetch_metrics(self) -> Dict[str, Any]:
        """Fetch comparative metrics from all architectures"""
        response = requests.get(f"{self.CONTROL_API}/api/compare/metrics")
        return response.json()

    def fetch_architecture_metrics(self, architecture: str) -> Dict[str, Any]:
        """Fetch detailed metrics for specific architecture"""
        response = requests.get(f"{self.CONTROL_API}/api/metrics/{architecture}")
        return response.json()

    def export_csv(self, data: Dict[str, Any]) -> str:
        """Export as CSV for Excel/R/Python analysis"""
        filename = f"experiment_results_{self.timestamp}.csv"

        with open(filename, 'w', newline='') as csvfile:
            fieldnames = [
                'Architecture',
                'Total_Transactions',
                'Total_Events',
                'Avg_Latency_ms',
                'Total_Violations',
                'Throughput_per_min',
                'Violation_Rate_%'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for arch, metrics in data.items():
                writer.writerow({
                    'Architecture': arch.upper(),
                    'Total_Transactions': metrics.get('total_transactions', 0),
                    'Total_Events': metrics.get('total_events', 0),
                    'Avg_Latency_ms': round(metrics.get('avg_latency_ms', 0), 2),
                    'Total_Violations': metrics.get('total_violations', 0),
                    'Throughput_per_min': round(metrics.get('throughput_per_min', 0), 2),
                    'Violation_Rate_%': round(metrics.get('violation_rate', 0), 2)
                })

        print(f"✅ CSV exported: {filename}")
        return filename

    def export_latex_table(self, data: Dict[str, Any]) -> str:
        """Export as LaTeX table for paper"""
        filename = f"experiment_table_{self.timestamp}.tex"

        latex = r"""\begin{table}[htbp]
\centering
\caption{Architectural Performance Comparison}
\label{tab:arch_comparison}
\begin{tabular}{lrrrrr}
\toprule
\textbf{Architecture} & \textbf{Transactions} & \textbf{Latency (ms)} & \textbf{Violations} & \textbf{Throughput} & \textbf{Violation Rate (\%)} \\
\midrule
"""

        for arch, metrics in data.items():
            latex += f"{arch.upper()} & "
            latex += f"{metrics.get('total_transactions', 0)} & "
            latex += f"{metrics.get('avg_latency_ms', 0):.2f} & "
            latex += f"{metrics.get('total_violations', 0)} & "
            latex += f"{metrics.get('throughput_per_min', 0):.2f} & "
            latex += f"{metrics.get('violation_rate', 0):.2f} \\\\\n"

        latex += r"""\bottomrule
\end{tabular}
\end{table}"""

        with open(filename, 'w') as f:
            f.write(latex)

        print(f"✅ LaTeX table exported: {filename}")
        return filename

    def export_markdown_table(self, data: Dict[str, Any]) -> str:
        """Export as Markdown table for documentation"""
        filename = f"experiment_table_{self.timestamp}.md"

        md = "# Experiment Results\n\n"
        md += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += "## Comparative Performance\n\n"
        md += "| Architecture | Transactions | Avg Latency (ms) | Violations | Throughput (req/min) | Violation Rate (%) |\n"
        md += "|--------------|--------------|------------------|------------|----------------------|--------------------|\n"

        for arch, metrics in data.items():
            md += f"| {arch.upper()} | "
            md += f"{metrics.get('total_transactions', 0)} | "
            md += f"{metrics.get('avg_latency_ms', 0):.2f} | "
            md += f"{metrics.get('total_violations', 0)} | "
            md += f"{metrics.get('throughput_per_min', 0):.2f} | "
            md += f"{metrics.get('violation_rate', 0):.2f} |\n"

        # Add analysis section
        md += "\n## Key Findings\n\n"

        # Find best/worst performers
        latencies = {arch: m.get('avg_latency_ms', 0) for arch, m in data.items()}
        throughputs = {arch: m.get('throughput_per_min', 0) for arch, m in data.items()}

        best_latency = min(latencies, key=latencies.get)
        best_throughput = max(throughputs, key=throughputs.get)

        md += f"- **Lowest Latency:** {best_latency.upper()} ({latencies[best_latency]:.2f} ms)\n"
        md += f"- **Highest Throughput:** {best_throughput.upper()} ({throughputs[best_throughput]:.2f} req/min)\n"

        with open(filename, 'w') as f:
            f.write(md)

        print(f"✅ Markdown table exported: {filename}")
        return filename

    def export_json_raw(self, data: Dict[str, Any]) -> str:
        """Export raw JSON for custom processing"""
        filename = f"experiment_raw_{self.timestamp}.json"

        export_data = {
            'timestamp': datetime.now().isoformat(),
            'architectures': data,
            'metadata': {
                'total_architectures': len(data),
                'export_tool': 'BPC4MSA Experiment Exporter v1.0'
            }
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"✅ JSON exported: {filename}")
        return filename

    def export_statistical_summary(self, data: Dict[str, Any]) -> str:
        """Export statistical summary for analysis"""
        filename = f"experiment_stats_{self.timestamp}.txt"

        output = []
        output.append("=" * 80)
        output.append("EXPERIMENT STATISTICAL SUMMARY")
        output.append("=" * 80)
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")

        for arch, metrics in data.items():
            output.append(f"\n{arch.upper()} Architecture:")
            output.append("-" * 40)
            output.append(f"  Total Transactions:    {metrics.get('total_transactions', 0):,}")
            output.append(f"  Total Events:          {metrics.get('total_events', 0):,}")
            output.append(f"  Avg Latency:           {metrics.get('avg_latency_ms', 0):.2f} ms")
            output.append(f"  Total Violations:      {metrics.get('total_violations', 0):,}")
            output.append(f"  Throughput:            {metrics.get('throughput_per_min', 0):.2f} req/min")
            output.append(f"  Violation Rate:        {metrics.get('violation_rate', 0):.2f}%")

        # Comparative analysis
        output.append("\n" + "=" * 80)
        output.append("COMPARATIVE ANALYSIS")
        output.append("=" * 80)

        latencies = {arch: m.get('avg_latency_ms', 0) for arch, m in data.items()}
        throughputs = {arch: m.get('throughput_per_min', 0) for arch, m in data.items()}
        violations = {arch: m.get('violation_rate', 0) for arch, m in data.items()}

        output.append(f"\nLatency (lower is better):")
        for arch in sorted(latencies, key=latencies.get):
            output.append(f"  {arch.upper():15s}: {latencies[arch]:10.2f} ms")

        output.append(f"\nThroughput (higher is better):")
        for arch in sorted(throughputs, key=throughputs.get, reverse=True):
            output.append(f"  {arch.upper():15s}: {throughputs[arch]:10.2f} req/min")

        output.append(f"\nViolation Rate (lower is better):")
        for arch in sorted(violations, key=violations.get):
            output.append(f"  {arch.upper():15s}: {violations[arch]:10.2f}%")

        content = "\n".join(output)
        with open(filename, 'w') as f:
            f.write(content)

        print(f"✅ Statistical summary exported: {filename}")
        print("\n" + content)
        return filename

    def export_all(self):
        """Export all formats"""
        print("Fetching experiment data...")
        data = self.fetch_metrics()

        print("\nExporting in all formats...\n")
        self.export_csv(data)
        self.export_latex_table(data)
        self.export_markdown_table(data)
        self.export_json_raw(data)
        self.export_statistical_summary(data)

        print("\n✅ All exports complete!")
        print(f"\nFiles generated with timestamp: {self.timestamp}")


def main():
    parser = argparse.ArgumentParser(description='Export experiment data for publication')
    parser.add_argument('--format', choices=['csv', 'latex', 'markdown', 'json', 'stats', 'all'],
                       default='all', help='Export format')

    args = parser.parse_args()

    exporter = ExperimentDataExporter()

    try:
        data = exporter.fetch_metrics()

        if args.format == 'csv':
            exporter.export_csv(data)
        elif args.format == 'latex':
            exporter.export_latex_table(data)
        elif args.format == 'markdown':
            exporter.export_markdown_table(data)
        elif args.format == 'json':
            exporter.export_json_raw(data)
        elif args.format == 'stats':
            exporter.export_statistical_summary(data)
        else:  # all
            exporter.export_all()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
