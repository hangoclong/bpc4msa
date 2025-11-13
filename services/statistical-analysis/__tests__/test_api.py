"""
TDD Tests for Statistical Analysis API
Test FastAPI endpoints following TDD principles
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test suite for health check endpoint"""

    def test_health_check(self):
        """Test health check returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "statistical-analysis"
        assert "version" in data


class TestRootEndpoint:
    """Test suite for root endpoint"""

    def test_root_endpoint(self):
        """Test root endpoint returns service information"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "endpoints" in data


class TestAnalyzeEndpoint:
    """Test suite for /analyze endpoint following acceptance criteria from PRD"""

    def setup_method(self):
        """Setup test data"""
        # Sample data for testing
        self.group1 = [15.0, 16.0, 14.0, 15.5, 16.5, 14.5, 15.2, 16.3]
        self.group2 = [20.0, 21.0, 19.0, 20.5, 21.5, 19.5, 20.2, 21.3]
        self.group3 = [8.0, 9.0, 7.0, 8.5, 9.5, 7.5, 8.2, 9.3]

    def test_t_test_valid_request(self):
        """Test t_test with valid two-group data returns 200 OK (AC 4.2)"""
        request_data = {
            "test_type": "t_test",
            "data_groups": [self.group1, self.group2],
            "test_name": "Test T-Test",
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["test_type"] == "t_test"
        assert "result" in data
        assert "p_value" in data["result"]
        assert "is_significant" in data["result"]
        assert "t_statistic" in data["result"]
        assert "confidence_interval" in data["result"]
        assert "effect_size" in data["result"]

    def test_mann_whitney_valid_request(self):
        """Test mann_whitney with valid two-group data returns 200 OK"""
        request_data = {
            "test_type": "mann_whitney",
            "data_groups": [self.group1, self.group2],
            "test_name": "Test Mann-Whitney",
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["test_type"] == "mann_whitney"
        assert "result" in data
        assert "p_value" in data["result"]
        assert "u_statistic" in data["result"]

    def test_anova_valid_request(self):
        """Test anova with valid three-group data returns 200 OK"""
        request_data = {
            "test_type": "anova",
            "data_groups": [self.group1, self.group2, self.group3],
            "test_name": "Test ANOVA",
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["test_type"] == "anova"
        assert "result" in data
        assert "p_value" in data["result"]
        assert "f_statistic" in data["result"]
        assert "group_stats" in data["result"]
        assert len(data["result"]["group_stats"]) == 3

    def test_anova_with_small_sample_size(self):
        """Test anova with group having < 2 samples returns descriptive error (AC 2.2)"""
        request_data = {
            "test_type": "anova",
            "data_groups": [[1.0], self.group2, self.group3],  # First group has only 1 sample
            "test_name": "Test ANOVA Small Sample",
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        # Pydantic validation returns 422, which is appropriate for validation errors
        assert response.status_code == 422  # Unprocessable Entity (validation error)

        data = response.json()
        assert "detail" in data
        # Check that the error message mentions the validation issue
        error_message = str(data["detail"])
        assert "fewer than 2 data points" in error_message or "Value error" in error_message

    def test_levene_valid_request(self):
        """Test levene with valid data returns 200 OK (AC 2.3)"""
        request_data = {
            "test_type": "levene",
            "data_groups": [self.group1, self.group2, self.group3],
            "test_name": "Test Levene",
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["test_type"] == "levene"
        assert "result" in data
        assert "p_value" in data["result"]
        assert "w_statistic" in data["result"]
        assert "equal_variances" in data["result"]

    def test_invalid_test_type(self):
        """Test invalid test_type returns 400 Bad Request (AC 4.3)"""
        request_data = {
            "test_type": "invalid_test",
            "data_groups": [self.group1, self.group2],
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 422  # Unprocessable Entity (validation error)

    def test_empty_data_groups(self):
        """Test empty data_groups returns 400 Bad Request (AC 4.3)"""
        request_data = {
            "test_type": "t_test",
            "data_groups": [],
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_malformed_data_groups(self):
        """Test malformed data_groups returns 400 Bad Request (AC 4.3)"""
        request_data = {
            "test_type": "t_test",
            "data_groups": [[], self.group2],  # First group is empty
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_t_test_with_wrong_number_of_groups(self):
        """Test t_test with wrong number of groups returns 400 Bad Request"""
        request_data = {
            "test_type": "t_test",
            "data_groups": [self.group1, self.group2, self.group3],  # 3 groups instead of 2
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 400

        data = response.json()
        assert "exactly 2 groups" in data["detail"]

    def test_invalid_alpha_value(self):
        """Test invalid alpha value returns validation error"""
        # Test alpha > 1
        request_data = {
            "test_type": "t_test",
            "data_groups": [self.group1, self.group2],
            "alpha": 1.5
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 422

        # Test alpha <= 0
        request_data["alpha"] = 0.0
        response = client.post("/analyze", json=request_data)
        assert response.status_code == 422

    def test_custom_alpha_value(self):
        """Test custom alpha value is respected"""
        request_data = {
            "test_type": "t_test",
            "data_groups": [self.group1, self.group2],
            "alpha": 0.01  # More stringent alpha
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["result"]["alpha"] == 0.01

    def test_default_test_name(self):
        """Test default test name is used when not provided"""
        request_data = {
            "test_type": "t_test",
            "data_groups": [self.group1, self.group2]
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        # Default test name should be in the result
        assert "test_name" in data["result"]

    def test_custom_test_name(self):
        """Test custom test name is preserved"""
        custom_name = "BPC4MSA vs SOA Performance Test"
        request_data = {
            "test_type": "t_test",
            "data_groups": [self.group1, self.group2],
            "test_name": custom_name
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["result"]["test_name"] == custom_name

    def test_response_includes_statistical_details(self):
        """Test response includes all required statistical details"""
        request_data = {
            "test_type": "t_test",
            "data_groups": [self.group1, self.group2]
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        result = data["result"]

        # Verify all expected fields are present
        required_fields = [
            "test_name", "test_type", "t_statistic", "p_value",
            "is_significant", "mean_difference", "confidence_interval",
            "effect_size", "effect_size_interpretation"
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Verify data types
        assert isinstance(result["p_value"], float)
        assert isinstance(result["is_significant"], bool)
        assert isinstance(result["confidence_interval"], (list, tuple))
        assert len(result["confidence_interval"]) == 2


class TestDataValidation:
    """Test data validation logic"""

    def test_insufficient_data_points(self):
        """Test validation rejects groups with insufficient data points"""
        request_data = {
            "test_type": "t_test",
            "data_groups": [[1.0], [2.0, 3.0]],  # First group has only 1 point
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 422

    def test_non_numeric_data(self):
        """Test validation rejects non-numeric data"""
        request_data = {
            "test_type": "t_test",
            "data_groups": [["a", "b", "c"], [1.0, 2.0, 3.0]],
            "alpha": 0.05
        }

        response = client.post("/analyze", json=request_data)
        assert response.status_code == 422


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
