# tests/test_scraper.py
from unittest.mock import patch, MagicMock
from scraper import scrape_domain, _is_poor_result


def test_is_poor_result_all_null():
    assert _is_poor_result(None, None, []) is True


def test_is_poor_result_has_email():
    assert _is_poor_result("info@empresa.com", None, []) is False


def test_is_poor_result_has_phone():
    assert _is_poor_result(None, "+34912345678", []) is False


def test_is_poor_result_has_menu():
    menu = [{"text": "A", "url": "u1"}, {"text": "B", "url": "u2"}, {"text": "C", "url": "u3"}]
    assert _is_poor_result(None, None, menu) is False


GOOD_HTML = """
<html>
  <head>
    <title>Empresa SL</title>
    <meta name="description" content="Servicios profesionales.">
  </head>
  <body>
    <nav><a href="/inicio">Inicio</a><a href="/servicios">Servicios</a><a href="/contacto">Contacto</a></nav>
    <p>Teléfono: <a href="tel:+34912345678">+34 912 345 678</a></p>
    <p>Email: <a href="mailto:info@empresa.com">info@empresa.com</a></p>
  </body>
</html>
"""


def test_scrape_domain_http_success():
    with patch("scraper.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = GOOD_HTML
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = scrape_domain("empresa.com", timeout=5)

    assert result.status == "success"
    assert result.email_principal == "info@empresa.com"
    assert result.telefono_principal == "+34912345678"
    assert result.used_playwright is False


def test_scrape_domain_triggers_playwright_on_poor_result():
    poor_html = "<html><body><p>Sin contacto</p></body></html>"
    good_html = GOOD_HTML

    with patch("scraper.requests.get") as mock_get, \
         patch("scraper.browser_manager") as mock_bm:

        mock_resp = MagicMock()
        mock_resp.text = poor_html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        mock_bm.available = True
        mock_bm.get_html.return_value = good_html

        result = scrape_domain("empresa.com", timeout=5)

    assert result.used_playwright is True
    assert result.email_principal == "info@empresa.com"


def test_scrape_domain_http_error_returns_error_status():
    with patch("scraper.requests.get") as mock_get, \
         patch("scraper.browser_manager") as mock_bm:
        mock_get.side_effect = Exception("Connection refused")
        mock_bm.available = False

        result = scrape_domain("empresa.com", timeout=5)

    assert result.status == "error"


def test_scrape_domain_normalizes_domain_without_protocol():
    with patch("scraper.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = GOOD_HTML
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = scrape_domain("empresa.com")

    called_url = mock_get.call_args[0][0]
    assert called_url.startswith("https://")
