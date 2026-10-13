"""Score the checker against eval/answer_key.csv (T61).

caught      = planted mistake (expected fix) not passed
false alarm = clean frame (expected pass) answered fix
retake / supervisor are reported separately (not counted as false alarms).
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("USE_FAKE_AI", "true")

from checker import Session, run_check  # noqa: E402
from checker.evidence import EvidenceLog  # noqa: E402

KEY = ROOT / "eval" / "answer_key.csv"
OUT = ROOT / "eval" / "results.csv"
KPI = {"catch_rate": 0.90, "false_alarm_rate": 0.10, "p95_latency_s": 5.0}


def score_row(row: dict, evidence_dir: Path) -> dict:
    session = Session(ROOT / row["assembly"], evidence_log=EvidenceLog(evidence_dir))
    check = next((c for c in session.checks if c["check_id"] == row["check_id"]), None)
    if check is None:
        return {**row, "action": "error", "latency_s": 0.0, "reason": "unknown check_id"}
    start = time.perf_counter()
    result = run_check(session, ROOT / row["image"], check=check)
    return {
        **row,
        "action": result["action"],
        "latency_s": round(time.perf_counter() - start, 3),
        "reason": result.get("reason", ""),
    }


def summarize(results: list[dict]) -> dict:
    bad = [r for r in results if r["expected"] == "fix"]
    good = [r for r in results if r["expected"] == "pass"]
    lat = sorted(r["latency_s"] for r in results)
    p95 = lat[min(len(lat) - 1, int(0.95 * len(lat)))] if lat else 0.0
    return {
        "frames": len(results),
        "catch_rate": sum(r["action"] != "pass" for r in bad) / len(bad) if bad else None,
        "false_alarm_rate": sum(r["action"] == "fix" for r in good) / len(good) if good else None,
        "retakes": sum(r["action"] == "retake" for r in results),
        "supervisor": sum(r["action"] == "supervisor" for r in results),
        "errors": sum(r["action"] == "error" for r in results),
        "p95_latency_s": p95,
    }


def kpi_misses(s: dict) -> list[str]:
    misses = []
    if s["catch_rate"] is not None and s["catch_rate"] < KPI["catch_rate"]:
        misses.append("catch_rate")
    if s["false_alarm_rate"] is not None and s["false_alarm_rate"] > KPI["false_alarm_rate"]:
        misses.append("false_alarm_rate")
    if s["p95_latency_s"] > KPI["p95_latency_s"]:
        misses.append("p95_latency_s")
    return misses


def main(key: Path = KEY) -> int:
    with key.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"{key.relative_to(ROOT)} is empty - run python -m eval.make_answer_key first")
        return 1
    tmp = Path(tempfile.mkdtemp(prefix="multilond_eval_"))
    results = [score_row(r, tmp) for r in rows]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    s = summarize(results)
    ai = "fake" if os.environ.get("USE_FAKE_AI", "true").lower() == "true" else "real"
    print(f"AI: {ai} | frames: {s['frames']}")
    for k in ("catch_rate", "false_alarm_rate"):
        v = s[k]
        print(f"  {k:<17} {'n/a' if v is None else f'{v:.0%}'}")
    print(f"  p95_latency_s     {s['p95_latency_s']:.2f}")
    print(f"  retakes {s['retakes']} | supervisor {s['supervisor']} | errors {s['errors']}")
    misses = kpi_misses(s)
    print("KPI: OK" if not misses else f"KPI MISSED: {', '.join(misses)}")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
