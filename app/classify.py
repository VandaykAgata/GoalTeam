import json
import logging
from pathlib import Path

from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from .config import settings
from .schemas import Classification, Lead, LeadCategory, Urgency

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "classify.md"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


def _render_prompt(lead: Lead) -> str:
    return (
        _PROMPT_TEMPLATE
        .replace("{{name}}", lead.name)
        .replace("{{source}}", lead.source)
        .replace("{{message}}", lead.message)
    )


def _mock_classification(lead: Lead) -> Classification:
    return Classification(
        summary=f"[mock] Inquiry from {lead.name}: {lead.message[:120]}",
        category=LeadCategory.warm,
        urgency=Urgency.medium,
        score=50,
        reasoning="Mock classifier. Set LLM_API_KEY to enable a real LLM.",
    )


async def classify(lead: Lead) -> Classification:
    if not settings.llm_api_key:
        logger.warning("LLM_API_KEY is empty, using mock classification")
        return _mock_classification(lead)

    client = AsyncOpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": _render_prompt(lead)}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
    except OpenAIError as e:
        logger.exception("LLM request failed, falling back to mock: %s", e)
        return _mock_classification(lead)

    raw = response.choices[0].message.content or ""
    try:
        data = json.loads(raw)
        return Classification(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.exception("LLM returned unparseable output, falling back to mock: %s", e)
        return _mock_classification(lead)
