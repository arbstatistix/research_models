from ollama import chat, ResponseError
from pydantic import BaseModel, Field
import logging
import json
import re

logger = logging.getLogger(__name__)

class RefinedPrompt(BaseModel):
    refined_prompt: str = Field(..., description="Improved version of the user's prompt")


class PromptRefiner:
    """Handles prompt refinement logic."""

    def __init__(self, model: str = "glm-4.7-flash", temperature: float = 0.0):
        self.model = model
        self.temperature = temperature
        self.system_prompt = """
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

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from text that may have markdown code blocks or extra content."""
        # Try to find JSON in code blocks
        code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        matches = re.findall(code_block_pattern, text)
        if matches:
            return matches[0].strip()
        
        # Try to find JSON between curly braces
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, text)
        if match:
            return match.group(0).strip()
        
        return text.strip()

    def _create_fallback_refinement(self, user_prompt: str) -> str:
        """Create a structured refinement when the model fails."""
        return f"""Objective: {user_prompt}

Please provide a rigorous quantitative analysis including:
- Mathematical formulation and notation
- Key assumptions and their implications
- Step-by-step derivation or algorithm
- Edge cases and limitations
- Practical implementation considerations"""

    def refine(self, user_prompt: str) -> str:
        """
        Refine the user prompt using the configured model.
        First tries structured output, falls back to plain text.
        """
        logger.info(f"Refining prompt with model: {self.model}")

        if not user_prompt:
            raise ValueError("User prompt cannot be empty")

        try:
            # Try structured output first
            response = chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                format=RefinedPrompt.model_json_schema(),
                options={"temperature": self.temperature},
            )

            content = response.message.content.strip()
            
            # Handle empty response
            if not content:
                logger.warning("Empty response from model, using fallback")
                return self._create_fallback_refinement(user_prompt)
            
            # Try to parse as JSON
            try:
                parsed = RefinedPrompt.model_validate_json(content)
                refined = parsed.refined_prompt.strip()
                logger.info("Successfully refined prompt using structured output")
                return refined
            except Exception as json_err:
                # Try to extract JSON from text
                extracted = self._extract_json_from_text(content)
                if extracted != content:
                    parsed = RefinedPrompt.model_validate_json(extracted)
                    refined = parsed.refined_prompt.strip()
                    logger.info("Successfully refined prompt after JSON extraction")
                    return refined
                raise json_err

        except Exception as e:
            logger.warning(f"Structured output failed ({type(e).__name__}: {e}), falling back to plain text")

            try:
                # Fallback to plain text
                response = chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    options={"temperature": self.temperature},
                )
                
                refined = response.message.content.strip()
                
                # Handle empty fallback response
                if not refined:
                    logger.warning("Empty fallback response, using default refinement")
                    return self._create_fallback_refinement(user_prompt)
                
                logger.info("Successfully refined prompt using plain text format")
                return refined
                
            except Exception as fallback_err:
                logger.error(f"Fallback also failed: {fallback_err}")
                return self._create_fallback_refinement(user_prompt)