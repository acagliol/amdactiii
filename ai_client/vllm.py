"""Single-image vLLM request and strict inspection-result validation."""

from __future__ import annotations

import base64
import io
import json
import math
import re
from pathlib import Path
from typing import Any

from openai import APIConnectionError, APIResponseValidationError, APIStatusError, APITimeoutError, OpenAI
from PIL import Image

PROMPT = """Inspect only the requested assembly check using the photo.
Return one JSON object with exactly these fields:
{"verdict": "yes|no|cant_tell", "reason": "short explanation", "problem_box": null}
Use yes only when the check is visibly satisfied, no for a visible defect,
and cant_tell when the image cannot establish the answer. Never guess.
For no, problem_box may be [ymin, xmin, ymax, xmax] in normalized 0-1000
coordinates if the defect can be located; otherwise null.
For yes or cant_tell, problem_box must be null. Return no other text.

Assembly guidance:
- Judge only what the question asks (e.g. clips seated, connector fully plugged).
- Partial seating, open latches, missing fasteners, wrong orientation → no.
- Motion blur, heavy glare, occlusion, or off-frame subject → cant_tell.
- Do not invent parts that are not visible. Keep reason under 25 words."""


class VLLMUnavailable(RuntimeError):
    """A connection, timeout, or server failure eligible for demo fallback."""


def _cant_tell(reason: str) -> dict[str, Any]:
    return {"verdict": "cant_tell", "reason": reason, "problem_box": None}


def _unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON fields.")
        result[key] = value
    return result


def parse_result(text: str) -> dict[str, Any]:
    """Validate one JSON object, optionally wrapped in a JSON code fence."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Empty inspection response.")
    text = text.strip()
    if text.startswith("```"):
        fence = re.fullmatch(r"```(?:json)?[ \t]*\r?\n(.*?)\r?\n```", text, re.DOTALL)
        if not fence:
            raise ValueError("Expected one JSON object.")
        text = fence.group(1)
    try:
        data = json.loads(text, object_pairs_hook=_unique_fields)
    except json.JSONDecodeError:
        raise ValueError("Malformed inspection JSON.") from None
    if not isinstance(data, dict) or set(data) != {"verdict", "reason", "problem_box"}:
        raise ValueError("Expected verdict, reason, and problem_box fields.")
    if not isinstance(data["verdict"], str) or data["verdict"] not in {"yes", "no", "cant_tell"}:
        raise ValueError("Invalid inspection verdict.")
    if not isinstance(data["reason"], str) or not data["reason"].strip():
        raise ValueError("Expected a nonempty inspection reason.")
    box = data["problem_box"]
    if box is not None:
        if data["verdict"] != "no":
            raise ValueError("Only a no verdict may include a problem box.")
        if not isinstance(box, list) or len(box) != 4 or not all(
            type(value) in {int, float} and 0 <= value <= 1000 and math.isfinite(value)
            for value in box
        ):
            raise ValueError("Expected four finite coordinates within 0-1000.")
        ymin, xmin, ymax, xmax = box
        if ymin >= ymax or xmin >= xmax:
            raise ValueError("Problem box must have positive width and height.")
    return {"verdict": data["verdict"], "reason": data["reason"].strip(), "problem_box": box}


def _image_url(image_path: str | Path) -> str:
    data = Path(image_path).read_bytes()
    with Image.open(io.BytesIO(data)) as image:
        mime = {"JPEG": "image/jpeg", "PNG": "image/png"}.get(image.format)
        if mime is None:
            raise ValueError("Use a JPEG or PNG image.")
        image.verify()
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def look(
    image_path: str | Path,
    question: str,
    *,
    base_url: str,
    model: str,
    api_key: str,
    timeout: float,
) -> dict[str, Any]:
    """Inspect one frame; return uncertainty for expected input or API failures."""
    if not isinstance(question, str) or not question.strip():
        return _cant_tell("Inspection question is empty.")
    try:
        image_url = _image_url(image_path)
    except (OSError, ValueError, SyntaxError):
        return _cant_tell("Could not read a JPEG/PNG inspection image.")
    try:
        with OpenAI(base_url=base_url, api_key=api_key, timeout=timeout, max_retries=0) as client:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ]},
                ],
                temperature=0,
                max_tokens=256,
            )
    except APITimeoutError:
        raise VLLMUnavailable("vLLM request timed out; retry this check.") from None
    except APIConnectionError:
        raise VLLMUnavailable("Cannot reach vLLM; check the endpoint and SSH tunnel.") from None
    except APIStatusError as exc:
        if exc.status_code >= 500:
            raise VLLMUnavailable(f"vLLM server is unavailable (HTTP {exc.status_code}).") from None
        if exc.status_code in {401, 403}:
            return _cant_tell("vLLM authentication failed; check VLLM_API_KEY.")
        if exc.status_code == 404:
            return _cant_tell("vLLM endpoint or model was not found; check VLLM_BASE_URL and VLLM_MODEL.")
        if exc.status_code == 429:
            return _cant_tell("vLLM server is busy; retry this check.")
        return _cant_tell(f"vLLM rejected the request (HTTP {exc.status_code}); check its vision configuration.")
    except (APIResponseValidationError, json.JSONDecodeError):
        return _cant_tell("vLLM returned an invalid completion response.")
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or not choices or getattr(choices[0], "finish_reason", None) != "stop":
        return _cant_tell("vLLM returned an incomplete or empty response.")
    message = getattr(choices[0], "message", None)
    if getattr(message, "refusal", None):
        return _cant_tell("vLLM could not answer this inspection.")
    try:
        return parse_result(getattr(message, "content", None))
    except ValueError as exc:
        return _cant_tell(f"Invalid vLLM response: {exc}")
