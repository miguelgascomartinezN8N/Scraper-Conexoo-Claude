# extractors/adstxt.py
from typing import Optional

import requests


def fetch_adstxt(domain: str, timeout: int = 3) -> list[str]:
    """
    Fetches /ads.txt for the domain and returns sorted unique exchange domains.

    Returns [] on 404, network error, or parse failure.
    """
    domain = domain.lstrip('https://').lstrip('http://').lstrip('www.')
    url = f'https://{domain}/ads.txt'
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={'User-Agent': 'n8n/1.0'},
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return []
        return _parse_adstxt(resp.text)
    except Exception:
        return []


def _parse_adstxt(content: str) -> list[str]:
    exchanges: set[str] = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:
            exchange = parts[0].lower()
            # Basic sanity: must look like a domain
            if '.' in exchange and len(exchange) <= 100:
                exchanges.add(exchange)
    return sorted(exchanges)
