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

from PIL import Image
from streamlit.testing.v1 import AppTest

from checker.evidence import EvidenceLog

APP = Path(__file__).resolve().parents[1] / "app" / "main.py"


class WorkerEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.log = EvidenceLog(Path(temp.name) / "evidence")
        self.upload = io.BytesIO()
        Image.new("RGB", (24, 24), color="red").save(self.upload, format="PNG")
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
