"""Checklist linter + session summary."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ["USE_FAKE_AI"] = "true"

from checker import Session  # noqa: E402
from checker.evidence import EvidenceLog  # noqa: E402
from checker.lint import lint_data, main  # noqa: E402


def test_repo_checklists_lint_clean() -> None:
    assert main([]) == 0
    print("OK  test_lint.repo_clean")


def test_lint_catches_mistakes() -> None:
    bad = {
        "assembly": "",
        "steps": [
            {"id": "a", "instruction": "x", "checks": [
                {"id": "c1", "type": "visal", "question": "Looks fine"},
                {"id": "c1", "question": "Ok?", "reference_photo": "nope.png"},
            ]},
            {"id": "a", "instruction": "", "hides": True},
            {"id": "z", "instruction": "close", "requires": ["later"]},
        ],
    }
    text = "\n".join(lint_data(bad))
    for needle in ["assembly", "unknown type", "yes/no", "duplicate id 'c1'",
                   "reference_photo", "duplicate id 'a'", "missing instruction",
                   "no 'requires'"]:
        assert needle in text, (needle, text)
    # Check prerequisites separately; the invalid type stops loader validation first.
    unknown = {"assembly": "Example", "steps": [
        {"id": "close", "instruction": "Close", "requires": ["later"]},
    ]}
    assert "unknown or later" in "\n".join(lint_data(unknown))
    print("OK  test_lint.catches_mistakes")


def test_session_summary() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="multilond_summary_"))
    s = Session(ROOT / "assemblies" / "pc_build.yaml", evidence_log=EvidenceLog(tmp / "e"))
    sm = s.summary()
    assert sm["done"] == 0 and not sm["complete"]
    assert sm["current_check_id"] == "ram_clips"
    s.override_pass("checked by hand for summary test")
    sm = s.summary()
    assert sm["passed"] == ["ram_clips"] and len(sm["overrides"]) == 1
    print("OK  test_lint.session_summary")
