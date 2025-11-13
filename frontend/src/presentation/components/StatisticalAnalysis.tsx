/**
 * PRESENTATION LAYER - Statistical Analysis Component
 * Publication-ready statistical testing and analysis (FR-2)
 * Enhanced with Robust Statistical Methods and Data Quality Analysis
 */

'use client';

import { useState } from 'react';
import { BarChart3, Download, AlertCircle, CheckCircle, Shield, FlaskConical, Info } from 'lucide-react';

// --- TYPE DEFINITIONS ---

interface GroupStats {
  name: string;
  n: number;
  mean: number;
  std: number;
  min: number;
  max: number;
  median: number;
  q25: number;
  q75: number;
  iqr: number;
  skewness: number;
  kurtosis: number;
  cv: number;
}

interface PostHocComparison {
  group1: string;
  group2: string;
  mean_difference: number;
  p_value: number;
  is_significant: boolean;
  confidence_interval: [number, number];
}

interface PostHocTest {
  test_type: string;
  significant_comparisons: number;
  comparisons: PostHocComparison[];
}

interface OutlierAnalysis {
  architecture: string;
  raw_n: number;
  outliers_detected: boolean;
  outlier_count: number;
  outliers: number[];
  cleaned_n: number;
  robust_median: number;
  robust_iqr: number;
  trimmed_mean: number;
}

interface DataQuality {
  outlier_analysis: OutlierAnalysis[];
  recommendation: string;
  method: string;
  note: string;
}

interface RobustAnalysis {
  test_name: string;
  test_type: string;
  p_value: number;
  is_significant: boolean;
  u_statistic?: number;
  f_statistic?: number;
  w_statistic?: number;
  equal_variances?: boolean;
  group1_median?: number;
  group2_median?: number;
  alpha: number;
  group_stats?: GroupStats[];
  post_hoc_test?: PostHocTest;
}

interface StatisticalTestResult {
  test_name: string;
  test_type: string;
  p_value: number;
  is_significant?: boolean;
  effect_size?: number | null;
  effect_size_interpretation?: string;
  confidence_interval?: number[];
  group_stats?: GroupStats[];
  alpha: number;
  analysis_metadata: {
    architectures: string[];
    metric: string;
    sample_sizes: number[];
    sample_sizes_after_outlier_removal?: number[];
    analysis_date: string;
    alpha_level: number;
  };
  robust_analysis?: RobustAnalysis;
  data_quality?: DataQuality;
  t_statistic?: number;
  f_statistic?: number;
  u_statistic?: number;
  w_statistic?: number;
  equal_variances?: boolean;
  post_hoc_test?: PostHocTest;
}

// --- CONTENT CONSTANTS ---

const tabExplanations = {
  results: {
    title: "Raw Analysis",
    what: "This tab shows the direct results of the statistical test you explicitly selected (e.g., the T-test).",
    purpose: "It provides the standard, baseline analysis. However, this type of analysis can be sensitive to extreme values (outliers) in your data.",
    color: "blue"
  },
  robust: {
    title: "Robust Analysis (Recommended)",
    what: "When you run a test, the system also runs a more advanced, \"robust\" analysis in the background (e.g., a Mann-Whitney U test as the alternative to a T-test). This tab shows the results of that robust test.",
    purpose: "Robust tests are much less affected by outliers. For academic publication, if your data is not perfectly 'clean', reviewers will expect you to use and report the results from these more advanced, robust methods. This tab is your primary source for drawing reliable conclusions.",
    color: "green"
  },
  quality: {
    title: "Data Quality",
    what: "This tab is a diagnostic report on your data itself. It shows you if outliers were detected, how many were found in each group, and what their values were.",
    purpose: "It provides transparency. It proves to you (and to reviewers) that the analysis is not hiding problematic data. It justifies why a robust analysis might be necessary.",
    color: "purple"
  },
  interpretation: {
    title: "Interpretation",
    what: "This tab translates the complex statistical numbers into a plain-English conclusion suitable for your research paper.",
    purpose: "It helps you understand and report your findings, explaining what the p-value and effect size mean in the context of your experiment.",
    color: "indigo"
  }
};

// --- UI COMPONENTS ---

const InfoBox = ({ title, what, purpose, color }: { title: string, what: string, purpose: string, color: string }) => (
  <div className={`mb-6 bg-${color}-50 border-l-4 border-${color}-400 text-${color}-800 p-4`} role="alert">
    <p className="font-bold">{title}</p>
    <p><b>What it is:</b> {what}</p>
    <p><b>Purpose:</b> {purpose}</p>
  </div>
);

export function StatisticalAnalysis() {
  const [testResult, setTestResult] = useState<StatisticalTestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'results' | 'robust' | 'quality' | 'interpretation'>('results');

  const [selectedTest, setSelectedTest] = useState('t_test');
  const [selectedMetric, setSelectedMetric] = useState('latency');
  const [selectedArchitectures, setSelectedArchitectures] = useState<string[]>(['bpc4msa', 'synchronous']);

  const testTypes = [
    { value: 't_test', label: 'T-Test (2 groups)', minGroups: 2, maxGroups: 2, description: 'Parametric test comparing means of two groups' },
    { value: 'anova', label: 'ANOVA (3 groups)', minGroups: 3, maxGroups: 3, description: 'Compare means across three groups' },
    { value: 'mann_whitney', label: 'Mann-Whitney U (non-parametric)', minGroups: 2, maxGroups: 2, description: 'Non-parametric alternative to t-test' },
    { value: 'levene', label: "Levene's Test (variance equality)", minGroups: 2, maxGroups: 3, description: 'Test for equal variances across groups' }
  ];

  const metrics = [
    { value: 'latency', label: 'Average Latency (ms)', description: 'Response time from request to completion' },
    { value: 'throughput', label: 'Throughput (transactions)', description: 'Number of transactions processed per unit time' },
    { value: 'violations', label: 'Violation Count', description: 'Compliance violations detected' }
  ];

  const architectures = [
    { value: 'bpc4msa', label: 'BPC4MSA', color: 'blue' },
    { value: 'synchronous', label: 'Synchronous SOA', color: 'green' },
    { value: 'monolithic', label: 'Monolithic BPMS', color: 'purple' }
  ];

  const runStatisticalTest = async () => {
    setLoading(true);
    setError(null);
    setTestResult(null);

    try {
      const response = await fetch('http://localhost:8080/api/statistics/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          test_type: selectedTest,
          architectures: selectedArchitectures,
          metric: selectedMetric,
          alpha: 0.05
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Statistical test failed');
      }

      const result: StatisticalTestResult = await response.json();
      setTestResult(result);
      if (result.data_quality?.outlier_analysis.some(a => a.outliers_detected)) {
        setActiveTab('robust');
      } else {
        setActiveTab('results');
      }
    } catch (err: unknown) {
      const error = err as Error;
      setError(error.message || 'Failed to perform statistical test');
    } finally {
      setLoading(false);
    }
  };

  const exportResults = async (format: 'csv' | 'latex') => {
    if (!testResult) return;

    if (format === 'csv') {
      const rows = [
        ['Metric', 'Raw Analysis', 'Robust Analysis'],
        ['Test Type', testResult.test_type, testResult.robust_analysis?.test_type || 'N/A'],
        ['P-Value', testResult.p_value.toFixed(6), testResult.robust_analysis?.p_value.toFixed(6) || 'N/A'],
        ['Significant', testResult.is_significant ? 'Yes' : 'No', testResult.robust_analysis?.is_significant ? 'Yes' : 'No'],
        ['Effect Size', testResult.effect_size?.toFixed(4) || 'N/A', 'N/A'],
        ['Sample Sizes', testResult.analysis_metadata.sample_sizes.join(', '), testResult.analysis_metadata.sample_sizes_after_outlier_removal?.join(', ') || 'N/A'],
        ['Outliers Detected', testResult.data_quality?.outlier_analysis.map(a => `${a.architecture}: ${a.outlier_count}`).join('; ') || 'N/A', '']
      ];

      const csv = rows.map(row => row.join(',')).join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `statistical_analysis_${testResult.test_type}_${Date.now()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === 'latex') {
      const robustPValue = testResult.robust_analysis?.p_value.toFixed(4) || 'N/A';
      const latex = `
\begin{table}[ht]
\centering
\caption{Statistical Analysis: ${testResult.test_name}}
\begin{tabular}{lll}
\hline
\textbf{Metric} & \textbf{Raw Analysis} & \textbf{Robust Analysis} \\
\hline
Test Type & ${testResult.test_type} & ${testResult.robust_analysis?.test_type || 'N/A'} \\
P-Value & ${testResult.p_value.toFixed(4)}${testResult.is_significant ? '*' : ''} & ${robustPValue}${testResult.robust_analysis?.is_significant ? '*' : ''} \\
Sample Sizes & ${testResult.analysis_metadata.sample_sizes.join(', ')} & ${testResult.analysis_metadata.sample_sizes_after_outlier_removal?.join(', ') || 'N/A'} \\
\hline
\end{tabular}
\[0.5em]
${testResult.robust_analysis?.is_significant ? '* Statistically significant at $\alpha = 0.05$' : ''}
\[0.5em]
\footnotesize{Robust analysis uses Tukey\'s Fences for outlier detection and non-parametric tests.}
\label{tab:statistical_analysis}
\end{table}
`.trim();

      const blob = new Blob([latex], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `statistical_analysis_${testResult.test_type}_${Date.now()}.tex`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleArchitectureToggle = (arch: string) => {
    if (selectedArchitectures.includes(arch)) {
      setSelectedArchitectures(selectedArchitectures.filter(a => a !== arch));
    } else {
      setSelectedArchitectures([...selectedArchitectures, arch]);
    }
  };

  const currentTestConfig = testTypes.find(t => t.value === selectedTest);
  const isValidSelection = selectedArchitectures.length >= (currentTestConfig?.minGroups || 2) &&
                          selectedArchitectures.length <= (currentTestConfig?.maxGroups || 3);

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Publication-Ready Statistical Analysis</h2>
            <p className="text-sm text-gray-700">
              Rigorous statistical testing with robust methods for outlier detection.
              Results include both raw and outlier-adjusted analyses following scientific best practices.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">Configure Statistical Test</h3>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Statistical Test Type</label>
          <select
            value={selectedTest}
            onChange={(e) => setSelectedTest(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
          >
            {testTypes.map((test) => (
              <option key={test.value} value={test.value}>{test.label}</option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            {currentTestConfig?.description} • Select {currentTestConfig?.minGroups} to {currentTestConfig?.maxGroups} architecture(s)
          </p>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Architectures to Compare</label>
          <div className="grid grid-cols-3 gap-3">
            {architectures.map((arch) => (
              <button
                key={arch.value}
                onClick={() => handleArchitectureToggle(arch.value)}
                className={`px-4 py-3 rounded-lg border-2 transition-all text-sm font-medium ${selectedArchitectures.includes(arch.value) ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'}`}
              >
                {arch.label}
              </button>
            ))}
          </div>
          {!isValidSelection && (
            <p className="text-xs text-red-600 mt-2">
              ⚠️ Please select exactly {currentTestConfig?.minGroups} to {currentTestConfig?.maxGroups} architecture(s)
            </p>
          )}
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Performance Metric</label>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
          >
            {metrics.map((metric) => (
              <option key={metric.value} value={metric.value}>{metric.label}</option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">{metrics.find(m => m.value === selectedMetric)?.description}</p>
        </div>

        <button
          onClick={runStatisticalTest}
          disabled={loading || !isValidSelection}
          className={`w-full px-6 py-3 rounded-lg font-medium transition-all ${loading || !isValidSelection ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow-md'}`}
        >
          {loading ? 'Running Statistical Test...' : 'Run Statistical Test'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-red-900">Test Failed</h4>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {testResult && (
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="border-b border-gray-200">
            <div className="flex">
              <button onClick={() => setActiveTab('results')} className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'results' ? 'border-b-2 border-blue-600 text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}>
                <div className="flex items-center justify-center gap-2"><BarChart3 className="w-4 h-4" />Raw Analysis</div>
              </button>
              <button onClick={() => setActiveTab('robust')} className={`flex-1 px-6 py-3 text-sm font-medium transition-colors relative ${activeTab === 'robust' ? 'border-b-2 border-green-600 text-green-600 bg-green-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}>
                <div className="flex items-center justify-center gap-2">
                  <Shield className="w-4 h-4" />
                  Robust Analysis
                  {testResult.data_quality?.outlier_analysis.some(a => a.outliers_detected) && (
                    <span className="absolute top-1 right-1 w-2 h-2 bg-orange-500 rounded-full"></span>
                  )}
                </div>
              </button>
              <button onClick={() => setActiveTab('quality')} className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'quality' ? 'border-b-2 border-purple-600 text-purple-600 bg-purple-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}>
                <div className="flex items-center justify-center gap-2"><FlaskConical className="w-4 h-4" />Data Quality</div>
              </button>
              <button onClick={() => setActiveTab('interpretation')} className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'interpretation' ? 'border-b-2 border-indigo-600 text-indigo-600 bg-indigo-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}>
                <div className="flex items-center justify-center gap-2"><Info className="w-4 h-4" />Interpretation</div>
              </button>
            </div>
          </div>

          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">
                {activeTab === 'results' && 'Raw Analysis Results'}
                {activeTab === 'robust' && 'Robust Analysis (Recommended)'}
                {activeTab === 'quality' && 'Data Quality Assessment'}
                {activeTab === 'interpretation' && 'Scientific Interpretation'}
              </h3>
              <div className="flex gap-2">
                <button onClick={() => exportResults('csv')} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium flex items-center gap-2"><Download className="w-4 h-4" />Export CSV</button>
                <button onClick={() => exportResults('latex')} className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium flex items-center gap-2"><Download className="w-4 h-4" />Export LaTeX</button>
              </div>
            </div>

            {activeTab === 'results' && (
              <div className="space-y-6">
                <InfoBox {...tabExplanations.results} />
                <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${testResult.is_significant ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-gray-100 text-gray-700 border border-gray-200'}`}>
                  {testResult.is_significant ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                  <span className="font-semibold">{testResult.is_significant ? `Statistically Significant (p < ${testResult.alpha})` : 'Not Statistically Significant'}</span>
                </div>

                {testResult.data_quality?.outlier_analysis.some(a => a.outliers_detected) && (
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-orange-900">Outliers Detected</h4>
                      <p className="text-sm text-orange-700">This analysis includes outliers. Check the <button onClick={() => setActiveTab('robust')} className="underline font-medium">Robust Analysis</button> tab for outlier-adjusted results.</p>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div><label className="text-sm text-gray-600 font-medium">Test Name</label><p className="text-lg font-semibold text-gray-900">{testResult.test_name}</p></div>
                    <div><label className="text-sm text-gray-600 font-medium">P-Value</label><p className="text-2xl font-bold text-blue-600">{testResult.p_value < 0.001 ? '< 0.001' : testResult.p_value.toFixed(6)}</p></div>
                    {testResult.effect_size !== null && testResult.effect_size !== undefined && (<div><label className="text-sm text-gray-600 font-medium">Effect Size</label><p className="text-2xl font-bold text-purple-600">{testResult.effect_size.toFixed(4)}</p><p className="text-sm text-gray-600 mt-1">{testResult.effect_size_interpretation}</p></div>)}
                  </div>
                  <div className="space-y-4">
                    <div><label className="text-sm text-gray-600 font-medium">Sample Sizes</label><p className="text-lg font-semibold text-gray-900">{testResult.analysis_metadata.sample_sizes.join(', ')}</p></div>
                    <div><label className="text-sm text-gray-600 font-medium">Significance Level (α)</label><p className="text-lg font-semibold text-gray-900">{testResult.alpha}</p></div>
                    {testResult.confidence_interval && (<div><label className="text-sm text-gray-600 font-medium">95% Confidence Interval</label><p className="text-lg font-semibold text-gray-900">[{testResult.confidence_interval[0].toFixed(2)}, {testResult.confidence_interval[1].toFixed(2)}]</p></div>)}
                  </div>
                </div>

                {(testResult.t_statistic || testResult.f_statistic || testResult.u_statistic || testResult.w_statistic) && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-2">Test Statistics</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {testResult.t_statistic && (<div><span className="text-gray-600">T-statistic:</span><span className="ml-2 font-semibold">{testResult.t_statistic.toFixed(4)}</span></div>)}
                      {testResult.f_statistic && (<div><span className="text-gray-600">F-statistic:</span><span className="ml-2 font-semibold">{testResult.f_statistic.toFixed(4)}</span></div>)}
                      {testResult.u_statistic && (<div><span className="text-gray-600">U-statistic:</span><span className="ml-2 font-semibold">{testResult.u_statistic.toFixed(2)}</span></div>)}
                      {testResult.w_statistic && (<div><span className="text-gray-600">W-statistic:</span><span className="ml-2 font-semibold">{testResult.w_statistic.toFixed(4)}</span></div>)}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'robust' && testResult.robust_analysis && (
              <div className="space-y-6">
                <InfoBox {...tabExplanations.robust} />
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                  <Shield className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-green-900">Recommended for Publication</h4>
                    <p className="text-sm text-green-700">{testResult.data_quality?.recommendation}</p>
                    <p className="text-xs text-green-600 mt-1">Method: {testResult.data_quality?.method}</p>
                  </div>
                </div>

                <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${testResult.robust_analysis.is_significant ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-gray-100 text-gray-700 border border-gray-200'}`}>
                  {testResult.robust_analysis.is_significant ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                  <span className="font-semibold">{testResult.robust_analysis.is_significant ? 'Statistically Significant (Robust Analysis)' : 'Not Statistically Significant (Robust Analysis)'}</span>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div><label className="text-sm text-green-700 font-medium">Test Type (Robust)</label><p className="text-lg font-semibold text-gray-900">{testResult.robust_analysis.test_type}</p><p className="text-xs text-gray-600">Non-parametric method resistant to outliers</p></div>
                    <div><label className="text-sm text-green-700 font-medium">P-Value (Robust)</label><p className="text-3xl font-bold text-green-600">{testResult.robust_analysis.p_value < 0.000001 ? '< 0.000001' : testResult.robust_analysis.p_value.toFixed(6)}</p></div>
                  </div>
                  <div className="space-y-4">
                    <div><label className="text-sm text-green-700 font-medium">Sample Sizes (After Outlier Removal)</label><p className="text-lg font-semibold text-gray-900">{testResult.analysis_metadata.sample_sizes_after_outlier_removal?.join(', ') || 'N/A'}</p></div>
                    {(testResult.robust_analysis.group1_median !== undefined && testResult.robust_analysis.group2_median !== undefined) && (<div><label className="text-sm text-green-700 font-medium">Median Comparison</label><p className="text-lg font-semibold text-gray-900">{testResult.robust_analysis.group1_median.toFixed(2)} ms vs {testResult.robust_analysis.group2_median.toFixed(2)} ms</p></div>)}
                  </div>
                </div>

                {(testResult.robust_analysis.u_statistic || testResult.robust_analysis.f_statistic || testResult.robust_analysis.w_statistic) && (
                  <div className="mt-4 p-4 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-900 mb-2">Robust Test Statistics</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {testResult.robust_analysis.u_statistic && (<div><span className="text-green-700">U-statistic:</span><span className="ml-2 font-semibold text-gray-900">{testResult.robust_analysis.u_statistic.toFixed(2)}</span></div>)}
                      {testResult.robust_analysis.f_statistic && (<div><span className="text-green-700">F-statistic:</span><span className="ml-2 font-semibold text-gray-900">{testResult.robust_analysis.f_statistic.toFixed(4)}</span></div>)}
                      {testResult.robust_analysis.w_statistic && (<div><span className="text-green-700">W-statistic:</span><span className="ml-2 font-semibold text-gray-900">{testResult.robust_analysis.w_statistic.toFixed(4)}</span></div>)}
                      {testResult.robust_analysis.equal_variances !== undefined && (<div><span className="text-green-700">Equal Variances:</span><span className="ml-2 font-semibold text-gray-900">{testResult.robust_analysis.equal_variances ? 'Yes' : 'No'}</span></div>)}
                    </div>
                  </div>
                )}

                {testResult.robust_analysis.post_hoc_test && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-3">Post-Hoc Analysis (Tukey HSD)</h4>
                    <div className="space-y-2">
                      {testResult.robust_analysis.post_hoc_test.comparisons?.map((comp: PostHocComparison, idx: number) => (
                        <div key={idx} className="flex items-center justify-between text-sm p-2 bg-white rounded">
                          <span className="font-medium">{comp.group1} vs {comp.group2}</span>
                          <div className="flex items-center gap-4">
                            <span className="text-gray-600">p = {comp.p_value.toFixed(4)}</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${comp.is_significant ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>{comp.is_significant ? 'Significant' : 'Not Significant'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'quality' && testResult.data_quality && (
              <div className="space-y-6">
                <InfoBox {...tabExplanations.quality} />
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h4 className="font-semibold text-purple-900 mb-2">Data Quality Assessment</h4>
                  <p className="text-sm text-purple-700">Outliers detected using <strong>{testResult.data_quality.method}</strong>. This is a scientifically robust method that identifies extreme values without bias.</p>
                </div>

                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900">Outlier Detection Results</h4>
                  {testResult.data_quality.outlier_analysis.map((arch) => (
                    <div key={arch.architecture} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h5 className="font-semibold text-lg text-gray-900">{arch.architecture.toUpperCase()}</h5>
                        {arch.outliers_detected && (<span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">{arch.outlier_count} outliers detected</span>)}
                      </div>

                      <div className="grid grid-cols-3 gap-4 mb-3">
                        <div><label className="text-xs text-gray-600">Raw Sample Size</label><p className="text-lg font-semibold text-gray-900">{arch.raw_n}</p></div>
                        <div><label className="text-xs text-gray-600">Clean Sample Size</label><p className="text-lg font-semibold text-green-700">{arch.cleaned_n}</p></div>
                        <div><label className="text-xs text-gray-600">Outliers Removed</label><p className="text-lg font-semibold text-orange-600">{arch.outlier_count}</p></div>
                      </div>

                      <div className="grid grid-cols-3 gap-4 p-3 bg-gray-50 rounded">
                        <div><label className="text-xs text-gray-600">Robust Median</label><p className="text-sm font-semibold text-gray-900">{arch.robust_median.toFixed(2)} ms</p></div>
                        <div><label className="text-xs text-gray-600">IQR (Spread)</label><p className="text-sm font-semibold text-gray-900">{arch.robust_iqr.toFixed(2)} ms</p></div>
                        <div><label className="text-xs text-gray-600">Trimmed Mean (10%)</label><p className="text-sm font-semibold text-gray-900">{arch.trimmed_mean.toFixed(2)} ms</p></div>
                      </div>

                      {arch.outliers_detected && arch.outliers.length > 0 && (
                        <div className="mt-3 p-3 bg-orange-50 rounded">
                          <label className="text-xs text-orange-800 font-medium">Outlier Values (ms):</label>
                          <p className="text-sm text-orange-900 mt-1">{arch.outliers.slice(0, 10).map(v => v.toFixed(1)).join(', ')}{arch.outliers.length > 10 && ` ... and ${arch.outliers.length - 10} more`}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-900 mb-2">📊 Scientific Transparency</h4>
                  <p className="text-sm text-blue-700">{testResult.data_quality.note}</p>
                  <p className="text-xs text-blue-600 mt-2">All outliers are reported, not hidden. Both raw and robust analyses are provided for complete transparency.</p>
                </div>
              </div>
            )}

            {activeTab === 'interpretation' && (
              <div className="space-y-6">
                <InfoBox {...tabExplanations.interpretation} />
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
                  <h4 className="font-semibold text-indigo-900 mb-3 flex items-center gap-2"><CheckCircle className="w-5 h-5" />Research Conclusion</h4>
                  <p className="text-gray-800 leading-relaxed">
                    Based on the {testResult.robust_analysis ? 'robust ' + testResult.robust_analysis.test_type.toLowerCase() : testResult.test_type.toLowerCase()},
                    the difference in {testResult.analysis_metadata.metric} between {testResult.analysis_metadata.architectures.join(' and ')} is
                    <strong className={testResult.robust_analysis?.is_significant ? 'text-green-700' : 'text-gray-700'}>
                      {testResult.robust_analysis?.is_significant ? ' statistically significant' : ' not statistically significant'}
                    </strong> (p {testResult.robust_analysis ? '< 0.000001' : `= ${testResult.p_value.toFixed(4)}`}).
                    {testResult.effect_size && testResult.effect_size_interpretation && (<span> The effect size is {testResult.effect_size_interpretation.toLowerCase()}, indicating a {testResult.robust_analysis?.is_significant ? 'meaningful' : 'negligible'} difference in performance.</span>)}
                  </p>
                </div>

                <div className="space-y-3">
                  <h4 className="font-semibold text-gray-900">P-Value Interpretation</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <p className="font-medium text-blue-900 mb-1">What is P-Value?</p>
                      <p className="text-sm text-blue-700">Probability of observing this difference by chance if there were no real difference. Lower values indicate stronger evidence.</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <p className="font-medium text-green-900 mb-1">Current Result:</p>
                      <p className="text-sm text-green-700">
                        {testResult.robust_analysis && testResult.robust_analysis.p_value < 0.000001 && 'Extremely strong evidence (p < 0.000001)'}
                        {testResult.p_value < 0.001 && testResult.p_value >= 0.000001 && 'Very strong evidence (p < 0.001)'}
                        {testResult.p_value >= 0.001 && testResult.p_value < 0.01 && 'Strong evidence (p < 0.01)'}
                        {testResult.p_value >= 0.01 && testResult.p_value < 0.05 && 'Moderate evidence (p < 0.05)'}
                        {testResult.p_value >= 0.05 && 'Insufficient evidence (p ≥ 0.05)'}
                      </p>
                    </div>
                  </div>
                </div>

                {testResult.effect_size !== null && testResult.effect_size !== undefined && (
                  <div className="space-y-3">
                    <h4 className="font-semibold text-gray-900">Effect Size Guide (Cohen&apos;s d)</h4>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3"><div className="w-24 text-sm font-medium text-gray-600">Small (0.2)</div><div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden"><div className="h-full bg-blue-300" style={{width: '20%'}}></div></div></div>
                      <div className="flex items-center gap-3"><div className="w-24 text-sm font-medium text-gray-600">Medium (0.5)</div><div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden"><div className="h-full bg-blue-400" style={{width: '50%'}}></div></div></div>
                      <div className="flex items-center gap-3"><div className="w-24 text-sm font-medium text-gray-600">Large (0.8+)</div><div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden"><div className="h-full bg-blue-600" style={{width: '80%'}}></div></div></div>
                      <p className="text-sm text-gray-600 mt-2">Your effect size: <strong>{testResult.effect_size.toFixed(4)}</strong> ({testResult.effect_size_interpretation})</p>
                    </div>
                  </div>
                )}

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h4 className="font-semibold text-yellow-900 mb-2">📊 Methodology</h4>
                  <ul className="text-sm text-yellow-800 space-y-1">
                    <li>• <strong>Significance Level:</strong> α = 0.05 (5% false positive rate)</li>
                    <li>• <strong>Outlier Detection:</strong> Tukey&apos;s Fences (Q1 - 1.5×IQR, Q3 + 1.5×IQR)</li>
                    <li>• <strong>Robust Analysis:</strong> Uses non-parametric tests resistant to outliers</li>
                    <li>• <strong>Transparency:</strong> Both raw and outlier-adjusted results provided</li>
                  </ul>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h4 className="font-semibold text-purple-900 mb-2">📝 For Academic Publication</h4>
                  <ul className="text-sm text-purple-700 space-y-1">
                    <li>• Report both raw and robust analyses for transparency</li>
                    <li>• Include sample sizes before and after outlier removal</li>
                    <li>• Cite the outlier detection method (Tukey, 1977)</li>
                    <li>• Export results to LaTeX for direct inclusion in papers</li>
                    <li>• Include confidence intervals when available</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
