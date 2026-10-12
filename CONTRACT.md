# Multilönd AI — Shared Contract

Frozen shapes for parallel work. Change only with team agree after Wed.

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `USE_FAKE_AI` | `true` | Use mock vision client (no GPU) |
| `VLLM_BASE_URL` | `http://localhost:8000/v1` | OpenAI-compatible vLLM endpoint |
| `VLLM_MODEL` | `google/gemma-4-26b-a4b-it` | Model id served by vLLM |
| `VLLM_API_KEY` | `EMPTY` | Local placeholder; replace for an authenticated server |
| `VLLM_TIMEOUT_SECONDS` | `10` | Request timeout; automatic retries disabled |
| `VLLM_FALLBACK_TO_FAKE` | `false` | Demo fallback on connection, timeout, or HTTP 5xx; reason starts with `DEMO FALLBACK` |
| `VLLM_DOUBLE_LOOK` | `false` | Two real vLLM looks + `agreement.reconcile` (yes/yes, no/no, else cant_tell) |

## AI look result (`ai_client`)

```python
{
  "verdict": "yes" | "no" | "cant_tell",
  "reason": str,
  "problem_box": [ymin, xmin, ymax, xmax] | None,  # normalized 0–1000 or None
}
```

## Checker action (`checker` → UI)

```python
{
  "action": "pass" | "fix" | "retake" | "supervisor",
  "reason": str,
  "problem_box": list | None,
  "hint": str | None,
  "step_id": str,
  "check_id": str,
}
```

## Agreement rules

| Look A | Look B | Action |
|--------|--------|--------|
| yes | yes | pass |
| no | no | fix |
| disagree / cant_tell | any | retake |
| 3 retakes in a row | — | supervisor |

Default is **one look**. Set `VLLM_DOUBLE_LOOK=true` to run two real looks and reconcile in `ai_client/agreement.py` before the checker sees the result.

## Lanes (avoid merge conflicts)

| Lane | Paths |
|------|-------|
| L-ASM | `assemblies/**` |
| L-CHECK | `checker/**` |
| L-AI | `ai_client/**` |
| L-APP | `app/**` |
| L-EVAL | `eval/**` |
