# Tests

Foundation tests live under `tests/foundation/`. They only cover shared contracts (loader, quality gate, session, fake AI). They do **not** edit `app/`, `ai_client/` (beyond calling), or other people’s lanes.

```bash
# from repo root
python tests/foundation/run_all.py
python -m unittest discover -s tests -v  # AI client, evidence storage, and Worker UI
python -m unittest tests.test_evidence_reader -v  # Dashboard queries and evidence panel
```

These tests use **synthetic** sharp/blur/dark images in a temp folder. They prove the pipeline wiring.

AI client tests serialize requests through the real SDK with an in-memory HTTP transport; no GPU or network is needed.

Put **real assembly phone photos** in `data/frames/` for demos (gitignored). Fake AI still keys off filenames (`_ok_`, `_bad_`). Real vision needs `USE_FAKE_AI=false` + AMD vLLM.
