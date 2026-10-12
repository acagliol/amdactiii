"""Session flow: quality → fake AI → pass/fix/retake/supervisor/override."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ["USE_FAKE_AI"] = "true"

from checker import Session, run_check  # noqa: E402
from checker.evidence import EvidenceLog  # noqa: E402

from ._images import write_blurry, write_dark, write_sharp  # noqa: E402

ASSEMBLY = ROOT / "assemblies" / "pc_build.yaml"


def test_full_walkthrough() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="multilond_session_"))
    session = Session(ASSEMBLY, evidence_log=EvidenceLog(tmp / "evidence"))

    r = run_check(session, write_blurry("shot_blur_01.jpg", tmp))
    assert r["action"] == "retake"
    assert "blur" in (r["hint"] or "").lower()
    assert "ram_clips" not in session.passed

    r = run_check(session, write_dark("shot_dark_01.jpg", tmp))
    assert r["action"] == "retake"
    assert "dark" in (r["hint"] or "").lower()
    assert session.retake_streak == 2

    r = run_check(session, write_sharp("ram_ok_01.jpg", tmp))
    assert r["action"] == "pass"
    assert "ram_clips" in session.passed
    assert session.retake_streak == 0

    r = run_check(session, write_sharp("gpu_bad_01.jpg", tmp))
    assert r["action"] == "fix"
    assert r["problem_box"] is not None

    r = run_check(session, write_sharp("gpu_ok_01.jpg", tmp))
    assert r["action"] == "pass"
    assert session.current() is None
    assert session.passed == {"ram_clips", "gpu_power_seated"}

    print("OK  test_session.walkthrough")


def test_override() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="multilond_override_"))
    session = Session(ASSEMBLY, evidence_log=EvidenceLog(tmp / "evidence"))
    bad = session.override_pass("short")
    assert bad["action"] == "retake"
    assert not session.passed

    good = session.override_pass("verified by hand — clips seated")
    assert good["action"] == "pass"
    assert "ram_clips" in session.passed
    assert session.current()["check_id"] == "gpu_power_seated"

    print("OK  test_session.override")


def test_supervisor_after_three_quality_retakes() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="multilond_supervisor_"))
    session = Session(ASSEMBLY, evidence_log=EvidenceLog(tmp / "evidence"))
    expected = ["retake", "retake", "supervisor"]
    names = ["a_blur.jpg", "b_dark.jpg", "c_blur.jpg"]
    makers = [write_blurry, write_dark, write_blurry]
    for i, (name, make) in enumerate(zip(names, makers)):
        r = run_check(session, make(name, tmp))
        assert r["action"] == expected[i], (i, r)
    assert not session.passed

    print("OK  test_session.supervisor")


def test_fake_ai_filename_retake() -> None:
    """Filename _blur_ → cant_tell when quality is skipped."""
    tmp = Path(tempfile.mkdtemp(prefix="multilond_fakeai_"))
    session = Session(ASSEMBLY, evidence_log=EvidenceLog(tmp / "evidence"))
    # sharp pixels so only fake AI drives the retake
    r = run_check(session, write_sharp("gpu_blur_01.jpg", tmp), skip_quality=True)
    assert r["action"] == "retake"
    print("OK  test_session.fake_ai_filename")
