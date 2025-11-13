"""
FastAPI Service for Statistical Analysis
Provides HTTP API for statistical computations
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
import numpy as np
from statistical_engine import StatisticalEngine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Statistical Analysis Service",
    description="Dedicated service for statistical analysis in BPC4MSA experiments",
    version="1.0.0"
)

# Pydantic models for request/response validation
class AnalysisRequest(BaseModel):
    """Request model for statistical analysis"""
    test_type: str = Field(
        ...,
        description="Type of statistical test: t_test, mann_whitney, anova, levene"
    )
    data_groups: List[List[float]] = Field(
        ...,
        description="List of data groups (each group is a list of numeric values)"
    )
    test_name: Optional[str] = Field(
        default="Statistical Test",
        description="Custom name for the test"
    )
    alpha: Optional[float] = Field(
        default=0.05,
        description="Significance level (default: 0.05)"
    )

    @field_validator('test_type')
    @classmethod
    def validate_test_type(cls, v: str) -> str:
        """Validate test type is supported"""
        valid_tests = ['t_test', 'mann_whitney', 'anova', 'levene']
        if v not in valid_tests:
            raise ValueError(
                f"Invalid test_type '{v}'. Must be one of: {', '.join(valid_tests)}"
            )
        return v

    @field_validator('data_groups')
    @classmethod
    def validate_data_groups(cls, v: List[List[float]]) -> List[List[float]]:
        """Validate data groups are not empty and have sufficient data"""
        if not v:
            raise ValueError("data_groups cannot be empty")

        for i, group in enumerate(v):
            if not group:
                raise ValueError(f"Group {i+1} is empty")
            if len(group) < 2:
                raise ValueError(f"Group {i+1} has fewer than 2 data points (got {len(group)})")

        return v

    @field_validator('alpha')
    @classmethod
    def validate_alpha(cls, v: float) -> float:
        """Validate alpha is between 0 and 1"""
        if not 0 < v < 1:
            raise ValueError("alpha must be between 0 and 1")
        return v


class AnalysisResponse(BaseModel):
    """Response model for statistical analysis"""
    success: bool
    test_type: str
    result: Dict[str, Any]
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "statistical-analysis",
        "version": "1.0.0"
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    Perform statistical analysis on provided data

    Args:
        request: AnalysisRequest containing test type, data groups, and parameters

    Returns:
        AnalysisResponse with test results

    Raises:
        HTTPException: If analysis fails or invalid input provided
    """
    try:
        # Initialize statistical engine with specified alpha
        engine = StatisticalEngine(alpha=request.alpha)

        # Convert data groups to numpy arrays
        data_arrays = [np.array(group) for group in request.data_groups]

        # Perform the requested statistical test
        result = None

        if request.test_type == 't_test':
            if len(data_arrays) != 2:
                raise HTTPException(
                    status_code=400,
                    detail=f"t_test requires exactly 2 groups, got {len(data_arrays)}"
                )
            result = engine.two_sample_t_test(
                data_arrays[0],
                data_arrays[1],
                request.test_name
            )

        elif request.test_type == 'mann_whitney':
            if len(data_arrays) != 2:
                raise HTTPException(
                    status_code=400,
                    detail=f"mann_whitney requires exactly 2 groups, got {len(data_arrays)}"
                )
            result = engine.mann_whitney_u_test(
                data_arrays[0],
                data_arrays[1],
                request.test_name
            )

        elif request.test_type == 'anova':
            if len(data_arrays) < 3:
                raise HTTPException(
                    status_code=400,
                    detail=f"anova requires at least 2 groups, got {len(data_arrays)}"
                )
            result = engine.one_way_anova(
                data_arrays,
                request.test_name
            )

        elif request.test_type == 'levene':
            if len(data_arrays) < 2:
                raise HTTPException(
                    status_code=400,
                    detail=f"levene requires at least 2 groups, got {len(data_arrays)}"
                )
            result = engine.levenes_test(data_arrays)

        logger.info(
            f"Successfully completed {request.test_type} analysis: "
            f"p_value={result.get('p_value', 'N/A')}, "
            f"significant={result.get('is_significant', 'N/A')}"
        )

        return {
            "success": True,
            "test_type": request.test_type,
            "result": result,
            "message": "Analysis completed successfully"
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except ValueError as e:
        logger.error(f"Validation error in {request.test_type}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in {request.test_type}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during analysis: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Statistical Analysis Service",
        "version": "1.0.0",
        "description": "Dedicated microservice for statistical analysis in BPC4MSA experiments",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
