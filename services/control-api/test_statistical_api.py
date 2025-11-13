#!/usr/bin/env python3
"""
Test script for Statistical Analysis API endpoints
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"

async def test_statistical_endpoints():
    """Test all statistical analysis endpoints"""

    async with httpx.AsyncClient() as client:
        print("=== Testing Statistical Analysis API ===")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()

        # Test 1: Statistical Engine Health
        print("1. Testing Statistical Engine Health...")
        try:
            response = await client.get(f"{BASE_URL}/api/statistics/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✓ Status: {health_data['status']}")
                print(f"   ✓ Version: {health_data['version']}")
                print(f"   ✓ Supported Tests: {health_data['supported_tests']}")
                print(f"   ✓ Supported Metrics: {health_data['supported_metrics']}")
            else:
                print(f"   ✗ Failed with status: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        # Test 2: Statistical Summary for BPC4MSA
        print("2. Testing Statistical Summary (BPC4MSA Latency)...")
        try:
            response = await client.get(f"{BASE_URL}/api/statistics/summary/bpc4msa?metric=latency")
            if response.status_code == 200:
                summary_data = response.json()
                print(f"   ✓ Architecture: {summary_data['architecture']}")
                print(f"   ✓ Metric: {summary_data['metric']}")
                print(f"   ✓ Sample Size: {summary_data['sample_size']}")
                if 'summary_statistics' in summary_data:
                    stats = summary_data['summary_statistics']
                    print(f"   ✓ Mean: {stats['mean']:.2f}")
                    print(f"   ✓ Std Dev: {stats['std']:.2f}")
                    print(f"   ✓ Min: {stats['min']:.2f}")
                    print(f"   ✓ Max: {stats['max']:.2f}")
                if 'normality_test' in summary_data:
                    normality = summary_data['normality_test']
                    print(f"   ✓ Normality Test W-stat: {normality['w_statistic']:.4f}")
                    print(f"   ✓ Is Normal: {normality['is_normal']}")
            else:
                print(f"   ✗ Failed with status: {response.status_code}")
                print(f"   ✗ Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        # Test 3: T-Test Comparison
        print("3. Testing T-Test Comparison (BPC4MSA vs Synchronous)...")
        test_request = {
            "test_type": "t_test",
            "architectures": ["bpc4msa", "synchronous"],
            "metric": "latency",
            "alpha": 0.05
        }

        try:
            response = await client.post(
                f"{BASE_URL}/api/statistics/compare",
                json=test_request
            )
            if response.status_code == 200:
                test_result = response.json()
                print(f"   ✓ Test Name: {test_result['test_name']}")
                print(f"   ✓ Test Type: {test_result['test_type']}")
                print(f"   ✓ P-value: {test_result['p_value']:.6f}")
                print(f"   ✓ Is Significant: {test_result['is_significant']}")
                print(f"   ✓ Effect Size: {test_result['effect_size']:.4f}")
                print(f"   ✓ Effect Interpretation: {test_result['effect_size_interpretation']}")
                if 'confidence_interval' in test_result:
                    ci = test_result['confidence_interval']
                    print(f"   ✓ 95% CI: [{ci[0]:.2f}, {ci[1]:.2f}]")
            else:
                print(f"   ✗ Failed with status: {response.status_code}")
                print(f"   ✗ Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        # Test 4: ANOVA Test
        print("4. Testing ANOVA (All 3 Architectures)...")
        anova_request = {
            "test_type": "anova",
            "architectures": ["bpc4msa", "synchronous", "monolithic"],
            "metric": "latency",
            "alpha": 0.05
        }

        try:
            response = await client.post(
                f"{BASE_URL}/api/statistics/compare",
                json=anova_request
            )
            if response.status_code == 200:
                anova_result = response.json()
                print(f"   ✓ Test Name: {anova_result['test_name']}")
                print(f"   ✓ F-statistic: {anova_result['f_statistic']:.4f}")
                print(f"   ✓ P-value: {anova_result['p_value']:.6f}")
                print(f"   ✓ Is Significant: {anova_result['is_significant']}")
                print(f"   ✓ Effect Size: {anova_result['effect_size']:.4f}")
                print(f"   ✓ Effect Interpretation: {anova_result['effect_size_interpretation']}")
                if 'post_hoc_test' in anova_result and anova_result['post_hoc_test']:
                    post_hoc = anova_result['post_hoc_test']
                    print(f"   ✓ Post-hoc Test: {post_hoc['test_type']}")
                    print(f"   ✓ Significant Comparisons: {post_hoc['significant_comparisons']}")
            else:
                print(f"   ✗ Failed with status: {response.status_code}")
                print(f"   ✗ Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        # Test 5: Export Statistical Results
        print("5. Testing Statistical Results Export...")
        try:
            response = await client.get(f"{BASE_URL}/api/statistics/export/json")
            if response.status_code == 200:
                export_data = response.json()
                print(f"   ✓ Export Status: Success")
                if 'analysis_metadata' in export_data:
                    metadata = export_data['analysis_metadata']
                    print(f"   ✓ Analysis Type: {metadata['analysis_type']}")
                    print(f"   ✓ Export Date: {metadata['export_date']}")
                    print(f"   ✓ Architectures: {metadata['architectures']}")
                if 'tests' in export_data:
                    print(f"   ✓ Number of Tests: {len(export_data['tests'])}")
                if 'summary_statistics' in export_data:
                    print(f"   ✓ Summary Statistics: {len(export_data['summary_statistics'])} entries")
            else:
                print(f"   ✗ Failed with status: {response.status_code}")
                print(f"   ✗ Response: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()

        print("=== Statistical API Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_statistical_endpoints())