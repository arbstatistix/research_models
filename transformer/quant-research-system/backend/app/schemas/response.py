from pydantic import BaseModel, Field
from typing import Optional


class PipelineResponse(BaseModel):
    """Response model for the research pipeline endpoint."""
    
    success: bool = Field(
        ...,
        description="Whether the pipeline execution was successful"
    )
    used_refinement: bool = Field(
        default=False,
        description="Whether the prompt was refined before sending to researcher"
    )
    original_prompt: str = Field(
        default="",
        description="The original user prompt as received"
    )
    prompt_sent_to_researcher: str = Field(
        default="",
        description="The prompt that was actually sent to the researcher (refined or original)"
    )
    final_answer: str = Field(
        default="",
        description="The research answer from the model (empty if error occurred)"
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Type of error if pipeline failed"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if pipeline failed"
    )
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status code for API errors"
    )
    traceback: Optional[str] = Field(
        default=None,
        description="Full traceback for debugging (only included on unexpected errors)"
    )
