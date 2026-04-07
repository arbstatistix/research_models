# Quant Research System

A full-stack application for quantitative financial research powered by local LLMs via Ollama. Features a Bloomberg Terminal-inspired interface with intelligent prompt refinement and expert-level research capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)

## Overview

This system provides a sophisticated research pipeline that:

1. **Refines vague prompts** into precise, technically actionable queries
2. **Generates expert-level responses** using a specialized quantitative finance persona
3. **Renders complex output** including LaTeX math, tables, and code blocks
4. **Persists chat history** across sessions with local storage

### Key Features

- 🧠 **Two-Stage Pipeline**: Automatic prompt refinement + expert researcher
- 📊 **Bloomberg-Style UI**: Dark theme terminal interface with chat sidebar
- 🔢 **LaTeX Math Rendering**: Full KaTeX support for equations
- 💾 **Persistent Sessions**: Chat history saved to localStorage
- ⚡ **Process Management**: Monitor and kill stuck model processes
- 🔄 **Non-Blocking API**: Server remains responsive during long inference
- 📝 **Comprehensive Logging**: Daily rotating logs with multiple severity levels

---

## Architecture

```
quant-research-system/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py       # API endpoints
│   │   ├── core/
│   │   │   ├── config.py       # Environment configuration
│   │   │   └── logger.py       # Daily rotating logger
│   │   ├── pipeline/
│   │   │   └── pipeline.py     # Main research pipeline
│   │   ├── schemas/
│   │   │   ├── request.py      # Pydantic request models
│   │   │   └── response.py     # Pydantic response models
│   │   ├── services/
│   │   │   ├── ollama_client.py    # Ollama API wrapper
│   │   │   └── pid_manager.py      # Process tracking
│   │   └── main.py             # FastAPI app entry
│   ├── logs/                   # Daily log files
│   ├── requirements.txt
│   └── run.py                  # Uvicorn launcher
├── frontend/                   # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── BloombergQuantTerminal.tsx  # Main terminal UI
│   │   │   ├── PIDManager.tsx              # Process monitor widget
│   │   │   └── chat/
│   │   │       └── ChatSidebar.tsx         # Session sidebar
│   │   ├── hooks/
│   │   │   ├── useChatHistory.ts   # Session persistence
│   │   │   └── usePipeline.ts      # API hook
│   │   ├── services/
│   │   │   └── api.ts              # Backend API client
│   │   ├── types/
│   │   │   ├── chat.ts             # Chat type definitions
│   │   │   └── pipeline.ts         # Pipeline type definitions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── shared/
│   └── pipeline_schema.json    # Shared schema definitions
├── .env                        # Environment variables
├── run.sh                      # Start both services
└── README.md
```

---

## Prerequisites

### Required

- **Python 3.11+**
- **Node.js 18+**
- **Ollama** with models installed

### Ollama Models

The system uses two models (configurable via `.env`):

```bash
# Install recommended models
ollama pull qwen3.5        # Default researcher (6.6 GB)
ollama pull glm-4.7-flash  # Alternative refiner (19 GB)
```

Check available models:
```bash
ollama list
```

---

## Quick Start

### 1. Clone and Navigate

```bash
cd /path/to/quant-research-system
```

### 2. Configure Environment (Optional)

Edit `.env` to customize models and settings:

```env
# Model Configuration
REFINER_MODEL=qwen3.5
RESEARCHER_MODEL=qwen3.5

# Refinement Settings
MAX_REFINE_WORDS=250
REFINER_TEMPERATURE=0.0
RESEARCHER_TEMPERATURE=0.2

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### 3. Start the Application

```bash
./run.sh
```

This will:
- Kill any existing processes on ports 8000/5173
- Create Python virtual environment (first run)
- Install Python dependencies
- Start backend at http://localhost:8000
- Install Node dependencies (first run)
- Start frontend at http://localhost:5173
- Handle graceful shutdown on Ctrl+C

### 4. Open the UI

Navigate to **http://localhost:5173** in your browser.

---

## Manual Setup

### Backend Only

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python run.py
```

### Frontend Only

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

---

## API Reference

### Base URL

```
http://localhost:8000/api
```

### Endpoints

#### `POST /api/research`

Process a research prompt through the pipeline.

**Request:**
```json
{
  "prompt": "Explain the Black-Scholes model"
}
```

**Response:**
```json
{
  "success": true,
  "used_refinement": true,
  "original_prompt": "Explain the Black-Scholes model",
  "prompt_sent_to_researcher": "Provide a rigorous derivation of the Black-Scholes PDE...",
  "final_answer": "## Black-Scholes Model\n\nThe Black-Scholes model...",
  "error_type": null,
  "error": null
}
```

#### `GET /api/models`

Get current model configuration.

**Response:**
```json
{
  "refiner_model": "qwen3.5",
  "researcher_model": "qwen3.5",
  "max_refine_words": 250,
  "refiner_temperature": 0.0,
  "researcher_temperature": 0.2
}
```

#### `GET /api/pids`

List active model processes.

**Response:**
```json
{
  "success": true,
  "count": 1,
  "pids": [
    {
      "pid": 12345,
      "type": "ollama_runner",
      "model": "qwen3.5",
      "prompt": "Explain arbitrage...",
      "created_at": "2026-04-07T16:28:28.301931",
      "status": "running",
      "cpu_percent": 85.2,
      "memory_mb": 1654
    }
  ]
}
```

#### `POST /api/pids/{pid}/kill`

Kill a specific process.

**Response:**
```json
{
  "pid": 12345,
  "success": true,
  "message": "Process ollama (PID 12345) terminated gracefully"
}
```

#### `POST /api/pids/kill-all`

Kill all tracked processes.

#### `GET /api/server/kill`

Emergency shutdown of the backend server.

#### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-07T16:30:10.761511"
}
```

---

## Pipeline Deep Dive

### Two-Stage Processing

```
User Prompt → [Refiner] → Refined Prompt → [Researcher] → Final Answer
```

#### Stage 1: Prompt Refinement

The refiner transforms vague queries into precise, actionable prompts:

| Before | After |
|--------|-------|
| "What is arbitrage?" | "Provide a rigorous definition of arbitrage within quantitative finance. Detail the mathematical conditions for no-arbitrage, the Fundamental Theorem of Asset Pricing, and common arbitrage strategies with their risk profiles." |
| "Explain options" | "Derive the Black-Scholes PDE from first principles using Itô calculus. Include the replication argument, risk-neutral pricing, and discuss model assumptions and their violations in practice." |

**Refinement is skipped** when:
- Prompt exceeds 250 words (configurable)
- Prompt is already technically detailed

#### Stage 2: Research Generation

The researcher model uses a specialized system prompt:

```
You are an elite quantitative financial researcher with expertise in:
- Stochastic calculus and measure-theoretic probability
- Derivatives pricing (Black-Scholes, SABR, Heston)
- Market microstructure and HFT systems
- Numerical methods (Monte Carlo, FDM)
- Time series modeling (ARIMA, GARCH, Kalman)
- Portfolio construction and risk management

Behavioral constraints:
1. Reason from first principles
2. Prefer formal derivations over intuition
3. State assumptions explicitly
4. Be critical of naive strategies
```

### Timeout Handling

The pipeline implements socket-level timeouts to prevent indefinite hangs:

- **Refiner**: 60 seconds
- **Researcher**: 120 seconds

If a timeout occurs, the pipeline returns an error response rather than hanging.

### Thread Pool Execution

Model inference runs in a separate thread pool, keeping the FastAPI event loop responsive:

```python
result = await loop.run_in_executor(
    pipeline_executor,
    pipeline.process_prompt,
    request.prompt
)
```

This ensures:
- Health checks respond during inference
- PID endpoints remain accessible
- Multiple requests can queue

---

## Frontend Features

### Bloomberg Terminal Interface

The UI mimics a professional trading terminal:

- **Dark theme** with amber/orange accents
- **Monospace fonts** for data display
- **Status indicators** for connection and processing state

### Chat Sidebar

- Create new chat sessions
- Browse history by title
- Delete individual sessions
- Sessions persist in localStorage

### Math Rendering

Full LaTeX support via KaTeX:

```latex
$$\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + rS\frac{\partial V}{\partial S} - rV = 0$$
```

### LLM Output Preprocessing

The frontend automatically cleans model output:

- Removes conversation tokens (`<|im_start|>`, etc.)
- Deduplicates repeated lines
- Strips spam patterns and excessive formatting
- Fixes malformed tables

### Process Manager Widget

Floating button (bottom-right) shows:

- Count of active model processes
- CPU and memory usage per process
- One-click kill functionality
- Emergency server shutdown

---

## Logging

### Log Files

Logs are written to `backend/logs/` with daily rotation:

```
logs/
├── 2026-04-07_all.log       # All log levels
├── 2026-04-07_info.log      # INFO and above
├── 2026-04-07_warnings.log  # WARNING and above
└── 2026-04-07_errors.log    # ERROR and above
```

### Log Format

```
2026-04-07 16:28:03 - pipeline - INFO - [pipeline.py:334] - Starting prompt processing pipeline
```

### Viewing Logs

```bash
# Follow all logs
tail -f backend/logs/$(date +%Y-%m-%d)_all.log

# View errors only
cat backend/logs/$(date +%Y-%m-%d)_errors.log
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REFINER_MODEL` | `qwen3.5` | Model for prompt refinement |
| `RESEARCHER_MODEL` | `qwen3.5` | Model for research generation |
| `MAX_REFINE_WORDS` | `250` | Skip refinement above this word count |
| `REFINER_TEMPERATURE` | `0.0` | Temperature for refiner (deterministic) |
| `RESEARCHER_TEMPERATURE` | `0.2` | Temperature for researcher (slight variation) |
| `BACKEND_HOST` | `0.0.0.0` | Backend bind address |
| `BACKEND_PORT` | `8000` | Backend port |
| `LOG_DIR` | `logs` | Log directory path |

### Recommended Model Configurations

| Use Case | Refiner | Researcher |
|----------|---------|------------|
| Fast (lower quality) | `qwen3.5` | `qwen3.5` |
| Balanced | `qwen3.5` | `glm-4.7-flash` |
| High quality (slow) | `glm-4.7-flash` | `glm-4.7-flash` |

---

## Troubleshooting

### Port Already in Use

```bash
# Kill processes on port 8000
lsof -ti:8000 | xargs kill -9

# Or use the startup script which handles this automatically
./run.sh
```

### Model Hanging / Slow Response

1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Check active processes via the PID Manager widget

3. Kill stuck processes:
   ```bash
   curl -X POST http://localhost:8000/api/pids/kill-all
   ```

4. Consider using a smaller model or increasing timeouts

### Empty Response / JSON Parse Error

This usually means the model timed out. Check:

1. `backend/logs/*_errors.log` for timeout messages
2. System resources (RAM, CPU) during inference
3. Try a smaller model

### CORS Errors

Ensure the frontend URL is in the CORS allowlist in `backend/app/main.py`:

```python
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

### Virtual Environment Issues

```bash
# Recreate venv
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload (default)
python run.py

# Run without reload
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Development server with HMR
npm run dev

# Type checking
npx tsc --noEmit

# Build for production
npm run build
```

### Adding New Endpoints

1. Add route in `backend/app/api/routes.py`
2. Add schema in `backend/app/schemas/`
3. Add frontend API call in `frontend/src/services/api.ts`
4. Add types in `frontend/src/types/`

---

## Tech Stack

### Backend

- **FastAPI** - Modern async Python web framework
- **Pydantic** - Data validation and serialization
- **Ollama** - Local LLM inference
- **Uvicorn** - ASGI server
- **psutil** - Process management

### Frontend

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **react-markdown** - Markdown rendering
- **KaTeX** - LaTeX math rendering
- **remark-gfm** - GitHub Flavored Markdown

---

## License

MIT License - See LICENSE file for details.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

---

## Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [KaTeX](https://katex.org/) for beautiful math rendering
