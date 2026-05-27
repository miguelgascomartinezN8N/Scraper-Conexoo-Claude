# tests/test_social.py
from bs4 import BeautifulSoup
from extractors.social import extract_social_links


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, 'lxml')


BASE = 'https://empresa.com'


def test_twitter_detected():
    html = '<a href="https://twitter.com/empresa_oficial">Twitter</a>'
    result = extract_social_links(_soup(html), BASE)
    assert 'twitter' in result
    assert 'twitter.com/empresa_oficial' in result['twitter']


def test_x_com_detected_as_twitter():
    html = '<a href="https://x.com/empresa">X</a>'
    result = extract_social_links(_soup(html), BASE)
    assert 'twitter' in result


def test_linkedin_company():
    html = '<a href="https://www.linkedin.com/company/mi-empresa">LinkedIn</a>'
    result = extract_social_links(_soup(html), BASE)
    assert 'linkedin' in result


def test_instagram():
    html = '<a href="https://instagram.com/empresa">IG</a>'
    result = extract_social_links(_soup(html), BASE)
    assert 'instagram' in result


def test_facebook():
    html = '<a href="https://www.facebook.com/empresapage">FB</a>'
    result = extract_social_links(_soup(html), BASE)
    assert 'facebook' in result


def test_own_domain_excluded():
    html = '<a href="https://empresa.com/blog">Blog propio</a>'
    result = extract_social_links(_soup(html), BASE)
    assert result == {}


def test_share_links_excluded():
    html = '<a href="https://twitter.com/intent/tweet?url=x">Compartir</a>'
    result = extract_social_links(_soup(html), BASE)
    assert 'twitter' not in result


def test_facebook_sharer_excluded():
    html = '<a href="https://www.facebook.com/sharer/sharer.php?u=x">FB share</a>'
    result = extract_social_links(_soup(html), BASE)
    assert 'facebook' not in result


def test_multiple_platforms():
    html = '''
    <a href="https://twitter.com/co">T</a>
    <a href="https://linkedin.com/company/co">Li</a>
    <a href="https://www.youtube.com/channel/UC123">YT</a>
    '''
    result = extract_social_links(_soup(html), BASE)
    assert 'twitter' in result
    assert 'linkedin' in result
    assert 'youtube' in result


def test_no_social_links():
    html = '<a href="https://empresa.com/about">About</a>'
    result = extract_social_links(_soup(html), BASE)
    assert result == {}
