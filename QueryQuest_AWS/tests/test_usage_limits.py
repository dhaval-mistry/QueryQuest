"""Public quotas must persist and reject requests before spending tokens."""
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch

from services.usage_limits import reserve_research, UsageLimitError


def request(ip="203.0.113.10"):
    return SimpleNamespace(headers={"x-forwarded-for": "forged-address, " + ip})


class UsageLimitTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        env = patch.dict(os.environ, {
            "QUERYQUEST_PUBLIC": "true", "QUERYQUEST_DATA_DIR": self.directory.name,
            "QUERYQUEST_USAGE_SECRET": "test-only-secret", "QUERYQUEST_MONTHLY_LIMIT": "5",
            "QUERYQUEST_DAILY_LIMIT": "5", "QUERYQUEST_VISITOR_DAILY_LIMIT": "2",
        })
        env.start()
        self.addCleanup(env.stop)

    def test_visitor_limit_persists_and_does_not_store_ip(self):
        reserve_research(request())
        reserve_research(request())
        with self.assertRaisesRegex(UsageLimitError, "today's research limit"):
            reserve_research(request())
        from pathlib import Path
        with closing(sqlite3.connect(Path(self.directory.name) / "usage.sqlite3")) as db:
            rows = db.execute("SELECT visitor,count FROM usage").fetchall()
        self.assertNotIn("203.0.113.10", str(rows))
        self.assertTrue(all(count == 2 for _, count in rows))

    def test_global_limit_is_atomic_across_visitors(self):
        def run(index):
            try:
                reserve_research(request(f"203.0.113.{index}"))
                return True
            except UsageLimitError:
                return False
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(run, range(12)))
        self.assertEqual(sum(results), 5)

    def test_local_mode_does_not_need_persistent_storage(self):
        with patch.dict(os.environ, {"QUERYQUEST_PUBLIC": "false"}):
            reserve_research()
