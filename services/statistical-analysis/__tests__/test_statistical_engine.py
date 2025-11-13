"""
TDD Tests for Statistical Analysis Engine
Test-driven development for publication-ready statistical analysis
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import statistical_engine
StatisticalEngine = statistical_engine.StatisticalEngine


class TestStatisticalEngine:
    """Test suite for StatisticalEngine class following TDD principles"""

    def setup_method(self):
        """Setup test data for each test method"""
        np.random.seed(42)  # Ensure reproducible test results

        # Generate sample performance data (response times in ms)
        self.bpc4msa_data = np.random.normal(15, 3, 100)  # Mean 15ms, SD 3ms
        self.soa_data = np.random.normal(20, 4, 100)      # Mean 20ms, SD 4ms
        self.monolithic_data = np.random.normal(8, 1.5, 100)  # Mean 8ms, SD 1.5ms

        # Sample throughput data (requests per second)
        self.bpc4msa_throughput = np.random.normal(120, 15, 50)
        self.soa_throughput = np.random.normal(95, 12, 50)
        self.monolithic_throughput = np.random.normal(180, 20, 50)

        # Initialize statistical engine
        self.engine = StatisticalEngine()

    def test_init(self):
        """Test StatisticalEngine initialization"""
        assert self.engine.alpha == 0.05
        assert self.engine.confidence_level == 0.95
        assert hasattr(self.engine, 'results')

    def test_two_sample_t_test(self):
        """Test two-sample t-test implementation"""
        # Test significant difference
        result = self.engine.two_sample_t_test(
            self.bpc4msa_data,
            self.soa_data,
            "BPC4MSA vs SOA Response Time"
        )

        # Verify result structure
        assert 't_statistic' in result
        assert 'p_value' in result
        assert 'is_significant' in result
        assert 'confidence_interval' in result
        assert 'effect_size' in result
        assert 'mean_difference' in result
        assert 'test_name' in result

        # Verify data types and ranges
        assert isinstance(result['p_value'], float)
        assert 0 <= result['p_value'] <= 1
        assert isinstance(result['is_significant'], bool)
        assert len(result['confidence_interval']) == 2
        assert result['confidence_interval'][0] < result['confidence_interval'][1]

        # Verify test name
        assert result['test_name'] == "BPC4MSA vs SOA Response Time"

        print(f"T-test result: {result}")

    def test_t_test_no_difference(self):
        """Test t-test with non-significant difference"""
        # Generate data with minimal difference
        data1 = np.random.normal(10, 2, 100)
        data2 = np.random.normal(10.5, 2, 100)

        result = self.engine.two_sample_t_test(data1, data2, "No Difference Test")

        # Should typically not be significant with such small difference
        # But we don't assert this as it's probabilistic
        assert 'is_significant' in result
        assert result['test_name'] == "No Difference Test"

    def test_one_way_anova(self):
        """Test one-way ANOVA implementation"""
        result = self.engine.one_way_anova(
            [self.bpc4msa_data, self.soa_data, self.monolithic_data],
            "Architecture Performance Comparison"
        )

        # Verify result structure
        assert 'f_statistic' in result
        assert 'p_value' in result
        assert 'is_significant' in result
        assert 'effect_size' in result  # eta-squared
        assert 'test_name' in result
        assert 'group_stats' in result

        # Verify data types
        assert isinstance(result['f_statistic'], float)
        assert isinstance(result['p_value'], float)
        assert isinstance(result['is_significant'], bool)
        assert 0 <= result['p_value'] <= 1

        # Verify group statistics
        group_stats = result['group_stats']
        assert len(group_stats) == 3
        for i, stats in enumerate(group_stats):
            assert 'mean' in stats
            assert 'std' in stats
            assert 'n' in stats
            assert stats['n'] == 100

        print(f"ANOVA result: {result}")

    def test_anova_two_groups(self):
        """Test ANOVA with only two groups (should work like t-test)"""
        result = self.engine.one_way_anova(
            [self.bpc4msa_data, self.soa_data],
            "Two Group ANOVA"
        )

        assert 'f_statistic' in result
        assert 'p_value' in result
        assert len(result['group_stats']) == 2

    def test_confidence_interval(self):
        """Test confidence interval calculation"""
        ci = self.engine.calculate_confidence_interval(self.bpc4msa_data)

        # Verify structure
        assert len(ci) == 2
        assert ci[0] < ci[1]  # Lower bound < Upper bound

        # Verify it contains the mean approximately
        mean = np.mean(self.bpc4msa_data)
        assert ci[0] < mean < ci[1]

        # Test with different confidence levels
        ci_90 = self.engine.calculate_confidence_interval(self.bpc4msa_data, 0.90)
        ci_99 = self.engine.calculate_confidence_interval(self.bpc4msa_data, 0.99)

        # Higher confidence should give wider interval
        assert (ci_99[1] - ci_99[0]) > (ci_90[1] - ci_90[0])

    def test_effect_size_cohens_d(self):
        """Test Cohen's d effect size calculation"""
        effect_size = self.engine.calculate_cohens_d(
            self.bpc4msa_data,
            self.soa_data
        )

        # Verify it's a float
        assert isinstance(effect_size, float)

        # Verify sign indicates direction (should be negative if mean1 < mean2)
        mean_diff = np.mean(self.bpc4msa_data) - np.mean(self.soa_data)
        assert (effect_size > 0) == (mean_diff > 0)

        # Test with identical data (should be ~0)
        identical_data = np.random.normal(10, 2, 100)
        effect_size_identical = self.engine.calculate_cohens_d(
            identical_data,
            identical_data
        )
        assert abs(effect_size_identical) < 0.1  # Should be close to 0

    def test_mann_whitney_u_test(self):
        """Test non-parametric Mann-Whitney U test"""
        result = self.engine.mann_whitney_u_test(
            self.bpc4msa_data,
            self.soa_data,
            "Non-parametric test"
        )

        assert 'u_statistic' in result
        assert 'p_value' in result
        assert 'is_significant' in result
        assert 'test_name' in result
        assert result['test_name'] == "Non-parametric test"

    def test_multiple_comparison_correction(self):
        """Test multiple comparison correction (Bonferroni)"""
        p_values = [0.01, 0.04, 0.15, 0.03, 0.25]
        corrected = self.engine.bonferroni_correction(p_values)

        assert len(corrected) == len(p_values)

        # Corrected p-values should be >= original
        for original, corrected_p in zip(p_values, corrected):
            assert corrected_p >= original

        # Should maintain original order (not sorted)
        assert len(corrected) == len(p_values)

    def test_levenes_test(self):
        """Test Levene's test for equality of variances"""
        result = self.engine.levenes_test(
            [self.bpc4msa_data, self.soa_data, self.monolithic_data]
        )

        assert 'w_statistic' in result
        assert 'p_value' in result
        assert 'equal_variances' in result
        assert isinstance(result['equal_variances'], bool)

    def test_shapiro_wilk_test(self):
        """Test Shapiro-Wilk test for normality"""
        result = self.engine.shapiro_wilk_test(self.bpc4msa_data)

        assert 'w_statistic' in result
        assert 'p_value' in result
        assert 'is_normal' in result
        assert isinstance(result['is_normal'], bool)
        assert 0 <= result['p_value'] <= 1

    def test_generate_summary_statistics(self):
        """Test generation of summary statistics"""
        stats = self.engine.generate_summary_statistics(
            self.bpc4msa_data,
            "BPC4MSA Response Time"
        )

        required_keys = [
            'name', 'n', 'mean', 'std', 'min', 'max', 'median',
            'q25', 'q75', 'iqr', 'skewness', 'kurtosis'
        ]

        for key in required_keys:
            assert key in stats

        assert stats['name'] == "BPC4MSA Response Time"
        assert stats['n'] == len(self.bpc4msa_data)
        assert stats['min'] <= stats['q25'] <= stats['median'] <= stats['q75'] <= stats['max']

    def test_export_results_to_json(self):
        """Test exporting results to JSON format"""
        # Perform some tests
        t_test_result = self.engine.two_sample_t_test(
            self.bpc4msa_data,
            self.soa_data,
            "Test Export"
        )

        anova_result = self.engine.one_way_anova(
            [self.bpc4msa_data, self.soa_data, self.monolithic_data],
            "ANOVA Export"
        )

        # Export to JSON
        json_data = self.engine.export_results_to_json()

        # Verify structure
        assert 'analysis_metadata' in json_data
        assert 'tests' in json_data
        assert 'summary_statistics' in json_data

        # Verify tests were saved
        assert len(json_data['tests']) >= 2

        # Find our test results
        test_names = [test['test_name'] for test in json_data['tests']]
        assert "Test Export" in test_names
        assert "ANOVA Export" in test_names

    def test_export_results_to_csv(self):
        """Test exporting results to CSV format"""
        # Perform a test
        self.engine.two_sample_t_test(
            self.bpc4msa_data,
            self.soa_data,
            "CSV Test"
        )

        # Export to CSV
        csv_content = self.engine.export_results_to_csv()

        # Verify it's valid CSV
        lines = csv_content.strip().split('\n')
        assert len(lines) > 1  # Header + at least one data row

        # Check header
        header = lines[0]
        expected_columns = ['test_name', 'test_type', 'p_value', 'is_significant', 'effect_size']
        for col in expected_columns:
            assert col in header

    def test_clear_results(self):
        """Test clearing stored results"""
        # Perform a test
        self.engine.two_sample_t_test(
            self.bpc4msa_data,
            self.soa_data,
            "Clear Test"
        )

        # Verify results exist
        assert len(self.engine.results['tests']) > 0

        # Clear results
        self.engine.clear_results()

        # Verify results are cleared
        assert len(self.engine.results['tests']) == 0
        assert len(self.engine.results['summary_statistics']) == 0

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Empty data
        with pytest.raises(ValueError):
            self.engine.two_sample_t_test([], [1, 2, 3], "Empty Data Test")

        # Single data point
        with pytest.raises(ValueError):
            self.engine.two_sample_t_test([1], [2, 3], "Single Point Test")

        # Invalid confidence level
        with pytest.raises(ValueError):
            self.engine.calculate_confidence_interval(self.bpc4msa_data, 1.5)

        with pytest.raises(ValueError):
            self.engine.calculate_confidence_interval(self.bpc4msa_data, -0.1)


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])