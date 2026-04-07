from typing import Optional
from pydantic import BaseModel, Field


class PipelineSuccessResponse(BaseModel):
    success: bool = Field(True, description="Whether the pipeline completed successfully")
    used_refinement: bool = Field(..., description="Whether the prompt was refined before research")
    original_prompt: str = Field(..., description="Original user prompt")
    prompt_sent_to_researcher: str = Field(..., description="Prompt actually sent to the researcher model")
    final_answer: str = Field(..., description="Final researcher output")


class PipelineErrorResponse(BaseModel):
    success: bool = Field(False, description="Whether the pipeline completed successfully")
    error_type: str = Field(..., description="Type/category of error")
    error: str = Field(..., description="Human-readable error message")
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP or provider status code if available",
    )
    traceback: Optional[str] = Field(
        default=None,
        description="Traceback for unexpected internal errors",
    )


class PipelineResponse(BaseModel):
    success: bool
    used_refinement: Optional[bool] = None
    original_prompt: Optional[str] = None
    prompt_sent_to_researcher: Optional[str] = None
    final_answer: Optional[str] = None
    error_type: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    traceback: Optional[str] = None