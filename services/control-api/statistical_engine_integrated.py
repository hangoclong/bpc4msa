"""
Integrated Statistical Analysis Engine for Control API
Simplified version for Docker deployment
"""

import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import pandas as pd
import json
import csv
import io
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class StatisticalEngine:
    """
    Comprehensive Statistical Analysis Engine for BPC4MSA Experiments
    Provides publication-ready statistical analysis with effect sizes and confidence intervals
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize statistical engine

        Args:
            alpha: Significance level for hypothesis tests (default 0.05)
        """
        self.alpha = alpha
        self.results = []
        logger.info(f"Statistical Engine initialized with alpha={alpha}")

    def two_sample_t_test(self, group1: np.ndarray, group2: np.ndarray, test_name: str) -> Dict[str, Any]:
        """
        Perform two-sample t-test with effect size and confidence interval

        Args:
            group1: First group data
            group2: Second group data
            test_name: Name of the test for identification

        Returns:
            Dictionary with comprehensive test results
        """
        try:
            # Perform independent samples t-test
            t_stat, p_value = stats.ttest_ind(group1, group2)

            # Calculate degrees of freedom
            df = len(group1) + len(group2) - 2

            # Calculate mean difference
            mean_diff = np.mean(group1) - np.mean(group2)

            # Calculate confidence interval for mean difference
            se = np.sqrt(np.var(group1, ddof=1)/len(group1) + np.var(group2, ddof=1)/len(group2))
            ci_lower, ci_upper = mean_diff + stats.t.ppf([self.alpha/2, 1-self.alpha/2], df) * se

            # Calculate effect size (Cohen's d)
            pooled_sd = np.sqrt(((len(group1)-1)*np.var(group1, ddof=1) +
                               (len(group2)-1)*np.var(group2, ddof=1)) / df)
            cohens_d = mean_diff / pooled_sd

            # Group statistics
            group1_stats = {
                'mean': float(np.mean(group1)),
                'std': float(np.std(group1, ddof=1)),
                'n': len(group1),
                'median': float(np.median(group1))
            }

            group2_stats = {
                'mean': float(np.mean(group2)),
                'std': float(np.std(group2, ddof=1)),
                'n': len(group2),
                'median': float(np.median(group2))
            }

            result = {
                'test_name': test_name,
                'test_type': 't_test',
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'degrees_of_freedom': df,
                'mean_difference': float(mean_diff),
                'confidence_interval': [float(ci_lower), float(ci_upper)],
                'effect_size': float(cohens_d),
                'effect_size_interpretation': self._interpret_cohens_d(abs(cohens_d)),
                'group1_stats': group1_stats,
                'group2_stats': group2_stats,
                'alpha': self.alpha,
                'is_significant': bool(p_value < self.alpha)
            }

            self.results.append(result)
            return result

        except Exception as e:
            logger.error(f"Error in t-test: {str(e)}")
            raise

    def one_way_anova(self, groups: List[np.ndarray], test_name: str) -> Dict[str, Any]:
        """
        Perform one-way ANOVA with effect size and post-hoc tests

        Args:
            groups: List of group data arrays
            test_name: Name of the test for identification

        Returns:
            Dictionary with comprehensive ANOVA results
        """
        try:
            # Perform one-way ANOVA
            f_stat, p_value = stats.f_oneway(*groups)

            # Calculate degrees of freedom
            df_between = len(groups) - 1
            df_within = sum(len(group) for group in groups) - len(groups)

            # Calculate effect size (eta-squared)
            ss_total = sum(np.var(np.concatenate(groups), ddof=1) * (len(np.concatenate(groups)) - 1))
            ss_between = sum(len(group) * (np.mean(group) - np.mean(np.concatenate(groups)))**2 for group in groups)
            eta_squared = ss_between / ss_total

            # Group statistics
            group_stats = {}
            for i, group in enumerate(groups):
                group_stats[f'group_{i+1}'] = {
                    'mean': float(np.mean(group)),
                    'std': float(np.std(group, ddof=1)),
                    'n': len(group),
                    'median': float(np.median(group))
                }

            result = {
                'test_name': test_name,
                'test_type': 'anova',
                'f_statistic': float(f_stat),
                'p_value': float(p_value),
                'degrees_of_freedom_between': df_between,
                'degrees_of_freedom_within': df_within,
                'effect_size': float(eta_squared),
                'effect_size_interpretation': self._interpret_eta_squared(eta_squared),
                'group_stats': group_stats,
                'alpha': self.alpha,
                'is_significant': bool(p_value < self.alpha)
            }

            # Perform post-hoc test if ANOVA is significant
            if p_value < self.alpha and len(groups) >= 3:
                post_hoc_result = self._perform_tukey_hsd(groups, [f'Group_{i+1}' for i in range(len(groups))])
                result['post_hoc_test'] = post_hoc_result

            self.results.append(result)
            return result

        except Exception as e:
            logger.error(f"Error in ANOVA: {str(e)}")
            raise

    def _perform_tukey_hsd(self, groups: List[np.ndarray], group_names: List[str]) -> Dict[str, Any]:
        """Perform Tukey HSD post-hoc test"""
        try:
            # Create data array and group labels for Tukey HSD
            data = []
            labels = []
            for i, group in enumerate(groups):
                data.extend(group)
                labels.extend([group_names[i]] * len(group))

            data_array = np.array(data)
            labels_array = np.array(labels)

            # Perform Tukey HSD
            tukey_result = pairwise_tukeyhsd(data_array, labels_array, alpha=self.alpha)

            return {
                'test_type': 'Tukey HSD',
                'significant_comparisons': int(np.any(tukey_result.reject)),
                'comparisons': [
                    {
                        'group1': row[0],
                        'group2': row[1],
                        'mean_difference': float(row[2]),
                        'p_value': float(row[3]),
                        'confidence_interval': [float(row[4]), float(row[5])],
                        'significant': bool(row[6])
                    }
                    for row in tukey_result._results_table.data[1:]  # Skip header
                ]
            }
        except Exception as e:
            logger.error(f"Error in Tukey HSD: {str(e)}")
            return {'test_type': 'Tukey HSD', 'error': str(e)}

    def mann_whitney_u_test(self, group1: np.ndarray, group2: np.ndarray, test_name: str) -> Dict[str, Any]:
        """Perform Mann-Whitney U test for non-parametric comparison"""
        try:
            u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')

            # Calculate effect size (r)
            n1, n2 = len(group1), len(group2)
            z_score = (u_stat - n1*n2/2) / np.sqrt(n1*n2*(n1+n2+1)/12)
            r_effect_size = z_score / np.sqrt(n1 + n2)

            result = {
                'test_name': test_name,
                'test_type': 'mann_whitney',
                'u_statistic': float(u_stat),
                'p_value': float(p_value),
                'effect_size': float(abs(r_effect_size)),
                'effect_size_interpretation': self._interpret_r_effect_size(abs(r_effect_size)),
                'group1_stats': {'n': n1, 'median': float(np.median(group1))},
                'group2_stats': {'n': n2, 'median': float(np.median(group2))},
                'alpha': self.alpha,
                'is_significant': bool(p_value < self.alpha)
            }

            self.results.append(result)
            return result

        except Exception as e:
            logger.error(f"Error in Mann-Whitney U test: {str(e)}")
            raise

    def generate_summary_statistics(self, data: np.ndarray, name: str) -> Dict[str, float]:
        """Generate comprehensive summary statistics"""
        return {
            'name': name,
            'n': len(data),
            'mean': float(np.mean(data)),
            'std': float(np.std(data, ddof=1)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'median': float(np.median(data)),
            'q25': float(np.percentile(data, 25)),
            'q75': float(np.percentile(data, 75)),
            'iqr': float(np.percentile(data, 75) - np.percentile(data, 25)),
            'skewness': float(stats.skew(data)),
            'kurtosis': float(stats.kurtosis(data))
        }

    def calculate_confidence_interval(self, data: np.ndarray, confidence: float = 0.95) -> List[float]:
        """Calculate confidence interval for the mean"""
        alpha = 1 - confidence
        mean = np.mean(data)
        sem = stats.sem(data)
        ci = stats.t.interval(1 - alpha, len(data) - 1, loc=mean, scale=sem)
        return [float(ci[0]), float(ci[1])]

    def export_results_to_json(self) -> str:
        """Export all results to JSON format"""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'alpha_level': self.alpha,
            'total_tests': len(self.results),
            'results': self.results
        }
        return json.dumps(export_data, indent=2)

    def export_results_to_csv(self) -> str:
        """Export all results to CSV format"""
        if not self.results:
            return "No results to export"

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'test_name', 'test_type', 'p_value', 'is_significant', 'effect_size',
            'effect_size_interpretation', 'alpha', 'timestamp'
        ])

        # Data rows
        for result in self.results:
            writer.writerow([
                result.get('test_name', ''),
                result.get('test_type', ''),
                result.get('p_value', ''),
                result.get('is_significant', ''),
                result.get('effect_size', ''),
                result.get('effect_size_interpretation', ''),
                result.get('alpha', ''),
                datetime.now().isoformat()
            ])

        return output.getvalue()

    def clear_results(self):
        """Clear all stored results"""
        self.results = []

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size"""
        if d < 0.2:
            return "Negligible"
        elif d < 0.5:
            return "Small"
        elif d < 0.8:
            return "Medium"
        else:
            return "Large"

    def _interpret_eta_squared(self, eta_sq: float) -> str:
        """Interpret eta-squared effect size"""
        if eta_sq < 0.01:
            return "Negligible"
        elif eta_sq < 0.06:
            return "Small"
        elif eta_sq < 0.14:
            return "Medium"
        else:
            return "Large"

    def _interpret_r_effect_size(self, r: float) -> str:
        """Interpret r effect size"""
        if r < 0.1:
            return "Negligible"
        elif r < 0.3:
            return "Small"
        elif r < 0.5:
            return "Medium"
        else:
            return "Large"