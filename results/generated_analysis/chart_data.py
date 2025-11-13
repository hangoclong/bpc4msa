
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# --- Aggregated Data for Visualization ---
# This data is generated from the experimental analysis script.
# Mean and Standard Deviation are calculated from the valid high-load runs.

data = {
    'Architecture': ['bpc4msa', 'monolithic', 'synchronous'],
    'Mean Throughput': [17657.29, 14634.84, 14401.04],
    'Std Dev Throughput': [1504.7232303649732, 3906.764966055675, 2746.7987179260153],
    'Mean Latency': [64.755, 3.125, 3.125],
    'Std Dev Latency': [81.83346778671915, 1.1384419177103418, 0.8131727983645299]
}

df = pd.DataFrame(data)

# --- Chart Generation Code ---
# Instructions:
# 1. Make sure you have a Python environment (venv recommended).
# 2. Install libraries: pip install pandas seaborn matplotlib
# 3. Run this script.

def generate_charts():
    '''Generates and saves publication-quality charts.'''
    
    # Set aesthetic style of the plots
    sns.set_theme(style="whitegrid")
    output_dir = 'generated_analysis'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- Chart 1: Throughput Comparison ---
    plt.figure(figsize=(10, 6))
    ax1 = sns.barplot(
        x='Architecture', 
        y='Mean Throughput',
        data=df, 
        capsize=.1, 
        palette='viridis'
    )
    
    # Add error bars
    ax1.errorbar(
        x=df.index, 
        y=df['Mean Throughput'], 
        yerr=df['Std Dev Throughput'], 
        fmt='none', 
        c='black', 
        capsize=5
    )

    ax1.set_title('Architectural Throughput Comparison (Mean ± SD)', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Throughput (requests/minute)', fontsize=12)
    ax1.set_xlabel('Architecture', fontsize=12)
    ax1.tick_params(axis='x', rotation=0)
    plt.tight_layout()
    throughput_chart_path = os.path.join(output_dir, 'throughput_comparison_chart.png')
    plt.savefig(throughput_chart_path, dpi=300)
    print(f"Saved throughput chart to {throughput_chart_path}")

    # --- Chart 2: Latency Comparison ---
    plt.figure(figsize=(10, 6))
    ax2 = sns.barplot(
        x='Architecture', 
        y='Mean Latency',
        data=df, 
        capsize=.1, 
        palette='plasma'
    )

    # Add error bars
    ax2.errorbar(
        x=df.index, 
        y=df['Mean Latency'], 
        yerr=df['Std Dev Latency'], 
        fmt='none', 
        c='black', 
        capsize=5
    )
    
    ax2.set_title('Architectural Latency Comparison (Mean ± SD)', fontsize=16, fontweight="bold")
    ax2.set_ylabel('Average Latency (ms)', fontsize=12)
    ax2.set_xlabel('Architecture', fontsize=12)
    ax2.tick_params(axis='x', rotation=0)
    plt.tight_layout()
    latency_chart_path = os.path.join(output_dir, 'latency_comparison_chart.png')
    plt.savefig(latency_chart_path, dpi=300)
    print(f"Saved latency chart to {latency_chart_path}")

if __name__ == '__main__':
    generate_charts()
