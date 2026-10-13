"""Build eval/answer_key.csv from folders (T60).

Supports both:
1. MVTec dataset folder structures:
   data/mvtec/<category>/test/{good, <defect_type>} + ground_truth/<defect_type>/*_mask.png
2. Standard workstation frames:
   data/frames/<check_id>_{ok,bad}_*.jpg
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from checker.loader import iter_checks, load_assembly  # noqa: E402

FRAMES_DIR = ROOT / "data" / "frames"
MVTEC_DIR = ROOT / "data" / "mvtec" / "cable"
OUT_CSV = ROOT / "eval" / "answer_key.csv"
DEFAULT_ASSEMBLY = "assemblies/pc_build.yaml"
PATTERN = re.compile(r"^(?P<check>.+?)_(?P<label>ok|bad)(_|\.)", re.I)
EXTS = {".jpg", ".jpeg", ".png"}


def extract_gt_box_from_mask(mask_path: Path) -> list[int] | None:
    """Read a ground truth binary mask and return normalized 0-1000 [ymin, xmin, ymax, xmax]."""
    if not mask_path.exists():
        return None
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return None
    ys, xs = np.where(mask > 128)
    if len(ys) == 0:
        return None
    h, w = mask.shape
    return [
        int(round(float(ys.min()) / h * 1000)),
        int(round(float(xs.min()) / w * 1000)),
        int(round(float(ys.max()) / h * 1000)),
        int(round(float(xs.max()) / w * 1000)),
    ]


def build_from_mvtec(
    mvtec_dir: Path,
    assembly_yaml: str = "assemblies/mvtec/cable.yaml"
) -> tuple[list[dict[str, Any]], list[str]]:
    """Crawl an MVTec category folder: test/good + test/<defect> and ground_truth/<defect>."""
    test_dir = mvtec_dir / "test"
    gt_dir = mvtec_dir / "ground_truth"
    if not test_dir.exists():
        return [], [f"Missing test directory at {test_dir}"]

    # Determine check_id from assembly
    asm_path = ROOT / assembly_yaml
    check_id = "cable_defect_free"
    if asm_path.exists():
        checks = [c for c in iter_checks(load_assembly(asm_path)) if c["kind"] == "visual"]
        if checks:
            check_id = checks[0]["check_id"]

    rows: list[dict[str, Any]] = []
    skipped: list[str] = []

    for category_dir in sorted(test_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        defect_type = category_dir.name
        is_clean = (defect_type.lower() == "good")
        expected = "pass" if is_clean else "fix"

        for img_path in sorted(category_dir.glob("*")):
            if img_path.suffix.lower() not in EXTS:
                continue

            mask_rel = ""
            gt_box_str = ""

            if not is_clean:
                mask_file = gt_dir / defect_type / f"{img_path.stem}_mask.png"
                if mask_file.exists():
                    mask_rel = mask_file.relative_to(ROOT).as_posix()
                    box = extract_gt_box_from_mask(mask_file)
                    if box:
                        gt_box_str = json.dumps(box)

            rows.append({
                "image": img_path.relative_to(ROOT).as_posix(),
                "assembly": assembly_yaml,
                "check_id": check_id,
                "expected": expected,
                "defect_type": defect_type,
                "mask_path": mask_rel,
                "gt_box": gt_box_str,
            })

    return rows, skipped


def build_from_frames(
    frames: Path = FRAMES_DIR,
    assembly: str = DEFAULT_ASSEMBLY
) -> tuple[list[dict[str, Any]], list[str]]:
    """Legacy filename-based builder: <check_id>_ok|bad_*."""
    asm_path = ROOT / assembly
    ids = set()
    if asm_path.exists():
        ids = {c["check_id"] for c in iter_checks(load_assembly(asm_path)) if c["kind"] == "visual"}
    rows, skipped = [], []
    for p in sorted(frames.rglob("*")):
        if p.suffix.lower() not in EXTS:
            continue
        m = PATTERN.match(p.name)
        if not m or (ids and m["check"] not in ids):
            skipped.append(p.name)
            continue
        rows.append({
            "image": p.relative_to(ROOT).as_posix(),
            "assembly": assembly,
            "check_id": m["check"],
            "expected": "pass" if m["label"].lower() == "ok" else "fix",
            "defect_type": "good" if m["label"].lower() == "ok" else "defect",
            "mask_path": "",
            "gt_box": "",
        })
    return rows, skipped


def build(
    mvtec_dir: Path | None = None,
    frames: Path | None = None,
    frames_dir: Path | None = None,
    assembly: str | None = None
) -> tuple[list[dict[str, Any]], list[str]]:
    """Auto-detect source or build from specified target."""
    f_dir = frames or frames_dir
    # If caller specifically passed frames directory, prioritize it
    if f_dir:
        return build_from_frames(f_dir, assembly or DEFAULT_ASSEMBLY)

    target_mvtec = mvtec_dir or (MVTEC_DIR if MVTEC_DIR.exists() else None)
    if target_mvtec and (target_mvtec / "test").exists():
        asm = assembly or "assemblies/mvtec/cable.yaml"
        return build_from_mvtec(target_mvtec, asm)
    return build_from_frames(f_dir or FRAMES_DIR, assembly or DEFAULT_ASSEMBLY)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build answer key CSV from dataset folders or frame names.")
    parser.add_argument("--mvtec", type=str, default=None, help="Path to MVTec category folder (e.g. data/mvtec/cable)")
    parser.add_argument("--frames", type=str, default=None, help="Path to frames folder")
    parser.add_argument("--assembly", type=str, default=None, help="Assembly YAML path")
    parser.add_argument("--out", type=str, default=str(OUT_CSV), help="Output answer key CSV path")
    args = parser.parse_args()

    mvtec_path = Path(args.mvtec) if args.mvtec else None
    frames_path = Path(args.frames) if args.frames else None
    rows, skipped = build(mvtec_path, frames_path, args.assembly)

    out_file = Path(args.out)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["image", "assembly", "check_id", "expected", "defect_type", "mask_path", "gt_box"]
    with out_file.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_file.relative_to(ROOT) if out_file.is_relative_to(ROOT) else out_file}")
    if skipped:
        print(f"Skipped {len(skipped)} files: {', '.join(skipped[:10])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
