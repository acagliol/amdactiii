"""Dashboard queries against real SQLite records and saved image files."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from streamlit.testing.v1 import AppTest

from checker import Session, run_check
from checker.evidence import EvidenceLog
from checker.evidence_reader import EvidenceReader
from tests.foundation._images import write_sharp

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


class EvidenceReaderTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.log = EvidenceLog(self.work / "store #? ü")
        self.reader = EvidenceReader(self.log.root)
        self.frame = self.work / "capture.png"
        Image.new("RGB", (24, 24), "red").save(self.frame)

    def add(self, unit="UNIT-001", assembly="PC build", action="pass", verdict="yes",
            timestamp="2026-10-13T00:00:00+00:00", box=None):
        saved = self.log.save(
            self.frame, unit_id=unit, assembly=assembly, verdict=verdict,
            result={"step_id": "ram", "check_id": "ram_clips", "action": action,
                    "reason": "Inspection detail.", "problem_box": box, "hint": "Inspect the clips."},
        )
        with closing(sqlite3.connect(self.log.db_path)) as connection, connection:
            connection.execute("UPDATE evidence SET timestamp = ? WHERE id = ?", (timestamp, saved.stem))
        return saved

    def seed(self):
        self.add()
        self.add(action="fix", verdict="no", timestamp="2026-10-13T10:00:00+00:00", box=[10, 20, 800, 900])
        self.add(unit="UNIT-002", action="retake", verdict=None, timestamp="2026-10-13T11:00:00+00:00")
        self.add(unit="UNIT-002", action="retake", verdict="cant_tell", timestamp="2026-10-13T12:00:00+00:00")
        self.add(unit="UNIT-002", action="supervisor", verdict="cant_tell", timestamp="2026-10-13T13:00:00+00:00")
        self.add(assembly="MVTec bottle", action="fix", verdict="no", timestamp="2026-10-14T00:00:00+00:00")
        self.add(unit="UNIT-003", verdict=None, timestamp="2026-10-14T12:00:00+00:00")

    def test_missing_database_returns_empty_without_creating_files(self):
        reader = EvidenceReader(self.work / "missing")
        self.assertEqual(reader.recent(), [])
        summary = reader.summary()
        self.assertEqual(summary["attempts"], 0)
        self.assertEqual(summary["units_seen"], 0)
        self.assertEqual(summary["actions"], dict.fromkeys(("pass", "fix", "retake", "supervisor"), 0))
        self.assertEqual(summary["verdicts"], dict.fromkeys(("yes", "no", "cant_tell", "no_verdict"), 0))
        self.assertIsNone(summary["first_timestamp"])
        self.assertIsNone(summary["last_timestamp"])
        self.assertFalse(reader.root.exists())
        self.assertEqual(self.reader.summary(), summary)
        self.assertEqual(self.reader.recent(), [])

    def test_rows_include_details_decoded_boxes_and_saved_photos(self):
        saved = self.add(action="fix", verdict="no", box=[10, 20, 800, 900])
        row, = self.reader.recent()
        self.assertEqual(row["id"], saved.stem)
        self.assertEqual(row["unit_id"], "UNIT-001")
        self.assertEqual(row["assembly"], "PC build")
        self.assertEqual(row["check_id"], "ram_clips")
        self.assertEqual(row["action"], "fix")
        self.assertEqual(row["verdict"], "no")
        self.assertEqual(row["reason"], "Inspection detail.")
        self.assertEqual(row["hint"], "Inspect the clips.")
        self.assertEqual(row["problem_box"], [10, 20, 800, 900])
        self.assertEqual(row["photo_path"], saved)
        self.assertEqual((self.log.root / row["frame_path"]).read_bytes(), self.frame.read_bytes())
        self.assertEqual(row["timestamp"], "2026-10-13T00:00:00+00:00")

    def test_filters_are_shared_by_rows_and_summary(self):
        self.seed()
        cases = [({"unit_id": "UNIT-001"}, 3), ({"assembly": "PC build"}, 6),
                 ({"action": "retake"}, 2), ({"unit_id": "UNIT-001", "assembly": "PC build", "action": "fix"}, 1),
                 ({"unit_id": "missing"}, 0)]
        for filters, count in cases:
            with self.subTest(filters=filters):
                self.assertEqual(len(self.reader.recent(**filters)), count)
                self.assertEqual(self.reader.summary(**filters)["attempts"], count)

    def test_summary_counts_all_matches_and_distinguishes_missing_verdicts(self):
        self.seed()
        self.assertEqual(len(self.reader.recent(limit=1)), 1)
        self.assertEqual(self.reader.summary(), {
            "attempts": 7, "units_seen": 3,
            "actions": {"pass": 2, "fix": 2, "retake": 2, "supervisor": 1},
            "verdicts": {"yes": 1, "no": 2, "cant_tell": 2, "no_verdict": 2},
            "first_timestamp": "2026-10-13T00:00:00+00:00",
            "last_timestamp": "2026-10-14T12:00:00+00:00",
        })

    def test_dates_include_start_exclude_end_and_normalize_timezones(self):
        self.seed()
        start = datetime(2026, 10, 13, tzinfo=UTC)
        end = start + timedelta(days=1)
        local = timezone(timedelta(hours=2))
        for filters in ({"start": start, "end": end},
                        {"start": start.astimezone(local), "end": end.astimezone(local)}):
            rows = self.reader.recent(**filters)
            self.assertEqual(len(rows), 5)
            self.assertEqual(self.reader.summary(**filters)["attempts"], 5)
            self.assertIn("2026-10-13T00:00:00+00:00", [row["timestamp"] for row in rows])
            self.assertNotIn("2026-10-14T00:00:00+00:00", [row["timestamp"] for row in rows])
        self.assertEqual(self.reader.summary(end=end)["attempts"], 5)
        self.assertEqual(self.reader.summary(start=end)["attempts"], 2)

    def test_invalid_filters_and_pagination_are_rejected(self):
        start = datetime(2026, 10, 13, tzinfo=UTC)
        for filters in ({"start": start.replace(tzinfo=None)}, {"end": start.replace(tzinfo=None)},
                        {"start": start, "end": start}, {"start": start, "end": start - timedelta(days=1)},
                        {"action": "unknown"}):
            with self.subTest(filters=filters):
                for query in (self.reader.recent, self.reader.summary):
                    with self.assertRaises(ValueError):
                        query(**filters)
        for filters in ({"limit": 0}, {"limit": -1}, {"limit": 501}, {"limit": True},
                        {"limit": 1.5}, {"offset": -1}, {"offset": True}):
            with self.subTest(filters=filters), self.assertRaises(ValueError):
                self.reader.recent(**filters)

    def test_filter_values_are_literal_sql_parameters(self):
        unit = "x' OR 1=1 --"
        assembly = "Manager's demo"
        self.add()
        self.add(unit=unit, assembly=assembly)
        self.assertEqual(len(self.reader.recent(unit_id=unit, assembly=assembly)), 1)
        self.assertEqual(self.reader.summary(unit_id=unit)["units_seen"], 1)
        self.assertEqual(self.reader.summary(unit_id="' OR 1=1 --")["attempts"], 0)

    def test_timestamp_order_pagination_and_ties(self):
        newest = self.add(timestamp="2026-10-14T00:00:00+00:00")
        oldest = self.add(timestamp="2026-10-12T00:00:00+00:00")
        tied = self.add(timestamp="2026-10-14T00:00:00+00:00")
        self.assertEqual([row["id"] for row in self.reader.recent()], [tied.stem, newest.stem, oldest.stem])
        self.assertEqual([row["id"] for row in self.reader.recent(limit=1, offset=1)], [newest.stem])
        self.assertEqual(self.reader.recent(offset=3), [])

    def test_reads_are_fresh_after_another_connection_writes(self):
        self.assertEqual(self.reader.summary()["attempts"], 0)
        saved = self.add()
        self.assertEqual(self.reader.summary()["attempts"], 1)
        self.assertEqual(self.reader.recent()[0]["id"], saved.stem)
        self.add(action="fix", verdict="no")
        self.assertEqual(self.reader.summary()["actions"]["fix"], 1)
        self.assertEqual(len(self.reader.recent()), 2)

    def test_missing_photo_preserves_record_and_summary(self):
        saved = self.add()
        saved.unlink()
        row, = self.reader.recent()
        self.assertIsNone(row["photo_path"])
        self.assertEqual(row["id"], saved.stem)
        self.assertEqual(self.reader.summary()["attempts"], 1)

    def test_photo_paths_cannot_escape_frames_directory(self):
        saved = self.add()
        link = self.log.frames_dir / "outside.png"
        link.symlink_to(self.frame)
        for value in (str(self.frame), "../../capture.png", "../capture.png", "frames/outside.png"):
            with self.subTest(value=value):
                with closing(sqlite3.connect(self.log.db_path)) as connection, connection:
                    connection.execute("UPDATE evidence SET frame_path = ?", (value,))
                self.assertIsNone(self.reader.recent()[0]["photo_path"])
        self.assertTrue(saved.is_file())

    def test_photo_paths_are_independent_of_working_directory(self):
        saved = self.add()
        original = Path.cwd()
        try:
            os.chdir(self.work)
            self.assertEqual(self.reader.recent()[0]["photo_path"], saved)
        finally:
            os.chdir(original)

    def test_connections_are_read_only_and_do_not_change_the_store(self):
        self.add()
        before = self.log.db_path.read_bytes()
        self.reader.recent()
        self.reader.summary()
        with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
            self.reader._query("DELETE FROM evidence", [])
        self.assertEqual(self.log.db_path.read_bytes(), before)
        self.assertEqual(self.reader.summary()["attempts"], 1)

    def test_corrupt_database_errors_are_not_reported_as_empty_data(self):
        self.log.db_path.write_bytes(b"not a sqlite database")
        for query in (self.reader.recent, self.reader.summary):
            with self.assertRaises(sqlite3.DatabaseError):
                query()

    def test_checker_attempt_is_immediately_available_to_dashboard(self):
        session = Session(ROOT / "assemblies" / "pc_build.yaml", unit_id="LIVE-001", evidence_log=self.log)
        frame = write_sharp("ram_bad_01.jpg", self.work)
        with patch.dict(os.environ, {"USE_FAKE_AI": "true"}):
            result = run_check(session, frame)
        row, = self.reader.recent(unit_id="LIVE-001")
        self.assertEqual(row["action"], result["action"])
        self.assertEqual(row["reason"], result["reason"])
        self.assertEqual(row["problem_box"], result["problem_box"])
        self.assertEqual(row["photo_path"], session.last_evidence_path)
        self.assertEqual(self.reader.summary(unit_id="LIVE-001")["actions"]["fix"], 1)

    def panel(self, root=None):
        script = (
            "from app.evidence_panel import render_recent_evidence\n"
            f"render_recent_evidence('UNIT-001', root={str(root or self.log.root)!r})\n"
        )
        return AppTest.from_string(script).run()

    def test_panel_handles_missing_empty_and_corrupt_database(self):
        for root, expected in ((self.work / "absent", "No evidence database"),
                               (self.log.root, "No rows for this unit")):
            app = self.panel(root)
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any(expected in item.value for item in app.caption))
        self.log.db_path.write_bytes(b"not sqlite")
        app = self.panel()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Could not read evidence DB" in item.value for item in app.caption))

    def test_panel_filters_units_and_refreshes_new_attempts(self):
        self.add(unit="OTHER-UNIT")
        self.add(action="fix", verdict="no")
        app = self.panel()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.markdown), 1)
        self.assertIn("UNIT-001", app.markdown[0].value)
        self.assertNotIn("OTHER-UNIT", app.markdown[0].value)
        self.assertTrue(any("Inspection detail." == item.value for item in app.caption))
        self.add()
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.markdown), 2)

    def test_panel_handles_a_missing_photo(self):
        self.add().unlink()
        app = self.panel()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.markdown), 1)
        self.assertTrue(any(item.value == "Photo unavailable." for item in app.caption))


if __name__ == "__main__":
    unittest.main()
