# API Module

HTTP endpoint definitions for the Quant Research Pipeline.

## Files

- `__init__.py` - Package marker
- `routes.py` - All API endpoint definitions

## Endpoints Overview

### Information Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |

### Research Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/research` | Process research prompt |
| GET | `/api/models` | Get model configuration |

### Process Management Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/pids` | List active processes |
| POST | `/api/pids/{pid}/kill` | Kill specific process |
| POST | `/api/pids/kill-all` | Kill all processes |
| GET | `/api/server/kill` | Emergency shutdown |

## Request/Response Flow

### POST /api/research

```
Request:
{
    "prompt": "What is the Black-Scholes model?"
}

Response (Success):
{
    "success": true,
    "used_refinement": true,
    "original_prompt": "What is the Black-Scholes model?",
    "prompt_sent_to_researcher": "Derive the Black-Scholes PDE...",
    "final_answer": "## Black-Scholes Model\n\n..."
}

Response (Error):
{
    "success": false,
    "error_type": "TimeoutError",
    "error": "Model inference timed out"
}
```

## Thread Pool Architecture

The research endpoint uses a thread pool to prevent blocking:

```
FastAPI Event Loop (async)
         │
         │ await run_in_executor()
         ▼
ThreadPoolExecutor (max_workers=2)
         │
         │ blocking call
         ▼
    pipeline.process_prompt()
         │
         │ blocking call
         ▼
    ollama.chat()
```

This allows:
- Health checks remain responsive during inference
- PID management endpoints stay accessible
- Multiple requests can queue (up to 2 concurrent)

## Error Handling

All endpoints follow this pattern:

```python
@router.post("/endpoint")
async def endpoint(request: RequestModel):
    logger.info("Request received")
    
    try:
        # Validate input
        if invalid:
            raise HTTPException(400, "Invalid input")
        
        # Process request
        result = await process()
        
        # Return success
        return ResponseModel(**result)
        
    except HTTPException:
        raise  # Re-raise HTTP errors
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")
```

## Logging

All endpoints log:
- Request arrival (INFO)
- Validation results (DEBUG)
- Processing steps (DEBUG/INFO)
- Response details (INFO)
- Errors (ERROR with traceback)

Request IDs are generated for tracing:
```
[162803123456] NEW RESEARCH REQUEST
[162803123456] Client IP: 127.0.0.1
[162803123456] Pipeline execution completed in 45.23s
```
