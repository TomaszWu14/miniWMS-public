"""Bramka odwiedzających demo: przedstawienie się przed wejściem."""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import DemoVisitor, Role
from .tests_recruiter import _demo_user

GOOD = {
    "first_name": "Anna",
    "last_name": "Nowak",
    "company": "ACME",
    "consent": "on",
    "website": "",
}


@override_settings(DEMO_MODE=True, DEMO_VISITOR_GATE=True)
class VisitorGateTests(TestCase):
    def setUp(self):
        cache.clear()
        _demo_user()

    def _pass_gate(self):
        self.client.post("/demo/przedstaw-sie/", {**GOOD, "flow": "manual"})

    def test_button_without_data_redirects_to_gate(self):
        resp = self.client.post("/login/demo/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_start_link_redirects_to_gate(self):
        resp = self.client.get("/demo/")
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_manual_demo_login_blocked_but_normal_account_not(self):
        User.objects.create_user("jan", password="x")
        resp = self.client.post(
            "/login/", {"username": "demo_operator", "password": "demo1234"}
        )
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])
        self.assertNotIn("_auth_user_id", self.client.session)
        self.client.post("/login/", {"username": "jan", "password": "x"})
        self.assertIn("_auth_user_id", self.client.session)

    def test_gate_page_and_login_page_open(self):
        resp = self.client.get("/demo/przedstaw-sie/")
        self.assertContains(resp, "Zanim wejdziesz do wersji demonstracyjnej")
        self.assertContains(resp, "art. 6 ust. 1 lit. f RODO")
        # adres kontaktowy ukryty przed botami zbierającymi adresy
        self.assertContains(resp, "tomasz.wierzbowski [at] op.pl")
        self.assertNotContains(resp, "tomasz.wierzbowski@op.pl")
        self.assertEqual(self.client.get("/login/").status_code, 200)
        self.assertEqual(self.client.get("/healthz").status_code, 200)

    def test_missing_or_invalid_data_refused(self):
        for bad in (
            {**GOOD, "first_name": ""},
            {**GOOD, "last_name": "A"},
            {**GOOD, "company": "x" * 101},
            {**GOOD, "company": "AC\x00ME"},
            {**GOOD, "first_name": "  "},
            {k: v for k, v in GOOD.items() if k != "consent"},
        ):
            resp = self.client.post("/demo/przedstaw-sie/", {**bad, "flow": "button"})
            self.assertEqual(resp.status_code, 400, bad)
        self.assertEqual(DemoVisitor.objects.count(), 0)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_honeypot_refused(self):
        resp = self.client.post(
            "/demo/przedstaw-sie/", {**GOOD, "website": "http://spam", "flow": "button"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(DemoVisitor.objects.count(), 0)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_valid_data_records_visitor_and_logs_in(self):
        resp = self.client.post(
            "/demo/przedstaw-sie/", {**GOOD, "first_name": "  Anna ", "flow": "button"}
        )
        self.assertRedirects(resp, "/")
        v = DemoVisitor.objects.get()
        self.assertEqual(
            (v.first_name, v.last_name, v.company), ("Anna", "Nowak", "ACME")
        )
        self.assertIn("_auth_user_id", self.client.session)
        cookie = resp.cookies["demo_visitor"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(int(cookie["max-age"]), 30 * 86400)

    def test_cookie_lets_later_entries_through(self):
        self._pass_gate()
        resp = self.client.post("/login/demo/")
        self.assertRedirects(resp, "/")
        self.assertEqual(DemoVisitor.objects.count(), 1)

    def test_forged_cookie_does_not_pass(self):
        self.client.cookies["demo_visitor"] = "1"
        resp = self.client.post("/login/demo/")
        self.assertIn("/demo/przedstaw-sie/", resp["Location"])

    def test_external_next_is_not_followed(self):
        resp = self.client.post(
            "/demo/przedstaw-sie/",
            {**GOOD, "flow": "button", "next": "https://evil.example/"},
        )
        self.assertRedirects(resp, "/")

    def test_gate_off_keeps_old_behaviour(self):
        with override_settings(DEMO_VISITOR_GATE=False):
            self.assertRedirects(self.client.post("/login/demo/"), "/")
            self.assertEqual(self.client.get("/demo/przedstaw-sie/").status_code, 404)

    def test_retention_90_days_on_write(self):
        old = DemoVisitor.objects.create(
            first_name="Stary",
            last_name="Wpis",
            company="X",
            created_at=timezone.now() - timedelta(days=91),
        )
        fresh = DemoVisitor.objects.create(
            first_name="Nowy",
            last_name="Wpis",
            company="X",
            created_at=timezone.now() - timedelta(days=89),
        )
        self._pass_gate()
        self.assertFalse(DemoVisitor.objects.filter(pk=old.pk).exists())
        self.assertTrue(DemoVisitor.objects.filter(pk=fresh.pk).exists())


@override_settings(DEMO_MODE=True, DEMO_VISITOR_GATE=True)
class VisitorListAndResetTests(TestCase):
    def setUp(self):
        cache.clear()
        DemoVisitor.objects.create(
            first_name="Stary",
            last_name="A",
            company="X",
            created_at=timezone.now() - timedelta(days=2),
        )
        DemoVisitor.objects.create(first_name="Nowy", last_name="B", company="Y")

    def test_demo_reset_keeps_visitors(self):
        op = _demo_user()
        self.client.force_login(op)
        self.client.post("/demo/przywroc/")
        self.assertEqual(DemoVisitor.objects.count(), 2)

    def test_list_admin_only_newest_first(self):
        url = "/odwiedzajacy/"
        self.assertEqual(self.client.get(url).status_code, 302)
        op = _demo_user()
        self.client.force_login(op)
        self.assertNotEqual(self.client.get(url).status_code, 200)
        admin = User.objects.create_user("adm", password="x")
        admin.profile.role = Role.ADMIN
        admin.profile.save()
        self.client.force_login(admin)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            [v.first_name for v in resp.context["visitors"]], ["Nowy", "Stary"]
        )
