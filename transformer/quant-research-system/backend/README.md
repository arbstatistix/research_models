# Backend - Quant Research Pipeline API

FastAPI-based REST API for quantitative financial research using local LLMs.

## Directory Structure

```
backend/
├── run.py                  # Application entry point (starts Uvicorn)
├── requirements.txt        # Python dependencies
├── logs/                   # Daily rotating log files
│   ├── YYYY-MM-DD_all.log      # All log levels
│   ├── YYYY-MM-DD_info.log     # INFO and above
│   ├── YYYY-MM-DD_warnings.log # WARNING and above
│   └── YYYY-MM-DD_errors.log   # ERROR and above
└── app/                    # Main application package
    ├── main.py             # FastAPI app definition
    ├── api/                # API endpoints
    ├── core/               # Configuration and logging
    ├── pipeline/           # Research pipeline logic
    ├── schemas/            # Request/response models
    ├── services/           # External services (PID manager)
    └── utils/              # Utility functions
```

## Execution Flow

### Startup Sequence

```
1. python run.py
   │
   ├─> Add backend/ to Python path
   ├─> Load configuration from .env
   ├─> Initialize daily logger
   └─> Start Uvicorn server
       │
       └─> app/main.py
           │
           ├─> Create FastAPI instance
           ├─> Configure CORS middleware
           ├─> Mount API router at /api
           └─> Register lifecycle events
               │
               └─> app/api/routes.py
                   │
                   ├─> Create thread pool executor
                   ├─> Load pipeline configuration
                   └─> Initialize QuantResearchPipeline
```

### Request Flow (POST /api/research)

```
Client Request
     │
     ▼
┌──────────────────────────────────────────────────────────────────┐
│  1. CORS Middleware checks origin (localhost:5173 allowed)       │
└──────────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────────┐
│  2. routes.py: process_research_prompt()                         │
│     - Validate prompt is not empty                               │
│     - Log request details (client IP, timestamp, prompt)         │
└──────────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────────┐
│  3. Submit to ThreadPoolExecutor (non-blocking)                  │
│     - Allows health checks during inference                      │
│     - Prevents event loop blocking                               │
└──────────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────────┐
│  4. pipeline.py: process_prompt()                                │
│     │                                                            │
│     ├─> should_refine() - Check if prompt needs refinement       │
│     │   └─> Word count < 80? Contains vague markers?             │
│     │                                                            │
│     ├─> refine_prompt() - If needed                              │
│     │   └─> Call Ollama with refiner model                       │
│     │   └─> Parse structured JSON response                       │
│     │   └─> Fallback to plain text if JSON fails                 │
│     │                                                            │
│     └─> run_researcher() - Generate answer                       │
│         └─> Register PID with PIDManager                         │
│         └─> Call Ollama with researcher model                    │
│         └─> Unregister PID on completion                         │
└──────────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────────┐
│  5. Return PipelineResponse to client                            │
│     - success: true/false                                        │
│     - used_refinement: whether prompt was refined                │
│     - final_answer: the generated response                       │
└──────────────────────────────────────────────────────────────────┘
```

## Module Descriptions

### run.py
Entry point that starts the Uvicorn ASGI server. Handles Python path setup and logging initialization.

### app/main.py
FastAPI application definition. Configures CORS, mounts routes, defines lifecycle events and global error handler.

### app/api/routes.py
All API endpoint definitions. Handles request validation, pipeline execution, and response formatting.

### app/core/config.py
Configuration management. Loads settings from environment variables with sensible defaults.

### app/core/logger.py
Logging system. Creates daily rotating log files with multiple severity levels.

### app/pipeline/pipeline.py
Core research logic. Implements prompt refinement and researcher model calls.

### app/schemas/request.py
Pydantic models for request validation (PromptRequest).

### app/schemas/response.py
Pydantic models for response structure (PipelineResponse).

### app/services/pid_manager.py
Process tracking. Monitors Ollama runner processes for debugging and kill functionality.

## Running the Backend

```bash
# From backend/ directory
python run.py

# Or with virtual environment
source venv/bin/activate
python run.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | / | API info |
| GET | /health | Health check |
| POST | /api/research | Process research prompt |
| GET | /api/models | Current model config |
| GET | /api/pids | List active processes |
| POST | /api/pids/{pid}/kill | Kill specific process |
| POST | /api/pids/kill-all | Kill all processes |
| GET | /api/server/kill | Emergency shutdown |

## Logging

All modules use the daily logger. Log files are created in `logs/`:

- `_all.log` - Everything (DEBUG+)
- `_info.log` - Operational events (INFO+)
- `_warnings.log` - Potential issues (WARNING+)
- `_errors.log` - Failures only (ERROR+)

View logs:
```bash
tail -f logs/$(date +%Y-%m-%d)_all.log
```
