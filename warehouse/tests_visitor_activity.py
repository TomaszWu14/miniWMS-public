"""Aktywność gościa demo: liczenie ekranów, sekcje, push „zaangażowany gość”."""

from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from .models import DemoVisitor, Role
from .tests_recruiter import _demo_user
from .tests_visitor_gate import GOOD
from .tests_visitor_notify import URL, _SyncThread
from .visitor_activity import MAX_SECTIONS, record_view, section_of
from .visitor_gate import visitor_id


def _signed(value: str) -> str:
    """Wartość podpisana tak samo jak w bramce (set_signed_cookie)."""
    response = HttpResponse()
    response.set_signed_cookie("demo_visitor", value)
    return response.cookies["demo_visitor"].value


@override_settings(DEMO_MODE=True, DEMO_VISITOR_GATE=True, NTFY_URL="")
class VisitorActivityTests(TestCase):
    def setUp(self):
        cache.clear()
        _demo_user()

    def _enter(self):
        self.client.post("/demo/przedstaw-sie/", {**GOOD, "flow": "button"})
        return DemoVisitor.objects.get()

    def test_cookie_carries_visitor_id(self):
        visitor = self._enter()
        request = RequestFactory().get("/")
        request.COOKIES["demo_visitor"] = self.client.cookies["demo_visitor"].value
        self.assertEqual(visitor_id(request), visitor.pk)

    def test_three_html_gets_counted_with_sections(self):
        visitor = self._enter()
        for path in ("/", "/materialy/", "/materialy/"):
            self.assertEqual(self.client.get(path).status_code, 200)
        visitor.refresh_from_db()
        self.assertEqual(visitor.page_views, 3)
        self.assertEqual(visitor.sections, {"start": 1, "materialy": 2})
        self.assertIsNotNone(visitor.last_seen_at)

    def test_static_health_api_404_and_post_not_counted(self):
        visitor = self._enter()
        self.client.get("/healthz")
        self.client.get("/static/warehouse/app.css")
        self.client.get("/skaner/api/hu/?code=X")
        self.client.get("/nie-ma-takiej-strony/")
        self.client.get("/demo/")  # przekierowanie, nie ekran
        self.client.post("/powitanie/ukryj/")
        visitor.refresh_from_db()
        self.assertEqual(visitor.page_views, 0)
        self.assertEqual(visitor.sections, {})
        self.assertIsNone(visitor.last_seen_at)

    def test_no_cookie_or_forged_or_old_flag_not_counted(self):
        visitor = DemoVisitor.objects.create(first_name="A", last_name="B", company="C")
        self.client.force_login(User.objects.get(username="demo_operator"))
        self.client.get("/")
        self.client.cookies["demo_visitor"] = f"id:{visitor.pk}"  # niepodpisane
        self.client.get("/")
        forged = _signed(f"id:{visitor.pk}")[:-2] + "xx"
        self.client.cookies["demo_visitor"] = forged
        self.client.get("/")
        self.client.cookies["demo_visitor"] = _signed("1")  # flaga sprzed zmiany
        self.assertEqual(self.client.get("/").status_code, 200)
        visitor.refresh_from_db()
        self.assertEqual(visitor.page_views, 0)

    def test_old_flag_still_passes_gate(self):
        self.client.cookies["demo_visitor"] = _signed("1")
        self.assertRedirects(self.client.post("/login/demo/"), "/")
        self.assertIn("_auth_user_id", self.client.session)

    def test_garbage_cookie_does_not_pass_gate(self):
        self.client.cookies["demo_visitor"] = _signed("1")[:-3] + "zzz"
        self.assertIn(
            "/demo/przedstaw-sie/", self.client.post("/login/demo/")["Location"]
        )

    def test_gate_off_counts_nothing(self):
        visitor = self._enter()
        with override_settings(DEMO_VISITOR_GATE=False):
            self.client.get("/")
        visitor.refresh_from_db()
        self.assertEqual(visitor.page_views, 0)

    def test_error_while_counting_does_not_break_response(self):
        self._enter()
        with (
            mock.patch(
                "warehouse.visitor_activity.record_view", side_effect=RuntimeError
            ),
            self.assertLogs("warehouse.visitor_activity", "WARNING"),
        ):
            resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_sections_limited_to_20_keys(self):
        visitor = DemoVisitor.objects.create(
            first_name="A",
            last_name="B",
            company="C",
            sections={f"s{i}": 1 for i in range(MAX_SECTIONS)},
        )
        record_view(visitor.pk, "/nowa-sekcja/")
        record_view(visitor.pk, "/s3/")
        visitor.refresh_from_db()
        self.assertEqual(len(visitor.sections), MAX_SECTIONS)
        self.assertNotIn("nowa-sekcja", visitor.sections)
        self.assertEqual(visitor.sections["s3"], 2)
        self.assertEqual(visitor.page_views, 2)

    def test_section_of(self):
        self.assertEqual(section_of("/"), "start")
        self.assertEqual(section_of("/palety/123"), "palety")
        self.assertEqual(section_of("/Przyjęcia/1/"), "przyjcia")
        self.assertEqual(section_of("/" + "a" * 60 + "/"), "a" * 40)
        self.assertEqual(section_of("/ąę/"), "")

    def test_deleted_visitor_ignored(self):
        record_view(999999, "/")
        self.assertFalse(DemoVisitor.objects.exists())

    def test_list_shows_activity_columns(self):
        now = timezone.now()
        DemoVisitor.objects.create(
            first_name="Ewa",
            last_name="K",
            company="X",
            created_at=now - timedelta(minutes=12),
            last_seen_at=now,
            page_views=7,
            sections={"palety": 4, "start": 2, "materialy": 1, "spis": 1},
        )
        DemoVisitor.objects.create(first_name="Bez", last_name="Ruchu", company="Y")
        admin = User.objects.create_user("adm", password="x")
        admin.profile.role = Role.ADMIN
        admin.profile.save()
        self.client.force_login(admin)
        resp = self.client.get("/odwiedzajacy/")
        for text in ("Ekrany", "Czas", "Najczęściej", "ok. 12 min"):
            self.assertContains(resp, text)
        self.assertContains(resp, "palety (4), start (2), materialy (1)")
        self.assertNotContains(resp, "spis (1)")
        self.assertContains(resp, "—")


@override_settings(
    DEMO_MODE=True, DEMO_VISITOR_GATE=True, NTFY_URL=URL, NTFY_ENGAGED_VIEWS=3
)
@mock.patch("warehouse.visitor_notify.threading.Thread", _SyncThread)
@mock.patch("warehouse.visitor_notify.urllib.request.urlopen")
class EngagedVisitorPushTests(TestCase):
    def setUp(self):
        cache.clear()
        _demo_user()

    def _enter_and_view(self, urlopen, views, company="ACME"):
        self.client.post(
            "/demo/przedstaw-sie/", {**GOOD, "company": company, "flow": "button"}
        )
        urlopen.reset_mock()  # bez pushu o nowym gościu
        for _ in range(views):
            self.client.get("/")

    def test_exactly_one_push_at_threshold(self, urlopen):
        self._enter_and_view(urlopen, 5)
        urlopen.assert_called_once()
        req = urlopen.call_args.args[0]
        headers = {k.lower(): v for k, v in req.header_items()}
        self.assertEqual(headers["title"], "Gosc oglada demo: miniWMS")
        self.assertEqual(headers["tags"], "eyes")
        self.assertEqual(headers["priority"], "default")
        self.assertEqual(
            req.data.decode("utf-8"),
            "Anna Nowak (ACME) obejrzał już 3 ekranów w miniWMS",
        )

    def test_below_threshold_no_push(self, urlopen):
        self._enter_and_view(urlopen, 2)
        urlopen.assert_not_called()

    @override_settings(NTFY_ENGAGED_VIEWS=0)
    def test_zero_disables(self, urlopen):
        self._enter_and_view(urlopen, 5)
        urlopen.assert_not_called()

    @override_settings(NTFY_WATCH_COMPANIES="acme")
    def test_watched_company_engaged_push_is_urgent(self, urlopen):
        self._enter_and_view(urlopen, 3, company="Acme Polska")
        req = urlopen.call_args.args[0]
        self.assertEqual(req.get_header("Priority"), "urgent")
        self.assertEqual(req.get_header("Tags"), "eyes")
