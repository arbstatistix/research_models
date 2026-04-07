from fastapi import APIRouter
from app.schemas.request import PromptRequest
from app.schemas.response import PipelineResponse
from app.pipeline.pipeline import QuantResearchPipeline
from app.core.config import PipelineConfig

router = APIRouter()

pipeline = QuantResearchPipeline(PipelineConfig())

@router.post("/api/research", response_model=PipelineResponse)
def research(req: PromptRequest) -> PipelineResponse:
    result = pipeline.process_prompt(req.prompt)
    return PipelineResponse(**result)