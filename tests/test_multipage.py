# tests/test_multipage.py
from unittest.mock import MagicMock, patch

from extractors.multipage import crawl_pages, LEAD_CALIENTE_RE


BASE = 'https://empresa.com'


def _mock_session(responses: dict):
    """responses: {url: (status, html)}"""
    session = MagicMock()

    def get_side_effect(url, **kwargs):
        resp = MagicMock()
        if url in responses:
            status, html = responses[url]
            resp.status_code = status
            resp.text = html
        else:
            resp.status_code = 404
            resp.text = ''
        return resp

    session.get.side_effect = get_side_effect
    return session


def test_contact_page_visited_when_in_menu():
    menu = ['https://empresa.com/contact']
    session = _mock_session({'https://empresa.com/contact': (200, '<p>Contact us</p>')})
    pages, pub_url = crawl_pages(BASE, menu, session)
    assert any(p.url == 'https://empresa.com/contact' for p in pages)
    assert pub_url is None


def test_advertise_page_sets_lead_caliente():
    menu = ['https://empresa.com/advertise']
    session = _mock_session({'https://empresa.com/advertise': (200, '<p>Advertise with us</p>')})
    pages, pub_url = crawl_pages(BASE, menu, session)
    assert any(p.is_lead_caliente for p in pages)
    assert pub_url == 'https://empresa.com/advertise'


def test_media_kit_page_sets_lead_caliente():
    menu = ['https://empresa.com/media-kit']
    session = _mock_session({'https://empresa.com/media-kit': (200, '<p>Media Kit</p>')})
    pages, pub_url = crawl_pages(BASE, menu, session)
    assert pub_url == 'https://empresa.com/media-kit'


def test_404_page_not_included():
    menu = ['https://empresa.com/contact']
    session = _mock_session({'https://empresa.com/contact': (404, '')})
    pages, pub_url = crawl_pages(BASE, menu, session)
    assert pages == []


def test_external_domain_not_crawled():
    menu = ['https://otro-dominio.com/contact']
    session = _mock_session({'https://otro-dominio.com/contact': (200, '<p>External</p>')})
    pages, pub_url = crawl_pages(BASE, menu, session)
    assert pages == []


def test_max_pages_limit():
    menu = [
        'https://empresa.com/contact',
        'https://empresa.com/about',
        'https://empresa.com/advertise',
        'https://empresa.com/media-kit',
        'https://empresa.com/colabora',
        'https://empresa.com/publicidad',
    ]
    responses = {u: (200, '<p>ok</p>') for u in menu}
    session = _mock_session(responses)
    pages, _ = crawl_pages(BASE, menu, session, max_pages=3)
    assert len(pages) <= 3


def test_lead_caliente_regex_variants():
    assert LEAD_CALIENTE_RE.search('/advertise')
    assert LEAD_CALIENTE_RE.search('/media-kit')
    assert LEAD_CALIENTE_RE.search('/media_kit')
    assert LEAD_CALIENTE_RE.search('/mediakit')
    assert LEAD_CALIENTE_RE.search('/publicidad')
    assert LEAD_CALIENTE_RE.search('/anunciate')
    assert not LEAD_CALIENTE_RE.search('/contact')
    assert not LEAD_CALIENTE_RE.search('/about')
