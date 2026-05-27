# tests/test_owner.py
from bs4 import BeautifulSoup
from extractors.owner import extract_owner


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, 'lxml')


def test_jsonld_name_passed_through():
    soup = _soup('<html><body></body></html>')
    result = extract_owner(soup, '', 'Acme Corp')
    assert result == 'Acme Corp'


def test_footer_copyright_extracted():
    html = '<html><body><footer>© 2024 María García S.L.</footer></body></html>'
    result = extract_owner(_soup(html), '')
    assert result is not None
    assert 'García' in result or 'Mar' in result


def test_self_intro_in_about_text():
    soup = _soup('<html><body></body></html>')
    about = "Hola, soy periodista freelance. Me llamo Laura Martínez y escribo sobre tecnología."
    result = extract_owner(soup, about)
    assert result == 'Laura Martínez'


def test_i_am_english():
    soup = _soup('<html><body></body></html>')
    about = "I am John Smith and I run this blog."
    result = extract_owner(soup, about)
    assert result == 'John Smith'


def test_meta_author_fallback():
    html = '<html><head><meta name="author" content="Sophie Dupont"></head><body></body></html>'
    result = extract_owner(_soup(html), '')
    assert result == 'Sophie Dupont'


def test_wordpress_discarded():
    html = '<html><body><footer>Powered by WordPress © 2024</footer></body></html>'
    result = extract_owner(_soup(html), '')
    assert result is None or 'WordPress' not in result


def test_short_name_discarded():
    soup = _soup('<html><body><footer>© AB</footer></body></html>')
    result = extract_owner(soup, '')
    assert result is None


def test_no_owner_returns_none():
    soup = _soup('<html><body><p>Sin datos</p></body></html>')
    result = extract_owner(soup, '')
    assert result is None
