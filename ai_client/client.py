"""Vision look entrypoint. Switches fake vs real vLLM via USE_FAKE_AI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def look(image_path: str | Path, question: str) -> dict[str, Any]:
    use_fake = os.getenv("USE_FAKE_AI", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if use_fake:
        from .fake_ai import look as fake_look

        return fake_look(image_path, question)

    # Real path lands in a later ticket (T53). Fail clearly for now.
    raise NotImplementedError(
        "Real vLLM client not wired yet. Set USE_FAKE_AI=true "
        "or implement ai_client against VLLM_BASE_URL."
    )
