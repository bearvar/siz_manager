from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from users.context_processors import ui_theme
from users.theme import (
    THEME_COOKIE_NAME,
    THEME_DARK,
    THEME_LIGHT,
    normalize_theme,
    set_theme_cookie,
)


class ThemeUtilityTests(SimpleTestCase):
    def test_normalize_theme_accepts_supported_values(self):
        self.assertEqual(normalize_theme("light"), THEME_LIGHT)
        self.assertEqual(normalize_theme("dark"), THEME_DARK)

    def test_normalize_theme_rejects_unsupported_values(self):
        self.assertIsNone(normalize_theme(""))
        self.assertIsNone(normalize_theme("system"))
        self.assertIsNone(normalize_theme(" DARK "))

    @override_settings(SESSION_COOKIE_SECURE=True)
    def test_set_theme_cookie_uses_safe_cookie_options(self):
        from django.http import JsonResponse

        response = JsonResponse({})
        set_theme_cookie(response, THEME_DARK)
        cookie = response.cookies[THEME_COOKIE_NAME]

        self.assertEqual(cookie.value, THEME_DARK)
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertTrue(cookie["secure"])
        self.assertTrue(cookie["httponly"])


class CustomUserThemeTests(TestCase):
    def test_new_user_defaults_to_light_theme(self):
        user = get_user_model().objects.create_user(
            username="theme-user",
            password="test-password-123",
            first_name="Theme",
            last_name="User",
            patronymic="",
            email="theme@example.com",
            position="Инженер",
            department="ИТ",
        )

        self.assertEqual(user.theme, THEME_LIGHT)


class ThemeContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_context_uses_authenticated_user_theme(self):
        request = self.factory.get("/")
        request.user = get_user_model().objects.create_user(
            username="dark-user",
            password="test-password-123",
            first_name="Dark",
            last_name="User",
            patronymic="",
            email="dark@example.com",
            position="Инженер",
            department="ИТ",
            theme=THEME_DARK,
        )

        self.assertEqual(ui_theme(request), {"ui_theme": THEME_DARK})

    def test_context_uses_cookie_for_anonymous_user(self):
        request = self.factory.get("/", HTTP_COOKIE=f"{THEME_COOKIE_NAME}=dark")
        request.user = AnonymousUser()

        self.assertEqual(ui_theme(request), {"ui_theme": THEME_DARK})

    def test_context_falls_back_to_light_for_invalid_cookie(self):
        request = self.factory.get("/", HTTP_COOKIE=f"{THEME_COOKIE_NAME}=system")
        request.user = AnonymousUser()

        self.assertEqual(ui_theme(request), {"ui_theme": THEME_LIGHT})


class SetThemeViewTests(TestCase):
    def test_anonymous_user_can_save_theme_to_cookie(self):
        response = self.client.post(reverse("users:set_theme"), {"theme": THEME_DARK})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"theme": THEME_DARK})
        self.assertEqual(response.cookies[THEME_COOKIE_NAME].value, THEME_DARK)

    def test_authenticated_user_saves_theme_to_database_and_cookie(self):
        user = get_user_model().objects.create_user(
            username="theme-save",
            password="test-password-123",
            first_name="Theme",
            last_name="Save",
            patronymic="",
            email="save@example.com",
            position="Инженер",
            department="ИТ",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("users:set_theme"), {"theme": THEME_DARK})

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.theme, THEME_DARK)
        self.assertEqual(response.cookies[THEME_COOKIE_NAME].value, THEME_DARK)

    def test_invalid_theme_is_rejected(self):
        user = get_user_model().objects.create_user(
            username="theme-invalid",
            password="test-password-123",
            first_name="Theme",
            last_name="Invalid",
            patronymic="",
            email="invalid@example.com",
            position="Инженер",
            department="ИТ",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("users:set_theme"), {"theme": "system"})

        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.theme, THEME_LIGHT)
        self.assertNotIn(THEME_COOKIE_NAME, response.cookies)

    def test_get_theme_endpoint_is_not_allowed(self):
        response = self.client.get(reverse("users:set_theme"))

        self.assertEqual(response.status_code, 405)


class ThemeTemplateTests(SimpleTestCase):
    def test_base_template_renders_data_theme(self):
        template = Path("manager/templates/base.html").read_text()

        self.assertIn('data-theme="{{ ui_theme|default:', template)
        self.assertIn("{% static 'js/theme-switcher.js' %}", template)
        self.assertIn("themeEndpoint", template)


class ThemeHeaderTemplateTests(SimpleTestCase):
    def test_header_contains_theme_switcher(self):
        template = Path("manager/templates/includes/header.html").read_text()

        self.assertIn('class="theme-switcher"', template)
        self.assertIn("data-theme-toggle", template)
        self.assertIn('aria-label="Переключить тему"', template)
        self.assertNotIn(">Светлая тема<", template)
        self.assertNotIn(">Темная тема<", template)


class ThemeStaticFileTests(SimpleTestCase):
    def test_theme_switcher_script_contains_csrf_post(self):
        script = Path("manager/static/js/theme-switcher.js").read_text()

        self.assertIn("fetch(window.sizTheme.themeEndpoint", script)
        self.assertIn("X-CSRFToken", script)
        self.assertIn("document.documentElement.dataset.theme", script)
        self.assertIn("[data-theme-toggle]", script)


class ThemeCssTests(SimpleTestCase):
    def test_custom_css_contains_dark_theme_tokens_and_switcher_styles(self):
        css = Path("manager/static/css/custom.css").read_text()

        self.assertIn('[data-theme="dark"]', css)
        self.assertIn("--siz-color-canvas: #0f1115", css)
        self.assertIn(".theme-switcher", css)
        self.assertIn(".theme-icon-sun", css)
        self.assertIn(".theme-icon-moon", css)
        self.assertIn(".table", css)
        self.assertIn(".form-control", css)
        self.assertIn(".dropdown-menu", css)


class ThemeReleaseBookkeepingTests(SimpleTestCase):
    def test_release_bookkeeping_exists(self):
        pyproject = Path("pyproject.toml").read_text()
        changelog = Path("versions/2.1.1.md").read_text()

        self.assertIn('version = "2.1.1"', pyproject)
        self.assertIn("# 2.1.1", changelog)
        self.assertIn("переключатель темы", changelog.lower())
