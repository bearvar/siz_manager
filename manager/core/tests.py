from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class DesignStaticTests(SimpleTestCase):
    def test_custom_css_uses_blue_design_tokens(self):
        css_path = Path(settings.BASE_DIR) / "static" / "css" / "custom.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn("--siz-color-brand-blue: #539fe1", css)
        self.assertIn("--siz-color-canvas: #f4f4f5", css)
        self.assertIn("--siz-color-border: #e4e4e7", css)
        self.assertIn("background: var(--siz-color-brand-blue)", css)
        self.assertNotIn("#019d91", css)

    def test_custom_css_styles_core_bootstrap_components(self):
        css_path = Path(settings.BASE_DIR) / "static" / "css" / "custom.css"
        css = css_path.read_text(encoding="utf-8")

        required_selectors = [
            ".top-navbar-container",
            ".top-navbar-container .container-fluid",
            ".btn-primary",
            ".card",
            ".table",
            ".form-control",
            ".dropdown-menu",
            "footer",
        ]
        for selector in required_selectors:
            with self.subTest(selector=selector):
                self.assertIn(selector, css)


class DesignTemplateTests(SimpleTestCase):
    def test_header_include_is_not_a_full_html_document(self):
        header_path = Path(settings.BASE_DIR) / "templates" / "includes" / "header.html"
        header_source = header_path.read_text(encoding="utf-8")
        header = header_source.lower()

        forbidden = ["<!doctype", "<html", "<head", "<body", "</html", "</body"]
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, header)
        self.assertIn("navbar-dark top-navbar-container", header_source)

    def test_base_template_owns_global_assets(self):
        base_path = Path(settings.BASE_DIR) / "templates" / "base.html"
        base = base_path.read_text(encoding="utf-8")

        self.assertIn("{% static 'css/bootstrap.min.css' %}", base)
        self.assertIn("{% static 'css/custom.css' %}", base)
        self.assertIn('class="app-shell"', base)

    def test_custom_css_keeps_header_layout_full_width(self):
        css_path = Path(settings.BASE_DIR) / "static" / "css" / "custom.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn("max-width: none", css)
        self.assertIn("margin-right: auto", css)
        self.assertIn("width: 142px", css)

    def test_create_employee_template_does_not_define_document_shell(self):
        template_path = Path(settings.BASE_DIR) / "templates" / "core" / "create_employee.html"
        template = template_path.read_text(encoding="utf-8").lower()

        forbidden = ["<body", "</body", "<main", "</main"]
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, template)
