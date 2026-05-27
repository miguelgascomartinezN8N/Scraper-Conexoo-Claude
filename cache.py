# cache.py
import re
from urllib.parse import urlparse

try:
    from cachetools import TTLCache
    _CACHETOOLS_AVAILABLE = True
except ImportError:
    _CACHETOOLS_AVAILABLE = False

_SEVEN_DAYS = 7 * 24 * 3600

if _CACHETOOLS_AVAILABLE:
    _publisher_cache: TTLCache = TTLCache(maxsize=10_000, ttl=_SEVEN_DAYS)
else:
    _publisher_cache: dict = {}  # type: ignore[assignment]


def _normalize_key(domain: str) -> str:
    """Lowercase, strip www, strip scheme."""
    if '://' not in domain:
        domain = 'https://' + domain
    host = urlparse(domain).netloc or domain
    host = re.sub(r'^www\.', '', host).lower().rstrip('/')
    return host


def cache_get(domain: str):
    return _publisher_cache.get(_normalize_key(domain))


def cache_set(domain: str, value) -> None:
    _publisher_cache[_normalize_key(domain)] = value


def cache_delete(domain: str) -> None:
    key = _normalize_key(domain)
    _publisher_cache.pop(key, None)
