# tests/test_smoke.py
"""
Smoke tests contra las fixtures baseline (A1.1).

Los tests de fixture siempre pasan sin red (los JSON ya están commiteados).
Los tests de integración llaman al scraper real solo si SCRAPER_URL está definido.

Control domains: ferlam-technologies.fr, wattco.com, jojofrench.fr
"""
import json
import os
import urllib.request
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCRAPER_URL = os.environ.get("SCRAPER_URL", "https://scraper-conexoo.appyweb.es")

CONTROL_DOMAINS = [
    "ferlam-technologies.fr",
    "wattco.com",
    "jojofrench.fr",
]

REQUIRED_RICH_FIELDS = [
    "domain",
    "status",
    "titulo_web",
    "meta_descripcion",
    "descripcion_negocio",
    "email_principal",
    "emails_adicionales",
    "telefono_principal",
    "telefonos_adicionales",
    "formulario_contacto_url",
    "menu_links",
    "used_playwright",
    "processing_time",
]


def _fixture_path(domain: str) -> Path:
    safe = domain.replace(".", "_").replace("-", "_")
    return FIXTURES_DIR / f"baseline_{safe}.json"


def _load_fixture(domain: str) -> dict:
    path = _fixture_path(domain)
    assert path.exists(), f"Fixture not found: {path}"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _call_scraper(domain: str, timeout: int = 25) -> dict:
    payload = json.dumps({"domains": [domain], "timeout": timeout}).encode()
    req = urllib.request.Request(
        f"{SCRAPER_URL}/scrape-rich",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "n8n/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
        return json.loads(resp.read())


# ── Fixture structure tests (no network needed) ───────────────────────────────

@pytest.mark.parametrize("domain", CONTROL_DOMAINS)
def test_fixture_exists(domain: str):
    assert _fixture_path(domain).exists(), f"Missing fixture for {domain}"


@pytest.mark.parametrize("domain", CONTROL_DOMAINS)
def test_fixture_has_results(domain: str):
    data = _load_fixture(domain)
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["domain"] == domain


@pytest.mark.parametrize("domain", CONTROL_DOMAINS)
def test_fixture_has_required_fields(domain: str):
    result = _load_fixture(domain)["results"][0]
    missing = [f for f in REQUIRED_RICH_FIELDS if f not in result]
    assert not missing, f"{domain}: missing fields {missing}"


@pytest.mark.parametrize("domain", CONTROL_DOMAINS)
def test_fixture_status_valid(domain: str):
    result = _load_fixture(domain)["results"][0]
    assert result["status"] in ("success", "no_contacts", "error", "timeout")


@pytest.mark.parametrize("domain", CONTROL_DOMAINS)
def test_fixture_titulo_web_not_empty(domain: str):
    result = _load_fixture(domain)["results"][0]
    # At least one of these should be present for a live site
    has_data = (
        result.get("titulo_web")
        or result.get("meta_descripcion")
        or result.get("descripcion_negocio")
    )
    assert has_data, f"{domain}: no title/meta/description in fixture"


@pytest.mark.parametrize("domain", CONTROL_DOMAINS)
def test_fixture_menu_links_is_list(domain: str):
    result = _load_fixture(domain)["results"][0]
    assert isinstance(result["menu_links"], list)


# ── Integration tests (require live scraper) ─────────────────────────────────

def _scraper_available() -> bool:
    try:
        req = urllib.request.Request(
            f"{SCRAPER_URL}/health",
            headers={"User-Agent": "n8n/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("status") == "healthy"
    except Exception:
        return False


skip_if_no_scraper = pytest.mark.skipif(
    not _scraper_available(),
    reason="Scraper not available — set SCRAPER_URL or ensure it's running",
)


@skip_if_no_scraper
@pytest.mark.parametrize("domain", CONTROL_DOMAINS)
def test_live_scraper_returns_valid_response(domain: str):
    data = _call_scraper(domain)
    assert "results" in data
    result = data["results"][0]
    assert result["domain"] == domain
    assert result["status"] in ("success", "no_contacts", "error", "timeout")
    missing = [f for f in REQUIRED_RICH_FIELDS if f not in result]
    assert not missing, f"Missing fields: {missing}"


@skip_if_no_scraper
def test_live_scraper_jojofrench_has_email():
    """jojofrench.fr tenía email en baseline — verifica regresión."""
    data = _call_scraper("jojofrench.fr")
    result = data["results"][0]
    assert result.get("email_principal") is not None, (
        "jojofrench.fr perdió su email — posible regresión en extractor"
    )


@skip_if_no_scraper
def test_live_scraper_ferlam_has_titulo():
    """ferlam-technologies.fr debería tener título aunque no tenga email."""
    data = _call_scraper("ferlam-technologies.fr")
    result = data["results"][0]
    assert result.get("titulo_web"), "ferlam-technologies.fr no devuelve titulo_web"
