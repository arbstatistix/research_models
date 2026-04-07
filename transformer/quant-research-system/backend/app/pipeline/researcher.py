from ollama import chat, ResponseError
import logging

logger = logging.getLogger(__name__)

class QuantResearcher:
    """Handles quantitative research using configured model."""

    def __init__(self, model: str = "qwen3.5", temperature: float = 0.2):
        self.model = model
        self.temperature = temperature
        self.system_prompt = """
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

CRITICAL OUTPUT FORMATTING RULES:

1. **ALWAYS wrap ALL mathematical expressions in LaTeX delimiters:**
   - Use `$...$` for inline math (e.g., `$d_1 = \\frac{\\ln(S/K) + (r + \\sigma^2/2)T}{\\sigma\\sqrt{T}}$`)
   - Use `$$...$$` for display equations on their own line

2. **NEVER output raw math without delimiters.** Examples of WRONG output:
   - WRONG: `d1 = ln(S/K) + (r + sigma^2/2)T / sigma*sqrt(T)`
   - CORRECT: `$d_1 = \\frac{\\ln(S/K) + (r + \\sigma^2/2)T}{\\sigma\\sqrt{T}}$`

3. **Use proper LaTeX syntax:**
   - Fractions: `\\frac{numerator}{denominator}`
   - Subscripts: `x_i`, `S_t`
   - Superscripts: `x^2`, `e^{-rT}`
   - Greek letters: `\\sigma`, `\\mu`, `\\Delta`, `\\Pi`
   - Functions: `\\ln()`, `\\max()`, `\\sqrt{}`

4. **Structure your response with markdown:**
   - Use `###` for section headers
   - Use bullet points with `*` for lists
   - Use `**bold**` for emphasis on key terms
   - Use tables with `|` for variable definitions when appropriate

5. **Output each equation only ONCE** - do not duplicate equations with different formatting.

Output style:

- Concise but dense
- Equation-driven where appropriate (with proper LaTeX delimiters)
- No fluff
- Treat the user as mathematically sophisticated
- ALWAYS use $...$ or $$...$$ for math
""".strip()

    def research(self, prompt: str) -> str:
        """Run research on the given prompt."""
        logger.info(f"Running research with model: {self.model}")

        if not prompt:
            raise ValueError("Prompt cannot be empty")

        response = chat(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            options={"temperature": self.temperature},
        )

        answer = response.message.content
        
        # Post-process to ensure math is properly wrapped
        answer = self._post_process_math(answer)
        
        logger.info(f"Research completed, response length: {len(answer)} chars")
        return answer
    
    def _post_process_math(self, text: str) -> str:
        """Post-process to fix common math formatting issues."""
        lines = text.split('\n')
        processed = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                processed.append(line)
                continue
            
            # Detect equation lines (contain = and math symbols but no $)
            is_equation = (
                '=' in stripped and
                not stripped.startswith('$') and
                not stripped.startswith('$$') and
                any(c in stripped for c in ['_', '^', '\\', 'σ', 'μ', 'Δ', 'Π', '∑', '∫'])
            )
            
            if is_equation:
                # Wrap in display math
                line = f"$${stripped}$$"
            
            processed.append(line)
        
        return '\n'.join(processed)