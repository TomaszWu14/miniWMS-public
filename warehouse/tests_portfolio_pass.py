"""Przepustka z portfolio (ciasteczko `gosc`): omija bramkę, bez sieci w testach."""

import urllib.error
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from .models import DemoVisitor
from .tests_recruiter import _demo_user

TOKEN = "tajny-token-gosc"
OPENER = "warehouse.portfolio_pass.urllib.request.build_opener"


def _opener(status=200, error=None):
    opener = mock.MagicMock()
    if error is not None:
        opener.open.side_effect = error
    else:
        resp = mock.MagicMock()
        resp.status = status
        opener.open.return_value.__enter__.return_value = resp
    return opener


@override_settings(
    DEMO_MODE=True, DEMO_VISITOR_GATE=True, NTFY_URL="https://ntfy.test/t"
)
class PortfolioPassTests(TestCase):
    def setUp(self):
        cache.clear()
        _demo_user()

    def _start(self, token=TOKEN):
        if token is not None:
            self.client.cookies["gosc"] = token
        return self.client.get("/demo/")

    def test_valid_pass_skips_gate_without_visitor_or_push(self):
        with (
            mock.patch(OPENER, return_value=_opener(200)) as build,
            mock.patch("warehouse.visitor_notify.urllib.request.urlopen") as push,
        ):
            resp = self._start()
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn("przedstaw-sie", resp["Location"])
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(DemoVisitor.objects.count(), 0)
        push.assert_not_called()
        req = build.return_value.open.call_args.args[0]
        self.assertEqual(req.full_url, "https://portfolio.twapp.pl/api/gosc")
        self.assertEqual(req.get_header("Cookie"), f"gosc={TOKEN}")
        self.assertEqual(build.return_value.open.call_args.kwargs["timeout"], 2)

    def test_valid_pass_is_cached(self):
        with mock.patch(OPENER, return_value=_opener(200)) as build:
            self._start()
            self.client.logout()
            self._start()
        self.assertEqual(build.return_value.open.call_count, 1)

    def test_valid_pass_for_button_and_manual_login(self):
        with mock.patch(OPENER, return_value=_opener(200)):
            self.client.cookies["gosc"] = TOKEN
            resp = self.client.post("/login/demo/")
        self.assertNotIn("przedstaw-sie", resp["Location"])
        self.assertIn("_auth_user_id", self.client.session)

    def test_401_shows_gate(self):
        err = urllib.error.HTTPError("u", 401, "no", {}, None)
        with mock.patch(OPENER, return_value=_opener(error=err)):
            resp = self._start()
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_timeout_shows_gate_and_does_not_crash(self):
        with mock.patch(OPENER, return_value=_opener(error=TimeoutError())) as build:
            resp = self._start()
            self.client.logout()
            resp2 = self._start()
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])
        self.assertIn("/demo/przedstaw-sie/", resp2["Location"])
        self.assertEqual(build.return_value.open.call_count, 1)  # krótki cache błędu

    def test_other_status_shows_gate(self):
        with mock.patch(OPENER, return_value=_opener(204)):
            resp = self._start()
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])

    def test_no_cookie_means_no_network_call(self):
        with mock.patch(OPENER) as build:
            resp = self._start(token=None)
        build.assert_not_called()
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])

    def test_oversized_token_means_no_network_call(self):
        with mock.patch(OPENER) as build:
            resp = self._start(token="x" * 201)
        build.assert_not_called()
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])

    @override_settings(PORTFOLIO_PASS=False)
    def test_disabled_by_env(self):
        with mock.patch(OPENER) as build:
            resp = self._start()
        build.assert_not_called()
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])

    @override_settings(PORTFOLIO_URL="http://portfolio.twapp.pl")
    def test_non_https_url_disables_check(self):
        with mock.patch(OPENER) as build:
            resp = self._start()
        build.assert_not_called()
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])

    def test_gate_page_has_no_portfolio_pixel_but_login_has(self):
        self.assertNotContains(
            self.client.get("/demo/przedstaw-sie/"), "portfolio.twapp.pl/px/"
        )
        self.assertContains(self.client.get("/login/"), "portfolio.twapp.pl/px/miniwms")
