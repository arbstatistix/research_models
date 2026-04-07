from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        description="User prompt to send through the quant research pipeline",
        examples=["what is the black-scholes formula?"],
    )