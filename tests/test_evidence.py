"""Evidence storage and checker integration, using real images and temporary SQLite."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

from checker import Session, run_check
from checker.evidence import EvidenceLog
from tests.foundation._images import write_blurry

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLY = ROOT / "assemblies" / "pc_build.yaml"


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.log = EvidenceLog(self.work / "evidence")
        self.env = patch.dict(os.environ, {"USE_FAKE_AI": "true"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def frame(self, name="part_bad_01.png", color="red"):
        path = self.work / name
        image = Image.new("RGB", (256, 256), color=color)
        draw = ImageDraw.Draw(image)
        for y in range(0, 256, 16):
            for x in range(0, 256, 16):
                if (x // 16 + y // 16) % 2:
                    draw.rectangle((x, y, x + 15, y + 15), fill=(220, 220, 220))
        image.save(path)
        return path

    def rows(self):
        with closing(sqlite3.connect(self.log.db_path)) as connection:
            connection.row_factory = sqlite3.Row
            return connection.execute("SELECT * FROM evidence ORDER BY rowid").fetchall()

    def save(self, image_path, *, action="fix", reason="Connector isn't seated."):
        return self.log.save(
            image_path,
            unit_id="UNIT-001",
            assembly="PC build",
            verdict="no",
            result={
                "step_id": "gpu_power",
                "check_id": "gpu_power_seated",
                "action": action,
                "reason": reason,
                "problem_box": [200, 200, 700, 700],
                "hint": "Reseat the connector.",
            },
        )

    def test_original_frame_and_metadata_are_saved(self):
        source = self.frame()
        before = datetime.now(timezone.utc)
        saved = self.save(source)
        after = datetime.now(timezone.utc)
        row, = self.rows()
        self.assertEqual(saved.read_bytes(), source.read_bytes())
        self.assertEqual(saved, self.log.root / row["frame_path"])
        self.assertEqual(saved.stem, row["id"])
        self.assertEqual(row["unit_id"], "UNIT-001")
        self.assertEqual(row["assembly"], "PC build")
        self.assertEqual(row["step_id"], "gpu_power")
        self.assertEqual(row["check_id"], "gpu_power_seated")
        self.assertEqual(row["verdict"], "no")
        self.assertEqual(row["action"], "fix")
        self.assertEqual(row["reason"], "Connector isn't seated.")
        self.assertEqual(json.loads(row["problem_box"]), [200, 200, 700, 700])
        self.assertEqual(row["hint"], "Reseat the connector.")
        timestamp = datetime.fromisoformat(row["timestamp"])
        self.assertEqual(timestamp.utcoffset().total_seconds(), 0)
        self.assertLessEqual(before, timestamp)
        self.assertLessEqual(timestamp, after)

    def test_repeated_filename_keeps_both_original_frames(self):
        source = self.frame(color="red")
        first = self.save(source)
        original = first.read_bytes()
        self.frame(color="blue")
        second = self.save(source)
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), original)
        self.assertEqual(second.read_bytes(), source.read_bytes())
        self.assertNotEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(len(self.rows()), 2)

    def test_data_survives_deleted_upload_and_separate_reader_process(self):
        source = self.frame()
        saved = self.save(source)
        source.unlink()
        reopened = EvidenceLog(self.log.root)
        output = subprocess.check_output(
            [
                sys.executable, "-c",
                "import sqlite3, sys; "
                "db = sqlite3.connect(sys.argv[1]); "
                "print(db.execute('SELECT unit_id FROM evidence').fetchone()[0])",
                str(reopened.db_path),
            ],
            text=True,
        )
        self.assertEqual(output.strip(), "UNIT-001")
        with Image.open(saved) as image:
            self.assertEqual(image.size, (256, 256))

    def test_missing_source_creates_no_record_or_frame(self):
        with self.assertRaises(FileNotFoundError):
            self.save(self.work / "missing.png")
        self.assertEqual(self.rows(), [])
        self.assertEqual(list(self.log.frames_dir.iterdir()), [])

    def test_partial_copy_failure_is_cleaned_up(self):
        def fail_after_partial_copy(source, destination):
            Path(destination).write_bytes(b"partial copy")
            raise OSError("No space left on device")

        with patch("checker.evidence.shutil.copyfile", side_effect=fail_after_partial_copy):
            with self.assertRaisesRegex(OSError, "No space"):
                self.save(self.frame())
        self.assertEqual(self.rows(), [])
        self.assertEqual(list(self.log.frames_dir.iterdir()), [])

    def test_rejected_database_insert_removes_copied_frame(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.save(self.frame(), action="invalid")
        self.assertEqual(self.rows(), [])
        self.assertEqual(list(self.log.frames_dir.iterdir()), [])

    def test_full_walkthrough_records_verdicts_and_actions(self):
        session = Session(ASSEMBLY, evidence_log=self.log)
        attempts = [
            ("ram_ok_01.png", "yes", "pass"),
            ("gpu_bad_01.png", "no", "fix"),
            ("gpu_blur_01.png", "cant_tell", "retake"),
            ("gpu_blur_02.png", "cant_tell", "retake"),
            ("gpu_blur_03.png", "cant_tell", "supervisor"),
            ("gpu_ok_01.png", "yes", "pass"),
        ]
        for filename, verdict, action in attempts:
            with self.subTest(action=action, filename=filename):
                result = run_check(session, self.frame(filename))
                self.assertEqual(result["action"], action)
                self.assertEqual(
                    set(result), {"action", "reason", "problem_box", "hint", "step_id", "check_id"}
                )
        rows = self.rows()
        self.assertEqual([row["verdict"] for row in rows], [v for _, v, _ in attempts])
        self.assertEqual([row["action"] for row in rows], [a for _, _, a in attempts])
        self.assertEqual({row["unit_id"] for row in rows}, {session.unit_id})
        self.assertIsNone(rows[0]["problem_box"])
        self.assertIsNone(rows[0]["hint"])
        self.assertEqual(session.current()["check_id"], "cooler_film_removed")
        self.assertEqual(session.retake_streak, 0)
        self.assertTrue(session.last_evidence_path.exists())
        self.assertEqual(len(list(self.log.frames_dir.iterdir())), len(attempts))

    def test_new_units_have_distinct_ids_and_can_use_a_serial_number(self):
        first = Session(ASSEMBLY, evidence_log=self.log)
        second = Session(ASSEMBLY, evidence_log=self.log)
        serial = Session(ASSEMBLY, unit_id="SERIAL-123", evidence_log=self.log)
        self.assertNotEqual(first.unit_id, second.unit_id)
        for session in (first, second, serial):
            run_check(session, self.frame("ram_ok_01.png"))
        self.assertEqual(
            [row["unit_id"] for row in self.rows()],
            [first.unit_id, second.unit_id, "SERIAL-123"],
        )

    def test_blocked_gate_is_logged_without_an_ai_verdict(self):
        session = Session(ASSEMBLY, evidence_log=self.log)
        check = dict(session.current(), requires=["other_check"])
        with patch("checker.engine.ai_look") as ai:
            result = run_check(session, self.frame(), check=check)
        ai.assert_not_called()
        row, = self.rows()
        self.assertEqual(result["action"], "retake")
        self.assertIsNone(row["verdict"])
        self.assertEqual(row["action"], "retake")
        self.assertIn("other_check", row["reason"])
        self.assertEqual(session.index, 0)
        self.assertEqual(session.retake_streak, 0)

    def test_storage_failure_leaves_pass_and_retake_state_unchanged(self):
        session = Session(ASSEMBLY, evidence_log=self.log)
        run_check(session, self.frame("ram_blur_01.png"))
        previous_frame = session.last_evidence_path
        with closing(sqlite3.connect(self.log.db_path)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER reject_evidence BEFORE INSERT ON evidence "
                "BEGIN SELECT RAISE(ABORT, 'simulated write failure'); END"
            )
        for name in ("ram_ok_01.png", "ram_bad_01.png", "ram_blur_02.png"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(sqlite3.IntegrityError, "write failure"):
                    run_check(session, self.frame(name))
                self.assertEqual(session.passed, set())
                self.assertEqual(session.index, 0)
                self.assertEqual(session.retake_streak, 1)
                self.assertEqual(session.last_evidence_path, previous_frame)
                self.assertEqual(len(self.rows()), 1)
                self.assertEqual(list(self.log.frames_dir.iterdir()), [previous_frame])
        with closing(sqlite3.connect(self.log.db_path)) as connection, connection:
            connection.execute("DROP TRIGGER reject_evidence")
        self.assertEqual(run_check(session, self.frame("ram_ok_01.png"))["action"], "pass")
        self.assertEqual(session.index, 1)
        self.assertEqual(len(self.rows()), 2)

    def test_quality_retakes_are_logged_before_state_changes(self):
        session = Session(ASSEMBLY, evidence_log=self.log)
        blurry = write_blurry("quality_blur.jpg", self.work)
        with patch("checker.engine.ai_look") as ai:
            for expected in ("retake", "retake", "supervisor"):
                result = run_check(session, blurry)
                self.assertEqual(result["action"], expected)
        ai.assert_not_called()
        self.assertEqual(session.retake_streak, 3)
        self.assertEqual([row["action"] for row in self.rows()], ["retake", "retake", "supervisor"])
        self.assertTrue(all(row["verdict"] is None for row in self.rows()))
        self.assertTrue(all(row["hint"] for row in self.rows()))
        previous_frame = session.last_evidence_path
        with patch.object(self.log, "save", side_effect=OSError("Disk full")):
            with self.assertRaises(OSError):
                run_check(session, blurry)
        self.assertEqual(session.retake_streak, 3)
        self.assertEqual(session.last_evidence_path, previous_frame)
        self.assertEqual(len(self.rows()), 3)

    def test_completed_session_does_not_add_another_evidence_record(self):
        session = Session(ASSEMBLY, evidence_log=self.log)
        frame = self.frame("part_ok_01.png")
        for _ in session.checks:
            if session.current()["kind"] == "manual":
                result = session.confirm_manual(True, image_path=frame)
            else:
                result = run_check(session, frame)
            self.assertEqual(result["action"], "pass")
        self.assertIsNone(session.current())
        self.assertEqual(run_check(session, self.work / "no_new_upload.png")["action"], "pass")
        self.assertEqual(len(self.rows()), len(session.checks))


if __name__ == "__main__":
    unittest.main()
