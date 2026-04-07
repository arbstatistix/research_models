from ollama import chat, ResponseError
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Wrapper client for Ollama API interactions."""
    
    def __init__(self, model: str = "qwen3.5", temperature: float = 0.2):
        self.model = model
        self.temperature = temperature
    
    def chat(
        self,
        messages: list,
        format: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a chat request to Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            format: Optional JSON schema for structured output
            options: Additional options like temperature
            
        Returns:
            The content of the response message
            
        Raises:
            ResponseError: If Ollama API returns an error
            Exception: For other unexpected errors
        """
        try:
            logger.debug(f"Sending chat request to model: {self.model}")
            
            chat_options = {"temperature": self.temperature}
            if options:
                chat_options.update(options)
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "options": chat_options
            }
            
            if format:
                kwargs["format"] = format
            
            response = chat(**kwargs)
            content = response.message.content
            
            logger.debug(f"Received response of length: {len(content)}")
            return content
            
        except ResponseError as e:
            logger.error(f"Ollama ResponseError: {e.error} (status: {e.status_code})")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Ollama chat: {type(e).__name__}: {e}")
            raise
    
    def chat_structured(
        self,
        messages: list,
        output_schema: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a chat request with structured output format.
        
        Args:
            messages: List of message dicts
            output_schema: JSON schema for the expected output
            options: Additional options
            
        Returns:
            The structured response content
        """
        return self.chat(messages, format=output_schema, options=options)
    
    def is_available(self) -> bool:
        """Check if the Ollama service is available."""
        try:
            # Try a simple request to check availability
            chat(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                options={"temperature": 0}
            )
            return True
        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False
