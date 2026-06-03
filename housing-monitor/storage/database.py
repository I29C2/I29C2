"""SQLite persistence layer with duplicate detection."""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models import Listing

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    name        TEXT PRIMARY KEY,
    last_scan   TEXT,
    last_count  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS listings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint   TEXT UNIQUE NOT NULL,
    source        TEXT NOT NULL,
    listing_url   TEXT NOT NULL,
    listing_id    TEXT,
    title         TEXT,
    address       TEXT,
    rooms         REAL,
    area          REAL,
    rent_cold     REAL,
    extra_costs   REAL,
    rent_warm     REAL,
    available_date TEXT,
    wbs_required  INTEGER DEFAULT 0,
    raw_text      TEXT,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    notified      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS notifications (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id        INTEGER NOT NULL,
    notification_time TEXT NOT NULL,
    status            TEXT NOT NULL,
    FOREIGN KEY(listing_id) REFERENCES listings(id)
);

CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source);
CREATE INDEX IF NOT EXISTS idx_listings_notified ON listings(notified);
"""


class Database:
    def __init__(self, path: str = "database/housing.db"):
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # --- listings ----------------------------------------------------------
    def exists(self, listing: Listing) -> bool:
        """Duplicate detection by fingerprint (url -> id -> title+address)."""
        cur = self.conn.execute(
            "SELECT 1 FROM listings WHERE fingerprint = ?", (listing.fingerprint,)
        )
        return cur.fetchone() is not None

    def upsert(self, listing: Listing) -> tuple[int, bool]:
        """Insert listing or refresh last_seen if it already exists.

        Returns (row_id, is_new).
        """
        now = datetime.now().isoformat(timespec="seconds")
        existing = self.conn.execute(
            "SELECT id FROM listings WHERE fingerprint = ?", (listing.fingerprint,)
        ).fetchone()
        if existing:
            self.conn.execute(
                "UPDATE listings SET last_seen = ? WHERE id = ?", (now, existing["id"])
            )
            self.conn.commit()
            return existing["id"], False

        cur = self.conn.execute(
            """
            INSERT INTO listings (
                fingerprint, source, listing_url, listing_id, title, address,
                rooms, area, rent_cold, extra_costs, rent_warm, available_date,
                wbs_required, raw_text, first_seen, last_seen, notified
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)
            """,
            (
                listing.fingerprint, listing.source, listing.listing_url,
                listing.listing_id, listing.title, listing.address,
                listing.rooms, listing.area, listing.rent_cold,
                listing.extra_costs, listing.rent_warm, listing.available_date,
                int(listing.wbs_required), listing.raw_text, now, now,
            ),
        )
        self.conn.commit()
        return cur.lastrowid, True

    def mark_notified(self, row_id: int, status: str = "sent") -> None:
        now = datetime.now().isoformat(timespec="seconds")
        self.conn.execute("UPDATE listings SET notified = 1 WHERE id = ?", (row_id,))
        self.conn.execute(
            "INSERT INTO notifications (listing_id, notification_time, status) VALUES (?,?,?)",
            (row_id, now, status),
        )
        self.conn.commit()

    def latest(self, limit: int = 5) -> List[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM listings ORDER BY first_seen DESC LIMIT ?", (limit,)
        ).fetchall()

    # --- sources / stats ---------------------------------------------------
    def record_scan(self, source: str, count: int) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        self.conn.execute(
            """
            INSERT INTO sources (name, last_scan, last_count) VALUES (?,?,?)
            ON CONFLICT(name) DO UPDATE SET last_scan=excluded.last_scan,
                                            last_count=excluded.last_count
            """,
            (source, now, count),
        )
        self.conn.commit()

    def stats(self) -> dict:
        total = self.conn.execute("SELECT COUNT(*) c FROM listings").fetchone()["c"]
        notified = self.conn.execute(
            "SELECT COUNT(*) c FROM listings WHERE notified = 1"
        ).fetchone()["c"]
        sent = self.conn.execute(
            "SELECT COUNT(*) c FROM notifications WHERE status = 'sent'"
        ).fetchone()["c"]
        last_scan = self.conn.execute(
            "SELECT MAX(last_scan) m FROM sources"
        ).fetchone()["m"]
        return {
            "total_listings": total,
            "notified_listings": notified,
            "notifications_sent": sent,
            "last_scan": last_scan,
        }
