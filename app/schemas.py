from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class LeadCategory(str, Enum):
    hot = "hot"
    warm = "warm"
    cold = "cold"
    spam = "spam"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class LeadIn(BaseModel):
    """Raw payload from the landing form. Validated but not yet normalized."""

    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=3, max_length=50)
    email: EmailStr
    message: str = Field(min_length=1, max_length=5000)
    source: str = Field(default="unknown", max_length=100)


class Lead(BaseModel):
    """Canonical lead after normalization. Safe to persist."""

    name: str
    phone: str
    email: str
    message: str
    source: str


class Classification(BaseModel):
    """Structured output from the LLM."""

    summary: str = Field(max_length=400)
    category: LeadCategory
    urgency: Urgency
    score: int = Field(ge=0, le=100)
    reasoning: str = Field(max_length=400)


class EnrichedLead(BaseModel):
    """A normalized lead plus its AI-derived classification."""

    lead: Lead
    classification: Classification
    received_at: datetime
