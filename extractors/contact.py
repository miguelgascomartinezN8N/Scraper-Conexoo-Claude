import re
from typing import Optional
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-zA-Z]{2,}')
OBFUSCATED_AT_DOT_RE = re.compile(
    r'([\w._%+-]+)\s*[\[\(]at[\]\)]\s*([\w.-]+)\s*[\[\(]dot[\]\)]\s*([\w]+)',
    re.IGNORECASE,
)
OBFUSCATED_AT_PAREN_RE = re.compile(
    r'([\w._%+-]+)\s*\(at\)\s*([\w.-]+\.[\w]{2,})',
    re.IGNORECASE,
)

EXCLUDED_DOMAINS = {'example.com', 'test.com', 'localhost', 'placeholder.com', 'sample.com', 'domain.com'}
EXCLUDED_PREFIXES = {'noreply', 'no-reply', 'mailer-daemon', 'postmaster', 'bounce', 'abuse'}
SOCIAL_DOMAINS = {'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com', 'tiktok.com'}
PRIORITY_PREFIXES = ['info', 'contacto', 'contact', 'hola', 'hello', 'consultas']

PHONE_CONTEXT_RE = re.compile(
    r'tel[eé]?[fF]?[oóO]?n?[oO]?|telf|phone|m[oó]vil|celular|whatsapp|llamar|ll[aá]manos|contacto',
    re.IGNORECASE,
)
PHONE_RE = re.compile(
    r'(?:\+\d{1,3}[\s\-.]?)?\(?\d{2,4}\)?[\s\-.]?\d{2,4}[\s\-.]?\d{2,4}(?:[\s\-.]?\d{1,4})?'
)


def _is_valid_email(email: str) -> bool:
    email = email.lower()
    if '@' not in email:
        return False
    prefix, domain = email.rsplit('@', 1)
    if domain in EXCLUDED_DOMAINS:
        return False
    if prefix in EXCLUDED_PREFIXES:
        return False
    if any(sd in domain for sd in SOCIAL_DOMAINS):
        return False
    if len(email) < 5 or len(email) > 254:
        return False
    return True


def _prioritize(emails: set) -> tuple[Optional[str], list[str]]:
    valid = sorted([e for e in emails if _is_valid_email(e)])
    if not valid:
        return None, []
    principal = None
    for prefix in PRIORITY_PREFIXES:
        match = next((e for e in valid if e.startswith(prefix + '@')), None)
        if match:
            principal = match
            break
    if not principal:
        principal = valid[0]
    adicionales = [e for e in valid if e != principal][:5]
    return principal, adicionales


def extract_emails(html: str) -> tuple[Optional[str], list[str]]:
    soup = BeautifulSoup(html, 'lxml')
    emails: set[str] = set()

    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().startswith('mailto:'):
            email = href[7:].split('?')[0].strip().lower()
            if email:
                emails.add(email)

    for attr in ('data-email', 'data-mail'):
        for el in soup.find_all(attrs={attr: True}):
            emails.add(el[attr].lower().strip())

    text = soup.get_text(' ')
    for m in EMAIL_RE.finditer(text):
        emails.add(m.group().lower())

    for m in OBFUSCATED_AT_DOT_RE.finditer(text):
        emails.add(f"{m.group(1)}@{m.group(2)}.{m.group(3)}".lower())

    for m in OBFUSCATED_AT_PAREN_RE.finditer(text):
        emails.add(f"{m.group(1)}@{m.group(2)}".lower())

    return _prioritize(emails)


def _clean_phone(phone: str) -> str:
    return re.sub(r'[\s\-.()\[\]]', '', phone)


def _digits_only(phone: str) -> str:
    return re.sub(r'\D', '', phone)


def extract_phones(html: str) -> tuple[Optional[str], list[str]]:
    soup = BeautifulSoup(html, 'lxml')
    phones: list[str] = []

    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().startswith('tel:'):
            raw = href[4:].strip()
            digits = _digits_only(raw)
            if 7 <= len(digits) <= 15:
                cleaned = _clean_phone(raw)
                if cleaned not in phones:
                    phones.append(cleaned)

    text = soup.get_text(' ')
    for m in PHONE_RE.finditer(text):
        raw = m.group()
        digits = _digits_only(raw)
        if not (7 <= len(digits) <= 15):
            continue
        start = max(0, m.start() - 80)
        end = min(len(text), m.end() + 80)
        context = text[start:end]
        if PHONE_CONTEXT_RE.search(context):
            cleaned = _clean_phone(raw)
            if cleaned not in phones:
                phones.append(cleaned)

    principal = phones[0] if phones else None
    adicionales = phones[1:4]
    return principal, adicionales
