"""Powiadomienie push (ntfy) o nowym gościu demo.

Wysyłane po udanym zapisie w bramce odwiedzających (`visitor_gate.py`).
Bez `NTFY_URL` — no-op, zero ruchu sieciowego. Wysyłka w wątku w tle
(timeout 5 s); każdy błąd to tylko ostrzeżenie w logu, nigdy błąd dla gościa.
"""

import logging
import threading
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

APP_NAME = "miniWMS"
TIMEOUT_S = 5
MAX_BODY = 300


def build_request(
    url: str, token: str, first_name: str, last_name: str, company: str
) -> urllib.request.Request:
    body = f"{first_name} {last_name} ({company}) wszedł do {APP_NAME}"[:MAX_BODY]
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Title": f"Nowy gosc: {APP_NAME}",
        "Tags": "bell",
        "Priority": "high",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(
        url, data=body.encode("utf-8"), headers=headers, method="POST"
    )


def _send(request: urllib.request.Request) -> None:
    try:
        # URL tylko z env operatora (nie od gościa), schemat http(s) sprawdzony
        # w notify_new_visitor — fałszywy alarm Bandit B310 / Semgrep dynamic-urllib.
        with urllib.request.urlopen(request, timeout=TIMEOUT_S):  # nosec B310  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
            pass
    except Exception:  # sieć/serwer ntfy nie mogą zepsuć wejścia do demo
        logger.warning("Nie wysłano powiadomienia ntfy o gościu demo", exc_info=True)


def notify_new_visitor(first_name: str, last_name: str, company: str) -> None:
    url = getattr(settings, "NTFY_URL", "")
    if not url:
        return
    if not url.startswith(("https://", "http://")):
        logger.warning("NTFY_URL musi zaczynać się od https:// lub http://")
        return
    try:
        request = build_request(
            url, getattr(settings, "NTFY_TOKEN", ""), first_name, last_name, company
        )
        threading.Thread(target=_send, args=(request,), daemon=True).start()
    except Exception:
        logger.warning(
            "Nie uruchomiono powiadomienia ntfy o gościu demo", exc_info=True
        )
