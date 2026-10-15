"""Tests for upgraded backend features: quality glare/contrast, agreement IoU, manual/gate engine & UI, reader analytics, and linter."""

import base64
import io
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw
from streamlit.testing.v1 import AppTest

from ai_client.agreement import box_iou, reconcile
from ai_client.vllm import MAX_SIDE_PX, _image_url
from checker import Session, run_check
from checker.evidence import EvidenceLog
from checker.evidence_reader import EvidenceReader
from checker.lint import lint_data
from checker.loader import iter_checks
from checker.quality import assess_quality

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLY = ROOT / "assemblies" / "pc_build.yaml"
APP = ROOT / "app" / "pages" / "1_Worker.py"
UTC = timezone.utc


def _sharp(size: tuple[int, int]) -> Image.Image:
    rng = np.random.default_rng(0)
    return Image.fromarray(rng.integers(40, 220, (size[1], size[0], 3), dtype=np.uint8))


class BackendPolishTests(unittest.TestCase):
    def test_quality_reads_non_ascii_path_and_returns_rich_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "檢查_frame.png"
            _sharp((400, 300)).save(path)
            res = assess_quality(path)
            self.assertTrue(res["ok"])
            self.assertIn("contrast_std", res["metrics"])
            self.assertIn("glare_ratio", res["metrics"])

    def test_quality_catches_localized_glare_blowout(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "glare.png"
            # 70% pure white glare (255), 30% dark texture so mean brightness <= 230 and lap_var >= 12
            arr = np.full((300, 300, 3), 255, dtype=np.uint8)
            rng = np.random.default_rng(42)
            arr[:90, :, :] = rng.integers(0, 60, (90, 300, 3), dtype=np.uint8)
            Image.fromarray(arr).save(path)
            res = assess_quality(path)
            self.assertFalse(res["ok"])
            self.assertIn("glare", res["hint"].lower())
            self.assertGreater(res["metrics"]["glare_ratio"], 0.65)

    def test_quality_missing_file_asks_for_retake(self):
        result = assess_quality(Path(tempfile.gettempdir()) / "nope_missing.png")
        self.assertFalse(result["ok"])
        self.assertIn("Could not read", result["hint"])

    def test_large_photo_is_downscaled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "big.png"
            _sharp((4000, 3000)).save(path)
            url = _image_url(path)
            self.assertTrue(url.startswith("data:image/jpeg;base64,"))
            with Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))) as img:
                self.assertEqual(max(img.size), MAX_SIDE_PX)

    def test_small_photo_sent_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "small.png"
            _sharp((640, 480)).save(path)
            self.assertEqual(_image_url(path).split(",", 1)[1], base64.b64encode(path.read_bytes()).decode())

    def test_agreement_merges_overlapping_boxes_and_keeps_disjoint_first_box(self):
        self.assertGreater(box_iou([100, 100, 300, 300], [120, 120, 320, 320]), 0.5)
        self.assertEqual(box_iou([0, 0, 50, 50], [500, 500, 600, 600]), 0.0)
        merged = reconcile(
            {"verdict": "no", "reason": "clip open", "problem_box": [100, 200, 300, 400]},
            {"verdict": "no", "reason": "clip unlatched", "problem_box": [120, 220, 320, 420]},
        )
        self.assertEqual(merged["verdict"], "no")
        self.assertEqual(merged["problem_box"], [110, 210, 310, 410])

        disjoint = reconcile(
            {"verdict": "no", "reason": "left clip", "problem_box": [10, 10, 50, 50]},
            {"verdict": "no", "reason": "right clip", "problem_box": [800, 800, 900, 900]},
        )
        self.assertEqual(disjoint["problem_box"], [10, 10, 50, 50])

    def test_lint_reports_malformed_shapes_and_string_requires(self):
        self.assertEqual(lint_data({"assembly": "x", "steps": "oops"}), ["'steps' must be a list"])
        errors = lint_data({"assembly": "x", "steps": ["just text", {"id": "s", "instruction": "i", "checks": ["c"]}]})
        self.assertTrue(any("must be a mapping" in e for e in errors))
        self.assertTrue(any("each check must be a mapping" in e for e in errors))
        bad_req = lint_data({
            "assembly": "x",
            "steps": [{"id": "s1", "instruction": "do", "requires": "not_a_list", "hides": True}],
        })
        self.assertTrue(any("'requires' must be a list" in e for e in bad_req))
        with self.assertRaises(ValueError):
            iter_checks({"assembly": "x", "steps": [{"id": "s1", "instruction": "do", "requires": "str_id"}]})

    def test_confirm_gate_and_run_check_without_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = EvidenceLog(Path(tmp) / "evidence")
            session = Session(ASSEMBLY, evidence_log=log)
            # confirm_gate on a visual step is rejected cleanly
            res = session.confirm_gate()
            self.assertEqual(res["action"], "retake")
            self.assertIn("not a gate", res["reason"])

            # Advance to gate step (index 5: close_panel) without passing prerequisites
            session.index = 5
            blocked = session.confirm_gate()
            self.assertEqual(blocked["action"], "retake")
            self.assertIn("Blocked until these pass", blocked["reason"])

            # Once all required checks are passed, confirm_gate unlocks and completes without needing a photo
            for cid in session.checks[5]["requires"]:
                session.passed.add(cid)
            unlocked = session.confirm_gate()
            self.assertEqual(unlocked["action"], "pass")
            self.assertIsNone(session.current())

    def test_evidence_reader_by_check_and_by_unit_analytics(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            log = EvidenceLog(work / "evidence")
            frame = work / "f.png"
            _sharp((256, 256)).save(frame)

            for unit, step, check, verdict, action in (
                ("U1", "ram", "ram_clips", "yes", "pass"),
                ("U1", "gpu_power", "gpu_power_seated", "no", "fix"),
                ("U1", "gpu_power", "gpu_power_seated", "yes", "pass"),
                ("U2", "ram", "ram_clips", "yes", "pass"),
                ("U2", "gpu_power", "gpu_power_seated", "cant_tell", "retake"),
            ):
                log.save(
                    frame,
                    unit_id=unit,
                    assembly="PC build",
                    verdict=verdict,
                    result={
                        "step_id": step,
                        "check_id": check,
                        "action": action,
                        "reason": "test",
                        "problem_box": None,
                        "hint": None,
                    },
                )

            reader = EvidenceReader(log.root)
            by_check = reader.by_check(assembly="PC build")
            self.assertEqual([c["check_id"] for c in by_check], ["gpu_power_seated", "ram_clips"])
            self.assertEqual(by_check[0]["attempts"], 3)
            self.assertEqual(by_check[0]["actions"]["fix"], 1)
            self.assertEqual(by_check[0]["actions"]["retake"], 1)
            self.assertEqual(by_check[0]["pass_rate"], round(1 / 3, 4))
            self.assertEqual(by_check[1]["pass_rate"], 1.0)

            by_unit = reader.by_unit(assembly="PC build")
            self.assertEqual(len(by_unit), 2)
            u1 = next(u for u in by_unit if u["unit_id"] == "U1")
            self.assertEqual(u1["attempts"], 3)
            self.assertEqual(u1["checks_passed"], 2)

    def test_worker_ui_completes_full_pc_build_including_manual_and_gate_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = EvidenceLog(Path(tmp) / "evidence")
            upload = io.BytesIO()
            img = Image.new("RGB", (256, 256), color="red")
            draw = ImageDraw.Draw(img)
            for y in range(0, 256, 16):
                for x in range(0, 256, 16):
                    if (x // 16 + y // 16) % 2:
                        draw.rectangle((x, y, x + 15, y + 15), fill=(220, 220, 220))
            img.save(upload, format="PNG")
            upload.name = "part_ok_01.png"

            with (
                patch.dict(os.environ, {"USE_FAKE_AI": "true"}),
                patch("checker.engine.EvidenceLog", return_value=log),
                patch("streamlit.file_uploader", return_value=upload),
            ):
                app = AppTest.from_file(str(APP), default_timeout=10).run()
                self.assertEqual(len(app.exception), 0)
                # 4 visual checks (ram_clips, gpu_power_seated, cooler_film_removed, cables_clear_of_fans)
                for _ in range(4):
                    app.button[0].click().run()
                    self.assertEqual(len(app.exception), 0)
                # 5th check is manual (fan_header_connected)
                self.assertEqual(app.session_state["session"].current()["kind"], "manual")
                app.button[0].click().run()
                self.assertEqual(len(app.exception), 0)
                # 6th check is gate (close_panel)
                self.assertEqual(app.session_state["session"].current()["kind"], "gate")
                app.button[0].click().run()
                self.assertEqual(len(app.exception), 0)
                self.assertIn("All checks complete", app.success[0].value)


if __name__ == "__main__":
    unittest.main()
