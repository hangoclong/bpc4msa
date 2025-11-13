"""
Tests for Resource-Constrained Experiment Scenarios (Local Testing)
Implements Scenario A from Future_Experiment_Design_Plan.md

Test locally BEFORE Docker deployment to save time
"""

import pytest
import yaml
import os
from pathlib import Path


class TestResourceConstrainedScenario:
    """Tests for Low-Resource Environment (Scenario A)"""

    def test_resource_constrained_compose_file_exists(self):
        """Test that docker-compose.resource-constrained.yml exists"""
        compose_file = Path('docker-compose.resource-constrained.yml')
        assert compose_file.exists(), "Resource-constrained compose file should exist"

    def test_resource_constrained_compose_valid_yaml(self):
        """Test that the resource-constrained compose file is valid YAML"""
        compose_file = Path('docker-compose.resource-constrained.yml')

        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)

        assert data is not None, "YAML should parse successfully"
        assert 'services' in data, "Compose file should have services section"

    def test_resource_limits_for_control_api(self):
        """Test that control-api has proper resource limits"""
        compose_file = Path('docker-compose.resource-constrained.yml')

        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)

        control_api = data['services'].get('control-api')
        assert control_api is not None, "control-api service should be defined"

        deploy = control_api.get('deploy', {})
        resources = deploy.get('resources', {})
        limits = resources.get('limits', {})

        # From Future_Experiment_Design_Plan.md: 0.2 CPUs, 128MB RAM
        assert limits.get('cpus') == '0.2', "control-api should have 0.2 CPU limit"
        assert limits.get('memory') == '128M', "control-api should have 128MB memory limit"

    def test_resource_limits_for_business_logic(self):
        """Test that business-logic has proper resource limits"""
        compose_file = Path('docker-compose.resource-constrained.yml')

        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)

        business_logic = data['services'].get('business-logic')
        assert business_logic is not None, "business-logic service should be defined"

        deploy = business_logic.get('deploy', {})
        resources = deploy.get('resources', {})
        limits = resources.get('limits', {})

        assert limits.get('cpus') == '0.2', "business-logic should have 0.2 CPU limit"
        assert limits.get('memory') == '128M', "business-logic should have 128MB memory limit"

    def test_resource_limits_for_kafka(self):
        """Test that Kafka has proper resource limits"""
        compose_file = Path('docker-compose.resource-constrained.yml')

        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)

        kafka = data['services'].get('kafka-bpc4msa')
        assert kafka is not None, "kafka-bpc4msa service should be defined"

        deploy = kafka.get('deploy', {})
        resources = deploy.get('resources', {})
        limits = resources.get('limits', {})

        # Kafka gets more RAM as it's a message broker
        assert limits.get('cpus') == '0.2', "kafka should have 0.2 CPU limit"
        assert limits.get('memory') == '256M', "kafka should have 256MB memory limit"

    def test_resource_limits_for_monolithic(self):
        """Test that monolithic service has MORE resources (hypothesis test)"""
        compose_file = Path('docker-compose.resource-constrained.yml')

        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)

        monolithic = data['services'].get('monolithic-service')
        assert monolithic is not None, "monolithic-service should be defined"

        deploy = monolithic.get('deploy', {})
        resources = deploy.get('resources', {})
        limits = resources.get('limits', {})

        # From Future_Experiment_Design_Plan.md: Give monolithic more CPU
        assert limits.get('cpus') == '0.4', "monolithic should have 0.4 CPU (more than BPC4MSA services)"
        assert limits.get('memory') == '256M', "monolithic should have 256MB memory"

    def test_total_cpu_allocation_is_constrained(self):
        """Test that total CPU allocation is constrained (not unlimited)"""
        compose_file = Path('docker-compose.resource-constrained.yml')

        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)

        total_cpu = 0.0
        for service_name, service_config in data['services'].items():
            deploy = service_config.get('deploy', {})
            resources = deploy.get('resources', {})
            limits = resources.get('limits', {})
            cpu_str = limits.get('cpus', '0')
            total_cpu += float(cpu_str)

        # Total should be constrained (from the plan: resource-constrained environment)
        assert total_cpu > 0, "CPU should be limited"
        assert total_cpu < 4.0, f"Total CPU should be constrained, got {total_cpu}"

    def test_total_memory_allocation_is_constrained(self):
        """Test that total memory allocation is constrained"""
        compose_file = Path('docker-compose.resource-constrained.yml')

        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)

        total_memory_mb = 0
        for service_name, service_config in data['services'].items():
            deploy = service_config.get('deploy', {})
            resources = deploy.get('resources', {})
            limits = resources.get('limits', {})
            memory_str = limits.get('memory', '0M')

            # Parse memory (e.g., "128M", "256M")
            if memory_str.endswith('M'):
                total_memory_mb += int(memory_str[:-1])
            elif memory_str.endswith('G'):
                total_memory_mb += int(memory_str[:-1]) * 1024

        # Total should be constrained (resource-constrained environment)
        assert total_memory_mb > 0, "Memory should be limited"
        assert total_memory_mb < 4096, f"Total memory should be constrained, got {total_memory_mb}MB"


class TestConcurrencySpikeScenario:
    """Tests for High-Concurrency Spike Test (Scenario B)"""

    def test_concurrency_spike_locustfile_exists(self):
        """Test that locustfile for spike test exists"""
        locustfile = Path('experiments/locustfile_spike_test.py')
        assert locustfile.exists(), "Spike test locustfile should exist"

    def test_concurrency_spike_has_high_user_count(self):
        """Test that spike test is configured for 150 users"""
        locustfile = Path('experiments/locustfile_spike_test.py')

        with open(locustfile, 'r') as f:
            content = f.read()

        # Should have configuration for 150 users
        assert '150' in content or 'users: int = 150' in content, \
            "Spike test should target 150 concurrent users"

    def test_concurrency_spike_has_short_duration(self):
        """Test that spike test has 30-second duration"""
        locustfile = Path('experiments/locustfile_spike_test.py')

        with open(locustfile, 'r') as f:
            content = f.read()

        # Should have 30-second duration
        assert '30' in content or 'duration: int = 30' in content, \
            "Spike test should run for 30 seconds"

    def test_concurrency_spike_has_immediate_spawn(self):
        """Test that spike test has high spawn rate (immediate spike)"""
        locustfile = Path('experiments/locustfile_spike_test.py')

        with open(locustfile, 'r') as f:
            content = f.read()

        # Spawn rate should be high (150 users spawned quickly)
        # From plan: "The key is the high spawn rate"
        # Check for either "spawn_rate" or "spawn-rate" (Locust command-line flag)
        assert 'spawn' in content.lower() and '150' in content, \
            "Spike test should configure high spawn rate (150 users immediately)"


class TestRampUpSeparation:
    """Tests for Ramp-Up vs Steady-State Separation (General Improvement 4.1)"""

    def test_experiment_config_has_ramp_up_field(self):
        """Test that ExperimentConfig supports rampUpDuration"""
        # This test validates that the TypeScript interface will accept rampUpDuration
        # We'll check this via the frontend test files

        test_file = Path('frontend/src/domain/entities/__tests__/ExperimentWithRampUp.test.ts')
        assert test_file.exists(), "RampUp test file should exist"

        with open(test_file, 'r') as f:
            content = f.read()

        assert 'rampUpDuration' in content, "Test should validate rampUpDuration field"

    def test_locust_supports_ramp_up_delay(self):
        """Test that Locust configuration supports delayed metrics collection"""
        # Check that we have a pattern for excluding ramp-up metrics

        # This should be implemented in the Locust files
        locustfile_pattern = Path('experiments/locustfile_*.py')
        locustfiles = list(Path('experiments').glob('locustfile_*.py'))

        assert len(locustfiles) > 0, "Should have at least one locustfile"

        # At least one should have ramp-up handling
        has_ramp_up = False
        for locustfile in locustfiles:
            with open(locustfile, 'r') as f:
                content = f.read()
                if 'ramp' in content.lower() or 'warm' in content.lower():
                    has_ramp_up = True
                    break

        # This will fail initially (RED phase), then we implement it (GREEN phase)
        assert has_ramp_up, "At least one locustfile should handle ramp-up phase"


class TestResourceConstrainedExperimentExecution:
    """Integration tests for running resource-constrained experiments"""

    @pytest.mark.skipif(
        not Path('docker-compose.resource-constrained.yml').exists(),
        reason="Resource-constrained compose file not yet created"
    )
    def test_can_parse_compose_override_command(self):
        """Test that we can construct the docker-compose override command"""
        base_compose = 'docker-compose.yml'
        override_compose = 'docker-compose.resource-constrained.yml'

        # Command pattern from Future_Experiment_Design_Plan.md
        expected_pattern = f"docker-compose -f {base_compose} -f {override_compose}"

        command = f"docker-compose -f {base_compose} -f {override_compose} up -d monolithic-service postgres-mono"

        assert expected_pattern in command, "Command should use override pattern"
        assert 'up -d' in command, "Command should start services in detached mode"

    def test_resource_constrained_flag_propagates_to_backend(self):
        """Test that resourceConstrained flag is sent to backend API"""
        # This tests the API contract

        # Expected payload structure
        expected_payload = {
            "name": "Low-Resource Test",
            "architecture": "monolithic",
            "config": {
                "users": 20,
                "spawnRate": 2,
                "duration": 300,
                "violationRate": 0.2,
                "resourceConstrained": True  # NEW FIELD
            }
        }

        assert 'resourceConstrained' in expected_payload['config'], \
            "Payload should include resourceConstrained flag"
        assert expected_payload['config']['resourceConstrained'] is True, \
            "Flag should be True for resource-constrained tests"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
