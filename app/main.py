import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import BackgroundTasks, FastAPI, HTTPException

from . import classify as classify_module
from . import normalize as normalize_module
from . import notify as notify_module
from . import storage
from .schemas import EnrichedLead, LeadIn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.init_db()
    yield


app = FastAPI(title="Landing Lead MVP", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/lead", status_code=201)
async def receive_lead(lead_in: LeadIn, background: BackgroundTasks) -> dict:
    try:
        lead = normalize_module.normalize(lead_in)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    classification = await classify_module.classify(lead)

    enriched = EnrichedLead(
        lead=lead,
        classification=classification,
        received_at=datetime.now(timezone.utc),
    )
    lead_id = storage.save(enriched)

    background.add_task(notify_module.notify, enriched, lead_id)

    return {
        "id": lead_id,
        "category": classification.category.value,
        "urgency": classification.urgency.value,
        "score": classification.score,
        "summary": classification.summary,
    }
