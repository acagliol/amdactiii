"""Vision look entrypoint. Switches fake vs real vLLM via USE_FAKE_AI."""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def _flag(name: str, default: str) -> bool:
    value = os.getenv(name, default).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false.")


def _settings() -> dict[str, Any]:
    base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1").strip().rstrip("/")
    try:
        url = urlsplit(base_url)
        port = url.port
        valid = (
            url.scheme in {"http", "https"} and url.hostname
            and not url.query and not url.fragment and not url.username and not url.password
            and (port is None or 1 <= port <= 65535)
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("VLLM_BASE_URL must be a valid HTTP(S) URL.")
    model = os.getenv("VLLM_MODEL", "google/gemma-4-26b-a4b-it").strip()
    if not model:
        raise ValueError("VLLM_MODEL must name the served vision model.")
    try:
        timeout = float(os.getenv("VLLM_TIMEOUT_SECONDS", "10"))
    except ValueError:
        raise ValueError("VLLM_TIMEOUT_SECONDS must be a positive number.") from None
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("VLLM_TIMEOUT_SECONDS must be a positive number.")
    return {
        "base_url": base_url,
        "model": model,
        "api_key": os.getenv("VLLM_API_KEY", "EMPTY").strip() or "EMPTY",
        "timeout": timeout,
    }


def _cant_tell(reason: str) -> dict[str, Any]:
    return {"verdict": "cant_tell", "reason": reason, "problem_box": None}


def look(image_path: str | Path, question: str) -> dict[str, Any]:
    try:
        use_fake = _flag("USE_FAKE_AI", "true")
    except ValueError as exc:
        return _cant_tell(f"Configuration error: {exc}")
    if use_fake:
        from .fake_ai import look as fake_look

        return fake_look(image_path, question)

    try:
        settings = _settings()
        fallback = _flag("VLLM_FALLBACK_TO_FAKE", "false")
    except ValueError as exc:
        return _cant_tell(f"Configuration error: {exc}")

    from .vllm import VLLMUnavailable, look as real_look

    try:
        return real_look(image_path, question, **settings)
    except VLLMUnavailable as exc:
        if fallback:
            from .fake_ai import look as fake_look

            result = fake_look(image_path, question)
            result["reason"] = f"DEMO FALLBACK ({exc}): {result['reason']}"
            return result
        return _cant_tell(str(exc))
