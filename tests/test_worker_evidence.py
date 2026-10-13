"""Exercise Streamlit reruns and evidence failures without a browser or GPU."""

from __future__ import annotations

import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw
from streamlit.testing.v1 import AppTest

from checker.evidence import EvidenceLog

APP = Path(__file__).resolve().parents[1] / "app" / "main.py"


class WorkerEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.log = EvidenceLog(Path(temp.name) / "evidence")
        self.upload = io.BytesIO()
        image = Image.new("RGB", (256, 256), color="red")
        draw = ImageDraw.Draw(image)
        for y in range(0, 256, 16):
            for x in range(0, 256, 16):
                if (x // 16 + y // 16) % 2:
                    draw.rectangle((x, y, x + 15, y + 15), fill=(220, 220, 220))
        image.save(self.upload, format="PNG")
        self.upload.name = "part_ok_01.png"
        for context in (
            patch.dict(os.environ, {"USE_FAKE_AI": "true"}),
            patch("checker.engine.EvidenceLog", return_value=self.log),
            patch("streamlit.file_uploader", return_value=self.upload),
        ):
            context.start()
            self.addCleanup(context.stop)
        self.app = AppTest.from_file(str(APP), default_timeout=10).run()
        self.assertEqual(len(self.app.exception), 0)

    def count(self):
        with closing(sqlite3.connect(self.log.db_path)) as connection:
            return connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]

    def test_pass_rerun_completion_and_new_unit(self):
        # Keep this persistence test on its original two visual checks.
        self.app.session_state["session"].checks = self.app.session_state["session"].checks[:2]
        original_unit = self.app.session_state["session"].unit_id
        self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.session_state["session"].index, 1)
        self.assertEqual(self.count(), 1)
        self.app.run()  # A normal rerender must neither loop nor log another attempt.
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.count(), 1)
        self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertIn("All checks complete", self.app.success[0].value)
        self.assertEqual(self.count(), 2)
        self.assertEqual(self.app.button[0].label, "Start new unit")
        self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertNotEqual(self.app.session_state["session"].unit_id, original_unit)
        self.assertEqual(self.app.session_state["session"].index, 0)
        self.assertNotIn("last_result", self.app.session_state)
        self.assertNotIn("last_image", self.app.session_state)
        self.assertEqual(self.app.text_input[0].value, self.app.session_state["session"].unit_id)
        self.assertFalse(self.app.text_input[0].disabled)
        self.assertEqual(self.count(), 2)

    def test_fix_keeps_permanent_image_after_temporary_upload_is_deleted(self):
        self.upload.name = "part_bad_01.png"
        self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.session_state["last_result"]["action"], "fix")
        saved = self.app.session_state["last_image"]
        self.assertEqual(saved.parent, self.log.frames_dir)
        self.assertEqual(saved.read_bytes(), self.upload.getvalue())
        self.app.run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertTrue(saved.exists())
        self.assertEqual(self.count(), 1)

    def test_serial_is_saved_and_locked_after_first_attempt(self):
        self.app.text_input[0].set_value("SERIAL-123").run()
        self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertTrue(self.app.text_input[0].disabled)
        with closing(sqlite3.connect(self.log.db_path)) as connection:
            serial, = connection.execute("SELECT unit_id FROM evidence").fetchone()
        self.assertEqual(serial, "SERIAL-123")

    def test_recent_evidence_uses_the_worker_store_and_current_unit(self):
        self.app.text_input[0].set_value("SERIAL-READ").run()
        self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        cards = [item.value for item in self.app.markdown if "**pass**" in item.value]
        self.assertEqual(len(cards), 1)
        self.assertIn("SERIAL-READ", cards[0])
        self.assertIn("ram_clips", cards[0])
        self.app.run()
        self.assertEqual(self.count(), 1)
        self.assertEqual(len([item for item in self.app.markdown if "**pass**" in item.value]), 1)

    def test_camera_photo_uses_the_same_evidence_store(self):
        with patch("streamlit.file_uploader", return_value=None):
            with patch("streamlit.camera_input", return_value=self.upload):
                self.app.run()
                self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.session_state["session"].index, 1)
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.app.session_state["last_image"].read_bytes(), self.upload.getvalue())

    def test_override_still_requires_a_reason_and_advances(self):
        self.app.button[1].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.session_state["session"].index, 0)
        self.assertEqual(self.app.session_state["last_result"]["action"], "retake")
        self.app.text_area[0].set_value("Verified by hand; clips fully seated.").run()
        self.app.button[1].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.session_state["session"].index, 1)
        self.assertEqual(len(self.app.session_state["session"].overrides), 1)
        self.assertEqual(self.count(), 0)

    def test_storage_failure_shows_error_and_does_not_unlock_step(self):
        with patch.object(self.log, "save", side_effect=OSError("Disk full")):
            self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertIn("Could not save this check", self.app.error[0].value)
        self.assertEqual(self.app.session_state["session"].index, 0)
        self.assertEqual(self.app.session_state["session"].passed, set())
        self.assertEqual(self.count(), 0)
        self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.session_state["session"].index, 1)
        self.assertEqual(self.count(), 1)


if __name__ == "__main__":
    unittest.main()
