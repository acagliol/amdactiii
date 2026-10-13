"""Build eval/answer_key.csv from frame filenames (T60).

<check_id>_ok_*.jpg -> pass, <check_id>_bad_*.jpg -> fix.
Frames whose check_id is not in the assembly are skipped and reported.
"""

from __future__ import annotations

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
            "image": p.relative_to(ROOT).as_posix(),
            "assembly": assembly,
            "check_id": m["check"],
            "expected": "pass" if m["label"].lower() == "ok" else "fix",
        })
    return rows, skipped


def main() -> int:
    rows, skipped = build()
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
