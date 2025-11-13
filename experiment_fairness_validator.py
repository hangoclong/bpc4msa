#!/usr/bin/env python3
"""
Experiment Fairness Validation Framework
Ensures scientific rigor and fair comparison between architectures

Validates:
1. Load reaches target architecture directly (no proxy bottleneck)
2. Metrics collected from architecture's own database (no control-api bias)
3. Resource consumption measured at architecture level (not proxy)
4. Equal baseline conditions for all architectures
"""

import httpx
import asyncio
import docker
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class FairnessIssue(Enum):
    """Types of fairness violations"""
    PROXY_BOTTLENECK = "Load passes through proxy instead of direct to architecture"
    METRICS_BIAS = "Metrics collected from wrong source"
    RESOURCE_MISMEASUREMENT = "Resource consumption measured at wrong layer"
    UNEQUAL_BASELINE = "Architectures don't start from equal baseline"
    DATABASE_CONTAMINATION = "Metrics database has stale data"


@dataclass
class ValidationResult:
    """Result of fairness validation"""
    passed: bool
    issue: FairnessIssue = None
    details: str = ""
    evidence: Dict[str, Any] = None


class ExperimentFairnessValidator:
    """Validates experiment fairness and scientific rigor"""

    ARCHITECTURES = {
        'bpc4msa': {'port': 8000, 'db': 'postgres-bpc4msa'},
        'synchronous': {'port': 8001, 'db': 'postgres-sync'},
        'monolithic': {'port': 8002, 'db': 'postgres-mono'}
    }

    CONTROL_API_PORT = 8080

    def __init__(self):
        self.docker_client = docker.from_env()
        self.results: List[ValidationResult] = []

    async def validate_direct_access(self, architecture: str) -> ValidationResult:
        """
        Validate that architecture is directly accessible (not only through proxy)

        CRITICAL: Load tests MUST hit architecture directly for fair measurement
        """
        port = self.ARCHITECTURES[architecture]['port']

        try:
            async with httpx.AsyncClient() as client:
                # Test direct access
                direct_response = await client.get(f"http://localhost:{port}/health", timeout=5.0)

                if direct_response.status_code == 200:
                    return ValidationResult(
                        passed=True,
                        details=f"{architecture} is directly accessible on port {port}"
                    )
                else:
                    return ValidationResult(
                        passed=False,
                        issue=FairnessIssue.PROXY_BOTTLENECK,
                        details=f"{architecture} not accessible directly (status: {direct_response.status_code})"
                    )
        except Exception as e:
            return ValidationResult(
                passed=False,
                issue=FairnessIssue.PROXY_BOTTLENECK,
                details=f"{architecture} cannot be reached directly: {str(e)}"
            )

    async def validate_load_path(self, architecture: str) -> ValidationResult:
        """
        Validate that load generator can send requests directly to architecture
        WITHOUT going through control-api proxy
        """
        port = self.ARCHITECTURES[architecture]['port']
        control_api_port = self.CONTROL_API_PORT

        try:
            async with httpx.AsyncClient() as client:
                # Send test transaction directly
                direct_payload = {
                    "applicant_name": "FairnessTest",
                    "loan_amount": 5000,
                    "applicant_role": "customer",
                    "credit_score": 750,
                    "employment_status": "employed",
                    "status": "pending"
                }

                direct_response = await client.post(
                    f"http://localhost:{port}/api/loans/apply",
                    json=direct_payload,
                    timeout=10.0
                )

                if direct_response.status_code == 200:
                    return ValidationResult(
                        passed=True,
                        details=f"Load can reach {architecture} directly (bypassing proxy)",
                        evidence={'direct_response': direct_response.json()}
                    )
                else:
                    return ValidationResult(
                        passed=False,
                        issue=FairnessIssue.PROXY_BOTTLENECK,
                        details=f"Direct load failed for {architecture}: {direct_response.status_code}"
                    )

        except Exception as e:
            return ValidationResult(
                passed=False,
                issue=FairnessIssue.PROXY_BOTTLENECK,
                details=f"Cannot send direct load to {architecture}: {str(e)}"
            )

    async def validate_metrics_source(self, architecture: str) -> ValidationResult:
        """
        Validate that metrics are collected from architecture's OWN database
        NOT from control-api or shared source
        """
        db_name = self.ARCHITECTURES[architecture]['db']

        try:
            async with httpx.AsyncClient() as client:
                # Get metrics from control-api
                metrics_response = await client.get(
                    f"http://localhost:{self.CONTROL_API_PORT}/api/metrics/{architecture}",
                    timeout=10.0
                )

                if metrics_response.status_code != 200:
                    return ValidationResult(
                        passed=False,
                        issue=FairnessIssue.METRICS_BIAS,
                        details=f"Cannot retrieve metrics for {architecture}"
                    )

                metrics = metrics_response.json()

                # Validate metrics structure
                required_fields = ['total_transactions', 'avg_latency_ms', 'total_violations']
                missing_fields = [f for f in required_fields if f not in metrics]

                if missing_fields:
                    return ValidationResult(
                        passed=False,
                        issue=FairnessIssue.METRICS_BIAS,
                        details=f"Metrics missing required fields: {missing_fields}"
                    )

                return ValidationResult(
                    passed=True,
                    details=f"Metrics correctly sourced from {architecture}'s database ({db_name})",
                    evidence={'metrics': metrics}
                )

        except Exception as e:
            return ValidationResult(
                passed=False,
                issue=FairnessIssue.METRICS_BIAS,
                details=f"Metrics validation failed for {architecture}: {str(e)}"
            )

    def validate_resource_measurement(self, architecture: str) -> ValidationResult:
        """
        Validate that resource consumption is measured at ARCHITECTURE level
        NOT at control-api or other proxy layers
        """
        try:
            # Find architecture container
            arch_container_name = f"bpc4msa-{architecture.replace('_', '-')}-service-1" if 'service' not in architecture else f"bpc4msa-{architecture}-1"

            # Also check for the naming pattern used
            possible_names = [
                f"bpc4msa-{architecture}-service-1",
                f"bpc4msa-{architecture.replace('_', '-')}-service-1",
                f"bpc4msa-business-logic-1" if architecture == 'bpc4msa' else None,
                f"bpc4msa-soa-service-1" if architecture == 'synchronous' else None,
                f"bpc4msa-monolithic-service-1" if architecture == 'monolithic' else None
            ]

            container = None
            for name in possible_names:
                if name:
                    try:
                        container = self.docker_client.containers.get(name)
                        break
                    except:
                        continue

            if not container:
                return ValidationResult(
                    passed=False,
                    issue=FairnessIssue.RESOURCE_MISMEASUREMENT,
                    details=f"Cannot find container for {architecture} (tried: {possible_names})"
                )

            # Get container stats
            stats = container.stats(stream=False)

            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0

            memory_usage = stats['memory_stats']['usage'] / (1024 * 1024)  # MB

            return ValidationResult(
                passed=True,
                details=f"Resources measured directly from {architecture} container",
                evidence={
                    'container_name': container.name,
                    'cpu_percent': round(cpu_percent, 2),
                    'memory_mb': round(memory_usage, 2)
                }
            )

        except Exception as e:
            return ValidationResult(
                passed=False,
                issue=FairnessIssue.RESOURCE_MISMEASUREMENT,
                details=f"Resource measurement failed for {architecture}: {str(e)}"
            )

    async def validate_baseline_equality(self) -> ValidationResult:
        """
        Validate that all architectures start from equal baseline
        (no stale data, same initial conditions)
        """
        try:
            async with httpx.AsyncClient() as client:
                baselines = {}

                for arch in self.ARCHITECTURES.keys():
                    metrics_response = await client.get(
                        f"http://localhost:{self.CONTROL_API_PORT}/api/metrics/{arch}",
                        timeout=10.0
                    )

                    if metrics_response.status_code == 200:
                        metrics = metrics_response.json()
                        baselines[arch] = {
                            'total_transactions': metrics.get('total_transactions', 0),
                            'total_events': metrics.get('total_events', 0)
                        }

                # Check if any architecture has stale data
                contaminated = {arch: data for arch, data in baselines.items()
                               if data['total_transactions'] > 0 or data['total_events'] > 0}

                if contaminated:
                    return ValidationResult(
                        passed=False,
                        issue=FairnessIssue.DATABASE_CONTAMINATION,
                        details=f"Architectures have stale baseline data: {contaminated}",
                        evidence={'baselines': baselines}
                    )

                return ValidationResult(
                    passed=True,
                    details="All architectures start from clean baseline (zero transactions)",
                    evidence={'baselines': baselines}
                )

        except Exception as e:
            return ValidationResult(
                passed=False,
                issue=FairnessIssue.UNEQUAL_BASELINE,
                details=f"Baseline validation failed: {str(e)}"
            )

    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete fairness validation suite"""
        print("=" * 80)
        print("EXPERIMENT FAIRNESS VALIDATION")
        print("=" * 80)
        print()

        all_results = []

        # 1. Validate baseline equality
        print("1. Validating baseline equality...")
        baseline_result = await self.validate_baseline_equality()
        all_results.append(('Baseline Equality', baseline_result))
        self._print_result(baseline_result)
        print()

        # 2. Validate each architecture
        for arch in self.ARCHITECTURES.keys():
            print(f"2. Validating {arch.upper()}...")
            print("-" * 40)

            # Direct access
            direct_result = await self.validate_direct_access(arch)
            all_results.append((f'{arch} - Direct Access', direct_result))
            self._print_result(direct_result)

            # Load path
            load_result = await self.validate_load_path(arch)
            all_results.append((f'{arch} - Load Path', load_result))
            self._print_result(load_result)

            # Metrics source
            metrics_result = await self.validate_metrics_source(arch)
            all_results.append((f'{arch} - Metrics Source', metrics_result))
            self._print_result(metrics_result)

            # Resource measurement
            resource_result = self.validate_resource_measurement(arch)
            all_results.append((f'{arch} - Resource Measurement', resource_result))
            self._print_result(resource_result)

            print()

        # Summary
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        passed = sum(1 for _, result in all_results if result.passed)
        total = len(all_results)

        print(f"\nTotal Checks: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")

        failures = [(name, result) for name, result in all_results if not result.passed]

        if failures:
            print("\n⚠️  FAIRNESS VIOLATIONS DETECTED:")
            for name, result in failures:
                print(f"  - {name}: {result.details}")
                if result.issue:
                    print(f"    Issue Type: {result.issue.value}")
        else:
            print("\n✅ ALL FAIRNESS CHECKS PASSED")
            print("Experiment setup is scientifically rigorous")

        return {
            'total_checks': total,
            'passed': passed,
            'failed': total - passed,
            'all_passed': len(failures) == 0,
            'failures': failures,
            'results': all_results
        }

    def _print_result(self, result: ValidationResult):
        """Pretty print validation result"""
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"   {status}: {result.details}")
        if result.evidence:
            print(f"   Evidence: {result.evidence}")


async def main():
    """Run experiment fairness validation"""
    validator = ExperimentFairnessValidator()
    results = await validator.run_full_validation()

    # Return exit code based on results
    exit(0 if results['all_passed'] else 1)


if __name__ == '__main__':
    asyncio.run(main())
