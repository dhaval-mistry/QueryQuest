"""Persistent limits for the public AWS deployment; disabled for local use."""
import hashlib
import hmac
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


class UsageLimitError(ValueError):
    pass


def public_mode():
    return os.getenv("QUERYQUEST_PUBLIC", "false").lower() == "true"


def reserve_research(request=None):
    """Atomically count attempts before any billable calls, including failures.

    The deployed proxy only admits CloudFront requests. CloudFront appends the
    actual viewer address to X-Forwarded-For, so use the rightmost address.
    Store only its keyed hash, never questions, articles, or raw IP addresses.
    """
    if not public_mode():
        return
    directory = Path(os.environ["QUERYQUEST_DATA_DIR"])
    directory.mkdir(parents=True, exist_ok=True)
    headers = getattr(request, "headers", {}) or {}
    address = headers.get("x-forwarded-for", "").split(",")[-1].strip()
    address = address or getattr(getattr(request, "client", None), "host", "unknown")
    secret = os.environ["QUERYQUEST_USAGE_SECRET"]
    visitor = hmac.new(secret.encode(), address.encode(), hashlib.sha256).hexdigest()
    now = datetime.now(timezone.utc)
    day, month = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")
    limits = [
        ("month:" + month, "all", int(os.getenv("QUERYQUEST_MONTHLY_LIMIT", "1000")), "The monthly research allowance has been reached. Please return next month."),
        ("day:" + day, "all", int(os.getenv("QUERYQUEST_DAILY_LIMIT", "50")), "Today's research allowance has been reached. Please return tomorrow."),
        ("day:" + day, visitor, int(os.getenv("QUERYQUEST_VISITOR_DAILY_LIMIT", "3")), "You have reached today's research limit. Please return tomorrow."),
    ]
    with closing(sqlite3.connect(directory / "usage.sqlite3", timeout=15)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS usage (period TEXT, visitor TEXT, count INTEGER NOT NULL, PRIMARY KEY(period, visitor))")
        db.execute("BEGIN IMMEDIATE")
        for period, key, limit, message in limits:
            if limit < 1:
                raise RuntimeError("Public usage limits must be positive")
            row = db.execute("SELECT count FROM usage WHERE period=? AND visitor=?", (period, key)).fetchone()
            if row and row[0] >= limit:
                raise UsageLimitError(message)
        for period, key, _, _ in limits:
            db.execute("INSERT INTO usage VALUES (?, ?, 1) ON CONFLICT(period,visitor) DO UPDATE SET count=count+1", (period, key))
        db.execute("DELETE FROM usage WHERE period NOT IN (?,?)", ("month:" + month, "day:" + day))
