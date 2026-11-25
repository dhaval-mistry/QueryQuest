"""Small, offline tests for the HTML formatting upgrade.

Run from the QueryQuest project root after copying the files:
    uv run python -m tests.test_article_html

These tests do NOT call OpenAI or Gmail. They use a sample Pydantic-like
article and inspect the HTML output plus the email's MIME structure.
"""

import unittest
from types import SimpleNamespace

from services.article_renderer import render_article_html, empty_article_html
from services.email_sender import build_email_message


class ArticleHtmlTests(unittest.TestCase):
    def setUp(self):
        # These simple objects expose the same fields as your real Pydantic
        # ResearchArticle model. No API token is required for this test.
        paragraph = SimpleNamespace(
            text="A useful finding with an untrusted <script>alert(1)</script> tag.",
            source_ids=[1, 2],
        )
        section = SimpleNamespace(
            heading="Architecture & reliability",
            paragraphs=[paragraph],
        )
        self.article = SimpleNamespace(
            title="AI research <overview>",
            summary="A concise, useful introduction.",
            sections=[section],
            conclusion="A clear, grounded recommendation.",
        )
        self.sources = [
            {"id": 1, "title": "Official documentation", "url": "https://example.com/docs"},
            {"id": 2, "title": "Malicious source", "url": "javascript:alert(1)"},
        ]

    def test_web_report_is_readable_and_escapes_untrusted_content(self):
        html = render_article_html(self.article, self.sources, 2, 5)
        self.assertIn("EXECUTIVE SUMMARY", html)
        self.assertIn("Architecture &amp; reliability", html)
        self.assertIn("Sources &amp; references", html)
        self.assertIn('href="https://example.com/docs"', html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertNotIn("javascript:alert(1)", html)
        self.assertIn("2 of 5 planned searches", html)

    def test_email_has_html_and_plain_text_alternatives(self):
        html = render_article_html(
            self.article, self.sources, 2, 5, for_email=True
        )
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<table", html)
        message = build_email_message(
            subject="QueryQuest test",
            body="A plain-text fallback with URLs.",
            sender="from@example.com",
            recipient="to@example.com",
            html_body=html,
        )
        self.assertEqual(message.get_content_type(), "multipart/alternative")
        self.assertIn("A plain-text fallback", message.get_body(preferencelist=("plain",)).get_content())
        self.assertIn("EXECUTIVE SUMMARY", message.get_body(preferencelist=("html",)).get_content())

    def test_placeholder(self):
        self.assertIn("Your research report will appear here", empty_article_html())


if __name__ == "__main__":
    unittest.main()
