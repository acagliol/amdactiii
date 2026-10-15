"""Tests for Manager Dashboard and Executive Summary Streamlit pages."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from PIL import Image
from streamlit.testing.v1 import AppTest

from checker.evidence import EvidenceLog

ROOT = Path(__file__).resolve().parents[1]
MANAGER_PAGE = ROOT / "app" / "pages" / "2_Manager.py"
EXECUTIVE_PAGE = ROOT / "app" / "pages" / "3_Executive.py"


class DashboardPagesTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.work = Path(self.temp_dir.name)
        self.evidence_dir = self.work / "evidence"
        self.log = EvidenceLog(self.evidence_dir)
        self.frame = self.work / "sample.png"
        Image.new("RGB", (32, 32), "blue").save(self.frame)

    def _seed_evidence(self):
        saved = self.log.save(
            self.frame,
            unit_id="UNIT-TEST-100",
            assembly="PC build",
            verdict="yes",
            result={
                "step_id": "ram",
                "check_id": "ram_clips",
                "action": "pass",
                "reason": "RAM clips engaged.",
                "problem_box": None,
                "hint": "Check clips.",
            },
        )
        saved2 = self.log.save(
            self.frame,
            unit_id="UNIT-TEST-100",
            assembly="PC build",
            verdict="no",
            result={
                "step_id": "gpu",
                "check_id": "gpu_power_seated",
                "action": "fix",
                "reason": "GPU power cable loose.",
                "problem_box": [100, 100, 200, 200],
                "hint": "Push cable firmly.",
            },
        )
        return saved, saved2

    def test_manager_page_loads_with_empty_or_missing_evidence(self):
        empty_dir = self.work / "empty_evidence"
        app = AppTest.from_file(str(MANAGER_PAGE), default_timeout=10)
        app.session_state["evidence_root"] = empty_dir
        app.run()
        self.assertEqual(len(app.exception), 0)

    def test_manager_page_loads_and_displays_metrics_with_seeded_data(self):
        self._seed_evidence()
        app = AppTest.from_file(str(MANAGER_PAGE), default_timeout=10)
        app.session_state["evidence_root"] = self.evidence_dir
        app.run()
        self.assertEqual(len(app.exception), 0)
        # Verify page title rendered
        self.assertTrue(any("Manager Dashboard" in m.value for m in app.title))

    def test_executive_page_loads_with_missing_scorecard(self):
        app = AppTest.from_file(str(EXECUTIVE_PAGE), default_timeout=10)
        app.session_state["evidence_root"] = self.evidence_dir
        app.session_state["scorecard_path"] = self.work / "non_existent_scorecard.json"
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Executive Summary" in m.value for m in app.title))

    def test_executive_page_loads_with_populated_scorecard(self):
        scorecard_file = self.work / "scorecard.json"
        scorecard_file.write_text(
            json.dumps({
                "frames": 50,
                "clean_frames": 20,
                "defect_frames": 30,
                "catch_rate": 0.94,
                "false_alarm_rate": 0.04,
                "mean_latency_s": 0.18,
                "p95_latency_s": 0.42,
                "mean_box_iou": 0.72,
                "grounding_hit_rate": 0.88,
                "by_category": {
                    "bent_wire": {"frames": 10, "caught": 10, "catch_rate": 1.0},
                    "missing_cable": {"frames": 20, "caught": 18, "catch_rate": 0.9},
                },
            })
        )
        self._seed_evidence()
        app = AppTest.from_file(str(EXECUTIVE_PAGE), default_timeout=10)
        app.session_state["evidence_root"] = self.evidence_dir
        app.session_state["scorecard_path"] = scorecard_file
        app.run()
        self.assertEqual(len(app.exception), 0)
        # Verify metric cards exist
        self.assertGreater(len(app.metric), 0)


if __name__ == "__main__":
    unittest.main()
