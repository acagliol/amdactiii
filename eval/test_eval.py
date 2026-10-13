"""Smoke test eval on synthetic frames: python -m eval.test_eval"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["USE_FAKE_AI"] = "true"

from eval.evaluate import kpi_misses, score_row, summarize  # noqa: E402
from eval.make_answer_key import build  # noqa: E402
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


if __name__ == "__main__":
    test_eval_pipeline()
