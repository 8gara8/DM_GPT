from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable


SCHEMA = """
CREATE TABLE IF NOT EXISTS watchlist (
    ticker TEXT PRIMARY KEY,
    tag TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signal_states (
    ticker TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    indicator_type TEXT NOT NULL,
    direction TEXT,
    phase TEXT NOT NULL,
    current_count INTEGER NOT NULL,
    count_started_date TEXT,
    setup_completed_date TEXT,
    tdst_level REAL,
    is_perfected INTEGER NOT NULL,
    countdown_bar_8_close REAL,
    composite_pattern TEXT,
    status TEXT,
    last_updated TEXT NOT NULL,
    PRIMARY KEY (ticker, timeframe, indicator_type)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    message TEXT NOT NULL,
    dedupe_key TEXT NOT NULL UNIQUE,
    triggered_at TEXT NOT NULL,
    sent INTEGER NOT NULL DEFAULT 0
);
"""


class Database:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def add_tickers(self, tickers: Iterable[str], tag: str | None = None) -> None:
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO watchlist(ticker, tag, created_at) VALUES(?,?,?)",
                [(t.upper(), tag, now) for t in tickers],
            )

    def remove_ticker(self, ticker: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))

    def list_tickers(self, tag: str | None = None):
        with self.connect() as conn:
            if tag:
                return conn.execute(
                    "SELECT ticker, tag, created_at FROM watchlist WHERE tag = ? ORDER BY ticker",
                    (tag,),
                ).fetchall()
            return conn.execute(
                "SELECT ticker, tag, created_at FROM watchlist ORDER BY ticker"
            ).fetchall()

    def upsert_signal_state(self, row: dict) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO signal_states(
                    ticker,timeframe,indicator_type,direction,phase,current_count,
                    count_started_date,setup_completed_date,tdst_level,is_perfected,
                    countdown_bar_8_close,composite_pattern,status,last_updated
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(ticker,timeframe,indicator_type) DO UPDATE SET
                    direction=excluded.direction,
                    phase=excluded.phase,
                    current_count=excluded.current_count,
                    count_started_date=excluded.count_started_date,
                    setup_completed_date=excluded.setup_completed_date,
                    tdst_level=excluded.tdst_level,
                    is_perfected=excluded.is_perfected,
                    countdown_bar_8_close=excluded.countdown_bar_8_close,
                    composite_pattern=excluded.composite_pattern,
                    status=excluded.status,
                    last_updated=excluded.last_updated
                """,
                (
                    row["ticker"],
                    row["timeframe"],
                    row["indicator_type"],
                    row["direction"],
                    row["phase"],
                    row["current_count"],
                    row.get("count_started_date"),
                    row.get("setup_completed_date"),
                    row.get("tdst_level"),
                    int(bool(row.get("is_perfected"))),
                    row.get("countdown_bar_8_close"),
                    row.get("composite_pattern"),
                    row.get("status"),
                    row["last_updated"],
                ),
            )

    def insert_alert(self, row: dict) -> bool:
        with self.connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO alerts(ticker,timeframe,alert_type,priority,message,dedupe_key,triggered_at,sent)
                    VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        row["ticker"],
                        row["timeframe"],
                        row["alert_type"],
                        row["priority"],
                        row["message"],
                        row["dedupe_key"],
                        row["triggered_at"],
                        int(bool(row.get("sent", False))),
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def list_signal_states(self):
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM signal_states ORDER BY ticker, timeframe"
            ).fetchall()

    def export_watchlist(self):
        return [dict(r) for r in self.list_tickers()]
