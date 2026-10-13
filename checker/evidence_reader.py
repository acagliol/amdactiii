"""Read-only evidence queries shared by Worker, manager, and CEO pages."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evidence import DEFAULT_ROOT

ACTIONS = ("pass", "fix", "retake", "supervisor")
VERDICTS = ("yes", "no", "cant_tell", "no_verdict")


def _where(
    unit_id: str | None, assembly: str | None, action: str | None,
    start: datetime | None, end: datetime | None,
) -> tuple[str, list[Any]]:
    clauses, params = [], []
    if action is not None and action not in ACTIONS:
        raise ValueError("Unknown evidence action.")
    for column, value in (("unit_id", unit_id), ("assembly", assembly), ("action", action)):
        if value is not None:
            clauses.append(f"{column} = ?")
            params.append(value)
    for bound in (start, end):
        if bound is not None and (bound.tzinfo is None or bound.utcoffset() is None):
            raise ValueError("Date filters must include a timezone.")
    if start is not None and end is not None and start >= end:
        raise ValueError("End must be later than start.")
    for operator, bound in ((">=", start), ("<", end)):
        if bound is not None:
            clauses.append(f"timestamp {operator} ?")
            params.append(bound.astimezone(timezone.utc).isoformat())
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), params


class EvidenceReader:
    """Read the existing store without creating folders, tables, or records."""

    def __init__(self, root: str | Path = DEFAULT_ROOT):
        self.root = Path(root).resolve()
        self.db_path = self.root / "evidence.sqlite3"

    def _query(self, sql: str, params: list[Any]) -> list[sqlite3.Row]:
        if not self.db_path.is_file():
            return []
        with closing(sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            return connection.execute(sql, params).fetchall()

    def _photo_path(self, relative: str) -> Path | None:
        try:
            if Path(relative).is_absolute():
                return None
            path = (self.root / relative).resolve()
            if path.is_relative_to(self.root / "frames") and path.is_file():
                return path
        except (OSError, ValueError):
            pass
        return None

    def recent(
        self, *, unit_id: str | None = None, assembly: str | None = None,
        action: str | None = None, start: datetime | None = None, end: datetime | None = None,
        limit: int = 100, offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return newest attempts; dates use an inclusive start and exclusive end."""
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("Limit must be an integer from 1 to 500.")
        if type(offset) is not int or offset < 0:
            raise ValueError("Offset must be a nonnegative integer.")
        where, params = _where(unit_id, assembly, action, start, end)
        rows = self._query(
            "SELECT * FROM evidence" + where + " ORDER BY timestamp DESC, rowid DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        results = []
        for row in rows:
            item = dict(row)
            item["problem_box"] = json.loads(item["problem_box"]) if item["problem_box"] is not None else None
            item["photo_path"] = self._photo_path(item["frame_path"])
            results.append(item)
        return results

    def summary(
        self, *, unit_id: str | None = None, assembly: str | None = None,
        action: str | None = None, start: datetime | None = None, end: datetime | None = None,
    ) -> dict[str, Any]:
        """Count all matching attempts and units seen, regardless of list pagination."""
        where, params = _where(unit_id, assembly, action, start, end)
        rows = self._query(
            """SELECT COUNT(*) AS attempts, COUNT(DISTINCT unit_id) AS units_seen,
                SUM(action = 'pass') AS action_pass, SUM(action = 'fix') AS action_fix,
                SUM(action = 'retake') AS action_retake, SUM(action = 'supervisor') AS action_supervisor,
                SUM(verdict = 'yes') AS verdict_yes, SUM(verdict = 'no') AS verdict_no,
                SUM(verdict = 'cant_tell') AS verdict_cant_tell,
                SUM(verdict IS NULL) AS verdict_no_verdict,
                MIN(timestamp) AS first_timestamp, MAX(timestamp) AS last_timestamp
                FROM evidence""" + where,
            params,
        )
        row = dict(rows[0]) if rows else {}
        return {
            "attempts": row.get("attempts", 0),
            "units_seen": row.get("units_seen", 0),
            "actions": {key: row.get("action_" + key) or 0 for key in ACTIONS},
            "verdicts": {key: row.get("verdict_" + key) or 0 for key in VERDICTS},
            "first_timestamp": row.get("first_timestamp"),
            "last_timestamp": row.get("last_timestamp"),
        }
