"""
================================================================================
QUANT RESEARCH PIPELINE - CONFIGURATION MANAGEMENT
================================================================================

This module handles all configuration loading from environment variables.
It provides centralized configuration management for the entire application.

CONFIGURATION SOURCES:
----------------------
1. Environment variables (highest priority)
2. .env file (loaded by python-dotenv)
3. Default values (fallback)

CONFIGURATION CATEGORIES:
-------------------------
1. Pipeline Config: Model selection, temperatures, word limits
2. Server Config: Host, port, CORS settings

ENVIRONMENT VARIABLES:
----------------------
Pipeline:
    REFINER_MODEL           Model for prompt refinement (default: qwen3.5)
    RESEARCHER_MODEL        Model for research generation (default: qwen3.5)
    MAX_REFINE_WORDS        Skip refinement above this word count (default: 250)
    REFINER_TEMPERATURE     Temperature for refiner (default: 0.0)
    RESEARCHER_TEMPERATURE  Temperature for researcher (default: 0.2)

Server:
    BACKEND_HOST           Server bind address (default: 0.0.0.0)
    BACKEND_PORT           Server port (default: 8000)

USAGE:
------
    from app.core.config import get_pipeline_config, settings
    
    # Get pipeline configuration
    config = get_pipeline_config()
    print(config.refiner_model)
    
    # Get server settings
    print(settings.host, settings.port)

RELATIONSHIPS:
--------------
- Used by: app.api.routes, app.pipeline.pipeline, run.py
- Depends on: app.pipeline.pipeline.PipelineConfig (dataclass)
- Loads: Environment variables via os.getenv

================================================================================
"""

import os
from typing import Optional

from app.pipeline.pipeline import PipelineConfig
from app.core.logger import setup_daily_logger

# =============================================================================
# LOGGER INITIALIZATION
# =============================================================================
logger = setup_daily_logger("config", log_dir="logs")


def get_pipeline_config() -> PipelineConfig:
    """
    Get pipeline configuration from environment variables.
    
    Loads configuration values from environment variables with sensible
    defaults. This allows runtime configuration without code changes.
    
    Configuration Values:
        - refiner_model: LLM model for prompt refinement
        - researcher_model: LLM model for research generation
        - max_refine_words: Word count threshold for skipping refinement
        - refiner_temperature: Sampling temperature for refiner (0.0 = deterministic)
        - researcher_temperature: Sampling temperature for researcher
    
    Returns:
        PipelineConfig: Dataclass with all pipeline configuration values
        
    Example:
        >>> config = get_pipeline_config()
        >>> print(f"Using {config.refiner_model} for refinement")
        Using qwen3.5 for refinement
        
    Note:
        Temperature of 0.0 makes output deterministic (same input = same output).
        Higher temperatures (0.5-1.0) increase creativity but reduce consistency.
    """
    logger.debug("Loading pipeline configuration from environment...")
    
    # ==========================================================================
    # LOAD CONFIGURATION VALUES
    # ==========================================================================
    
    # Model selection
    refiner_model = os.getenv("REFINER_MODEL", "qwen3.5")
    researcher_model = os.getenv("RESEARCHER_MODEL", "qwen3.5")
    
    # Refinement settings
    max_refine_words = int(os.getenv("MAX_REFINE_WORDS", "250"))
    
    # Temperature settings (controls randomness)
    refiner_temperature = float(os.getenv("REFINER_TEMPERATURE", "0.0"))
    researcher_temperature = float(os.getenv("RESEARCHER_TEMPERATURE", "0.2"))
    
    # ==========================================================================
    # LOG CONFIGURATION
    # ==========================================================================
    logger.info("Pipeline configuration loaded:")
    logger.info(f"  Refiner model: {refiner_model}")
    logger.info(f"  Researcher model: {researcher_model}")
    logger.info(f"  Max refine words: {max_refine_words}")
    logger.info(f"  Refiner temperature: {refiner_temperature}")
    logger.info(f"  Researcher temperature: {researcher_temperature}")
    
    # ==========================================================================
    # CREATE AND RETURN CONFIG
    # ==========================================================================
    config = PipelineConfig(
        refiner_model=refiner_model,
        researcher_model=researcher_model,
        max_refine_words=max_refine_words,
        refiner_temperature=refiner_temperature,
        researcher_temperature=researcher_temperature,
    )
    
    logger.debug("PipelineConfig instance created successfully")
    return config


class Settings:
    """
    Application settings for the Uvicorn server.
    
    This class holds server-level configuration that is separate from
    the pipeline configuration. It's designed for settings that affect
    how the server runs rather than how requests are processed.
    
    Attributes:
        host (str): IP address to bind the server to
        port (int): Port number to listen on
        
    Environment Variables:
        BACKEND_HOST: Server bind address (default: 0.0.0.0)
        BACKEND_PORT: Server port (default: 8000)
        
    Usage:
        >>> from app.core.config import settings
        >>> print(f"Server at {settings.host}:{settings.port}")
        Server at 0.0.0.0:8000
        
    Note:
        Using 0.0.0.0 as host makes the server accessible from any network
        interface. Use 127.0.0.1 for localhost-only access.
    """
    
    def __init__(self):
        """Initialize settings from environment variables."""
        logger.debug("Initializing server settings...")
        
        # Server bind address
        # 0.0.0.0 = all interfaces, 127.0.0.1 = localhost only
        self.host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
        
        # Server port number
        self.port: int = int(os.getenv("BACKEND_PORT", "8000"))
        
        logger.info(f"Server settings: host={self.host}, port={self.port}")
        logger.debug("Server settings initialized successfully")
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Settings(host='{self.host}', port={self.port})"


# =============================================================================
# GLOBAL SETTINGS INSTANCE
# =============================================================================
# Create a singleton instance for use throughout the application
# This is instantiated at module import time
logger.debug("Creating global Settings instance...")
settings = Settings()
logger.debug(f"Global settings created: {settings}")
