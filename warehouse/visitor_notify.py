"""Powiadomienia push (ntfy) o gościach demo.

- nowy gość — po udanym zapisie w bramce odwiedzających (`visitor_gate.py`),
- „zaangażowany gość” — gdy liczba obejrzanych ekranów dojdzie do
  `NTFY_ENGAGED_VIEWS` (`visitor_activity.py`).
Firma pasująca do `NTFY_WATCH_COMPANIES` → priorytet `urgent` i alarm w tytule.
Bez `NTFY_URL` — no-op, zero ruchu sieciowego. Wysyłka w wątku w tle
(timeout 5 s); każdy błąd to tylko ostrzeżenie w logu, nigdy błąd dla gościa.
"""

import logging
import threading
import unicodedata
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

APP_NAME = "miniWMS"
TIMEOUT_S = 5
MAX_BODY = 300
MIN_PHRASE = 2


def normalize(text: str) -> str:
    """casefold + bez znaków diakrytycznych + pojedyncze spacje."""
    decomposed = unicodedata.normalize("NFKD", (text or "").casefold())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped.replace("ł", "l").split())


def watched_company(company: str) -> bool:
    """Czy firma gościa zawiera którąś frazę z `NTFY_WATCH_COMPANIES`."""
    raw = getattr(settings, "NTFY_WATCH_COMPANIES", "") or ""
    name = normalize(company)
    if not name:
        return False
    for phrase in raw.split(","):
        phrase = normalize(phrase)
        if len(phrase) >= MIN_PHRASE and phrase in name:
            return True
    return False


def build_request(
    url: str,
    token: str,
    first_name: str,
    last_name: str,
    company: str,
    watched: bool = False,
) -> urllib.request.Request:
    body = f"{first_name} {last_name} ({company}) wszedł do {APP_NAME}"
    if watched:
        return _request(
            url,
            token,
            title=f"UWAGA firma z listy: {APP_NAME}",
            tags="rotating_light",
            priority="urgent",
            body="⚠️ " + body,
        )
    return _request(
        url,
        token,
        title=f"Nowy gosc: {APP_NAME}",
        tags="bell",
        priority="high",
        body=body,
    )


def build_engaged_request(
    url: str, token: str, first_name: str, last_name: str, company: str, views: int
) -> urllib.request.Request:
    body = f"{first_name} {last_name} ({company}) obejrzał już {views} ekranów w {APP_NAME}"
    return _request(
        url,
        token,
        title=f"Gosc oglada demo: {APP_NAME}",
        tags="eyes",
        priority="urgent" if watched_company(company) else "default",
        body=body,
    )


def _request(
    url: str, token: str, *, title: str, tags: str, priority: str, body: str
) -> urllib.request.Request:
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Title": title,  # nagłówki HTTP tylko ASCII
        "Tags": tags,
        "Priority": priority,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(
        url, data=body[:MAX_BODY].encode("utf-8"), headers=headers, method="POST"
    )


def _send(request: urllib.request.Request) -> None:
    try:
        # URL tylko z env operatora (nie od gościa), schemat http(s) sprawdzony
        # w _dispatch — fałszywy alarm Bandit B310 / Semgrep dynamic-urllib.
        with urllib.request.urlopen(request, timeout=TIMEOUT_S):  # nosec B310  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
            pass
    except Exception:  # sieć/serwer ntfy nie mogą zepsuć wejścia do demo
        logger.warning("Nie wysłano powiadomienia ntfy o gościu demo", exc_info=True)


def _dispatch(build, *args) -> None:
    """Sprawdza `NTFY_URL`, buduje żądanie i wysyła je w wątku w tle."""
    url = getattr(settings, "NTFY_URL", "")
    if not url:
        return
    if not url.startswith(("https://", "http://")):
        logger.warning("NTFY_URL musi zaczynać się od https:// lub http://")
        return
    try:
        request = build(url, getattr(settings, "NTFY_TOKEN", ""), *args)
        threading.Thread(target=_send, args=(request,), daemon=True).start()
    except Exception:
        logger.warning(
            "Nie uruchomiono powiadomienia ntfy o gościu demo", exc_info=True
        )


def notify_new_visitor(first_name: str, last_name: str, company: str) -> None:
    _dispatch(build_request, first_name, last_name, company, watched_company(company))


def notify_engaged_visitor(
    first_name: str, last_name: str, company: str, views: int
) -> None:
    _dispatch(build_engaged_request, first_name, last_name, company, views)
