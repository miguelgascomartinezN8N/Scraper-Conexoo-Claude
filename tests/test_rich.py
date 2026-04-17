# tests/test_rich.py
from extractors.rich import extract_rich, find_about_url


def test_title_extracted():
    html = "<html><head><title>Empresa SL | Servicios de Marketing</title></head><body></body></html>"
    result = extract_rich(html, "https://empresa.com")
    assert result["titulo_web"] == "Empresa SL"


def test_title_cleans_separator_dash():
    html = "<html><head><title>Empresa SL - Servicios</title></head><body></body></html>"
    result = extract_rich(html, "https://empresa.com")
    assert result["titulo_web"] == "Empresa SL"


def test_title_cleans_separator_pipe():
    html = "<html><head><title>Inicio | Empresa SL</title></head><body></body></html>"
    result = extract_rich(html, "https://empresa.com")
    assert result["titulo_web"] == "Inicio"


def test_meta_description_extracted():
    html = '<html><head><meta name="description" content="Somos una agencia de marketing digital."></head><body></body></html>'
    result = extract_rich(html, "https://empresa.com")
    assert result["meta_descripcion"] == "Somos una agencia de marketing digital."


def test_meta_og_description_fallback():
    html = '<html><head><meta property="og:description" content="OG description aquí."></head><body></body></html>'
    result = extract_rich(html, "https://empresa.com")
    assert result["meta_descripcion"] == "OG description aquí."


def test_texto_homepage_strips_scripts():
    html = """
    <html><body>
      <script>var x = 1;</script>
      <p>Texto visible de la empresa aquí presente en el cuerpo principal.</p>
      <style>body { color: red; }</style>
    </body></html>
    """
    result = extract_rich(html, "https://empresa.com")
    assert "var x" not in (result["texto_homepage"] or "")
    assert "color: red" not in (result["texto_homepage"] or "")


def test_texto_homepage_max_chars(monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "rich_text_max_chars", 50)
    long_text = "A" * 200
    html = f"<html><body><p>{long_text}</p></body></html>"
    result = extract_rich(html, "https://empresa.com")
    assert len(result.get("texto_homepage") or "") <= 50


def test_descripcion_negocio_combines_fields():
    html = """
    <html>
      <head>
        <title>Empresa SL</title>
        <meta name="description" content="Agencia de marketing.">
      </head>
      <body><p>Ofrecemos servicios de SEO y publicidad online para empresas.</p></body>
    </html>
    """
    result = extract_rich(html, "https://empresa.com")
    assert result["descripcion_negocio"] is not None
    assert "Empresa SL" in result["descripcion_negocio"]
    assert "Agencia de marketing" in result["descripcion_negocio"]


def test_formulario_contacto_url_detected():
    html = '<html><body><a href="/contacto">Contáctanos</a></body></html>'
    result = extract_rich(html, "https://empresa.com")
    assert result["formulario_contacto_url"] == "https://empresa.com/contacto"


def test_find_about_url_detects_about():
    html = '<html><body><a href="/quienes-somos">Quiénes somos</a></body></html>'
    url = find_about_url(html, "https://empresa.com")
    assert url == "https://empresa.com/quienes-somos"


def test_find_about_url_returns_none_when_not_found():
    html = "<html><body><p>Sin links de about</p></body></html>"
    url = find_about_url(html, "https://empresa.com")
    assert url is None
