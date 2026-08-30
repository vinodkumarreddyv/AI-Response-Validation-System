from typing import Optional

from pydantic import BaseModel, Field


class EvaluationInput(BaseModel):
    question: str = Field(..., min_length=1)

    ai_response: str = Field(..., min_length=1)

    reference_answer: Optional[str] = None

    source_document: Optional[str] = None