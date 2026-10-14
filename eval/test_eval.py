"""Smoke test eval on synthetic frames: python -m eval.test_eval"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["USE_FAKE_AI"] = "true"

from eval.evaluate import kpi_misses, per_assembly, score_row, summarize  # noqa: E402
from eval.make_answer_key import build, build_mvtec  # noqa: E402
from tests.foundation._images import write_sharp  # noqa: E402


def test_eval_pipeline() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="multilond_evaltest_", dir=ROOT / "data"))
    try:
        write_sharp("ram_clips_ok_01.jpg", tmp)
        write_sharp("gpu_power_seated_bad_01.jpg", tmp)
        write_sharp("random_photo.jpg", tmp)
        rows, skipped = build(frames=tmp)
        assert {r["expected"] for r in rows} == {"pass", "fix"}, rows
        assert skipped == ["random_photo.jpg"]
        results = [score_row(r, tmp / "evidence") for r in rows]
        s = summarize(results)
        assert s["frames"] == 2 and s["errors"] == 0, s
        assert isinstance(kpi_misses(s), list)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("OK  eval.pipeline")


def test_mvtec_answer_key() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="multilond_mvtec_"))
    try:
        write_sharp("000_ok.png", tmp / "bottle" / "test" / "good")
        write_sharp("001_bad.png", tmp / "bottle" / "test" / "contamination")
        write_sharp("x.png", tmp / "not_a_category" / "test" / "good")
        rows, skipped = build_mvtec(tmp)
        assert [(r["check_id"], r["expected"]) for r in rows] == [
            ("bottle_defect_free", "fix"), ("bottle_defect_free", "pass"),
        ], rows
        assert skipped == ["not_a_category/ (no checklist)"], skipped
        results = [score_row(r, tmp / "evidence") for r in rows]
        groups = per_assembly(results)
        assert list(groups) == ["assemblies/mvtec/bottle.yaml"], groups
        assert groups["assemblies/mvtec/bottle.yaml"]["errors"] == 0
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("OK  eval.mvtec")


if __name__ == "__main__":
    test_eval_pipeline()
    test_mvtec_answer_key()
