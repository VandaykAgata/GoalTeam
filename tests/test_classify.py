from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app import classify as classify_module
from app.schemas import Lead, LeadCategory


def _lead() -> Lead:
    return Lead(
        name="Olena",
        phone="+14155550100",
        email="olena@example.com",
        message="Need a landing page ASAP, budget $5k.",
        source="landing",
    )


def _openai_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


async def test_mock_used_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(classify_module.settings, "llm_api_key", "")
    result = await classify_module.classify(_lead())
    assert result.summary.startswith("[mock]")
    assert result.category == LeadCategory.warm


async def test_real_call_parses_json(monkeypatch):
    monkeypatch.setattr(classify_module.settings, "llm_api_key", "fake-key")

    fake_response = _openai_response(
        '{"summary": "Wants a landing page urgently", '
        '"category": "hot", "urgency": "high", '
        '"score": 88, "reasoning": "Budget and ASAP signal."}'
    )

    with patch.object(classify_module, "AsyncOpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create = AsyncMock(return_value=fake_response)
        result = await classify_module.classify(_lead())

    assert result.category == LeadCategory.hot
    assert result.score == 88
    assert "landing page" in result.summary.lower()


async def test_falls_back_to_mock_on_unparseable_json(monkeypatch):
    monkeypatch.setattr(classify_module.settings, "llm_api_key", "fake-key")

    fake_response = _openai_response("definitely not JSON")

    with patch.object(classify_module, "AsyncOpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create = AsyncMock(return_value=fake_response)
        result = await classify_module.classify(_lead())

    assert result.summary.startswith("[mock]")


async def test_falls_back_to_mock_on_invalid_schema(monkeypatch):
    monkeypatch.setattr(classify_module.settings, "llm_api_key", "fake-key")

    fake_response = _openai_response(
        '{"summary": "x", "category": "lukewarm", "urgency": "high", "score": 50, "reasoning": "x"}'
    )

    with patch.object(classify_module, "AsyncOpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create = AsyncMock(return_value=fake_response)
        result = await classify_module.classify(_lead())

    assert result.summary.startswith("[mock]")
