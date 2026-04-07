# Backend App Package

Main application package containing all business logic and API definitions.

## Module Structure

```
app/
├── __init__.py         # Package marker
├── main.py             # FastAPI application instance
├── api/                # HTTP endpoint definitions
│   ├── __init__.py
│   └── routes.py       # All API routes
├── core/               # Core utilities
│   ├── __init__.py
│   ├── config.py       # Configuration management
│   └── logger.py       # Logging system
├── pipeline/           # Research pipeline
│   ├── __init__.py
│   ├── pipeline.py     # Main pipeline class
│   ├── refiner.py      # Prompt refinement (if separated)
│   └── researcher.py   # Research generation (if separated)
├── schemas/            # Data models
│   ├── __init__.py
│   ├── request.py      # Request validation models
│   └── response.py     # Response structure models
├── services/           # External service integrations
│   ├── __init__.py
│   ├── ollama_client.py    # Ollama API wrapper
│   └── pid_manager.py      # Process tracking
└── utils/              # Utility functions
    ├── __init__.py
    └── helpers.py      # General helpers
```

## Module Relationships

```
                    ┌─────────────────┐
                    │    main.py      │
                    │ (FastAPI app)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
       ┌──────────┐   ┌──────────┐   ┌──────────┐
       │  api/    │   │  core/   │   │ schemas/ │
       │ routes   │   │ config   │   │ request  │
       └────┬─────┘   │ logger   │   │ response │
            │         └────┬─────┘   └────┬─────┘
            │              │              │
            ▼              │              │
       ┌──────────┐        │              │
       │ pipeline/│◄───────┴──────────────┘
       │ pipeline │
       └────┬─────┘
            │
            ▼
       ┌──────────┐
       │ services/│
       │pid_manager
       └──────────┘
```

## Data Flow

### Request Processing

1. **Request arrives** at FastAPI endpoint in `api/routes.py`
2. **Validation** via Pydantic model from `schemas/request.py`
3. **Configuration** loaded from `core/config.py`
4. **Pipeline execution** in `pipeline/pipeline.py`
5. **Process tracking** via `services/pid_manager.py`
6. **Response formatting** via `schemas/response.py`
7. **Logging** throughout via `core/logger.py`

### Import Order

```python
# main.py imports
from app.api.routes import router
from app.core.logger import setup_daily_logger

# routes.py imports
from app.schemas.request import PromptRequest
from app.schemas.response import PipelineResponse
from app.pipeline.pipeline import QuantResearchPipeline
from app.core.config import get_pipeline_config
from app.core.logger import setup_daily_logger
from app.services.pid_manager import get_pid_manager

# pipeline.py imports
from app.core.logger import setup_daily_logger
from app.services.pid_manager import get_pid_manager
```

## Key Classes

### QuantResearchPipeline (pipeline/pipeline.py)
Main business logic class. Handles:
- Prompt refinement decision
- Ollama model calls
- Error handling and timeout management

### PIDManager (services/pid_manager.py)
Process tracking class. Handles:
- Registering active model processes
- Monitoring resource usage
- Killing stuck processes

### PipelineConfig (pipeline/pipeline.py)
Configuration dataclass with:
- Model names
- Temperature settings
- Word count thresholds

## Error Handling Strategy

1. **Validation errors** → 400 Bad Request
2. **Ollama errors** → Logged + returned in response
3. **Timeouts** → Logged + returned in response
4. **Unexpected errors** → 500 + logged with traceback

All errors are logged with:
- Timestamp
- Error type
- Error message
- Full traceback (for unexpected errors)
- Request context (client IP, prompt preview)
