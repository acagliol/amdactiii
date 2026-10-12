# Multilönd AI — Shared Contract

Frozen shapes for parallel work. Change only with team agree after Wed.

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `USE_FAKE_AI` | `true` | Use mock vision client (no GPU) |
| `VLLM_BASE_URL` | `http://localhost:8000/v1` | OpenAI-compatible vLLM endpoint |
| `VLLM_MODEL` | `google/gemma-4-26b-a4b-it` | Model id served by vLLM |

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

Foundation uses **one look** for simplicity; double-look can wrap the same client later.

## Lanes (avoid merge conflicts)

| Lane | Paths |
|------|-------|
| L-ASM | `assemblies/**` |
| L-CHECK | `checker/**` |
| L-AI | `ai_client/**` |
| L-APP | `app/**` |
| L-EVAL | `eval/**` |
