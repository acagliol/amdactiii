"""Build eval/answer_key.csv from frame filenames (T60).

<check_id>_ok_*.jpg -> pass, <check_id>_bad_*.jpg -> fix.
Frames whose check_id is not in the assembly are skipped and reported.

MVTec AD (optional, --mvtec DIR): DIR/<category>/test/<defect>/*.png
  good -> pass, any other defect folder -> fix, scored against
  assemblies/mvtec/<category>.yaml (its first visual check).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from checker.loader import iter_checks, load_assembly  # noqa: E402

FRAMES = ROOT / "data" / "frames"
OUT = ROOT / "eval" / "answer_key.csv"
DEFAULT_ASSEMBLY = "assemblies/pc_build.yaml"
PATTERN = re.compile(r"^(?P<check>.+?)_(?P<label>ok|bad)(_|\.)", re.I)
EXTS = {".jpg", ".jpeg", ".png"}


def build(frames: Path = FRAMES, assembly: str = DEFAULT_ASSEMBLY) -> tuple[list[dict], list[str]]:
    ids = {c["check_id"] for c in iter_checks(load_assembly(ROOT / assembly)) if c["kind"] == "visual"}
    rows, skipped = [], []
    for p in sorted(frames.rglob("*")):
        if p.suffix.lower() not in EXTS:
            continue
        m = PATTERN.match(p.name)
        if not m or m["check"] not in ids:
            skipped.append(p.name)
            continue
        rows.append({
            "image": _rel(p),
            "assembly": assembly,
            "check_id": m["check"],
            "expected": "pass" if m["label"].lower() == "ok" else "fix",
        })
    return rows, skipped


def build_mvtec(mvtec_root: Path) -> tuple[list[dict], list[str]]:
    rows, skipped = [], []
    for cat_dir in sorted(p for p in mvtec_root.iterdir() if p.is_dir()):
        yaml_path = ROOT / "assemblies" / "mvtec" / f"{cat_dir.name}.yaml"
        if not yaml_path.exists():
            skipped.append(f"{cat_dir.name}/ (no checklist)")
            continue
        visual = [c for c in iter_checks(load_assembly(yaml_path)) if c["kind"] == "visual"]
        check_id = visual[0]["check_id"]
        for p in sorted((cat_dir / "test").rglob("*")):
            if p.suffix.lower() not in EXTS:
                continue
            rows.append({
                "image": _rel(p),
                "assembly": yaml_path.relative_to(ROOT).as_posix(),
                "check_id": check_id,
                "expected": "pass" if p.parent.name == "good" else "fix",
            })
    return rows, skipped


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mvtec", type=Path, help="MVTec AD root (category folders)")
    args = ap.parse_args(argv)
    rows, skipped = build()
    if args.mvtec:
        more, more_skipped = build_mvtec(args.mvtec)
        rows += more
        skipped += more_skipped
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image", "assembly", "check_id", "expected"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT.relative_to(ROOT)}")
    if skipped:
        print(f"Skipped {len(skipped)} (name not <check_id>_ok|bad_*): {', '.join(skipped[:10])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
