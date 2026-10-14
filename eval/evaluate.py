"""Scorecard evaluator against eval/answer_key.csv (T61).

Computes:
1. Classification KPIs: Catch rate (>=90%), False alarm rate (<=10%), Retake rate, Latency (<5s).
2. Grounding quality: Box vs GT Box IoU, Box vs Pixel Mask overlap (coverage & hit rate).
Outputs:
- ASCII scorecard in stdout
- eval/results.csv (per-frame detail)
- eval/scorecard.json (machine-readable metrics for dashboard and pitch deck)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("USE_FAKE_AI", "true")

from checker import Session, run_check  # noqa: E402
from checker.evidence import EvidenceLog  # noqa: E402

KEY = ROOT / "eval" / "answer_key.csv"
OUT_CSV = ROOT / "eval" / "results.csv"
OUT_JSON = ROOT / "eval" / "scorecard.json"

KPI = {
    "catch_rate": 0.90,
    "false_alarm_rate": 0.10,
    "p95_latency_s": 5.0,
    "grounding_hit_rate": 0.75,
}


def compute_box_iou(box1: list[int] | None, box2: list[int] | None) -> float:
    """Calculate IoU between two 0-1000 normalized boxes [ymin, xmin, ymax, xmax]."""
    if not box1 or not box2 or len(box1) != 4 or len(box2) != 4:
        return 0.0
    y1m, x1m, y1M, x1M = box1
    y2m, x2m, y2M, x2M = box2

    inter_h = max(0, min(y1M, y2M) - max(y1m, y2m))
    inter_w = max(0, min(x1M, x2M) - max(x1m, x2m))
    inter_area = inter_h * inter_w

    area1 = max(0, y1M - y1m) * max(0, x1M - x1m)
    area2 = max(0, y2M - y2m) * max(0, x2M - x2m)
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return round(float(inter_area / union_area), 4)


def compute_mask_overlap(box: list[int] | None, mask_path: str | Path | None) -> dict[str, Any]:
    """Calculate pixel overlap between predicted box and ground-truth binary mask PNG."""
    if not box or not mask_path or len(box) != 4:
        return {"mask_iou": 0.0, "defect_coverage": 0.0, "hit": False}

    full_mask_path = ROOT / mask_path if not Path(mask_path).is_absolute() else Path(mask_path)
    if not full_mask_path.exists():
        return {"mask_iou": 0.0, "defect_coverage": 0.0, "hit": False}

    mask = cv2.imread(str(full_mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return {"mask_iou": 0.0, "defect_coverage": 0.0, "hit": False}

    h, w = mask.shape
    gt_defect = (mask > 128)
    gt_count = int(np.sum(gt_defect))
    if gt_count == 0:
        return {"mask_iou": 0.0, "defect_coverage": 0.0, "hit": False}

    ymin, xmin, ymax, xmax = box
    py_min = max(0, min(h - 1, int(round(ymin / 1000.0 * h))))
    px_min = max(0, min(w - 1, int(round(xmin / 1000.0 * w))))
    py_max = max(0, min(h, int(round(ymax / 1000.0 * h)) + 1))
    px_max = max(0, min(w, int(round(xmax / 1000.0 * w)) + 1))

    box_mask = np.zeros_like(mask, dtype=bool)
    box_mask[py_min:py_max, px_min:px_max] = True

    inter = int(np.sum(gt_defect & box_mask))
    union = int(np.sum(gt_defect | box_mask))

    mask_iou = round(float(inter / union), 4) if union > 0 else 0.0
    coverage = round(float(inter / gt_count), 4) if gt_count > 0 else 0.0
    hit = bool(mask_iou >= 0.20 or coverage >= 0.30)

    return {
        "mask_iou": mask_iou,
        "defect_coverage": coverage,
        "hit": hit,
    }


def score_row(row: dict[str, Any], evidence_dir: Path) -> dict[str, Any]:
    """Execute inspection on a single test frame and compute metrics."""
    session = Session(ROOT / row["assembly"], evidence_log=EvidenceLog(evidence_dir))
    check = next((c for c in session.checks if c["check_id"] == row["check_id"]), None)
    if check is None:
        return {
            **row,
            "action": "error",
            "latency_s": 0.0,
            "pred_box": None,
            "box_iou": 0.0,
            "mask_coverage": 0.0,
            "grounding_hit": False,
            "reason": "unknown check_id",
        }

    start = time.perf_counter()
    img_path = ROOT / row["image"]
    result = run_check(session, img_path, check=check)
    latency = round(time.perf_counter() - start, 3)

    pred_box = result.get("problem_box")

    # Compute Box vs GT Box & Mask overlap if defect sample
    box_iou_val = 0.0
    mask_cov_val = 0.0
    hit_val = False

    if row["expected"] == "fix":
        gt_box_str = row.get("gt_box")
        gt_box = json.loads(gt_box_str) if gt_box_str else None
        if pred_box and gt_box:
            box_iou_val = compute_box_iou(pred_box, gt_box)

        mask_rel = row.get("mask_path")
        if mask_rel:
            mask_res = compute_mask_overlap(pred_box, mask_rel)
            mask_cov_val = mask_res["defect_coverage"]
            hit_val = mask_res["hit"] or (box_iou_val >= 0.25)
        elif box_iou_val >= 0.25:
            hit_val = True

    return {
        **row,
        "action": result["action"],
        "latency_s": latency,
        "pred_box": json.dumps(pred_box) if pred_box else "",
        "box_iou": box_iou_val,
        "mask_coverage": mask_cov_val,
        "grounding_hit": hit_val,
        "reason": result.get("reason", ""),
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate summary scorecard metrics and KPI comparisons."""
    bad = [r for r in results if r["expected"] == "fix"]
    good = [r for r in results if r["expected"] == "pass"]

    lat = sorted(r["latency_s"] for r in results)
    p95 = lat[min(len(lat) - 1, int(0.95 * len(lat)))] if lat else 0.0
    mean_lat = round(sum(lat) / len(lat), 3) if lat else 0.0

    # Classification metrics
    caught_count = sum(r["action"] != "pass" for r in bad)
    catch_rate = (caught_count / len(bad)) if bad else None

    false_alarms = sum(r["action"] == "fix" for r in good)
    false_alarm_rate = (false_alarms / len(good)) if good else None

    retakes = sum(r["action"] == "retake" for r in results)
    supervisors = sum(r["action"] == "supervisor" for r in results)
    errors = sum(r["action"] == "error" for r in results)

    # Grounding overlap metrics on defects
    defect_results = [r for r in bad if r["action"] == "fix"]
    valid_ious = [r["box_iou"] for r in defect_results if r["box_iou"] > 0]
    mean_box_iou = round(sum(valid_ious) / len(valid_ious), 3) if valid_ious else 0.0

    hits = sum(1 for r in defect_results if r["grounding_hit"])
    grounding_hit_rate = (hits / len(bad)) if bad else None

    # Breakdown by defect category
    by_category: dict[str, dict[str, Any]] = {}
    categories = sorted(list({r.get("defect_type", "unknown") for r in results}))
    for cat in categories:
        cat_rows = [r for r in results if r.get("defect_type") == cat]
        cat_caught = sum(r["action"] != "pass" for r in cat_rows if r["expected"] == "fix")
        cat_total = len(cat_rows)
        by_category[cat] = {
            "total": cat_total,
            "caught": cat_caught if cat != "good" else sum(r["action"] == "pass" for r in cat_rows),
            "rate": round(cat_caught / cat_total, 3) if cat != "good" and cat_total > 0 else round(sum(r["action"] == "pass" for r in cat_rows) / cat_total, 3),
        }

    return {
        "frames": len(results),
        "clean_frames": len(good),
        "defect_frames": len(bad),
        "catch_rate": catch_rate,
        "false_alarm_rate": false_alarm_rate,
        "retakes": retakes,
        "supervisor": supervisors,
        "errors": errors,
        "mean_latency_s": mean_lat,
        "p95_latency_s": p95,
        "mean_box_iou": mean_box_iou,
        "grounding_hit_rate": grounding_hit_rate,
        "by_category": by_category,
    }


def kpi_misses(s: dict[str, Any]) -> list[str]:
    """Check if any core KPI targets were missed."""
    misses = []
    if s["catch_rate"] is not None and s["catch_rate"] < KPI["catch_rate"]:
        misses.append(f"catch_rate ({s['catch_rate']:.1%} < {KPI['catch_rate']:.0%})")
    if s["false_alarm_rate"] is not None and s["false_alarm_rate"] > KPI["false_alarm_rate"]:
        misses.append(f"false_alarm_rate ({s['false_alarm_rate']:.1%} > {KPI['false_alarm_rate']:.0%})")
    if s["p95_latency_s"] > KPI["p95_latency_s"]:
        misses.append(f"p95_latency_s ({s['p95_latency_s']:.2f}s > {KPI['p95_latency_s']:.1f}s)")
    return misses


def print_scorecard(s: dict[str, Any], ai_backend: str, misses: list[str]) -> None:
    """Print an ASCII scorecard table for terminal and pitch deck inclusion."""
    status_icon = "✅ PASSED" if not misses else "⚠️ KPI MISSED"
    print("\n" + "=" * 76)
    print(f"               MULTILÖND AI — EVALUATION SCORECARD ({status_icon})")
    print("=" * 76)
    print(f" AI Backend:     {ai_backend.upper()}")
    print(f" Total Samples:  {s['frames']} ({s['clean_frames']} clean / {s['defect_frames']} defects)")
    print("-" * 76)
    print(f" {'Metric':<26} {'Result':<16} {'Target':<14} {'Status'}")
    print("-" * 76)

    cr_str = f"{s['catch_rate']:.1%}" if s['catch_rate'] is not None else "n/a"
    cr_pass = "✅ PASS" if (s['catch_rate'] is not None and s['catch_rate'] >= KPI['catch_rate']) else "❌ FAIL"
    print(f" {'Defect Catch Rate':<26} {cr_str:<16} {'≥ 90.0%':<14} {cr_pass}")

    fa_str = f"{s['false_alarm_rate']:.1%}" if s['false_alarm_rate'] is not None else "n/a"
    fa_pass = "✅ PASS" if (s['false_alarm_rate'] is not None and s['false_alarm_rate'] <= KPI['false_alarm_rate']) else "❌ FAIL"
    print(f" {'False Alarm Rate':<26} {fa_str:<16} {'≤ 10.0%':<14} {fa_pass}")

    lat_str = f"{s['p95_latency_s']:.2f}s (mean {s['mean_latency_s']:.2f}s)"
    lat_pass = "✅ PASS" if s['p95_latency_s'] <= KPI['p95_latency_s'] else "❌ FAIL"
    print(f" {'Inference Latency (P95)':<26} {lat_str:<16} {'< 5.0s':<14} {lat_pass}")

    iou_str = f"{s['mean_box_iou']:.2f}"
    print(f" {'Grounding Mean Box IoU':<26} {iou_str:<16} {'—':<14} {'ℹ️ INFO'}")

    gh_str = f"{s['grounding_hit_rate']:.1%}" if s['grounding_hit_rate'] is not None else "n/a"
    gh_pass = "✅ PASS" if (s['grounding_hit_rate'] is not None and s['grounding_hit_rate'] >= KPI['grounding_hit_rate']) else "ℹ️ INFO"
    print(f" {'Grounding Hit Rate (Mask)':<26} {gh_str:<16} {'≥ 75.0%':<14} {gh_pass}")

    print("-" * 76)
    print(f" Retakes: {s['retakes']} | Supervisors: {s['supervisor']} | Errors: {s['errors']}")

    if s.get("by_category"):
        print("-" * 76)
        print(" Category Breakdown:")
        for cat, data in s["by_category"].items():
            print(f"   • {cat:<24} {data['caught']}/{data['total']} ({data['rate']:.0%})")

    print("=" * 76 + "\n")


def main(key_path: Path = KEY, out_csv: Path = OUT_CSV, out_json: Path = OUT_JSON) -> int:
    is_real_ai = os.environ.get("USE_FAKE_AI", "true").lower() != "true"
    default_pace = 4.0 if is_real_ai else 0.0

    parser = argparse.ArgumentParser(description="Evaluate inspection accuracy and grounding scorecard.")
    parser.add_argument("--key", type=str, default=str(key_path), help="Path to answer_key.csv")
    parser.add_argument("--out-csv", type=str, default=str(out_csv), help="Path to results CSV output")
    parser.add_argument("--out-json", type=str, default=str(out_json), help="Path to scorecard JSON output")
    parser.add_argument(
        "--pace",
        type=float,
        default=default_pace,
        help="Seconds to wait between requests (default: 4.0s for real AI to respect 20 req/min limit, 0 for fake AI)"
    )
    args = parser.parse_args()

    active_key = Path(args.key)
    if not active_key.exists():
        print(f"Error: {active_key.relative_to(ROOT)} not found! Run python -m eval.make_answer_key first.")
        return 1

    with active_key.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"{active_key.relative_to(ROOT)} is empty! Run python -m eval.make_answer_key first.")
        return 1

    evidence_tmp = Path(tempfile.mkdtemp(prefix="multilond_eval_run_"))
    results = []
    total = len(rows)
    for idx, r in enumerate(rows):
        if idx > 0 and args.pace > 0:
            time.sleep(args.pace)
        res = score_row(r, evidence_tmp)
        results.append(res)
        if is_real_ai:
            print(f"  [{idx + 1}/{total}] {r.get('image', '')}: {res['action']} ({res['latency_s']}s)")

    # Save results.csv
    csv_dest = Path(args.out_csv)
    csv_dest.parent.mkdir(parents=True, exist_ok=True)
    with csv_dest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    # Summarize & compute KPIs
    summary = summarize(results)
    misses = kpi_misses(summary)

    # Save scorecard.json
    json_dest = Path(args.out_json)
    json_dest.parent.mkdir(parents=True, exist_ok=True)
    with json_dest.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    ai_env = "fake_ai (offline)" if os.environ.get("USE_FAKE_AI", "true").lower() == "true" else "vLLM on AMD MI300X"
    print_scorecard(summary, ai_env, misses)
    print(f"Detailed results saved to: {csv_dest.relative_to(ROOT) if csv_dest.is_relative_to(ROOT) else csv_dest}")
    print(f"Scorecard JSON saved to:   {json_dest.relative_to(ROOT) if json_dest.is_relative_to(ROOT) else json_dest}")

    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
