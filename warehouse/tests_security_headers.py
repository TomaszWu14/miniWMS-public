"""Nagłówki bezpieczeństwa na każdej odpowiedzi (config/middleware.py + Django)."""

from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase, TestCase

from config.middleware import PERMISSIONS_POLICY, SecurityHeadersMiddleware


class SecurityHeadersTests(TestCase):
    def test_html_page_has_security_headers(self):
        resp = self.client.get("/login/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["X-Content-Type-Options"], "nosniff")
        self.assertEqual(resp["X-Frame-Options"], "DENY")
        self.assertEqual(resp["Referrer-Policy"], "same-origin")
        self.assertEqual(resp["Cross-Origin-Opener-Policy"], "same-origin")
        self.assertEqual(resp["Permissions-Policy"], PERMISSIONS_POLICY)
        self.assertIn("camera=(self)", resp["Permissions-Policy"])

    def test_json_response_is_not_cached(self):
        resp = self.client.get("/healthz")
        self.assertTrue(resp["Content-Type"].startswith("application/json"))
        self.assertEqual(resp["Cache-Control"], "no-store")
        self.assertEqual(resp["X-Content-Type-Options"], "nosniff")


class SecurityHeadersMiddlewareUnitTests(SimpleTestCase):
    def test_explicit_headers_are_not_overridden(self):
        def view(request):
            resp = JsonResponse({"ok": True})
            resp["Cache-Control"] = "max-age=60"
            resp["Permissions-Policy"] = "camera=()"
            return resp

        resp = SecurityHeadersMiddleware(view)(RequestFactory().get("/x"))
        self.assertEqual(resp["Cache-Control"], "max-age=60")
        self.assertEqual(resp["Permissions-Policy"], "camera=()")
