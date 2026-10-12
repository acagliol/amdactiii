"""Foundation smoke test — no Streamlit UI required.

Usage (from repo root):
  python scripts/smoke_test.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["USE_FAKE_AI"] = "true"

from checker import Session, run_check  # noqa: E402
from checker.loader import load_assembly  # noqa: E402


def _touch(name: str) -> Path:
    path = Path(tempfile.gettempdir()) / name
    path.write_bytes(b"fake-image-bytes")
    return path


def main() -> None:
    assembly_path = ROOT / "assemblies" / "pc_build.yaml"
    data = load_assembly(assembly_path)
    assert data["assembly"] == "PC build"
    assert len(data["steps"]) >= 3
    print("OK  load_assembly")

    session = Session(assembly_path)
    assert session.current()["check_id"] == "ram_clips"

    r_ok = run_check(session, _touch("ram_ok_01.jpg"))
    assert r_ok["action"] == "pass", r_ok
    assert "ram_clips" in session.passed
    print("OK  pass on *_ok_*")

    r_bad = run_check(session, _touch("gpu_bad_01.jpg"))
    assert r_bad["action"] == "fix", r_bad
    assert r_bad["problem_box"] is not None
    print("OK  fix on *_bad_*")

    # Still on gpu check — blur → retake
    r_blur = run_check(session, _touch("gpu_blur_01.jpg"))
    assert r_blur["action"] == "retake", r_blur
    print("OK  retake on *_blur_*")

    # Pass gpu, then close_panel has no visual check — session completes visual list
    r_gpu = run_check(session, _touch("gpu_ok_01.jpg"))
    assert r_gpu["action"] == "pass", r_gpu
    assert session.current() is None
    print("OK  all visual checks complete")

    print("\nAll foundation smoke tests passed.")


if __name__ == "__main__":
    main()
