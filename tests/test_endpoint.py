import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_happy_path_persists_normalized_lead(client):
    response = client.post(
        "/lead",
        json={
            "name": "Jane Doe",
            "phone": "+1 (415) 555-0100",
            "email": "Jane@Example.COM",
            "message": "Need a landing page ASAP, budget around $5k.",
            "source": "Google Ads",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"] in {"hot", "warm", "cold", "spam"}
    assert "id" in body

    with sqlite3.connect(settings.db_path) as conn:
        row = conn.execute(
            "SELECT name, phone, email, source FROM leads WHERE id = ?",
            (body["id"],),
        ).fetchone()
    assert row == ("Jane Doe", "+14155550100", "jane@example.com", "google_ads")


def test_invalid_email_is_rejected(client):
    response = client.post(
        "/lead",
        json={
            "name": "Jane",
            "phone": "+14155550100",
            "email": "not-an-email",
            "message": "Hi",
            "source": "landing",
        },
    )
    assert response.status_code == 422


def test_unparseable_phone_is_rejected(client):
    response = client.post(
        "/lead",
        json={
            "name": "Jane",
            "phone": "abcdef",
            "email": "jane@example.com",
            "message": "Hi",
            "source": "landing",
        },
    )
    assert response.status_code == 422
