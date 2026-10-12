"""Run all foundation tests.

Usage (from repo root):
  python tests/foundation/run_all.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("USE_FAKE_AI", "true")

from tests.foundation import test_loader, test_quality, test_session  # noqa: E402


def main() -> int:
    print("Foundation tests (synthetic images — not assembly photos)\n")
    try:
        test_loader.test_load_assembly()
        test_quality.test_quality_gate()
        test_session.test_full_walkthrough()
        test_session.test_override()
        test_session.test_supervisor_after_three_quality_retakes()
        test_session.test_fake_ai_filename_retake()
    except AssertionError as exc:
        print(f"\nFAILED: {exc}")
        return 1
    print("\nAll foundation tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
