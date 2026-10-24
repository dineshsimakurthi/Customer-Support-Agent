"""Pydantic models: force the LLM to return validated, structured output."""
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "ACCOUNT", "CANCEL", "CONTACT", "DELIVERY", "FEEDBACK", "INVOICE",
    "ORDER", "PAYMENT", "REFUND", "SHIPPING", "SUBSCRIPTION",
]


class Classification(BaseModel):
    category: Category
    urgency: Literal["low", "medium", "high", "critical"]
    sentiment: Literal["positive", "neutral", "negative", "angry"]
    reasoning: str = Field(description="One short sentence explaining the choice")


class ConfidenceResult(BaseModel):
    score: float = Field(ge=0, le=1, description="0 = unsupported, 1 = fully supported by sources")
    reasoning: str
