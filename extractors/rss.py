# extractors/rss.py
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CANDIDATE_RSS_PATHS = ['/feed', '/rss.xml', '/feed/', '/rss', '/blog/feed/', '/feed/rss/']


def _parse_latest_date(rss_url: str, session: requests.Session, timeout: int) -> Optional[str]:
    try:
        import feedparser
    except ImportError:
        return None
    try:
        resp = session.get(rss_url, timeout=timeout, headers={'User-Agent': 'n8n/1.0'})
        if resp.status_code != 200:
            return None
        feed = feedparser.parse(resp.text)
        dates = []
        for entry in feed.entries:
            published = entry.get('published') or entry.get('updated')
            if published:
                dates.append(published)
        return dates[0] if dates else None
    except Exception:
        return None


def find_rss_feed(
    soup: BeautifulSoup,
    base_url: str,
    session: requests.Session,
    timeout: int = 5,
) -> Optional[dict]:
    """
    Finds the RSS/Atom feed for the site.

    Returns {rss_url, ultimo_post_fecha} or None if not found.
    """
    # 1. <link rel="alternate" type="application/rss+xml">
    for link in soup.find_all('link', rel='alternate'):
        link_type = link.get('type', '')
        if 'rss' in link_type or 'atom' in link_type:
            href = link.get('href', '')
            if href:
                rss_url = urljoin(base_url, href)
                fecha = _parse_latest_date(rss_url, session, timeout)
                return {'rss_url': rss_url, 'ultimo_post_fecha': fecha}

    # 2. Probe common paths with HEAD request
    for path in CANDIDATE_RSS_PATHS:
        url = urljoin(base_url, path)
        try:
            resp = session.head(
                url,
                timeout=timeout,
                headers={'User-Agent': 'n8n/1.0'},
                allow_redirects=True,
            )
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                if 'xml' in content_type or 'rss' in content_type or 'atom' in content_type:
                    fecha = _parse_latest_date(url, session, timeout)
                    return {'rss_url': url, 'ultimo_post_fecha': fecha}
        except Exception:
            continue

    return None
