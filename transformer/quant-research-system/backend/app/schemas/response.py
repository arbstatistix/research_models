"""
================================================================================
QUANT RESEARCH PIPELINE - RESPONSE SCHEMAS
================================================================================

This module defines Pydantic models for API response structures.
These models ensure consistent response formats across all endpoints.

PURPOSE:
--------
- Define consistent response structure
- Generate OpenAPI schema for documentation
- Validate response data before sending
- Provide type hints for IDE support

MODELS:
-------
- PipelineResponse: Response for POST /api/research

RESPONSE STRUCTURE:
-------------------
Successful response:
    {
        "success": true,
        "used_refinement": true,
        "original_prompt": "user's question",
        "prompt_sent_to_researcher": "refined question",
        "final_answer": "detailed response..."
    }

Failed response:
    {
        "success": false,
        "used_refinement": false,
        "original_prompt": "user's question",
        "prompt_sent_to_researcher": "user's question",
        "final_answer": "",
        "error_type": "TimeoutError",
        "error": "Model inference timed out after 120s"
    }

RELATIONSHIPS:
--------------
- Used by: app.api.routes (as response_model)
- Created from: app.pipeline.pipeline result dict
- Generates: OpenAPI schema for /docs endpoint

================================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional


class PipelineResponse(BaseModel):
    """
    Response model for the research pipeline endpoint.
    
    This model defines the structure of responses from POST /api/research.
    It handles both successful responses and error cases with a consistent
    format that the frontend can easily process.
    
    Success Fields:
        success: True if pipeline completed without errors
        used_refinement: True if prompt was refined before research
        original_prompt: The user's original input
        prompt_sent_to_researcher: What was actually sent to the model
        final_answer: The generated research response
    
    Error Fields (only populated on failure):
        error_type: Exception class name (e.g., "TimeoutError")
        error: Human-readable error message
        status_code: HTTP status if applicable
        traceback: Full Python traceback (debug only)
    
    Example Success:
        {
            "success": true,
            "used_refinement": true,
            "original_prompt": "What is arbitrage?",
            "prompt_sent_to_researcher": "Define arbitrage in quantitative...",
            "final_answer": "## Arbitrage\\n\\nArbitrage is the..."
        }
    
    Example Error:
        {
            "success": false,
            "used_refinement": false,
            "original_prompt": "What is arbitrage?",
            "prompt_sent_to_researcher": "What is arbitrage?",
            "final_answer": "",
            "error_type": "TimeoutError",
            "error": "Model inference timed out after 120 seconds"
        }
    """
    
    # =========================================================================
    # SUCCESS FIELDS
    # =========================================================================
    
    success: bool = Field(
        ...,
        description="Whether the pipeline execution completed successfully. "
                    "True means final_answer contains valid content."
    )
    
    used_refinement: bool = Field(
        default=False,
        description="Whether the original prompt was refined before sending "
                    "to the researcher model. Short or vague prompts are "
                    "typically refined for better results."
    )
    
    original_prompt: str = Field(
        default="",
        description="The exact prompt as submitted by the user, "
                    "before any refinement or processing."
    )
    
    prompt_sent_to_researcher: str = Field(
        default="",
        description="The actual prompt that was sent to the researcher model. "
                    "This may be different from original_prompt if refinement "
                    "was applied, or identical if refinement was skipped/failed."
    )
    
    final_answer: str = Field(
        default="",
        description="The generated research response from the model. "
                    "Contains markdown-formatted content with equations, "
                    "code blocks, and structured explanations. "
                    "Empty string if the pipeline failed."
    )
    
    # =========================================================================
    # ERROR FIELDS
    # =========================================================================
    
    error_type: Optional[str] = Field(
        default=None,
        description="The type/class of error that occurred. "
                    "Examples: 'TimeoutError', 'ValueError', 'ResponseError'. "
                    "Only populated when success=false."
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Human-readable error message describing what went wrong. "
                    "Only populated when success=false."
    )
    
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status code if the error came from an API call "
                    "(e.g., Ollama returning an error). "
                    "Only populated for HTTP-related errors."
    )
    
    traceback: Optional[str] = Field(
        default=None,
        description="Full Python traceback for debugging purposes. "
                    "Only populated for unexpected errors in development. "
                    "Should not be exposed in production."
    )
    
    class Config:
        """Pydantic model configuration."""
        
        # Generate JSON schema with examples
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "used_refinement": True,
                    "original_prompt": "explain black scholes",
                    "prompt_sent_to_researcher": "Derive the Black-Scholes partial differential equation from first principles using Itô's lemma. Include the key assumptions and provide the solution for a European call option.",
                    "final_answer": "## Black-Scholes Model\n\n### Derivation\n\nThe Black-Scholes PDE can be derived using...",
                    "error_type": None,
                    "error": None
                },
                {
                    "success": False,
                    "used_refinement": False,
                    "original_prompt": "test",
                    "prompt_sent_to_researcher": "test",
                    "final_answer": "",
                    "error_type": "TimeoutError",
                    "error": "Model inference timed out after 120 seconds"
                }
            ]
        }


class ModelsResponse(BaseModel):
    """
    Response model for GET /api/models endpoint.
    
    Returns the current pipeline model configuration.
    Useful for debugging and monitoring which models are in use.
    """
    
    refiner_model: str = Field(
        description="The model used for prompt refinement"
    )
    
    researcher_model: str = Field(
        description="The model used for research generation"
    )
    
    max_refine_words: int = Field(
        description="Word count threshold above which refinement is skipped"
    )
    
    refiner_temperature: float = Field(
        description="Sampling temperature for the refiner (0.0 = deterministic)"
    )
    
    researcher_temperature: float = Field(
        description="Sampling temperature for the researcher"
    )


class PIDInfo(BaseModel):
    """
    Information about a tracked process.
    
    Used in the response from GET /api/pids.
    """
    
    pid: int = Field(description="Process ID")
    type: str = Field(description="Process type (e.g., 'ollama_runner')")
    model: str = Field(description="Model name being run")
    prompt: Optional[str] = Field(description="Truncated prompt (max 100 chars)")
    created_at: str = Field(description="ISO timestamp when registered")
    status: str = Field(description="Current status: 'running' or 'terminated'")
    cpu_percent: Optional[float] = Field(description="Current CPU usage percentage")
    memory_mb: Optional[float] = Field(description="Current memory usage in MB")


class PIDListResponse(BaseModel):
    """
    Response model for GET /api/pids endpoint.
    """
    
    success: bool = Field(default=True)
    count: int = Field(description="Number of active processes")
    pids: list[PIDInfo] = Field(description="List of active process details")


class KillResponse(BaseModel):
    """
    Response model for kill endpoints.
    """
    
    pid: int = Field(description="The targeted process ID")
    success: bool = Field(description="Whether the kill succeeded")
    message: str = Field(description="Human-readable result message")
