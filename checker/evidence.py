"""Persist each check attempt as an original frame plus a SQLite record."""

from __future__ import annotations

import json
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "evidence"


class EvidenceLog:
    """Small local evidence store; paths in SQLite are relative to ``root``."""

    def __init__(self, root: str | Path = DEFAULT_ROOT):
        self.root = Path(root).resolve()
        self.frames_dir = self.root / "frames"
        self.db_path = self.root / "evidence.sqlite3"
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    unit_id TEXT NOT NULL,
                    assembly TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    check_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    frame_path TEXT NOT NULL,
                    verdict TEXT CHECK (verdict IN ('yes', 'no', 'cant_tell')),
                    action TEXT NOT NULL
                        CHECK (action IN ('pass', 'fix', 'retake', 'supervisor')),
                    reason TEXT NOT NULL,
                    problem_box TEXT,
                    hint TEXT
                )
                """
            )

    def save(
        self,
        image_path: str | Path,
        *,
        unit_id: str,
        assembly: str,
        verdict: str | None,
        result: dict[str, Any],
    ) -> Path:
        """Save and return the frame path; remove the copy on storage failure.

        A null verdict means the gate blocked the attempt before AI ran.
        """
        source = Path(image_path)
        evidence_id = uuid4().hex
        relative_path = Path("frames") / f"{evidence_id}{source.suffix.lower()}"
        frame_path = self.root / relative_path
        values = (
            evidence_id,
            unit_id,
            assembly,
            result["step_id"],
            result["check_id"],
            datetime.now(timezone.utc).isoformat(),
            relative_path.as_posix(),
            verdict,
            result["action"],
            result["reason"],
            json.dumps(result["problem_box"]) if result.get("problem_box") is not None else None,
            result.get("hint"),
        )
        try:
            shutil.copyfile(source, frame_path)
            with closing(sqlite3.connect(self.db_path)) as connection, connection:
                connection.execute(
                    """
                    INSERT INTO evidence (
                        id, unit_id, assembly, step_id, check_id, timestamp,
                        frame_path, verdict, action, reason, problem_box, hint
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
        except Exception:
            frame_path.unlink(missing_ok=True)
            raise
        return frame_path
