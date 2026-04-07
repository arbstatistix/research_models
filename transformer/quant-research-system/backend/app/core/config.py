import os
from app.pipeline.pipeline import PipelineConfig

def get_pipeline_config() -> PipelineConfig:
    """
    Get pipeline configuration from environment variables with sensible defaults.
    """
    return PipelineConfig(
        refiner_model=os.getenv("REFINER_MODEL", "qwen3.5"),
        researcher_model=os.getenv("RESEARCHER_MODEL", "qwen3.5"),
        max_refine_words=int(os.getenv("MAX_REFINE_WORDS", "250")),
        refiner_temperature=float(os.getenv("REFINER_TEMPERATURE", "0.0")),
        researcher_temperature=float(os.getenv("RESEARCHER_TEMPERATURE", "0.2")),
    )


# Export settings for uvicorn
class Settings:
    """Application settings for uvicorn and other services."""
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))


settings = Settings()