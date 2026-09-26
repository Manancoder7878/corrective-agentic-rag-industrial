
from pydantic import BaseModel, Field, field_validator


class DiagnosticRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Technician symptom or fault description.")
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()

        if not any(char.isalnum() for char in value):
            raise ValueError(
                "Query must contain meaningful text, an event code, "
                "or an alphanumeric fault description."
            )

        return value


class CitedSource(BaseModel):
    chunk_id: str
    page: int
    content: str


class DiagnosticResponse(BaseModel):
    query: str
    rewritten_query: str | None = None
    diagnosis: str
    sources: list[CitedSource]
    retrieval_status: str
    loop_count: int