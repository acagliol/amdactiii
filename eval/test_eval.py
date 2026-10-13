"""Smoke test eval on synthetic frames: python -m eval.test_eval"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["USE_FAKE_AI"] = "true"

from eval.evaluate import compute_box_iou, compute_mask_overlap, kpi_misses, score_row, summarize  # noqa: E402
from eval.make_answer_key import build, extract_gt_box_from_mask  # noqa: E402
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


def test_box_and_mask_metrics() -> None:
    # 1. Box IoU
    box1 = [100, 100, 300, 300]
    box2 = [100, 100, 300, 300]
    assert compute_box_iou(box1, box2) == 1.0

    box_disjoint = [500, 500, 700, 700]
    assert compute_box_iou(box1, box_disjoint) == 0.0

    box_partial = [100, 100, 200, 300]
    assert 0.0 < compute_box_iou(box1, box_partial) < 1.0

    # 2. Mask overlap on real MVTec mask if available
    sample_mask = ROOT / "data" / "mvtec" / "cable" / "ground_truth" / "cable_swap" / "000_mask.png"
    if sample_mask.exists():
        gt_box = extract_gt_box_from_mask(sample_mask)
        assert gt_box is not None and len(gt_box) == 4
        res = compute_mask_overlap(gt_box, sample_mask)
        assert res["hit"] is True
        assert res["defect_coverage"] > 0.8
    print("OK  eval.metrics")


if __name__ == "__main__":
    test_eval_pipeline()
    test_box_and_mask_metrics()
