"""Offline checks for streamed UI states; no model or search requests."""
import os
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import app
from services.research_progress import ResearchUpdate, progress_html


def sample_result():
    article = SimpleNamespace(title="A report", summary="Summary", conclusion="Conclusion", sections=[
        SimpleNamespace(heading="Evidence", paragraphs=[SimpleNamespace(text="Finding", source_ids=[1])])
    ])
    return article, [{"id": 1, "title": "Source", "url": "https://example.com/"}], 2, 5


class ProgressUiTests(unittest.TestCase):
    def test_ui_streams_stages_then_enables_only_valid_report_delivery(self):
        def steps(question):
            for stage in ("planner", "search", "writer"):
                yield ResearchUpdate(stage, stage + " is running")
            yield ResearchUpdate("complete", "Your report is ready", sample_result())
        with patch("app.research_steps", side_effect=steps):
            outputs = list(app.research("Question"))
        self.assertFalse(outputs[0][3]["interactive"])
        for output, name in zip(outputs[1:4], ("Planner", "Search", "Writer")):
            self.assertIn(name + "</strong><small>Running", output[2])
        self.assertIn("A report", outputs[-1][0])
        self.assertEqual(outputs[-1][1]["title"], "A report")
        self.assertTrue(outputs[-1][3]["interactive"])
        self.assertTrue(outputs[-1][5]["interactive"])
        self.assertNotIn("qq-active", outputs[-1][2])

    def test_failure_stops_animation_and_leaves_retry_available(self):
        def steps(question):
            yield ResearchUpdate("writer", "Writing")
            raise RuntimeError("private provider diagnostic")
        with patch("app.research_steps", side_effect=steps), self.assertLogs("app", level="ERROR"):
            outputs = list(app.research("Question"))
        self.assertIn("qq-failed", outputs[-1][2])
        self.assertIn("during writing", outputs[-1][2])
        self.assertNotIn("private provider diagnostic", outputs[-1][2])
        self.assertNotIn("qq-active", outputs[-1][2])
        self.assertEqual(outputs[-1][1], {})
        self.assertTrue(outputs[-1][3]["interactive"])
        self.assertFalse(outputs[-1][5]["interactive"])

    def test_progress_escapes_search_text_and_reset_clears_delivery(self):
        html = progress_html("search", "<script>alert(1)</script>")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        reset = app.clear_chat()
        self.assertEqual(reset[2], {})
        self.assertFalse(reset[-1]["interactive"])
        self.assertNotIn("qq-active", reset[3])

    def test_app_builds_with_streaming_handler(self):
        demo = app.build_app()
        self.assertTrue(any(fn.fn is app.research for fn in demo.fns.values()))


if __name__ == "__main__":
    unittest.main()
