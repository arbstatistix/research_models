# Pipeline Module

Core research pipeline implementing the two-stage LLM processing.

## Files

- `__init__.py` - Package marker
- `pipeline.py` - Main QuantResearchPipeline class
- `refiner.py` - Prompt refinement logic (if separated)
- `researcher.py` - Research generation logic (if separated)

## Two-Stage Pipeline

```
User Prompt
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1: REFINEMENT (Optional)                             │
│                                                             │
│  Input:  "What is arbitrage?"                               │
│                                                             │
│  Process:                                                   │
│  1. Check word count (< 80 words → refine)                  │
│  2. Check for vague markers ("explain", "what is", etc.)    │
│  3. If refinement needed:                                   │
│     - Send to refiner model with system prompt              │
│     - Parse structured JSON response                        │
│     - Fall back to plain text if JSON fails                 │
│                                                             │
│  Output: "Define arbitrage within quantitative finance.     │
│           Include the mathematical conditions for           │
│           no-arbitrage and common arbitrage strategies."    │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2: RESEARCH                                          │
│                                                             │
│  Input: Refined prompt (or original if refinement skipped)  │
│                                                             │
│  Process:                                                   │
│  1. Register Ollama runner PID for tracking                 │
│  2. Send to researcher model with expert system prompt      │
│  3. Wait for response (up to 120s timeout)                  │
│  4. Unregister PID on completion                            │
│                                                             │
│  Output: Detailed, equation-rich research response          │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### PipelineConfig (dataclass)

```python
@dataclass
class PipelineConfig:
    refiner_model: str = "qwen3.5"
    researcher_model: str = "qwen3.5"
    max_refine_words: int = 250
    refiner_temperature: float = 0.0
    researcher_temperature: float = 0.2
```

### QuantResearchPipeline (class)

Main pipeline class with methods:

| Method | Purpose |
|--------|---------|
| `__init__` | Initialize with config, setup prompts |
| `should_refine` | Decide if prompt needs refinement |
| `refine_prompt` | Refine prompt via LLM |
| `run_researcher` | Generate research response |
| `process_prompt` | Main entry point |

### System Prompts

**Refiner prompt** instructs the model to:
- Preserve user intent
- Make prompt more precise
- Add structure (objectives, assumptions, format)
- Output only the improved prompt

**Researcher prompt** instructs the model to:
- Reason from first principles
- Prefer formal derivations and equations
- State assumptions explicitly
- Be critical of naive strategies
- Treat user as mathematically sophisticated

## Error Handling

### Timeout Strategy

```python
OLLAMA_TIMEOUT = 60  # seconds for refiner
# Researcher gets 2x timeout (120s)

# Socket-level timeout
socket.setdefaulttimeout(OLLAMA_TIMEOUT)
try:
    response = chat(...)
finally:
    socket.setdefaulttimeout(original_timeout)
```

### Fallback Strategy

```
Structured JSON output
         │
         │ fails
         ▼
Plain text output
         │
         │ fails
         ▼
Use original prompt (skip refinement)
         │
         │ researcher fails
         ▼
Return error response
```

## Usage

```python
from app.pipeline.pipeline import QuantResearchPipeline, PipelineConfig

# Create config
config = PipelineConfig(
    refiner_model="qwen3.5",
    researcher_model="glm-4.7-flash"
)

# Create pipeline
pipeline = QuantResearchPipeline(config, log_dir="logs")

# Process prompt
result = pipeline.process_prompt("What is the Black-Scholes model?")

# Result structure
{
    "success": True,
    "used_refinement": True,
    "original_prompt": "What is the Black-Scholes model?",
    "prompt_sent_to_researcher": "Derive the Black-Scholes PDE...",
    "final_answer": "## Black-Scholes Model\n\n..."
}
```

## Logging

The pipeline logs extensively:

```
INFO  - Starting prompt processing pipeline
INFO  - Original prompt: What is the Black-Scholes model?...
INFO  - Prompt is short (6 words), will refine
INFO  - Attempting to refine prompt with model: qwen3.5
INFO  - Successfully refined prompt using structured output
INFO  - Running researcher model: qwen3.5
INFO  - Registered Ollama runner PID: 12345
INFO  - Researcher generated response of length: 5432 chars
INFO  - Pipeline completed successfully
```
