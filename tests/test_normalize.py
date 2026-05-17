import pytest

from app.normalize import normalize, normalize_email, normalize_phone, normalize_source
from app.schemas import LeadIn


class TestNormalizePhone:
    def test_strips_punctuation_and_keeps_plus(self):
        assert normalize_phone("+1 (415) 555-0100") == "+14155550100"

    def test_adds_leading_plus_when_missing(self):
        assert normalize_phone("380965852251") == "+380965852251"

    def test_strips_letters_and_unicode(self):
        assert normalize_phone("tel: 38 096 — 585 22 51") == "+380965852251"

    def test_raises_on_too_few_digits(self):
        with pytest.raises(ValueError):
            normalize_phone("---")


class TestNormalizeEmail:
    def test_lowercases_and_trims(self):
        assert normalize_email("  Hi@Example.COM  ") == "hi@example.com"


class TestNormalizeSource:
    def test_lowercases_and_underscores(self):
        assert normalize_source("Google Ads") == "google_ads"

    def test_empty_becomes_unknown(self):
        assert normalize_source("   ") == "unknown"


def test_normalize_returns_canonical_lead():
    lead_in = LeadIn(
        name="  Olena  ",
        phone="+1 (415) 555-0100",
        email="  Olena@Example.COM ",
        message="  Need a landing page.  ",
        source="Google Ads",
    )
    lead = normalize(lead_in)
    assert lead.name == "Olena"
    assert lead.phone == "+14155550100"
    assert lead.email == "olena@example.com"
    assert lead.message == "Need a landing page."
    assert lead.source == "google_ads"
