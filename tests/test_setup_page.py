"""Tests for Setup Mode checklist authoring page."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from checker.lint import lint_data
from checker.loader import load_assembly

ROOT = Path(__file__).resolve().parents[1]
SETUP_PAGE = ROOT / "app" / "pages" / "4_Setup.py"


class SetupPageTests(unittest.TestCase):
    def test_setup_page_loads_without_exception(self):
        app = AppTest.from_file(str(SETUP_PAGE), default_timeout=10).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Checklist Setup" in t.value for t in app.title))

    def test_linter_validation_integrated(self):
        # Valid data
        valid_data = {
            "assembly": "Test Assembly",
            "steps": [
                {
                    "id": "step_a",
                    "instruction": "Assemble part A.",
                    "checks": [
                        {
                            "id": "check_a",
                            "type": "visual",
                            "question": "Is part A in place?",
                        }
                    ],
                }
            ],
        }
        errors = lint_data(valid_data, root=ROOT)
        self.assertEqual(len(errors), 0)

        # Invalid data (missing assembly and missing instruction)
        invalid_data = {
            "assembly": "",
            "steps": [
                {
                    "id": "step_1",
                    "instruction": "",
                    "checks": [],
                }
            ],
        }
        errors = lint_data(invalid_data, root=ROOT)
        self.assertGreater(len(errors), 0)

    def test_gate_step_validation(self):
        # Gate step hiding earlier work must require checks
        gate_data = {
            "assembly": "Gate Assembly",
            "steps": [
                {
                    "id": "step_1",
                    "instruction": "First check.",
                    "checks": [{"id": "chk_1", "type": "visual", "question": "Ok?"}],
                },
                {
                    "id": "close_cover",
                    "instruction": "Close cover.",
                    "hides": True,
                    "requires": ["chk_1"],
                },
            ],
        }
        errors = lint_data(gate_data, root=ROOT)
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
