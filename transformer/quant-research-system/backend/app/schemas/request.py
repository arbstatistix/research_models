"""
================================================================================
QUANT RESEARCH PIPELINE - REQUEST SCHEMAS
================================================================================

This module defines Pydantic models for API request validation.
Pydantic provides automatic validation, serialization, and documentation.

PURPOSE:
--------
- Validate incoming request data
- Generate OpenAPI schema for documentation
- Provide clear error messages for invalid input
- Type hints for IDE support

MODELS:
-------
- PromptRequest: Request body for POST /api/research

VALIDATION:
-----------
Pydantic automatically validates:
- Required fields are present
- Field types match expected types
- Field constraints are met (min_length, max_length, etc.)

RELATIONSHIPS:
--------------
- Used by: app.api.routes (as request body type)
- Generates: OpenAPI schema for /docs endpoint

================================================================================
"""

from pydantic import BaseModel, Field
from typing import Optional


class PromptRequest(BaseModel):
    """
    Request model for the research pipeline endpoint.
    
    This model validates and documents the expected request body
    for POST /api/research. It ensures the prompt is provided
    and meets minimum requirements.
    
    Attributes:
        prompt: The user's research question or query.
               Must be non-empty string.
    
    Validation:
        - prompt is required (no default value)
        - prompt must have at least 1 character (min_length=1)
        - Whitespace-only strings are technically valid but
          should be rejected by the endpoint logic
    
    Example Request:
        {
            "prompt": "What is the Black-Scholes model?"
        }
        
    Example Invalid:
        {} - Missing prompt field
        {"prompt": ""} - Empty string
    
    OpenAPI Schema:
        This model generates OpenAPI documentation visible at /docs
        including the examples and descriptions.
    """
    
    prompt: str = Field(
        ...,  # ... means required (no default)
        min_length=1,
        max_length=50000,  # Prevent extremely long prompts
        description="User prompt to send through the quant research pipeline. "
                    "Can be a question, topic, or detailed research request.",
        examples=[
            "What is the Black-Scholes formula?",
            "Explain arbitrage in quantitative finance",
            "Derive the Greeks for a European call option",
            "How does the Heston model handle stochastic volatility?"
        ],
    )
    
    class Config:
        """Pydantic model configuration."""
        
        # Generate JSON schema with examples
        json_schema_extra = {
            "example": {
                "prompt": "Explain the concept of delta hedging in options trading"
            }
        }


class PromptRequestWithOptions(BaseModel):
    """
    Extended request model with additional options.
    
    This model allows clients to specify processing options
    in addition to the prompt. Currently reserved for future use.
    
    Attributes:
        prompt: The user's research question (required)
        skip_refinement: If true, skip prompt refinement step
        model_override: Use a specific model instead of default
        max_tokens: Limit response length
        
    Note:
        This model is defined but not currently used by the API.
        It's here for future extensibility.
    """
    
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="User prompt to process"
    )
    
    skip_refinement: bool = Field(
        default=False,
        description="Skip the prompt refinement step and send directly to researcher"
    )
    
    model_override: Optional[str] = Field(
        default=None,
        description="Override the default researcher model (e.g., 'glm-4.7-flash')"
    )
    
    max_tokens: Optional[int] = Field(
        default=None,
        ge=100,
        le=32000,
        description="Maximum tokens in response (if supported by model)"
    )
    
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Override sampling temperature (0.0-2.0)"
    )
