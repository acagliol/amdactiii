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

    # 2. Mask overlap test using synthetic mask
    tmp_dir = Path(tempfile.mkdtemp(prefix="mask_test_"))
    try:
        import cv2
        import numpy as np
        syn_mask_path = tmp_dir / "test_mask.png"
        mask_arr = np.zeros((100, 100), dtype=np.uint8)
        mask_arr[20:60, 20:60] = 255  # defect from 20% to 60% -> [200, 200, 600, 600]
        cv2.imwrite(str(syn_mask_path), mask_arr)

        gt_box = extract_gt_box_from_mask(syn_mask_path)
        assert gt_box == [200, 200, 590, 590], gt_box
        res = compute_mask_overlap(gt_box, syn_mask_path)
        assert res["hit"] is True
        assert res["defect_coverage"] >= 0.99
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
    print("OK  eval.metrics")


if __name__ == "__main__":
    test_eval_pipeline()
    test_box_and_mask_metrics()
