"""Przepustka z portfolio: ciasteczko `gosc` zwalnia z bramki „przedstaw się”.

Gość przedstawia się raz w portfolio, które ustawia `gosc` (HttpOnly, domena
`.twapp.pl`). Tu pytamy portfolio server-to-server (`GET {PORTFOLIO_URL}/api/gosc`,
tylko ciasteczko `gosc`, 2 s, bez przekierowań); liczy się wyłącznie status 200.
Nie zapisujemy gościa ani nie wysyłamy pusha — robi to portfolio (piksel /px/).
Wynik pozytywny trzymamy w cache po hashu tokenu (token nie trafia do logów);
błąd/timeout krótko też, żeby niedziałające portfolio nie spowalniało każdego żądania.
"""

import hashlib
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest

logger = logging.getLogger(__name__)

COOKIE_NAME = "gosc"
MAX_TOKEN_LEN = 200
TIMEOUT = 2
OK_TTL = 600
ERROR_TTL = 30


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # 3xx kończy się HTTPError → przepustka nieważna


def _base_url() -> str | None:
    if not getattr(settings, "PORTFOLIO_PASS", True):
        return None
    url = str(getattr(settings, "PORTFOLIO_URL", "") or "").rstrip("/")
    if not url.startswith("https://"):
        logger.warning(
            "PORTFOLIO_URL musi zaczynać się od https:// — przepustka wyłączona"
        )
        return None
    return url


def _ask_portfolio(base: str, token: str) -> tuple[bool, bool]:
    """(ważna, błąd_sieci) — ważna tylko przy statusie 200."""
    req = urllib.request.Request(  # noqa: S310 — schemat https wymuszony w _base_url
        f"{base}/api/gosc", headers={"Cookie": f"{COOKIE_NAME}={token}"}
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            return resp.status == 200, False
    except urllib.error.HTTPError:
        return False, False  # 401 itp.: odpowiedź portfolio, nie awaria
    except Exception:  # sieć, timeout, TLS — bramka działa jak dotąd
        logger.warning("Portfolio nie odpowiedziało przy sprawdzaniu przepustki")
        return False, True


def portfolio_pass_valid(request: HttpRequest) -> bool:
    token = request.COOKIES.get(COOKIE_NAME, "")
    if not token or len(token) > MAX_TOKEN_LEN:
        return False
    base = _base_url()
    if base is None:
        return False
    key = "portfolio-pass:" + hashlib.sha256(token.encode()).hexdigest()
    cached = cache.get(key)
    if cached is not None:
        return bool(cached)
    valid, error = _ask_portfolio(base, token)
    if valid:
        cache.set(key, True, OK_TTL)
    elif error:
        cache.set(key, False, ERROR_TTL)
    return valid
