# Multilönd AI — Build Plan (Oct 13 → 18)

6 people · ~1–3 hours/day each · Cursor / Claude OK · **pick-up backlog** (no fixed roles)  
Repo: `github/` ([acagliol/amdactiii](https://github.com/acagliol/amdactiii.git))  
Deadline: **Oct 18, 2026 ~15:00 UTC** (also 12:00 PM CEST onsite)

---

## TL;DR

**Start local (fake AI), not GPU.** Anyone grabs an open ticket in a free lane. Goal: **2–3 people coding at once** with almost no file conflicts.

Build order (phases, not people):

1. Contract + skeleton  
2. Checklist / checker / fake AI / Worker UI (parallel)  
3. Quality gate + evidence log  
4. Real AMD vLLM  
5. Eval numbers  
6. Demo video + submit  

---

## How the team works (no assigned roles)

### Pick-up rules

1. Open Discord (or a shared note) → look at **Backlog** below.  
2. Claim a ticket: `CLAIM T12` + your name + branch name.  
3. Only touch files listed on that ticket’s **Lane**.  
4. When done: PR / push + `DONE T12` + what to test.  
5. If blocked >20 min, drop it and pick another open ticket (or ask in chat).

### Parallelism rule (avoid conflicts)

At any moment, **at most one person per lane**. That means **2–3 people can always work safely** by picking different lanes. With 6 people, some do non-code tickets (photos, AMD cloud, slides, eval data) while 2–3 code.

| Lane ID | Touch only these paths | Safe to parallel with |
|---------|------------------------|------------------------|
| **L-CONTRACT** | `CONTRACT.md`, `requirements.txt`, `.env.example`, top-level glue | Do this first / alone briefly |
| **L-ASM** | `assemblies/**` | Everything except someone rewriting the same YAML |
| **L-CHECK** | `checker/**` (not `quality.py` if claimed separately) | L-AI, L-APP, L-EVAL, L-DATA |
| **L-QUAL** | `checker/quality.py` + tests for it only | L-AI, L-APP, L-ASM, L-EVAL |
| **L-AI** | `ai_client/**` | L-CHECK, L-APP, L-ASM, L-DATA |
| **L-APP** | `app/**` | L-AI, L-CHECK, L-ASM, L-DATA |
| **L-EVID** | `checker/evidence.py` or `app/db.py` (pick one file in ticket) | Avoid same time as L-CHECK if same file |
| **L-AMD** | docs/scripts under `scripts/` or `docs/amd_*.md` (create if needed) | All code lanes |
| **L-EVAL** | `eval/**` | All except heavy prompt thrash in L-AI |
| **L-DATA** | local `data/` only (gitignored) — photos/videos | Everyone |
| **L-STORY** | pitch, video script, cover, lablab form text (outside code or `/docs`) | Everyone |
| **L-INTEG** | wiring imports, README runbook, deploy | Prefer when others pause / end of day |

**Branch naming:** `t12-fake-ai`, `t08-worker-ui`, etc.  
**PR size:** one ticket ≈ one PR. Don’t “while I’m here” edit another lane.

### Frozen interface (everyone codes against this)

Put in repo as `CONTRACT.md` early (ticket T01). Do not change after Wed without a chat agree.

```python
# Model / fake AI returns:
{
  "verdict": "yes" | "no" | "cant_tell",
  "reason": str,
  "problem_box": [ymin, xmin, ymax, xmax] | None
}

# Checker returns to UI:
{
  "action": "pass" | "fix" | "retake" | "supervisor",
  "reason": str,
  "problem_box": list | None,
  "hint": str | None
}
```

Env:

- `USE_FAKE_AI=true|false`
- `VLLM_BASE_URL=http://localhost:8000/v1`
- `VLLM_MODEL=...`

---

## Capacity

| | Low | Mid | High |
|--|-----|-----|------|
| Team hours/day | ~6 | ~12 | ~18 |
| Build days (13→17) | ~5 | | |
| Total | ~30 | ~60 | ~90 |

Plan for ~60h. Nice-to-haves only after Worker loop demos on fake AI.

---

## Must ship vs later

### Must ship

- [ ] `assemblies/pc_build.yaml` — 4–6 visual checks + gated close-panel  
- [ ] Pass / Fix / Retake / supervisor-after-3-retakes  
- [ ] Streamlit Worker (upload or camera, badge, bbox)  
- [ ] Fake AI always works  
- [ ] Real AMD vLLM path in the product  
- [ ] Evidence log (SQLite + frames)  
- [ ] README that runs  
- [ ] Live demo URL  
- [ ] Video ≤5 min + pitch PDF + cover 16:9  
- [ ] Small eval + catch / false-alarm numbers  

### Later (only if must is green)

Manager / supervisor / exec dashboards · more assemblies · 1fps live motion · Evolus/Google extras · heavy polish  

---

## Backlog (claim these)

Status: `OPEN` → `CLAIMED` → `DONE` · Update in Discord; optionally tick here.

### Phase A — unblock everyone (do first, ~1–2 people)

| ID | Ticket | Lane | Depends | Est |
|----|--------|------|---------|-----|
| T01 | Write `CONTRACT.md` + env vars list | L-CONTRACT | — | 30m |
| T02 | `requirements.txt` + venv instructions in README | L-CONTRACT | — | 30m |
| T03 | Package stubs: `__init__.py` in app/checker/ai_client | L-INTEG | T01 | 20m |

**Phase A done when:** clone → venv → pip install works.

### Phase B — three parallel tracks (target: 3 people at once)

| ID | Ticket | Lane | Depends | Est |
|----|--------|------|---------|-----|
| T10 | Author `assemblies/pc_build.yaml` (3 checks + panel gate) | L-ASM | T01 | 1h |
| T11 | YAML loader `checker/loader.py` | L-CHECK | T01 | 1h |
| T12 | Step engine: current step, requires, unlock next | L-CHECK | T11 | 1–2h |
| T13 | Agreement table → pass/fix/retake/supervisor | L-CHECK | T12 | 1h |
| T20 | `ai_client/fake_ai.py` (canned + filename keywords `_bad_` `_blur_`) | L-AI | T01 | 1h |
| T21 | `ai_client/client.py` switch on `USE_FAKE_AI` | L-AI | T20 | 45m |
| T22 | Prompt + strict JSON parse helpers (even if fake-only first) | L-AI | T21 | 1h |
| T30 | Streamlit Worker shell: show step + upload + Check button | L-APP | T01 | 1–2h |
| T31 | Wire Worker → checker → show badge | L-APP | T12, T21, T30 | 1h |
| T32 | Draw bbox overlay on result image | L-APP | T31 | 45m |

**Best simultaneous set:** `T10` + `T20` + `T30` (three lanes, zero overlap).  
Then: `T11/T12` + `T21` + `T31`.

**Phase B done when:** `USE_FAKE_AI=true streamlit run app/main.py` completes one fake check.

### Phase C — make the demo story real (still parallel)

| ID | Ticket | Lane | Depends | Est |
|----|--------|------|---------|-----|
| T40 | OpenCV quality gate `checker/quality.py` | L-QUAL | T01 | 1–2h |
| T41 | Hook quality gate before AI call | L-CHECK or L-INTEG | T40, T12 | 45m |
| T42 | Expand YAML to 4–6 checks (still one assembly) | L-ASM | T10 | 1h |
| T43 | Override with written reason + unlock | L-APP | T31 | 45m |
| T44 | Evidence log SQLite + save frame | L-EVID | T31 | 1–2h |
| T45 | Shoot 20–30 photos good/bad/blurry into local `data/frames/` | L-DATA | — | 1–2h |
| T46 | Fake AI responds correctly to those filenames | L-AI | T20, T45 | 45m |

**Good 3-person combo:** `T40` + `T44` + `T45`, or `T42` + `T43` + `T46`.

**Phase C done when:** full fake walkthrough: pass → blocked panel → fix → unlock → logged.

### Phase D — AMD (one person cloud, others keep shipping)

| ID | Ticket | Lane | Depends | Est |
|----|--------|------|---------|-----|
| T50 | AMD cloud instance up + notes (`docs/amd_setup.md`) | L-AMD | — | 1–3h |
| T51 | vLLM serve vision model on `:8000` | L-AMD | T50 | 1–2h |
| T52 | SSH tunnel instructions in README | L-AMD | T51 | 30m |
| T53 | Real OpenAI-compatible client + timeout + fallback to fake | L-AI | T21, T51 | 1–2h |
| T54 | `.env.example` only (no secrets) | L-CONTRACT | T53 | 20m |
| T55 | Prove one real inference from Worker UI | L-INTEG | T53, T31 | 1h |

**While T50–T52 run:** others take T40–T46 or T60+.

**Phase D done when:** real GPU check works once; fake still works offline.

### Phase E — eval + harden

| ID | Ticket | Lane | Depends | Est |
|----|--------|------|---------|-----|
| T60 | `eval/answer_key.csv` from collected frames | L-EVAL | T45 | 1h |
| T61 | `eval/evaluate.py` → catch / false-alarm / latency | L-EVAL | T60, T12 | 1–2h |
| T62 | Prompt harden on planted mistakes | L-AI | T53, T60 | 1–2h |
| T63 | Deploy demo host + cold-start README | L-INTEG | Phase C | 1–2h |
| T64 | Demo script (3 min spoken) | L-STORY | Phase C | 45m |
| T65 | UI bugfix only (big badge, retake hint) | L-APP | T31 | 1h |

**KPI aspire:** catch ≥90% planted · false alarm ≤10% clean · latency <5s on MI300X.

### Phase F — ship

| ID | Ticket | Lane | Depends | Est |
|----|--------|------|---------|-----|
| T70 | Record demo video ≤5 min | L-STORY | T64, T55 | 2h |
| T71 | Pitch PDF + cover 16:9 | L-STORY | T64 | 1–2h |
| T72 | Fill lablab submission draft | L-STORY | T63 | 1h |
| T73 | Feature freeze + bug bash (P0 only) | any lane | Sat noon | ongoing |
| T74 | Final submit before deadline | L-STORY | T70–T72 | 30m |

---

## Day board (what should be open)

### Tue Oct 13

- Unblock: **T01–T03**  
- Then run **3 parallel:** T10 + T20 + T30  
- Stretch: T11, T21  

**Exit:** one fake check in UI.

### Wed Oct 14

- Open: T12, T13, T31, T32, T40, T45  
- Keep 2–3 coding lanes full; others shoot photos (T45)

**Exit:** full fake assembly path + gate.

### Thu Oct 15

- Start AMD: T50–T52 (1 person)  
- Parallel: T44, T46, T42, T43, T53 when API ready  

**Exit:** ≥1 real GPU inference; evidence logging.

### Fri Oct 16

- Open: T60–T65  
- Freeze YAML contents (T42 done — stop editing unless P0)

**Exit:** KPI numbers + deploy + demo script.

### Sat Oct 17

- **Noon: feature freeze** (T73)  
- T70–T72  

**Exit:** video + form 90% ready.

### Sun Oct 18

- Morning smoke test → **T74 submit early**  
- Do not plan on the 6h manual late window  

---

## Example: 3 people online at once

| Person | Claims | Lane |
|--------|--------|------|
| A | T20 fake AI | L-AI |
| B | T30 Worker shell | L-APP |
| C | T10 YAML checklist | L-ASM |

Next hour:

| Person | Claims | Lane |
|--------|--------|------|
| A | T21 client switch | L-AI |
| B | waits or does T45 photos | L-DATA |
| C | T11 loader | L-CHECK |

Next:

| A | T40 quality | L-QUAL |
| B | T31 wire UI | L-APP |
| C | T12 engine | L-CHECK |

Nobody edits the same file.

---

## Cursor / Claude prompt (paste every session)

> Multilönd AI, AMD ACT III. I claimed ticket **T__**. I may only edit: **[lane paths]**. Honor `CONTRACT.md`. Keep `USE_FAKE_AI` working. Small PR, no refactors outside my files, no new frameworks.

**Don’t:** rewrite architecture · add FastAPI/React · start Manager dashboard before Phase C green · edit two lanes in one PR.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Merge hell | One lane per person; small PRs; L-INTEG at end of day |
| GPU late | Fake path is the demo backup; AMD tickets start Thu latest |
| Flaky JSON | Parse fail → retake; agreement table |
| Scope creep | Nice-to-have list is closed until must-ship checkboxes are done |
| Idle people | Always T45/T60/T64/T71 non-code tickets available |

---

## Demo-ready checklist

1. Fresh clone + README install works  
2. Fake mode full story offline  
3. Real AMD call in recorded demo  
4. Planted mistake → red box + reason  
5. Panel gated until prerequisites pass  
6. Evidence row for that unit  
7. 30s pitch: user, value, why AMD  

---

## Claim board (copy to Discord)

```
OPEN: T01 T02 T03 T10 T11 T12 T13 T20 T21 T22 T30 T31 T32 T40 T41 T42 T43 T44 T45 T46 T50 T51 T52 T53 T54 T55 T60 T61 T62 T63 T64 T65 T70 T71 T72 T73 T74

CLAIMED:
(none)

DONE:
(none)
```

---

## Bottom line

**No fixed roles** — claim tickets.  
**2–3 coders in parallel** = different lanes (ASM / AI / APP is the default trio).  
**Start now:** T01–T03, then T10 + T20 + T30.  
**AMD by Thu · freeze Sat noon · submit Sun morning.**
