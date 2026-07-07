from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "alerts.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                message TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        connection.commit()


def insert_alert(alert_type: str, risk_level: str, message: str, risk_score: int, timestamp: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO alerts (alert_type, risk_level, message, risk_score, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (alert_type, risk_level, message, risk_score, timestamp),
        )
        connection.commit()
        return int(cursor.lastrowid)


def fetch_alerts() -> List[Dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, alert_type, risk_level, message, risk_score, timestamp
            FROM alerts
            ORDER BY id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def clear_alerts() -> int:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM alerts")
        connection.commit()
        return int(cursor.rowcount)

