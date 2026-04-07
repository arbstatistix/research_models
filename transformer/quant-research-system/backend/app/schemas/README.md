# Schemas Module

Pydantic models for request validation and response structure.

## Files

- `__init__.py` - Package marker
- `request.py` - Request body validation models
- `response.py` - Response structure models

## Purpose

Pydantic models provide:
- **Automatic validation** - Invalid data raises clear errors
- **Type coercion** - Strings converted to int/float where needed
- **Documentation** - OpenAPI schema generated automatically
- **IDE support** - Type hints for autocomplete

## Request Models

### PromptRequest

```python
class PromptRequest(BaseModel):
    prompt: str = Field(
        ...,              # Required (no default)
        min_length=1,     # Can't be empty
        max_length=50000, # Reasonable limit
        description="User prompt to process"
    )
```

**Valid requests:**
```json
{"prompt": "What is arbitrage?"}
{"prompt": "Derive the Black-Scholes formula from first principles."}
```

**Invalid requests:**
```json
{}                    # Missing prompt field
{"prompt": ""}        # Empty string (min_length=1)
{"prompt": 123}       # Wrong type (not string)
```

## Response Models

### PipelineResponse

```python
class PipelineResponse(BaseModel):
    # Success fields
    success: bool
    used_refinement: bool = False
    original_prompt: str = ""
    prompt_sent_to_researcher: str = ""
    final_answer: str = ""
    
    # Error fields (optional)
    error_type: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    traceback: Optional[str] = None
```

**Success response:**
```json
{
    "success": true,
    "used_refinement": true,
    "original_prompt": "explain black scholes",
    "prompt_sent_to_researcher": "Derive the Black-Scholes PDE...",
    "final_answer": "## Black-Scholes Model\n\n..."
}
```

**Error response:**
```json
{
    "success": false,
    "used_refinement": false,
    "original_prompt": "test",
    "prompt_sent_to_researcher": "test",
    "final_answer": "",
    "error_type": "TimeoutError",
    "error": "Model inference timed out after 120 seconds"
}
```

## OpenAPI Integration

Models automatically generate OpenAPI schemas visible at `/docs`:

```python
class Config:
    json_schema_extra = {
        "example": {
            "prompt": "Explain delta hedging"
        }
    }
```

## Validation Flow

```
HTTP Request Body (JSON)
         │
         ▼
    Parse JSON
         │
         ▼
   Pydantic Model
         │
    ┌────┴────┐
    │         │
    ▼         ▼
 Valid    Invalid
    │         │
    ▼         ▼
 Continue  422 Error
```

## Usage in Routes

```python
from app.schemas.request import PromptRequest
from app.schemas.response import PipelineResponse

@router.post("/research", response_model=PipelineResponse)
async def research(request: PromptRequest):
    # request.prompt is validated and typed
    result = pipeline.process_prompt(request.prompt)
    
    # Return dict, Pydantic converts to response model
    return PipelineResponse(**result)
```

## Adding New Models

```python
from pydantic import BaseModel, Field
from typing import Optional

class NewRequest(BaseModel):
    """Description for OpenAPI docs."""
    
    field1: str = Field(
        ...,                    # Required
        min_length=1,
        description="Field description"
    )
    
    field2: Optional[int] = Field(
        default=None,           # Optional with default
        ge=0,                   # Greater than or equal to 0
        le=100,                 # Less than or equal to 100
        description="Optional numeric field"
    )
```
