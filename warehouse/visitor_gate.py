"""Bramka odwiedzających demo: uprzejme, obowiązkowe przedstawienie się.

Działa tylko przy DEMO_MODE i DEMO_VISITOR_GATE. Chroni wejścia na konta demo
(„Wejdź jako demo”, /demo/, ręczne logowanie na demo_*) — zwykłe konta,
/healthz, /login/ i statyki zostają bez zmian.
Znacznik „przedstawił się” to podpisane ciasteczko na 30 dni (nie sesja —
ta wygasa po 30 min bezczynności).
"""

import unicodedata
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .models import DemoVisitor
from .roles import admin_required

COOKIE_NAME = "demo_visitor"
COOKIE_MAX_AGE = int(timedelta(days=30).total_seconds())


def gate_enabled() -> bool:
    return bool(settings.DEMO_MODE and settings.DEMO_VISITOR_GATE)


def gate_passed(request: HttpRequest) -> bool:
    return (
        request.get_signed_cookie(COOKIE_NAME, default=None, max_age=COOKIE_MAX_AGE)
        == "1"
    )


def gate_redirect(request: HttpRequest, flow: str, next_url: str = ""):
    """Przekierowanie do formularza; `flow` mówi, co zrobić po zapisaniu."""
    from urllib.parse import urlencode

    query = {"flow": flow}
    if next_url:
        query["next"] = next_url
    return redirect(f"/demo/przedstaw-sie/?{urlencode(query)}")


def _clean_name(value: str) -> str:
    value = (value or "").strip()
    if not 2 <= len(value) <= 100:
        raise forms.ValidationError("Wpisz od 2 do 100 znaków.")
    if any(unicodedata.category(ch).startswith("C") for ch in value):
        raise forms.ValidationError("Niedozwolone znaki sterujące.")
    return value


class VisitorForm(forms.Form):
    first_name = forms.CharField(label="Imię", max_length=200, strip=False)
    last_name = forms.CharField(label="Nazwisko", max_length=200, strip=False)
    company = forms.CharField(label="Firma", max_length=200, strip=False)
    consent = forms.BooleanField(
        label="Zapoznałem(-am) się z informacją o przetwarzaniu danych",
        error_messages={"required": "Potwierdź zapoznanie się z informacją."},
    )
    website = forms.CharField(required=False)  # honeypot — człowiek nie widzi

    def clean_first_name(self):
        return _clean_name(self.cleaned_data["first_name"])

    def clean_last_name(self):
        return _clean_name(self.cleaned_data["last_name"])

    def clean_company(self):
        return _clean_name(self.cleaned_data["company"])

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Odrzucono.")
        return ""


@require_http_methods(["GET", "POST"])
def visitor_gate(request: HttpRequest) -> HttpResponse:
    if not gate_enabled():
        raise Http404
    from .demo import demo_enter  # import leniwy: demo.py importuje ten moduł

    flow = request.POST.get("flow") or request.GET.get("flow", "")
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if request.method == "POST":
        form = VisitorForm(request.POST)
        if form.is_valid():
            DemoVisitor.purge_old()
            DemoVisitor.objects.create(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                company=form.cleaned_data["company"],
            )
            if flow == "button":
                response = demo_enter(request, next_url)
            elif flow == "start":
                response = redirect("demo_start")
            else:
                messages.success(
                    request, "Dziękuję! Teraz możesz zalogować się na konto demo."
                )
                response = redirect("login")
            response.set_signed_cookie(
                COOKIE_NAME,
                "1",
                max_age=COOKIE_MAX_AGE,
                httponly=True,
                samesite="Lax",
                secure=settings.SESSION_COOKIE_SECURE,
            )
            return response
        status = 400
    else:
        form = VisitorForm()
        status = 200
    safe_next = (
        next_url
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()})
        else ""
    )
    return render(
        request,
        "warehouse/demo_gate.html",
        {"form": form, "flow": flow, "next": safe_next},
        status=status,
    )


@admin_required
def visitor_list(request: HttpRequest) -> HttpResponse:
    page = Paginator(DemoVisitor.objects.all(), 100).get_page(request.GET.get("page"))
    return render(
        request,
        "warehouse/visitor_list.html",
        {"visitors": page, "page_obj": page, "retention": DemoVisitor.RETENTION_DAYS},
    )
