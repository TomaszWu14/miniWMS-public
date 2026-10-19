"""Nagłówki bezpieczeństwa uzupełniające `SecurityMiddleware` Django.

Django już ustawia: X-Content-Type-Options (nosniff), Referrer-Policy (same-origin),
Cross-Origin-Opener-Policy (same-origin), X-Frame-Options (DENY,
`XFrameOptionsMiddleware`) i HSTS (tylko prod, za HTTPS — `prod.py`).
Tu dochodzi Permissions-Policy oraz `Cache-Control: no-store` dla odpowiedzi JSON.
Wszystko przez `setdefault` — świadome ustawienia widoków/plików statycznych wygrywają.
"""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

# Aparat jest potrzebny skanerowi (scanner_camera.js) — tylko z własnej domeny.
PERMISSIONS_POLICY = "camera=(self), microphone=(), geolocation=(), payment=(), usb=()"


class SecurityHeadersMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response.headers.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("application/json"):
            # Dane magazynowe z API skanera nie mogą zostać w cache przeglądarki/proxy.
            response.headers.setdefault("Cache-Control", "no-store")
        return response
