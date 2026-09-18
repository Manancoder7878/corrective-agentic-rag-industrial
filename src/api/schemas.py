from typing import List, Optional
from pydantic import BaseModel, Field


class DiagnosticRequest(BaseModel):
    query: str = Field(..., min_length=5, description="Technician symptom or fault description.")


class CitedSource(BaseModel):
    chunk_id: str
    page: int
    content: str


class DiagnosticResponse(BaseModel):
    query: str
    rewritten_query: Optional[str] = None
    diagnosis: str
    sources: List[CitedSource]
    retrieval_status: str
    loop_count: int