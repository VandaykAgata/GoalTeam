import html
import logging

import httpx

from .config import settings
from .schemas import EnrichedLead

logger = logging.getLogger(__name__)

_TELEGRAM_TIMEOUT_SECONDS = 5.0


def _format_message(enriched: EnrichedLead, lead_id: int) -> str:
    lead = enriched.lead
    c = enriched.classification
    e = html.escape
    return (
        f"<b>New lead #{lead_id}</b> — {e(c.category.value.upper())} ({c.score}/100)\n"
        f"\n"
        f"<b>Summary:</b> {e(c.summary)}\n"
        f"<b>Urgency:</b> {e(c.urgency.value)}\n"
        f"\n"
        f"Name: {e(lead.name)}\n"
        f"Phone: <code>{e(lead.phone)}</code>\n"
        f"Email: {e(lead.email)}\n"
        f"Source: {e(lead.source)}\n"
        f"\n"
        f"<i>{e(c.reasoning)}</i>"
    )


async def notify(enriched: EnrichedLead, lead_id: int) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.info("Telegram notify skipped — token or chat_id is not configured")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": _format_message(enriched, lead_id),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=_TELEGRAM_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as e:
        logger.exception("Telegram notify failed for lead #%s: %s", lead_id, e)
