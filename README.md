# Multilönd AI

> **Catching hidden assembly mistakes while they are still visible.**  
> *AMD Developer Hackathon: ACT III · Track: Intelligent Industry*

---

## 📌 Executive Summary & One-Line Pitch

> *"In hand assembly, some mistakes get hidden by the next step, and catching them later costs 10 to 100 times more. Multilönd AI checks those steps while they are still visible, and keeps photo proof for every unit."*

**Multilönd AI** is an intelligent vision assistant for manual assembly lines. By watching the workstation through a standard camera, local edge checks (OpenCV) filter frames, while an open multimodal vision model (Gemma 4 / Qwen-VL) running on an **AMD Instinct™ MI300X GPU (via ROCm & vLLM)** inspects assembly steps in near real-time, pinpointing defects with visual grounding (bounding boxes) and blocking subsequent "cover-up" steps until defects are resolved.

---

## ⚠️ The Problem: The 1–10–100 Rule

In factories where humans assemble products by hand (electronics, appliances, machinery), internal connections and fasteners are frequently covered up by housings, brackets, or side panels in subsequent steps.

```
Workstation (while visible)       Final Factory Test (teardown)      Customer Warranty / Recall
         [$1 to fix]             ───►         [$10 to fix]         ───►         [$100+ to fix]
```

### Typical Hand-Assembly Mistakes
- Connector not fully clicked in or latch unengaged
- Missing parts: screws, clips, washers, thermal pads, rubber seals
- Wrong part installed (e.g., identical-looking connectors or screws)
- Reverse orientation (flipped connectors, upside-down components)
- Pinched cables or wires touching sharp chassis edges / fans
- Protective plastic peel stickers left on heatsinks / thermal interfaces

### Why Current Solutions Fall Short
- **Paper / Tablet Checklists:** Workers check boxes out of habit; leaves no visual proof.
- **Supervisors:** Cannot oversee every station and unit 100% of the time.
- **End-of-line Electrical Tests:** Miss latent defects (e.g., a half-seated plug that passes test today but vibrates loose in customer homes).
- **Custom AOI (Automated Optical Inspection) Machines:** Expensive ($50k–$200k+), rigid, require dedicated vision engineers, and cannot adapt to multi-product lines.

---

## 💡 How Multilönd AI Works

1. **Non-Intrusive Workflow:** The camera runs above the workstation. The worker builds naturally without stopping to press buttons on every motion.
2. **Edge Motion & Quality Filter (OpenCV on Laptop):** Grabs ~1 frame per second. Skips frames with rapid motion blur, hand occlusions, or low lighting before contacting the GPU.
3. **Multimodal Inspection (vLLM on AMD MI300X):** Sends crisp frames alongside step checklist instructions and reference images to the vision model.
4. **Visual Grounding:** The model pinpoints errors and returns bounding box coordinates (`problem_box: [ymin, xmin, ymax, xmax]`) with clear explanations.
5. **Deterministic Logic: "The Model Only Looks, Python Decides":**
   Strict deterministic agreement logic prevents hallucinations and maintains predictable behavior:

| Answer 1 | Answer 2 | Result | Action |
|:---|:---|:---|:---|
| **yes** | **yes** | **Pass** | Unlocks the next assembly step |
| **no** | **no** | **Fix it** | Displays red bounding box on exact defect + reason |
| **Disagree** or **"can't tell"** | Any | **Retake** | Displays camera framing/lighting hint to the worker |
| **3 Retakes in a row** | - | **Supervisor Alert** | Requires manual override with written justification |

6. **Gated Checkpoints:** The system explicitly gates "hiding steps" (e.g., closing the chassis panel or installing a cover) until all critical prerequisites are verified and logged.
7. **Evidence Log:** Each check attempt's photo, unit ID, timestamp, and verdict are stored locally (SQLite + frames).

---

## 👥 Personas: Who Sees What

| Role | Interface | Key Functions |
|:---|:---|:---|
| **Worker** | **Worker Screen** | Step-by-step guidance, live feedback badge (**Pass**, **Fix it**, **Retake**), red bounding boxes on defects, override option. |
| **Supervisor** | **Supervisor Portal** | Real-time alerts for repeated retakes or overrides; interactive setup mode to author new YAML checklists in plain English. |
| **Quality Manager / COO** | **Manager Dashboard** | First-Pass Yield (FPY), failure trends by shift/station, searchable photo audit trail by unit serial number. |
| **Executive / CEO** | **Executive Summary** | Defect prevention counts, estimated warranty dollars saved, line rollout recommendations. |

> *Ethical Design Note:* Camera frames focus strictly on the workstation and component surface—never worker faces. Metrics are designed for worker coaching and process improvement, not punitive monitoring.

---

## 🏗️ System Architecture

```
┌───────────────────────────────────────────┐         Private Encrypted SSH Tunnel
│      Edge Workstation (Laptop / PC)       │        ┌────────────────────────────┐
│                                           │        │                            │
│  ┌──────────────┐      ┌───────────────┐  │        │   ┌────────────────────┐   │
│  │  Webcam /    │ ───► │ OpenCV Quality│  │        │   │ vLLM Inference Svr │   │
│  │ Mobile Feed  │      │  Gate Filter  │  │        │   │ (OpenAI-compatible)│   │
│  └──────────────┘      └───────┬───────┘  │        │   └─────────┬──────────┘   │
│                                │ frame    │        │             │              │
│  ┌──────────────┐      ┌───────▼───────┐  │ HTTP   │   ┌─────────▼──────────┐   │
│  │  Streamlit   │ ◄─── │  Step Checker │ ─┼────────┼──►│  Gemma 4 Vision /  │   │
│  │Worker/Manager│      │ (Python Logic)│  │ :8000  │   │      Qwen-VL       │   │
│  └──────────────┘      └───────┬───────┘  │        │   └────────────────────┘   │
│                                │ log      │        │                            │
│                        ┌───────▼───────┐  │        │   ┌────────────────────┐   │
│                        │ Evidence Log  │  │        │   │  AMD Instinct™     │   │
│                        │SQLite + Photos│  │        │   │  MI300X (192 GB)   │   │
│                        └───────────────┘  │        │   │    ROCm Platform   │   │
│                                           │        │   └────────────────────┘   │
└───────────────────────────────────────────┘        └────────────────────────────┘
                                                      AMD Developer Cloud
```

---

## 🚀 Why AMD Instinct™ & Open Models?

1. **Factory Privacy & Data Sovereignty:** Factory photos depict proprietary, unreleased intellectual property. Running open weights on private AMD hardware ensures photos never leak to public commercial APIs.
2. **Massive Unified Memory (192 GB VRAM):** The AMD Instinct™ MI300X accommodates large high-resolution vision-language models on a single GPU without aggressive quantization.
3. **High-Throughput Batch Inference:** ROCm + vLLM enables high concurrency, scoring batch evaluation sets in minutes.
4. **Predictable On-Premise Costs:** Flat hardware operating cost replaces variable per-token API billing.

---

## 📂 Repository Structure

```text
amdactiii/
├── app/                  # Streamlit application: Worker screen & Manager dashboard
├── checker/              # Core step logic, checklist loader, OpenCV photo quality checks
├── ai_client/            # vLLM integration for AMD MI300X (+ fake_ai.py for Day 1 development)
├── assemblies/           # Declarative assembly checklists (e.g., pc_build.yaml)
├── eval/                 # Evaluation harness, test runner, and answer_key.csv
├── data/                 # Video recordings and extracted test frames (git-ignored)
│   ├── frames/
│   └── recordings/
├── .gitignore            # Excludes local virtual environments, cache, and raw data
└── README.md             # Project documentation and hackathon blueprint
```

---

## ⚙️ Quickstart & Development

### 1. Prerequisites
- Python 3.10+
- Webcam or phone camera stream
- (Optional for local testing) AMD Developer Cloud access with MI300X GPU & ROCm

### 2. Environment Setup
```bash
git clone https://github.com/acagliol/amdactiii.git
cd amdactiii
python3 -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional; USE_FAKE_AI defaults to true
```

Shared shapes for parallel work: see [`CONTRACT.md`](./CONTRACT.md).

### Local evidence log (T44)

Every check attempt saves its original photo and a SQLite row, including failed
checks and retakes. The row contains unit/assembly/step/check IDs, a UTC timestamp,
AI verdict, checker action, reason, bounding box, and hint. Prerequisite- or
quality-blocked attempts have a null verdict. Completed sessions add no record.

- Database: `data/evidence/evidence.sqlite3`
- Photos: `data/evidence/frames/<attempt-id>.<extension>`
- Paths in SQLite are relative to `data/evidence/`; this folder is gitignored.
- Each unit gets a stable generated ID, shown in the Worker UI. **Start new unit**
  creates a new ID. A serial can be entered before the first attempt; it is then
  locked for that unit. Code callers can provide `Session(..., unit_id="SERIAL-123")`.
- Storage must succeed before checker state changes. On failure, retry the check.

Inspect recent attempts from the repo root (requires the SQLite CLI):

```bash
sqlite3 -header -column data/evidence/evidence.sqlite3 \
  "SELECT unit_id, check_id, timestamp, verdict, action, frame_path FROM evidence ORDER BY rowid DESC LIMIT 10;"
```

Run tests after installing `requirements.txt`:

```bash
python -m unittest discover -s tests -v
python tests/foundation/run_all.py
```

Tests use temporary storage, image files, Streamlit AppTest, and the real AI SDK
with an in-memory HTTP transport. They cover evidence, checker/UI behavior,
request payloads, configuration, and API failures without a GPU or network.

This is a local audit log, not tamper-proof storage. A hard crash between copying
a photo and committing SQLite can leave an unreferenced photo. Saved evidence
survives app restarts; in-progress checker sessions do not resume automatically.

Manager/CEO pages can use the read-only `EvidenceReader` for filtered records,
photo paths, and attempt counts. See [Tiff's integration handoff](docs/dashboard_evidence.md).

### 3. Day 1 Zero-GPU Testing (`fake_ai.py`)
No waiting for GPU provisioning! Test core logic, then the UI:

```bash
# Foundation tests (loader, quality gate, session, fake AI) — see tests/README.md
set USE_FAKE_AI=true          # Windows PowerShell: $env:USE_FAKE_AI='true'
python tests/foundation/run_all.py

# Worker UI — for demos, put real phone photos in data/frames/
# With fake AI, filenames still drive verdicts: *_ok_*, *_bad_*, *_blur_*
streamlit run app/main.py
```

### 4. Running with AMD Developer Cloud (MI300X + vLLM)
The client is implemented; live GPU inference and model compatibility are still
pending validation (T55). Confirm the vision model with the GPU owner before
using the existing example below.

On the remote AMD MI300X instance:
```bash
# Launch vLLM with Gemma 4 Vision on localhost
vllm serve google/gemma-4-26b-a4b-it \
    --host 127.0.0.1 \
    --port 8000 \
    --trust-remote-code
```

On your local workstation, open an encrypted SSH tunnel:
```bash
ssh -L 8000:127.0.0.1:8000 user@<AMD_CLOUD_IP>
```

The client loads `.env` from the repository root, even from another working
directory. Shell variables take precedence. Restart the app after editing `.env`.
Copy `.env.example`, then set `USE_FAKE_AI=false` and `VLLM_MODEL` to the model
served by vLLM. Keep `/v1` in `VLLM_BASE_URL`. `VLLM_API_KEY=EMPTY` is a local
placeholder; replace it if the server requires authentication.

Set environment variables and run:
```bash
export USE_FAKE_AI=false
export VLLM_BASE_URL="http://localhost:8000/v1"
streamlit run app/main.py
```

To check one photo directly from the repository root:

```bash
USE_FAKE_AI=false python - <<'PY'
from ai_client import look
print(look("data/frames/ram_ok_01.jpg", "Are both RAM clips closed?"))
PY
```

Requests use `VLLM_TIMEOUT_SECONDS=10` with no automatic retries. Expected input,
configuration, API, and response errors return `cant_tell`, so the checker asks
for a retake. `VLLM_FALLBACK_TO_FAKE=true` enables demo fallback only for connection,
timeout, or HTTP 5xx failures. Its reason starts with `DEMO FALLBACK` in both the
UI and evidence log; leave it disabled for real inspections.

Optional: `VLLM_DOUBLE_LOOK=true` runs **two** real looks and reconciles them
(`yes`/`yes` → pass, `no`/`no` → defect, otherwise `cant_tell`). Default is off
(one look) to keep latency low.

More detail: [`docs/amd_setup.md`](./docs/amd_setup.md) · demo spoken flow: [`docs/DEMO_SCRIPT.md`](./docs/DEMO_SCRIPT.md).

---

## 📋 Checklist Definition (`assemblies/`)

Checklists are defined declaratively in YAML. Example snippet from `assemblies/pc_build.yaml`:

```yaml
assembly: "PC build"
steps:
  - id: "ram"
    instruction: "Insert RAM module into slot A2 until both clips snap shut."
    checks:
      - id: "ram_clips"
        type: "visual"
        question: "Are both white clips at the ends of the RAM stick closed against the stick?"
        show: "Point camera at RAM slot, ~20 cm away."
        reference_photo: "refs/ram_clips_ok.jpg"

  - id: "close_panel"
    instruction: "Close the side panel."
    requires: ["ram_clips", "gpu_power"]  # Blocked until prerequisite checks pass

  - id: "panel_screws"
    instruction: "Tighten side panel thumbscrews."
    checks:
      - id: "screw_tightness"
        type: "manual"  # Physical sensation check confirmed by technician
        question: "Panel screws tightened firmly."
```

---

## 📊 Evaluation & Verification (`eval/`)

Testing is performed against a benchmark suite with known ground truth (`eval/answer_key.csv`):
- **10 Correct Runs** (clean assemblies)
- **10 Planted Mistakes** (open RAM clips, unplugged GPU power, misseated cables)
- **10 Degraded Quality Photos** (blurs, extreme glare, out-of-frame -> expected verdict: `can't tell`)

### Target Key Performance Indicators (KPIs)
- **Defect Catch Rate:** $\ge 90\%$ (at least 9 / 10 planted errors flagged)
- **False Alarm Rate:** $\le 10\%$ (no more than 1 / 10 correct assemblies flagged)
- **Check Latency:** $< 5$ seconds on AMD MI300X
- **Retake Handling:** Clear guidance provided on ambiguous / poor-quality frames

Run evaluation:
```bash
python eval/evaluate.py --checklist assemblies/pc_build.yaml --data eval/answer_key.csv
```

---

## 🏆 Hackathon Details

- **Event:** AMD Developer Hackathon: ACT III
- **Track:** Intelligent Industry
- **Timeline:** October 12 – 18, 2026
- **Stack:** Python, Streamlit, OpenCV, SQLite, vLLM, ROCm, AMD Instinct™ MI300X, Gemma 4 Vision / Qwen-VL
