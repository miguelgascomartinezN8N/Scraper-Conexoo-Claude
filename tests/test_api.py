# tests/test_api.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _mock_scrape(domain, timeout=10):
    from scraper import ScrapeResult
    return ScrapeResult(
        domain=domain,
        status="success",
        email_principal="info@empresa.com",
        emails_adicionales=[],
        telefono_principal="+34912345678",
        telefonos_adicionales=[],
        menu_links=[{"text": "Inicio", "url": f"https://{domain}/"}],
        titulo_web="Empresa SL",
        meta_descripcion="Servicios profesionales.",
        descripcion_negocio="Empresa SL. Servicios profesionales.",
        formulario_contacto_url=f"https://{domain}/contacto",
        used_playwright=False,
        processing_time=0.5,
    )


def test_health_returns_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert "playwright" in data


def test_scrape_endpoint_returns_results():
    with patch("main.scrape_domain", side_effect=_mock_scrape):
        r = client.post("/scrape", json={"domains": ["empresa.com"]})
    assert r.status_code == 200
    data = r.json()
    assert "request_id" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["status"] == "success"


def test_scrape_endpoint_rejects_too_many_domains():
    domains = [f"domain{i}.com" for i in range(101)]
    r = client.post("/scrape", json={"domains": domains})
    assert r.status_code == 400


def test_menu_endpoint_returns_links():
    with patch("main.scrape_domain", side_effect=_mock_scrape):
        r = client.post("/menu/extract", json={"domains": ["empresa.com"]})
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) == 1
    assert len(data["results"][0]["menu_links"]) >= 1


def test_scrape_rich_endpoint_returns_full_data():
    with patch("main.scrape_domain", side_effect=_mock_scrape):
        r = client.post("/scrape-rich", json={"domains": ["empresa.com"]})
    assert r.status_code == 200
    data = r.json()
    result = data["results"][0]
    assert result["titulo_web"] == "Empresa SL"
    assert result["email_principal"] == "info@empresa.com"
    assert result["descripcion_negocio"] is not None


def test_scrape_empty_domains_returns_400():
    r = client.post("/scrape", json={"domains": []})
    assert r.status_code == 400
