import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import settings
from .schemas import EnrichedLead

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"


@contextmanager
def _connect():
    conn = sqlite3.connect(settings.db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))


def save(enriched: EnrichedLead) -> int:
    lead = enriched.lead
    c = enriched.classification
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO leads (
                name, phone, email, message, source,
                summary, category, urgency, score, reasoning, received_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead.name,
                lead.phone,
                lead.email,
                lead.message,
                lead.source,
                c.summary,
                c.category.value,
                c.urgency.value,
                c.score,
                c.reasoning,
                enriched.received_at.isoformat(),
            ),
        )
        return cur.lastrowid
