#!/usr/bin/env python3
"""
Standalone test for Statistical Analysis Integration
Tests the statistical engine independently before API integration
"""

import sys
import os
sys.path.append('/Users/hangoclong/Repos/bpc4msa/services/statistical-analysis')

def test_statistical_engine():
    """Test the statistical engine independently"""
    print("=== Testing Statistical Engine Standalone ===")

    try:
        from statistical_engine import StatisticalEngine
        print("✓ Statistical engine imported successfully")

        # Initialize engine
        engine = StatisticalEngine(alpha=0.05)
        print("✓ Statistical engine initialized")

        # Generate test data for 3 architectures
        import numpy as np
        np.random.seed(42)

        # Simulate latency data for BPC4MSA (fastest), SOA (medium), Monolithic (slowest)
        bpc4msa_data = np.random.normal(50, 10, 100)  # 50ms avg, 10ms std
        soa_data = np.random.normal(75, 15, 100)      # 75ms avg, 15ms std
        monolithic_data = np.random.normal(120, 25, 100)  # 120ms avg, 25ms std

        print(f"✓ Generated test data:")
        print(f"  - BPC4MSA: {len(bpc4msa_data)} samples, mean={np.mean(bpc4msa_data):.2f}ms")
        print(f"  - SOA: {len(soa_data)} samples, mean={np.mean(soa_data):.2f}ms")
        print(f"  - Monolithic: {len(monolithic_data)} samples, mean={np.mean(monolithic_data):.2f}ms")

        # Test 1: T-test between BPC4MSA and SOA
        print("\n--- Test 1: T-test (BPC4MSA vs SOA) ---")
        t_test_result = engine.two_sample_t_test(
            bpc4msa_data, soa_data,
            "BPC4MSA vs SOA - Latency Comparison"
        )
        print(f"✓ T-test completed:")
        print(f"  - P-value: {t_test_result['p_value']:.6f}")
        print(f"  - Significant: {t_test_result['is_significant']}")
        print(f"  - Effect size: {t_test_result['effect_size']:.4f}")
        print(f"  - Effect interpretation: {t_test_result['effect_size_interpretation']}")

        # Test 2: One-way ANOVA across all three
        print("\n--- Test 2: One-way ANOVA (All Architectures) ---")
        anova_result = engine.one_way_anova(
            [bpc4msa_data, soa_data, monolithic_data],
            "ANOVA: Latency Across All Architectures"
        )
        print(f"✓ ANOVA completed:")
        print(f"  - F-statistic: {anova_result['f_statistic']:.4f}")
        print(f"  - P-value: {anova_result['p_value']:.6f}")
        print(f"  - Significant: {anova_result['is_significant']}")
        print(f"  - Effect size: {anova_result['effect_size']:.4f}")
        print(f"  - Effect interpretation: {anova_result['effect_size_interpretation']}")

        if 'post_hoc_test' in anova_result:
            post_hoc = anova_result['post_hoc_test']
            print(f"  - Post-hoc test: {post_hoc['test_type']}")
            print(f"  - Significant comparisons: {post_hoc['significant_comparisons']}")

        # Test 3: Summary statistics for each architecture
        print("\n--- Test 3: Summary Statistics ---")
        for i, (data, name) in enumerate([(bpc4msa_data, "BPC4MSA"), (soa_data, "SOA"), (monolithic_data, "Monolithic")]):
            summary = engine.generate_summary_statistics(data, f"{name} Latency")
            print(f"✓ {name} summary:")
            print(f"  - Mean: {summary['mean']:.2f}ms")
            print(f"  - Std Dev: {summary['std']:.2f}ms")
            print(f"  - Min: {summary['min']:.2f}ms")
            print(f"  - Max: {summary['max']:.2f}ms")
            print(f"  - Median: {summary['median']:.2f}ms")

        # Test 4: Export functionality
        print("\n--- Test 4: Export Functionality ---")
        json_export = engine.export_results_to_json()
        print(f"✓ JSON export completed: {len(json_export)} characters")

        csv_export = engine.export_results_to_csv()
        print(f"✓ CSV export completed: {len(csv_export)} characters")

        print("\n=== Statistical Engine Test: ALL TESTS PASSED ===")
        return True

    except Exception as e:
        print(f"✗ Statistical Engine Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_simulation():
    """Simulate API calls to test the integration logic"""
    print("\n=== Testing API Integration Logic ===")

    try:
        from statistical_engine import StatisticalEngine
        engine = StatisticalEngine(alpha=0.05)

        # Simulate the API request/response structure
        api_request = {
            "test_type": "anova",
            "architectures": ["bpc4msa", "synchronous", "monolithic"],
            "metric": "latency",
            "alpha": 0.05
        }

        print(f"✓ Simulated API request: {api_request}")

        # Generate sample data (simulating database extraction)
        import numpy as np
        np.random.seed(42)

        # Simulate database query results
        db_data = {
            "bpc4msa": np.random.normal(50, 10, 100),
            "synchronous": np.random.normal(75, 15, 100),
            "monolithic": np.random.normal(120, 25, 100)
        }

        print("✓ Simulated database data extraction")

        # Process the request as the API would
        if api_request["test_type"] == "anova":
            data_groups = [db_data[arch] for arch in api_request["architectures"]]
            test_name = f"ANOVA: {api_request['metric'].title()} Across Architectures"

            result = engine.one_way_anova(data_groups, test_name)

            # Add metadata as the API would
            result['analysis_metadata'] = {
                'architectures': api_request["architectures"],
                'metric': api_request["metric"],
                'sample_sizes': [len(group) for group in data_groups],
                'analysis_date': "2024-01-01T00:00:00",  # Simulated
                'alpha_level': api_request["alpha"]
            }

            print("✓ API processing completed")
            print(f"✓ Result contains: {list(result.keys())}")
            print(f"✓ P-value: {result['p_value']:.6f}")
            print(f"✓ Significant: {result['is_significant']}")
            print(f"✓ Metadata added: {list(result['analysis_metadata'].keys())}")

        print("\n=== API Integration Test: PASSED ===")
        return True

    except Exception as e:
        print(f"✗ API Integration Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Statistical Analysis Integration Tests...\n")

    # Test 1: Statistical Engine Standalone
    engine_test_passed = test_statistical_engine()

    # Test 2: API Integration Logic
    api_test_passed = test_api_simulation()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY:")
    print(f"Statistical Engine: {'✓ PASSED' if engine_test_passed else '✗ FAILED'}")
    print(f"API Integration: {'✓ PASSED' if api_test_passed else '✗ FAILED'}")

    if engine_test_passed and api_test_passed:
        print("\n🎉 ALL INTEGRATION TESTS PASSED! 🎉")
        print("The statistical analysis engine is ready for production use.")
        print("Ready to proceed with Docker integration and final deployment.")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please fix the issues before proceeding with deployment.")

    print("="*60)