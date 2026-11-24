from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    k: int = Field(default=4, ge=1, le=12)


class SourceItem(BaseModel):
    source: str
    page: int | None = None
    chunk: str


class QuestionResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
