from dataclasses import dataclass
from typing import Dict, Any
import logging
from datetime import datetime
from pathlib import Path
import traceback
import socket
import os
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ollama import chat, ResponseError
from pydantic import BaseModel, Field

from app.core.logger import setup_daily_logger
from app.services.pid_manager import get_pid_manager

# Timeout for Ollama requests (seconds)
OLLAMA_TIMEOUT = 60

# Thread pool for running blocking Ollama calls
ollama_executor = ThreadPoolExecutor(max_workers=2)


def get_ollama_runner_pid() -> int:
    """Get the PID of the current ollama runner process for this model."""
    try:
        # Find ollama runner processes
        result = subprocess.run(
            ["pgrep", "-f", "ollama runner"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            pids = [int(p.strip()) for p in result.stdout.strip().split('\n') if p.strip()]
            # Return the most recent one (highest PID)
            return max(pids) if pids else 0
    except Exception:
        pass
    return 0


@dataclass
class PipelineConfig:
    refiner_model: str = "glm-4.7-flash"
    researcher_model: str = "qwen3.5"
    max_refine_words: int = 250
    refiner_temperature: float = 0.0
    researcher_temperature: float = 0.2


class RefinedPrompt(BaseModel):
    refined_prompt: str = Field(..., description="Improved version of the user's prompt")


class QuantResearchPipeline:

    def __init__(self, config: PipelineConfig, log_dir: str = "logs"):
        self.config = config
        self.log_dir = Path(log_dir)
        self.logger = setup_daily_logger("pipeline", log_dir=log_dir)
        
        self.logger.info("=" * 80)
        self.logger.info("QuantResearchPipeline initializing...")
        self.logger.info(f"Config: refiner={config.refiner_model}, researcher={config.researcher_model}")
        self.logger.info(f"  max_refine_words={config.max_refine_words}")
        self.logger.info(f"  refiner_temp={config.refiner_temperature}, researcher_temp={config.researcher_temperature}")
        
        self.researcher_system_prompt = """
You are an elite quantitative financial researcher and engineer with deep expertise in:

- Stochastic calculus, measure-theoretic probability, and statistical inference
- Derivatives pricing (Black-Scholes, local/stochastic volatility, SABR, Heston)
- Market microstructure and high-frequency trading systems
- Numerical methods (Monte Carlo, finite difference methods, optimization)
- Time series modeling (ARIMA, GARCH, state-space models, Kalman filtering)
- Portfolio construction, risk management, and factor modeling

Behavioral constraints:

1. Always reason from first principles and mathematical structure.
2. Prefer formal derivations, equations, and precise definitions over intuition.
3. Avoid vague or high-level explanations unless explicitly requested.
4. When discussing finance, anchor arguments in no-arbitrage, replication, and probabilistic frameworks.
5. Explicitly state assumptions (e.g., log-normality, frictionless markets, stationarity).
6. When relevant, provide computational methods or algorithmic formulations.
7. Be critical of naive strategies and highlight model risk, overfitting, and structural limitations.
8. Use precise notation where useful and avoid unnecessary simplification.
9. Do not give generic textbook summaries—focus on depth, rigor, and edge.

Output style:

- Concise but dense
- Equation-driven where appropriate
- No fluff
- Treat the user as mathematically sophisticated
""".strip()

        self._setup_prompts()
        self.logger.info("QuantResearchPipeline initialized successfully")
        self.logger.info("=" * 80)

    def _setup_prompts(self):
        """Initialize system prompts for refiner and researcher."""
        self.logger.debug("Setting up system prompts")
        
        self.refiner_system_prompt = """
You are a prompt refiner.

Your job is NOT to answer the user's question.
Your only job is to rewrite the user's prompt so that a downstream expert quantitative researcher can answer it better.

Rules:
1. Preserve the user's intent exactly.
2. Do not add facts, assumptions, or invented context.
3. Make the prompt more precise, explicit, and technically actionable.
4. If the prompt is vague, add useful structure:
   - objective
   - assumptions requested
   - mathematical depth
   - desired output format
   - relevant constraints
5. Keep it concise.
6. Output only the improved prompt.
""".strip()

    def word_count(self, text: str) -> int:
        """Count words in text with error handling."""
        try:
            if not text:
                self.logger.warning("Empty text provided to word_count")
                return 0
            count = len(text.strip().split())
            self.logger.debug(f"Word count: {count}")
            return count
        except Exception as e:
            self.logger.error(f"Error in word_count: {e}", exc_info=True)
            return 0

    def should_refine(self, prompt: str) -> bool:
        """Determine if prompt should be refined based on length and content."""
        try:
            self.logger.debug(f"Evaluating if refinement needed for prompt: {prompt[:50]}...")
            
            if not prompt:
                self.logger.warning("Empty prompt provided to should_refine")
                return False
            
            wc = self.word_count(prompt)

            if wc == 0:
                self.logger.info("Prompt has 0 words, skipping refinement")
                return False
            if wc > self.config.max_refine_words:
                self.logger.info(f"Prompt too long ({wc} words > {self.config.max_refine_words}), skipping refinement")
                return False

            if wc < 80:
                self.logger.info(f"Prompt is short ({wc} words), will refine")
                return True

            lower = prompt.lower()
            vague_markers = [
                "explain",
                "tell me about",
                "help me with",
                "what do you think",
                "derive",
                "analyze",
                "strategy",
                "model",
                "volatility",
                "options",
                "pricing",
            ]

            has_vague_marker = any(marker in lower for marker in vague_markers)
            if has_vague_marker:
                self.logger.info(f"Prompt contains vague markers, will refine")
            else:
                self.logger.info(f"Prompt is specific enough, skipping refinement")
            
            return has_vague_marker
        
        except Exception as e:
            self.logger.error(f"Error in should_refine: {e}", exc_info=True)
            return False

    def refine_prompt(self, user_prompt: str) -> str:
        """
        First try structured output.
        If the local Ollama/model setup does not support it cleanly,
        fall back to plain text.
        """
        self.logger.info(f"Attempting to refine prompt with model: {self.config.refiner_model}")
        
        if not user_prompt:
            self.logger.error("Cannot refine empty prompt")
            raise ValueError("User prompt cannot be empty")
        
        try:
            self.logger.debug("Trying structured output format")
            # Set socket timeout for this request
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(OLLAMA_TIMEOUT)
            try:
                response = chat(
                    model=self.config.refiner_model,
                    messages=[
                        {"role": "system", "content": self.refiner_system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    format=RefinedPrompt.model_json_schema(),
                    options={"temperature": self.config.refiner_temperature},
                )
            finally:
                socket.setdefaulttimeout(original_timeout)

            parsed = RefinedPrompt.model_validate_json(response.message.content)
            refined = parsed.refined_prompt.strip()
            self.logger.info(f"Successfully refined prompt using structured output")
            self.logger.debug(f"Refined prompt: {refined[:100]}...")
            return refined

        except socket.timeout:
            self.logger.error(f"Timeout after {OLLAMA_TIMEOUT}s in structured refinement")
            self.logger.warning("Falling back to plain text format")
            raise
        
        except ResponseError as e:
            self.logger.error(f"Ollama ResponseError in structured refinement: {e.error} (status: {e.status_code})")
            self.logger.warning("Falling back to plain text format")
            raise
        
        except Exception as e:
            self.logger.warning(f"Structured output failed ({type(e).__name__}: {e}), falling back to plain text")
            
            try:
                # Set socket timeout for this request
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(OLLAMA_TIMEOUT)
                try:
                    response = chat(
                        model=self.config.refiner_model,
                        messages=[
                            {"role": "system", "content": self.refiner_system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        options={"temperature": self.config.refiner_temperature},
                    )
                finally:
                    socket.setdefaulttimeout(original_timeout)
                refined = response.message.content.strip()
                self.logger.info(f"Successfully refined prompt using plain text format")
                self.logger.debug(f"Refined prompt: {refined[:100]}...")
                return refined
            
            except ResponseError as e:
                self.logger.error(f"Ollama ResponseError in plain text refinement: {e.error} (status: {e.status_code})", exc_info=True)
                raise
            except socket.timeout:
                self.logger.error(f"Timeout after {OLLAMA_TIMEOUT}s in plain text refinement")
                raise
            
            except Exception as inner_e:
                self.logger.error(f"Failed to refine prompt in plain text format: {inner_e}", exc_info=True)
                raise

    def run_researcher(self, prompt: str) -> str:
        """Run the researcher model with error handling and logging."""
        self.logger.info(f"Running researcher model: {self.config.researcher_model}")
        
        if not prompt:
            self.logger.error("Cannot run researcher with empty prompt")
            raise ValueError("Prompt cannot be empty")
        
        pid_manager = get_pid_manager()
        registered_pid = None
        
        try:
            self.logger.debug(f"Sending prompt to researcher: {prompt[:100]}...")
            
            # Register the Ollama runner PID before starting
            registered_pid = get_ollama_runner_pid()
            if registered_pid:
                pid_manager.register_pid(
                    registered_pid, 
                    process_type="ollama_runner",
                    model=self.config.researcher_model,
                    prompt=prompt
                )
                self.logger.info(f"Registered Ollama runner PID: {registered_pid}")
            
            # Set socket timeout for this request (longer for researcher)
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(OLLAMA_TIMEOUT * 2)  # 2x timeout for researcher
            try:
                response = chat(
                    model=self.config.researcher_model,
                    messages=[
                        {"role": "system", "content": self.researcher_system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    options={"temperature": self.config.researcher_temperature},
                )
            finally:
                socket.setdefaulttimeout(original_timeout)
            
            # Unregister PID after successful completion
            if registered_pid:
                pid_manager.unregister_pid(registered_pid)
            
            answer = response.message.content
            self.logger.info(f"Researcher generated response of length: {len(answer)} chars")
            self.logger.debug(f"Response preview: {answer[:200]}...")
            return answer
        
        except ResponseError as e:
            self.logger.error(f"Ollama ResponseError in researcher: {e.error} (status: {e.status_code})", exc_info=True)
            raise
        except socket.timeout:
            self.logger.error(f"Timeout after {OLLAMA_TIMEOUT * 2}s in researcher")
            raise
        except Exception as e:
            self.logger.error(f"Error in run_researcher: {type(e).__name__}: {e}", exc_info=True)
            raise
        finally:
            # Always try to unregister PID on exit
            if registered_pid:
                pid_manager.unregister_pid(registered_pid)

    def process_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """Main pipeline to process user prompt through refinement and research."""
        self.logger.info("=" * 80)
        self.logger.info(f"Starting prompt processing pipeline")
        self.logger.info(f"Original prompt: {user_prompt[:100]}...")
        
        if not user_prompt or not user_prompt.strip():
            self.logger.error("Received empty or whitespace-only prompt")
            return {
                "success": False,
                "used_refinement": False,
                "original_prompt": user_prompt or "",
                "prompt_sent_to_researcher": user_prompt or "",
                "final_answer": "",
                "error_type": "ValueError",
                "error": "User prompt cannot be empty",
            }
        
        try:
            if self.should_refine(user_prompt):
                self.logger.info("Prompt requires refinement")
                try:
                    prompt_for_researcher = self.refine_prompt(user_prompt)
                    used_refinement = True
                    self.logger.info("Prompt refinement successful")
                except Exception as refine_error:
                    self.logger.error(f"Refinement failed: {refine_error}", exc_info=True)
                    self.logger.warning("Proceeding with original prompt")
                    prompt_for_researcher = user_prompt
                    used_refinement = False
            else:
                self.logger.info("Prompt does not require refinement")
                prompt_for_researcher = user_prompt
                used_refinement = False

            self.logger.info("Sending prompt to researcher")
            final_answer = self.run_researcher(prompt_for_researcher)
            
            self.logger.info("Pipeline completed successfully")
            self.logger.info("=" * 80)

            return {
                "success": True,
                "used_refinement": used_refinement,
                "original_prompt": user_prompt,
                "prompt_sent_to_researcher": prompt_for_researcher,
                "final_answer": final_answer,
            }

        except ResponseError as e:
            self.logger.error(f"Ollama API error: {e.error} (HTTP {e.status_code})", exc_info=True)
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "used_refinement": False,
                "original_prompt": user_prompt,
                "prompt_sent_to_researcher": user_prompt,
                "final_answer": "",
                "error_type": "ollama_response_error",
                "error": e.error,
                "status_code": e.status_code,
            }

        except ValueError as e:
            self.logger.error(f"Validation error: {e}", exc_info=True)
            return {
                "success": False,
                "used_refinement": False,
                "original_prompt": user_prompt,
                "prompt_sent_to_researcher": user_prompt,
                "final_answer": "",
                "error_type": "ValueError",
                "error": str(e),
            }

        except Exception as e:
            self.logger.error(f"Unexpected error in pipeline: {type(e).__name__}: {e}", exc_info=True)
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "used_refinement": False,
                "original_prompt": user_prompt,
                "prompt_sent_to_researcher": user_prompt,
                "final_answer": "",
                "error_type": type(e).__name__,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
