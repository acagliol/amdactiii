"""OpenCV quality gate (blur / dark). Uses synthetic patterns only."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from checker import assess_quality  # noqa: E402

from ._images import write_blurry, write_dark, write_sharp  # noqa: E402


def test_quality_gate() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="multilond_quality_"))

    q_ok = assess_quality(write_sharp("sharp.jpg", tmp))
    assert q_ok["ok"], q_ok

    q_blur = assess_quality(write_blurry("blur.jpg", tmp))
    assert not q_blur["ok"], q_blur
    assert "blur" in (q_blur["hint"] or "").lower()

    q_dark = assess_quality(write_dark("dark.jpg", tmp))
    assert not q_dark["ok"], q_dark
    assert "dark" in (q_dark["hint"] or "").lower()

    print("OK  test_quality")
