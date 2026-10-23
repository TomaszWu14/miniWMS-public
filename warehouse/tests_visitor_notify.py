"""Powiadomienie push (ntfy) o nowym gościu demo — HTTP zawsze mockowany."""

from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from .models import DemoVisitor
from .tests_recruiter import _demo_user
from .tests_visitor_gate import GOOD

URL = "https://ntfy.example/tajny-temat"


class _SyncThread:
    """Zamiast wątku w tle — uruchamia cel od razu (deterministyczny test)."""

    def __init__(self, target, args=(), daemon=None):
        self._target, self._args = target, args

    def start(self):
        self._target(*self._args)


@override_settings(DEMO_MODE=True, DEMO_VISITOR_GATE=True, NTFY_URL=URL, NTFY_TOKEN="")
@mock.patch("warehouse.visitor_notify.threading.Thread", _SyncThread)
@mock.patch("warehouse.visitor_notify.urllib.request.urlopen")
class VisitorNotifyTests(TestCase):
    def setUp(self):
        cache.clear()
        _demo_user()

    def _post(self, data):
        return self.client.post("/demo/przedstaw-sie/", {**data, "flow": "button"})

    def test_valid_form_sends_one_notification(self, urlopen):
        resp = self._post(GOOD)
        self.assertRedirects(resp, "/")
        urlopen.assert_called_once()
        req = urlopen.call_args.args[0]
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 5)
        self.assertEqual(req.full_url, URL)
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(
            req.data.decode("utf-8"), "Anna Nowak (ACME) wszedł do miniWMS"
        )
        headers = {k.lower(): v for k, v in req.header_items()}
        self.assertEqual(headers["title"], "Nowy gosc: miniWMS")
        self.assertEqual(headers["tags"], "bell")
        self.assertEqual(headers["priority"], "high")
        self.assertNotIn("authorization", headers)
        for value in headers.values():
            value.encode("ascii")  # nagłówki tylko ASCII

    def test_body_truncated_to_300(self, urlopen):
        self._post(
            {
                **GOOD,
                "first_name": "Ą" * 100,
                "last_name": "Ę" * 100,
                "company": "Ż" * 100,
            }
        )
        self.assertEqual(len(urlopen.call_args.args[0].data.decode("utf-8")), 300)

    @override_settings(NTFY_TOKEN="sekret")
    def test_token_adds_authorization_header(self, urlopen):
        self._post(GOOD)
        req = urlopen.call_args.args[0]
        self.assertEqual(req.get_header("Authorization"), "Bearer sekret")

    def test_honeypot_and_invalid_data_send_nothing(self, urlopen):
        self._post({**GOOD, "website": "http://spam"})
        self._post({**GOOD, "last_name": "A"})
        self._post({k: v for k, v in GOOD.items() if k != "consent"})
        urlopen.assert_not_called()
        self.assertEqual(DemoVisitor.objects.count(), 0)

    @override_settings(NTFY_URL="")
    def test_no_url_no_traffic(self, urlopen):
        self.assertRedirects(self._post(GOOD), "/")
        urlopen.assert_not_called()

    @override_settings(NTFY_URL="file:///etc/passwd")
    def test_non_http_url_ignored(self, urlopen):
        self.assertRedirects(self._post(GOOD), "/")
        urlopen.assert_not_called()

    def test_send_error_does_not_break_visitor_flow(self, urlopen):
        urlopen.side_effect = OSError("ntfy nie odpowiada")
        with self.assertLogs("warehouse.visitor_notify", "WARNING"):
            resp = self._post(GOOD)
        self.assertRedirects(resp, "/")
        self.assertEqual(DemoVisitor.objects.count(), 1)
        self.assertIn("_auth_user_id", self.client.session)

    def test_gate_page_mentions_ntfy_and_activity(self, urlopen):
        resp = self.client.get("/demo/przedstaw-sie/")
        self.assertContains(
            resp,
            "O każdej wizycie (imię, nazwisko, firma) dostaję powiadomienie na telefon"
            " przez usługę powiadomień push ntfy. Zapisuję też, ile i jakie ekrany"
            " wersji demonstracyjnej obejrzałeś (bez adresu IP), żeby wiedzieć, co"
            " zainteresowało gości. Poza tym nikomu danych nie przekazuję.",
        )
        self.assertNotContains(resp, "push ntfy; poza tym")

    def _headers(self, urlopen):
        req = urlopen.call_args.args[0]
        return req, {k.lower(): v for k, v in req.header_items()}

    @override_settings(NTFY_WATCH_COMPANIES="globex, acme")
    def test_watched_company_sends_urgent_alarm(self, urlopen):
        self._post({**GOOD, "company": "ÄCME  Sp. z o.o."})
        urlopen.assert_called_once()
        req, headers = self._headers(urlopen)
        self.assertEqual(headers["priority"], "urgent")
        self.assertEqual(headers["tags"], "rotating_light")
        self.assertEqual(headers["title"], "UWAGA firma z listy: miniWMS")
        headers["title"].encode("ascii")
        self.assertEqual(
            req.data.decode("utf-8"),
            "⚠️ Anna Nowak (ÄCME  Sp. z o.o.) wszedł do miniWMS",
        )

    @override_settings(NTFY_WATCH_COMPANIES="Łódź")
    def test_watch_phrase_diacritics_and_case(self, urlopen):
        self._post({**GOOD, "company": "Hurtownia LODZ"})
        self.assertEqual(self._headers(urlopen)[1]["priority"], "urgent")

    @override_settings(NTFY_WATCH_COMPANIES="globex, initech")
    def test_no_match_sends_normal_push(self, urlopen):
        self._post(GOOD)
        req, headers = self._headers(urlopen)
        self.assertEqual(headers["priority"], "high")
        self.assertEqual(headers["title"], "Nowy gosc: miniWMS")
        self.assertFalse(req.data.decode("utf-8").startswith("⚠️"))

    @override_settings(NTFY_WATCH_COMPANIES=" , a, ")
    def test_empty_or_too_short_phrases_ignored(self, urlopen):
        self._post(GOOD)
        self.assertEqual(self._headers(urlopen)[1]["priority"], "high")

    @override_settings(NTFY_WATCH_COMPANIES="acme", NTFY_URL="")
    def test_watched_without_url_sends_nothing(self, urlopen):
        self._post(GOOD)
        urlopen.assert_not_called()
