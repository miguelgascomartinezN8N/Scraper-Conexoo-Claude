# tests/test_adstxt.py
from unittest.mock import MagicMock, patch

from extractors.adstxt import _parse_adstxt, fetch_adstxt


def test_parse_standard_adstxt():
    content = """
# ads.txt file
google.com, pub-123, DIRECT, f08c47fec0942fa0
mediavine.com, 12345, DIRECT
taboola.com, 678, RESELLER
"""
    result = _parse_adstxt(content)
    assert 'google.com' in result
    assert 'mediavine.com' in result
    assert 'taboola.com' in result


def test_parse_skips_comments():
    content = "# this is a comment\ngoogle.com, pub-123, DIRECT"
    result = _parse_adstxt(content)
    assert result == ['google.com']


def test_parse_skips_incomplete_lines():
    content = "google.com\nnot-enough-commas, DIRECT"
    result = _parse_adstxt(content)
    assert result == []


def test_parse_deduplicates_exchanges():
    content = "google.com, pub-1, DIRECT\ngoogle.com, pub-2, RESELLER"
    result = _parse_adstxt(content)
    assert result.count('google.com') == 1


def test_parse_returns_sorted():
    content = "taboola.com, 1, DIRECT\ngoogle.com, 2, DIRECT\nmediavine.com, 3, DIRECT"
    result = _parse_adstxt(content)
    assert result == sorted(result)


def test_parse_empty_content():
    assert _parse_adstxt('') == []
    assert _parse_adstxt('# only comments\n# nothing here') == []


def test_fetch_returns_empty_on_404():
    with patch('requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        result = fetch_adstxt('example.com')
        assert result == []


def test_fetch_returns_empty_on_network_error():
    with patch('requests.get', side_effect=Exception('timeout')):
        result = fetch_adstxt('example.com')
        assert result == []


def test_fetch_parses_200_response():
    with patch('requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "google.com, pub-123, DIRECT, f08c47fec0942fa0\nezoic.com, 999, DIRECT"
        mock_get.return_value = mock_resp
        result = fetch_adstxt('empresa.com')
        assert 'google.com' in result
        assert 'ezoic.com' in result
