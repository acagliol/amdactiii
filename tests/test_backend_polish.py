"""Non-ASCII frame paths and oversized photos (backend polish)."""

import base64
import io
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from ai_client.vllm import MAX_SIDE_PX, _image_url
from checker.lint import lint_data
from checker.quality import assess_quality


def _sharp(size: tuple[int, int]) -> Image.Image:
    rng = np.random.default_rng(0)
    return Image.fromarray(rng.integers(40, 220, (size[1], size[0], 3), dtype=np.uint8))


class BackendPolishTests(unittest.TestCase):
    def test_quality_reads_non_ascii_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "檢查_frame.png"
            _sharp((400, 300)).save(path)
            self.assertTrue(assess_quality(path)["ok"])

    def test_quality_missing_file_asks_for_retake(self):
        result = assess_quality(Path(tempfile.gettempdir()) / "nope_missing.png")
        self.assertFalse(result["ok"])
        self.assertIn("Could not read", result["hint"])

    def test_large_photo_is_downscaled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "big.png"
            _sharp((4000, 3000)).save(path)
            url = _image_url(path)
            self.assertTrue(url.startswith("data:image/jpeg;base64,"))
            with Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))) as img:
                self.assertEqual(max(img.size), MAX_SIDE_PX)

    def test_small_photo_sent_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "small.png"
            _sharp((640, 480)).save(path)
            self.assertEqual(_image_url(path).split(",", 1)[1], base64.b64encode(path.read_bytes()).decode())


    def test_lint_reports_malformed_shapes_instead_of_crashing(self):
        self.assertEqual(lint_data({"assembly": "x", "steps": "oops"}), ["'steps' must be a list"])
        errors = lint_data({"assembly": "x", "steps": ["just text", {"id": "s", "instruction": "i", "checks": ["c"]}]})
        self.assertTrue(any("must be a mapping" in e for e in errors))
        self.assertTrue(any("each check must be a mapping" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
