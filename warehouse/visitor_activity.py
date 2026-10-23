"""Aktywność gościa demo po wejściu: ile i jakie ekrany obejrzał.

Middleware liczy tylko udane (2xx) GET-y stron HTML od gościa z podpisanym
ciasteczkiem bramki niosącym id wpisu (`visitor_gate.visitor_id`). Statyki,
/healthz, JSON skanera, przekierowania i błędy się nie liczą. Bez IP —
tylko licznik, czas ostatniego ekranu i sekcja (pierwszy segment ścieżki).
Każdy wyjątek → ostrzeżenie w logu; odpowiedź zawsze wraca bez zmian.
"""

import logging
import re
from collections.abc import Callable

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from .models import DemoVisitor
from .visitor_gate import gate_enabled, visitor_id
from .visitor_notify import notify_engaged_visitor

logger = logging.getLogger(__name__)

MAX_SECTIONS = 20
MAX_SECTION_LEN = 40
SKIP_PREFIXES = ("/healthz", "/favicon", "/robots.txt")
_NOT_ALLOWED = re.compile(r"[^a-z0-9_-]")


def section_of(path: str) -> str:
    """`/palety/123` → `palety`, `/` → `start`; tylko [a-z0-9_-], max 40 znaków."""
    first = path.strip("/").split("/", 1)[0].lower()
    if not first:
        return "start"
    return _NOT_ALLOWED.sub("", first)[:MAX_SECTION_LEN]


def _countable(request: HttpRequest, response: HttpResponse) -> bool:
    if request.method != "GET" or not 200 <= response.status_code < 300:
        return False
    if not response.get("Content-Type", "").startswith("text/html"):
        return False
    path = request.path
    static = "/" + settings.STATIC_URL.lstrip("/")
    if path.startswith(static) or path.startswith(SKIP_PREFIXES):
        return False
    return "/api/" not in path


def record_view(pk: int, path: str) -> None:
    """page_views += 1, last_seen_at = teraz, sekcja += 1 (max 20 sekcji)."""
    with transaction.atomic():
        visitor = DemoVisitor.objects.select_for_update().filter(pk=pk).first()
        if visitor is None:  # wpis usunięty (retencja) — nic do liczenia
            return
        sections = dict(visitor.sections or {})
        section = section_of(path)
        if section and (section in sections or len(sections) < MAX_SECTIONS):
            sections[section] = int(sections.get(section, 0)) + 1
        visitor.page_views += 1
        visitor.last_seen_at = timezone.now()
        visitor.sections = sections
        visitor.save(update_fields=["page_views", "last_seen_at", "sections"])
    threshold = int(getattr(settings, "NTFY_ENGAGED_VIEWS", 10) or 0)
    if threshold > 0 and visitor.page_views == threshold:
        notify_engaged_visitor(
            visitor.first_name, visitor.last_name, visitor.company, visitor.page_views
        )


class VisitorActivityMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        try:
            if gate_enabled() and _countable(request, response):
                pk = visitor_id(request)
                if pk is not None:
                    record_view(pk, request.path)
        except Exception:  # licznik nigdy nie psuje odpowiedzi
            logger.warning("Nie zapisano aktywności gościa demo", exc_info=True)
        return response
