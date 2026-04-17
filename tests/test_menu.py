# tests/test_menu.py
from extractors.menu import extract_menu


def test_menu_extracts_nav_links():
    html = """
    <nav>
      <a href="/inicio">Inicio</a>
      <a href="/servicios">Servicios</a>
      <a href="/contacto">Contacto</a>
    </nav>
    """
    links = extract_menu(html, "https://empresa.com")
    texts = [l["text"] for l in links]
    assert "Inicio" in texts
    assert "Servicios" in texts
    assert "Contacto" in texts


def test_menu_filters_external_links():
    html = """
    <nav>
      <a href="/inicio">Inicio</a>
      <a href="https://facebook.com/empresa">Facebook</a>
    </nav>
    """
    links = extract_menu(html, "https://empresa.com")
    urls = [l["url"] for l in links]
    assert not any("facebook.com" in u for u in urls)


def test_menu_filters_excluded_keywords():
    html = """
    <nav>
      <a href="/servicios">Servicios</a>
      <a href="/login">Login</a>
      <a href="/cart">Carrito</a>
      <a href="/privacy">Privacidad</a>
    </nav>
    """
    links = extract_menu(html, "https://empresa.com")
    texts = [l["text"].lower() for l in links]
    assert "login" not in texts
    assert "carrito" not in texts


def test_menu_deduplicates_urls():
    html = """
    <nav>
      <a href="/servicios">Servicios</a>
      <a href="/servicios">Nuestros Servicios</a>
    </nav>
    """
    links = extract_menu(html, "https://empresa.com")
    urls = [l["url"] for l in links]
    assert len(urls) == len(set(urls))


def test_menu_max_20_items():
    items = "".join([f'<a href="/page{i}">Page {i}</a>' for i in range(30)])
    html = f"<nav>{items}</nav>"
    links = extract_menu(html, "https://empresa.com")
    assert len(links) <= 20


def test_menu_builds_absolute_urls():
    html = '<nav><a href="/about">About</a></nav>'
    links = extract_menu(html, "https://empresa.com")
    assert links[0]["url"] == "https://empresa.com/about"


def test_menu_ignores_anchor_only_links():
    html = '<nav><a href="#section">Ir</a><a href="/page">Página</a></nav>'
    links = extract_menu(html, "https://empresa.com")
    urls = [l["url"] for l in links]
    assert not any(u == "#section" for u in urls)
