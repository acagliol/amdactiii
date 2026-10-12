"""Synthetic images for foundation tests only (temp dir — not assembly photos)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import numpy as np

WIDTH, HEIGHT = 640, 480


def _checkerboard(cell: int, lo: int, hi: int) -> np.ndarray:
    ys, xs = np.mgrid[0:HEIGHT, 0:WIDTH]
    board = np.where(((xs // cell) + (ys // cell)) % 2 == 0, hi, lo).astype(np.uint8)
    return cv2.cvtColor(board, cv2.COLOR_GRAY2BGR)


def write_sharp(name: str, directory: Path | None = None) -> Path:
    directory = directory or Path(tempfile.mkdtemp(prefix="multilond_test_"))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    cv2.imwrite(str(path), _checkerboard(40, 40, 220))
    return path


def write_blurry(name: str, directory: Path | None = None) -> Path:
    directory = directory or Path(tempfile.mkdtemp(prefix="multilond_test_"))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    img = cv2.GaussianBlur(_checkerboard(40, 40, 220), (61, 61), 0)
    cv2.imwrite(str(path), img)
    return path


def write_dark(name: str, directory: Path | None = None) -> Path:
    """Fine cells stay sharp enough so the brightness check is what fails."""
    directory = directory or Path(tempfile.mkdtemp(prefix="multilond_test_"))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    cv2.imwrite(str(path), _checkerboard(8, 5, 55))
    return path
