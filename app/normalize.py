import re

from .schemas import Lead, LeadIn

_NON_DIGIT = re.compile(r"\D+")
_WHITESPACE = re.compile(r"\s+")


def normalize_phone(raw: str) -> str:
    digits = _NON_DIGIT.sub("", raw)
    if len(digits) < 7:
        raise ValueError(f"phone has too few digits: {raw!r}")
    return f"+{digits}"


def normalize_email(raw: str) -> str:
    return raw.strip().lower()


def normalize_source(raw: str) -> str:
    cleaned = _WHITESPACE.sub("_", raw.strip().lower())
    return cleaned or "unknown"


def normalize(lead_in: LeadIn) -> Lead:
    return Lead(
        name=lead_in.name.strip(),
        phone=normalize_phone(lead_in.phone),
        email=normalize_email(lead_in.email),
        message=lead_in.message.strip(),
        source=normalize_source(lead_in.source),
    )
