"""Assembly YAML loader."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from checker.loader import iter_visual_checks, load_assembly  # noqa: E402

ASSEMBLY = ROOT / "assemblies" / "pc_build.yaml"


def test_load_assembly() -> None:
    data = load_assembly(ASSEMBLY)
    assert data["assembly"] == "PC build"
    assert len(data["steps"]) >= 3
    checks = iter_visual_checks(data)
    ids = [c["check_id"] for c in checks]
    assert "ram_clips" in ids
    assert "gpu_power_seated" in ids
    print("OK  test_loader")
