# tests/test_publisher.py
import time
from unittest.mock import MagicMock, patch

import pytest

from cache import cache_delete, cache_get, cache_set, _normalize_key


# ── Cache unit tests ─────────────────────────────────────────────────────────

def test_cache_normalize_strips_www():
    assert _normalize_key('www.example.com') == 'example.com'


def test_cache_normalize_strips_scheme():
    assert _normalize_key('https://example.com') == 'example.com'


def test_cache_normalize_lowercase():
    assert _normalize_key('Example.COM') == 'example.com'


def test_cache_set_and_get():
    cache_set('test-cache-domain.com', {'status': 'success'})
    result = cache_get('test-cache-domain.com')
    assert result == {'status': 'success'}
    cache_delete('test-cache-domain.com')


def test_cache_delete():
    cache_set('delete-me.com', {'x': 1})
    cache_delete('delete-me.com')
    assert cache_get('delete-me.com') is None


def test_cache_miss_returns_none():
    assert cache_get('definitely-not-cached-xyz123.com') is None


def test_cache_hit_is_fast():
    cache_set('speed-test.com', {'status': 'cached'})
    start = time.time()
    for _ in range(1000):
        cache_get('speed-test.com')
    elapsed = time.time() - start
    assert elapsed < 0.1, f"1000 cache reads took {elapsed:.3f}s — too slow"
    cache_delete('speed-test.com')


# ── scrape_publisher integration (mocked) ───────────────────────────────────

@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure test domain is not cached between tests."""
    cache_delete('mock-publisher.com')
    yield
    cache_delete('mock-publisher.com')


MOCK_HTML = """
<html lang="en">
<head>
  <title>Mock Publisher - Tech News</title>
  <meta name="description" content="Best tech news site">
  <link rel="alternate" type="application/rss+xml" href="/feed">
</head>
<body>
  <nav>
    <a href="/contact">Contact</a>
    <a href="/advertise">Advertise</a>
  </nav>
  <p>Contact us at info@mockpublisher.com or call +34 612 345 678 (teléfono)</p>
  <footer>© 2024 Mock Publisher Ltd.</footer>
</body>
</html>
"""


def test_scrape_publisher_returns_required_fields():
    from scraper import scrape_publisher

    with patch('scraper._fetch_http', return_value=MOCK_HTML), \
         patch('scraper.fetch_adstxt', return_value=['google.com']), \
         patch('extractors.rss.find_rss_feed', return_value=None), \
         patch('extractors.multipage.crawl_pages', return_value=([], None)):

        result = scrape_publisher('mock-publisher.com', crawl=False)

    assert result['domain'] == 'mock-publisher.com'
    assert result['status'] in ('success', 'no_contacts', 'error')
    assert 'titulo_web' in result
    assert 'redes_sociales' in result
    assert 'ads_partners' in result


def test_scrape_publisher_caches_result():
    from scraper import scrape_publisher

    with patch('scraper._fetch_http', return_value=MOCK_HTML), \
         patch('scraper.fetch_adstxt', return_value=[]), \
         patch('extractors.rss.find_rss_feed', return_value=None), \
         patch('extractors.multipage.crawl_pages', return_value=([], None)):

        result1 = scrape_publisher('mock-publisher.com', crawl=False)
        # Second call should use cache — _fetch_http should NOT be called again
        with patch('scraper._fetch_http', side_effect=AssertionError("Should not fetch again")):
            result2 = scrape_publisher('mock-publisher.com', crawl=False)

    assert result1 == result2


def test_scrape_publisher_error_on_fetch_failure():
    from scraper import scrape_publisher

    with patch('scraper._fetch_http', return_value=None), \
         patch('scraper.browser_manager') as mock_bm:
        mock_bm.available = False
        result = scrape_publisher('failing-domain.com', crawl=False)

    assert result['status'] == 'error'
    cache_delete('failing-domain.com')
