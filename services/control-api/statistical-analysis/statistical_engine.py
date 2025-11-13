"""
Statistical Engine for BPC4MSA Publication Analysis
Implements rigorous statistical analysis for peer-reviewed research
"""

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from typing import Dict, List, Tuple, Any, Optional
import json
import csv
import io
from datetime import datetime
import warnings

# Suppress unnecessary warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)


class StatisticalEngine:
    """
    Comprehensive statistical analysis engine for BPC4MSA experiments.
    Provides publication-ready statistical tests and analysis.
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize the statistical engine with significance level.

        Args:
            alpha (float): Significance level for statistical tests (default: 0.05)
        """
        self.alpha = alpha
        self.confidence_level = 1 - alpha
        self.results = {
            'tests': [],
            'summary_statistics': [],
            'analysis_metadata': {}
        }
        self._initialize_metadata()

    def _initialize_metadata(self):
        """Initialize analysis metadata"""
        self.results['analysis_metadata'] = {
            'analysis_date': datetime.now().isoformat(),
            'alpha_level': self.alpha,
            'confidence_level': self.confidence_level,
            'software_version': '1.0.0',
            'analyst': 'BPC4MSA Statistical Engine'
        }

    def two_sample_t_test(self, group1: np.ndarray, group2: np.ndarray,
                         test_name: str = "Two-Sample T-Test") -> Dict[str, Any]:
        """
        Perform independent two-sample t-test with effect size and confidence intervals.

        Args:
            group1 (np.ndarray): First group data
            group2 (np.ndarray): Second group data
            test_name (str): Name for this test

        Returns:
            Dict: Comprehensive test results including statistics and effect sizes
        """
        # Input validation
        self._validate_data([group1, group2])

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(group1, group2)

        # Calculate effect size (Cohen's d)
        effect_size = self.calculate_cohens_d(group1, group2)

        # Calculate confidence interval for mean difference
        mean_diff = np.mean(group1) - np.mean(group2)
        se_diff = np.sqrt(np.var(group1, ddof=1)/len(group1) +
                         np.var(group2, ddof=1)/len(group2))
        df = len(group1) + len(group2) - 2
        t_critical = stats.t.ppf(1 - self.alpha/2, df)
        margin_error = t_critical * se_diff

        ci_lower = mean_diff - margin_error
        ci_upper = mean_diff + margin_error

        # Additional statistics
        group1_stats = self.generate_summary_statistics(group1, "Group 1")
        group2_stats = self.generate_summary_statistics(group2, "Group 2")

        result = {
            'test_name': test_name,
            'test_type': 'Two-Sample T-Test',
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'is_significant': bool(p_value < self.alpha),
            'degrees_of_freedom': df,
            'mean_difference': float(mean_diff),
            'confidence_interval': (float(ci_lower), float(ci_upper)),
            'effect_size': float(effect_size),
            'effect_size_interpretation': self._interpret_cohens_d(effect_size),
            'group1_stats': group1_stats,
            'group2_stats': group2_stats,
            'alpha': self.alpha
        }

        self.results['tests'].append(result)
        return result

    def one_way_anova(self, groups: List[np.ndarray],
                     test_name: str = "One-Way ANOVA") -> Dict[str, Any]:
        """
        Perform one-way ANOVA with effect size and post-hoc tests.

        Args:
            groups (List[np.ndarray]): List of group data arrays
            test_name (str): Name for this test

        Returns:
            Dict: Comprehensive ANOVA results
        """
        # Input validation
        self._validate_data(groups)

        if len(groups) < 2:
            raise ValueError("ANOVA requires at least 2 groups")

        # Perform ANOVA
        f_stat, p_value = stats.f_oneway(*groups)

        # Calculate effect size (eta-squared)
        effect_size = self._calculate_eta_squared(groups)

        # Generate group statistics
        group_stats = []
        for i, group in enumerate(groups):
            stats_dict = self.generate_summary_statistics(group, f"Group {i+1}")
            group_stats.append(stats_dict)

        # Perform post-hoc test if significant
        post_hoc_results = None
        if p_value < self.alpha and len(groups) > 2:
            post_hoc_results = self._perform_tukey_hsd(groups)

        result = {
            'test_name': test_name,
            'test_type': 'One-Way ANOVA',
            'f_statistic': float(f_stat),
            'p_value': float(p_value),
            'is_significant': bool(p_value < self.alpha),
            'degrees_of_freedom_between': len(groups) - 1,
            'degrees_of_freedom_within': sum(len(g) for g in groups) - len(groups),
            'effect_size': float(effect_size),
            'effect_size_interpretation': self._interpret_eta_squared(effect_size),
            'group_stats': group_stats,
            'post_hoc_test': post_hoc_results,
            'alpha': self.alpha
        }

        self.results['tests'].append(result)
        return result

    def calculate_confidence_interval(self, data: np.ndarray,
                                    confidence: float = None) -> Tuple[float, float]:
        """
        Calculate confidence interval for mean.

        Args:
            data (np.ndarray): Data array
            confidence (float): Confidence level (default: uses engine confidence level)

        Returns:
            Tuple[float, float]: (lower_bound, upper_bound)
        """
        if confidence is None:
            confidence = self.confidence_level

        if not 0 < confidence < 1:
            raise ValueError("Confidence level must be between 0 and 1")

        mean = np.mean(data)
        sem = stats.sem(data)
        df = len(data) - 1

        t_critical = stats.t.ppf((1 + confidence) / 2, df)
        margin_error = t_critical * sem

        return (mean - margin_error, mean + margin_error)

    def calculate_cohens_d(self, group1: np.ndarray, group2: np.ndarray) -> float:
        """
        Calculate Cohen's d effect size for two groups.

        Args:
            group1 (np.ndarray): First group data
            group2 (np.ndarray): Second group data

        Returns:
            float: Cohen's d effect size
        """
        mean1, mean2 = np.mean(group1), np.mean(group2)
        n1, n2 = len(group1), len(group2)

        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * np.var(group1, ddof=1) +
                             (n2 - 1) * np.var(group2, ddof=1)) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0.0

        cohens_d = (mean1 - mean2) / pooled_std
        return float(cohens_d)

    def mann_whitney_u_test(self, group1: np.ndarray, group2: np.ndarray,
                           test_name: str = "Mann-Whitney U Test") -> Dict[str, Any]:
        """
        Perform Mann-Whitney U test (non-parametric alternative to t-test).

        Args:
            group1 (np.ndarray): First group data
            group2 (np.ndarray): Second group data
            test_name (str): Name for this test

        Returns:
            Dict: Test results
        """
        self._validate_data([group1, group2])

        u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')

        result = {
            'test_name': test_name,
            'test_type': 'Mann-Whitney U Test',
            'u_statistic': float(u_stat),
            'p_value': float(p_value),
            'is_significant': bool(p_value < self.alpha),
            'group1_median': float(np.median(group1)),
            'group2_median': float(np.median(group2)),
            'alpha': self.alpha
        }

        self.results['tests'].append(result)
        return result

    def levenes_test(self, groups: List[np.ndarray]) -> Dict[str, Any]:
        """
        Perform Levene's test for equality of variances.

        Args:
            groups (List[np.ndarray]): List of group data arrays

        Returns:
            Dict: Test results
        """
        self._validate_data(groups)

        w_stat, p_value = stats.levene(*groups)

        result = {
            'test_name': "Levene's Test for Equal Variances",
            'test_type': 'Levene Test',
            'w_statistic': float(w_stat),
            'p_value': float(p_value),
            'equal_variances': bool(p_value >= self.alpha),
            'alpha': self.alpha
        }

        self.results['tests'].append(result)
        return result

    def shapiro_wilk_test(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Perform Shapiro-Wilk test for normality.

        Args:
            data (np.ndarray): Data array to test for normality

        Returns:
            Dict: Test results
        """
        if len(data) < 3:
            raise ValueError("Shapiro-Wilk test requires at least 3 data points")

        w_stat, p_value = stats.shapiro(data)

        result = {
            'test_name': "Shapiro-Wilk Normality Test",
            'test_type': 'Normality Test',
            'w_statistic': float(w_stat),
            'p_value': float(p_value),
            'is_normal': bool(p_value >= self.alpha),
            'sample_size': len(data),
            'alpha': self.alpha
        }

        self.results['tests'].append(result)
        return result

    def bonferroni_correction(self, p_values: List[float]) -> List[float]:
        """
        Apply Bonferroni correction for multiple comparisons.

        Args:
            p_values (List[float]): List of p-values to correct

        Returns:
            List[float]: Corrected p-values
        """
        if not p_values:
            return []

        n_tests = len(p_values)
        corrected = [min(p * n_tests, 1.0) for p in p_values]
        return corrected

    def generate_summary_statistics(self, data: np.ndarray, name: str = "Data") -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics.

        Args:
            data (np.ndarray): Data array
            name (str): Name for the dataset

        Returns:
            Dict: Summary statistics
        """
        if len(data) == 0:
            raise ValueError("Cannot generate statistics for empty data")

        q75, q25 = np.percentile(data, [75, 25])

        stats_dict = {
            'name': name,
            'n': len(data),
            'mean': float(np.mean(data)),
            'std': float(np.std(data, ddof=1)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'median': float(np.median(data)),
            'q25': float(q25),
            'q75': float(q75),
            'iqr': float(q75 - q25),
            'skewness': float(stats.skew(data)),
            'kurtosis': float(stats.kurtosis(data)),
            'cv': float(np.std(data, ddof=1) / np.mean(data)) if np.mean(data) != 0 else float('inf')
        }

        # Store in results
        self.results['summary_statistics'].append(stats_dict)

        return stats_dict

    def export_results_to_json(self) -> Dict[str, Any]:
        """
        Export all results to JSON format for analysis and reporting.

        Returns:
            Dict: Complete results in JSON-serializable format
        """
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj

        return convert_numpy_types(self.results)

    def export_results_to_csv(self) -> str:
        """
        Export test results to CSV format.

        Returns:
            str: CSV content as string
        """
        output = io.StringIO()

        if not self.results['tests']:
            return "No test results to export"

        # Define CSV columns
        fieldnames = [
            'test_name', 'test_type', 'p_value', 'is_significant',
            'effect_size', 'alpha', 'analysis_date'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for test in self.results['tests']:
            row = {
                'test_name': test.get('test_name', ''),
                'test_type': test.get('test_type', ''),
                'p_value': test.get('p_value', ''),
                'is_significant': test.get('is_significant', ''),
                'effect_size': test.get('effect_size', ''),
                'alpha': test.get('alpha', self.alpha),
                'analysis_date': self.results['analysis_metadata']['analysis_date']
            }
            writer.writerow(row)

        return output.getvalue()

    def clear_results(self):
        """Clear all stored results"""
        self.results = {
            'tests': [],
            'summary_statistics': [],
            'analysis_metadata': {}
        }
        self._initialize_metadata()

    # Private helper methods

    def _validate_data(self, data_groups: List[np.ndarray]):
        """Validate input data for statistical tests"""
        for i, data in enumerate(data_groups):
            if len(data) == 0:
                raise ValueError(f"Group {i+1} is empty")
            if len(data) < 2:
                raise ValueError(f"Group {i+1} has fewer than 2 data points")

    def _calculate_eta_squared(self, groups: List[np.ndarray]) -> float:
        """Calculate eta-squared effect size for ANOVA"""
        all_data = np.concatenate(groups)
        grand_mean = np.mean(all_data)

        # Between-group sum of squares
        ss_between = sum(len(group) * (np.mean(group) - grand_mean)**2 for group in groups)

        # Total sum of squares
        ss_total = sum((x - grand_mean)**2 for x in all_data)

        if ss_total == 0:
            return 0.0

        eta_squared = ss_between / ss_total
        return float(eta_squared)

    def _perform_tukey_hsd(self, groups: List[np.ndarray]) -> Dict[str, Any]:
        """Perform Tukey's HSD post-hoc test"""
        # Create data for Tukey test
        group_labels = []
        data_for_tukey = []

        for i, group in enumerate(groups):
            group_labels.extend([f'Group_{i+1}'] * len(group))
            data_for_tukey.extend(group)

        tukey_result = pairwise_tukeyhsd(data_for_tukey, group_labels, alpha=self.alpha)

        return {
            'test_type': "Tukey HSD",
            'significant_comparisons': int(np.any(tukey_result.reject)),
            'comparisons': [
                {
                    'group1': comp[0],
                    'group2': comp[1],
                    'mean_difference': float(comp[2]),
                    'p_value': float(comp[3]),
                    'is_significant': bool(comp[4]),
                    'confidence_interval': (float(comp[5]), float(comp[6]))
                }
                for comp in tukey_result._results_table.data[1:]
            ]
        }

    def _interpret_cohens_d(self, effect_size: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_effect = abs(effect_size)
        if abs_effect < 0.2:
            return "Negligible"
        elif abs_effect < 0.5:
            return "Small"
        elif abs_effect < 0.8:
            return "Medium"
        else:
            return "Large"

    def _interpret_eta_squared(self, eta_squared: float) -> str:
        """Interpret eta-squared effect size"""
        if eta_squared < 0.01:
            return "Negligible"
        elif eta_squared < 0.06:
            return "Small"
        elif eta_squared < 0.14:
            return "Medium"
        else:
            return "Large"