"""
Baseline Fairness Validation for BPC4MSA Experiments
Ensures statistical fairness and eliminates bias in architecture comparisons
"""

import numpy as np
import scipy.stats as stats
from typing import Dict, List, Tuple, Any
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaselineFairnessValidator:
    """
    Validates baseline fairness in BPC4MSA experiments
    Ensures all architectures start from comparable baseline conditions
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize fairness validator

        Args:
            alpha: Significance level for fairness tests
        """
        self.alpha = alpha
        self.fairness_results = []

    def validate_baseline_equivalence(self, metrics_data: Dict[str, Dict[str, List[float]]]) -> Dict[str, Any]:
        """
        Validate baseline equivalence across architectures

        Args:
            metrics_data: Dict with architecture names as keys and metric names as values
                         Example: {
                            'bpc4msa': {'cpu_usage': [10, 12, 11], 'memory': [50, 52, 51]},
                            'synchronous': {'cpu_usage': [11, 13, 12], 'memory': [51, 53, 52]},
                            'monolithic': {'cpu_usage': [10, 11, 12], 'memory': [50, 51, 52]}
                         }

        Returns:
            Comprehensive fairness validation report
        """
        try:
            architectures = list(metrics_data.keys())
            metrics = list(metrics_data[architectures[0]].keys()) if architectures else []

            logger.info(f"Validating baseline fairness for {len(architectures)} architectures across {len(metrics)} metrics")

            validation_report = {
                'validation_timestamp': datetime.now().isoformat(),
                'alpha_level': self.alpha,
                'architectures': architectures,
                'metrics_tested': metrics,
                'fairness_assessments': {},
                'overall_fairness_score': 0.0,
                'recommendations': []
            }

            fairness_scores = []

            # Test each metric for baseline equivalence
            for metric in metrics:
                metric_result = self._test_metric_fairness(metric, metrics_data, architectures)
                validation_report['fairness_assessments'][metric] = metric_result
                fairness_scores.append(metric_result['fairness_score'])

            # Calculate overall fairness score
            validation_report['overall_fairness_score'] = np.mean(fairness_scores) if fairness_scores else 0.0

            # Generate recommendations
            validation_report['recommendations'] = self._generate_fairness_recommendations(
                validation_report['fairness_assessments']
            )

            self.fairness_results.append(validation_report)
            return validation_report

        except Exception as e:
            logger.error(f"Error in baseline fairness validation: {str(e)}")
            raise

    def _test_metric_fairness(self, metric: str, metrics_data: Dict[str, Dict[str, List[float]]], architectures: List[str]) -> Dict[str, Any]:
        """Test fairness for a specific metric across all architectures"""
        try:
            # Extract data for this metric
            groups = [np.array(metrics_data[arch][metric]) for arch in architectures]

            # Perform statistical tests
            fairness_result = {
                'metric': metric,
                'sample_sizes': [len(group) for group in groups],
                'means': [float(np.mean(group)) for group in groups],
                'stds': [float(np.std(group, ddof=1)) for group in groups],
                'coefficient_of_variation': [float(np.std(group, ddof=1)/np.mean(group)) for group in groups],
                'statistical_tests': {},
                'fairness_score': 0.0,
                'is_fair': False,
                'issues': []
            }

            # Test 1: ANOVA for equality of means
            if len(groups) >= 3:
                f_stat, p_value_anova = stats.f_oneway(*groups)
                fairness_result['statistical_tests']['anova'] = {
                    'f_statistic': float(f_stat),
                    'p_value': float(p_value_anova),
                    'means_equal': bool(p_value_anova >= self.alpha)
                }
            elif len(groups) == 2:
                t_stat, p_value_t = stats.ttest_ind(groups[0], groups[1])
                fairness_result['statistical_tests']['t_test'] = {
                    't_statistic': float(t_stat),
                    'p_value': float(p_value_t),
                    'means_equal': bool(p_value_t >= self.alpha)
                }

            # Test 2: Levene's test for equality of variances
            levene_stat, p_value_levene = stats.levene(*groups)
            fairness_result['statistical_tests']['levenes_test'] = {
                'w_statistic': float(levene_stat),
                'p_value': float(p_value_levene),
                'variances_equal': bool(p_value_levene >= self.alpha)
            }

            # Test 3: Coefficient of variation consistency
            cv_values = fairness_result['coefficient_of_variation']
            cv_range = max(cv_values) - min(cv_values)
            cv_consistent = cv_range < 0.1  # CV difference less than 10%

            fairness_result['statistical_tests']['cv_consistency'] = {
                'cv_range': float(cv_range),
                'cv_consistent': cv_consistent
            }

            # Calculate fairness score
            fairness_score = self._calculate_metric_fairness_score(fairness_result)
            fairness_result['fairness_score'] = fairness_score
            fairness_result['is_fair'] = fairness_score >= 0.8  # 80% fairness threshold

            # Identify issues
            fairness_result['issues'] = self._identify_fairness_issues(fairness_result)

            return fairness_result

        except Exception as e:
            logger.error(f"Error testing metric fairness for {metric}: {str(e)}")
            return {
                'metric': metric,
                'error': str(e),
                'fairness_score': 0.0,
                'is_fair': False
            }

    def _calculate_metric_fairness_score(self, fairness_result: Dict[str, Any]) -> float:
        """Calculate fairness score for a metric (0-1 scale)"""
        score = 1.0

        tests = fairness_result['statistical_tests']

        # Penalty for unequal means (30% weight)
        if 'anova' in tests:
            if not tests['anova']['means_equal']:
                score -= 0.3
        elif 't_test' in tests:
            if not tests['t_test']['means_equal']:
                score -= 0.3

        # Penalty for unequal variances (20% weight)
        if not tests['levenes_test']['variances_equal']:
            score -= 0.2

        # Penalty for inconsistent CV (20% weight)
        if not tests['cv_consistency']['cv_consistent']:
            score -= 0.2

        # Penalty for high variation between means (30% weight)
        means = fairness_result['means']
        mean_range = max(means) - min(means)
        mean_avg = np.mean(means)
        if mean_avg > 0:
            relative_range = mean_range / mean_avg
            if relative_range > 0.1:  # More than 10% difference in means
                score -= min(0.3, relative_range * 2)

        return max(0.0, score)

    def _identify_fairness_issues(self, fairness_result: Dict[str, Any]) -> List[str]:
        """Identify specific fairness issues for a metric"""
        issues = []
        tests = fairness_result['statistical_tests']

        if 'anova' in tests and not tests['anova']['means_equal']:
            issues.append("Means are significantly different across architectures (ANOVA)")
        elif 't_test' in tests and not tests['t_test']['means_equal']:
            issues.append("Means are significantly different across architectures (t-test)")

        if not tests['levenes_test']['variances_equal']:
            issues.append("Variances are significantly different across architectures (Levene's test)")

        if not tests['cv_consistency']['cv_consistent']:
            issues.append("Coefficient of variation varies too much across architectures")

        # Check for large mean differences
        means = fairness_result['means']
        mean_range = max(means) - min(means)
        mean_avg = np.mean(means)
        if mean_avg > 0 and (mean_range / mean_avg) > 0.1:
            issues.append(f"Large relative difference in means: {mean_range/mean_avg:.1%}")

        return issues

    def _generate_fairness_recommendations(self, fairness_assessments: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate recommendations for improving fairness"""
        recommendations = []

        # Overall fairness assessment
        fairness_scores = [assessment.get('fairness_score', 0) for assessment in fairness_assessments.values()]
        avg_fairness = np.mean(fairness_scores) if fairness_scores else 0

        if avg_fairness < 0.8:
            recommendations.append("Overall baseline fairness is below 80%. Consider re-balancing the experimental setup.")

        # Specific metric recommendations
        for metric, assessment in fairness_assessments.items():
            if assessment.get('fairness_score', 0) < 0.8:
                issues = assessment.get('issues', [])
                for issue in issues:
                    if "means are significantly different" in issue:
                        recommendations.append(f"For {metric}: Normalize initial conditions to reduce mean differences")
                    elif "variances are significantly different" in issue:
                        recommendations.append(f"For {metric}: Standardize variance across architectures")
                    elif "coefficient of variation" in issue:
                        recommendations.append(f"For {metric}: Stabilize variability patterns across architectures")

        # General recommendations
        if not recommendations:
            recommendations.append("Baseline fairness is acceptable. Continue with experiment execution.")
        else:
            recommendations.append("Re-run baseline validation after implementing corrections.")
            recommendations.append("Document any necessary baseline adjustments in the experimental methodology.")

        return recommendations

    def validate_resource_allocation_fairness(self, resource_data: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Validate fairness in resource allocation across architectures

        Args:
            resource_data: Resource allocation data
                          Example: {
                              'bpc4msa': {'cpu_cores': 2, 'memory_mb': 1024, 'disk_mb': 2048},
                              'synchronous': {'cpu_cores': 2, 'memory_mb': 1024, 'disk_mb': 2048},
                              'monolithic': {'cpu_cores': 2, 'memory_mb': 1024, 'disk_mb': 2048}
                          }

        Returns:
            Resource allocation fairness report
        """
        try:
            architectures = list(resource_data.keys())
            resources = list(resource_data[architectures[0]].keys()) if architectures else []

            validation_report = {
                'validation_timestamp': datetime.now().isoformat(),
                'validation_type': 'resource_allocation',
                'architectures': architectures,
                'resources_tested': resources,
                'allocation_assessments': {},
                'overall_equity_score': 0.0,
                'recommendations': []
            }

            equity_scores = []

            # Test each resource for allocation equity
            for resource in resources:
                allocation_values = [resource_data[arch][resource] for arch in architectures]

                assessment = {
                    'resource': resource,
                    'allocations': allocation_values,
                    'is_equitable': len(set(allocation_values)) == 1,  # All equal
                    'equity_score': 1.0 if len(set(allocation_values)) == 1 else 0.0,
                    'variance': float(np.var(allocation_values)),
                    'coefficient_of_variation': float(np.std(allocation_values) / np.mean(allocation_values)) if np.mean(allocation_values) > 0 else 0.0
                }

                validation_report['allocation_assessments'][resource] = assessment
                equity_scores.append(assessment['equity_score'])

            # Calculate overall equity score
            validation_report['overall_equity_score'] = np.mean(equity_scores) if equity_scores else 0.0

            # Generate recommendations
            if validation_report['overall_equity_score'] < 1.0:
                validation_report['recommendations'].append("Ensure equal resource allocation across all architectures for fair comparison.")
            else:
                validation_report['recommendations'].append("Resource allocation is equitable across all architectures.")

            return validation_report

        except Exception as e:
            logger.error(f"Error in resource allocation fairness validation: {str(e)}")
            raise

    def generate_fairness_report(self) -> str:
        """Generate comprehensive fairness report"""
        if not self.fairness_results:
            return "No fairness validations performed"

        report = {
            'report_timestamp': datetime.now().isoformat(),
            'total_validations': len(self.fairness_results),
            'validations': self.fairness_results,
            'summary': {
                'overall_average_fairness': np.mean([v.get('overall_fairness_score', 0) for v in self.fairness_results]),
                'total_recommendations': sum(len(v.get('recommendations', [])) for v in self.fairness_results)
            }
        }

        return json.dumps(report, indent=2)

    def clear_results(self):
        """Clear all fairness validation results"""
        self.fairness_results = []