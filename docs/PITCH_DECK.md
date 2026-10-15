# Multilönd AI — Pitch Deck Guide & Slide Blueprint

**Format:** 16:9 Presentation Slides (Designed for PowerPoint / `Multil_nd_AI_logo_directions.pptx`)  
**Target Duration:** ~3 minutes spoken (matches `docs/DEMO_SCRIPT.md`)  
**Hackathon:** AMD Developer Hackathon: ACT III — Intelligent Industry  
**Hardware & Stack:** AMD Token Factory (Radeon Cloud GPUs) · vLLM · Google Gemma-4-31B-IT · Python · OpenCV · SQLite  

---

## Slide 1: Title & Hook (Cover)

### Slide Content (16:9 Layout)
* **Visual:** Use official cover design (`docs/cover.png` / `Multil_nd_AI_logo_directions.pptx`).
* **Title:** **MULTILÖND AI**
* **Subtitle:** Catch hidden assembly mistakes before they're hidden.
* **Tagline:** Active computer vision inspection with interlocked assembly gates for zero-defect hardware packaging and assembly.
* **Footer:** `INTELLIGENT INDUSTRY · AMD DEVELOPER HACKATHON`

### Speaker Script (~20 seconds)
> *"Every year, high-value electronics and industrial hardware are recalled or scrapped because of simple hand-assembly and pack-out slips. Welcome to Multilönd AI — an intelligent computer vision assistant running open models on AMD that catches assembly mistakes before the box lid or chassis panel closes."*

---

## Slide 2: The Problem: The Hidden Defect Trap

### Slide Content (16:9 Layout)
* **Header:** **The 1-10-100 Cost Multiplier in Assembly**
* **Sub-header:** Why manual inspection fails once enclosures close:
  * **Human Fatigue in Repetitive Assembly:** Missing accessories, unseated connectors, unlatched clips, and wrong wire harnesses naturally slip through manual assembly shifts.
  * **The "Closed Enclosure" Trap:** Once a step covers earlier work — such as closing a packing box lid or screwing on a PC side panel — internal mistakes are physically buried.
  * **The 1-10-100 Quality Rule:**
    * **1× Cost at the Station:** Instant fix by the operator while the item is still in hand.
    * **10× Cost at Testing Line:** Requires full teardown, re-inspection, and technician diagnostic time.
    * **100× Cost in the Field:** Warranty RMA, customer returns, shipping overhead, and brand damage.

### Visual Suggestions
* The **1-10-100 Rule** escalation graphic:
  * Station: **1×** (instant fix)
  * Testing Line: **10×** (teardown rework)
  * Field / Customer: **100×** (RMA / recall risk)

### Speaker Script (~30 seconds)
> *"Manual assembly and packing are naturally vulnerable to human fatigue. A missing accessory, an unseated connector, or a swapped wire will inevitably happen on the line. But the true cost trap occurs when the operator closes the box lid or attaches the chassis panel. That mistake is now buried. The classic manufacturing 1-10-100 rule proves that fixing a defect in the field costs 100 times more than catching it while the part was still in the operator's hands."*

---

## Slide 3: The Solution: Active Station Quality Interlock

### Slide Content (16:9 Layout)
* **Header:** **Multilönd AI: The Station Guardian**
* **Core Capabilities:**
  * **Active Visual Checklist:** Step-by-step guidance showing target inspection points and real-time instructions.
  * **Interlocked Assembly Gates:** Digital lock. The system actively locks the operator from proceeding to "Close Box Lid" until all component checks pass.
  * **Immediate Visual Feedback:** Status badges (**Pass** / **Fix it** / **Retake**) with localized red bounding-box defect overlays.
  * **Live Demo Focus:** **Accessory-box pack-out** (5 steps verifying cable, power brick, antenna, and accessories, with the lid step locked).
  * **Universal Extensibility:** Works for PC build, automotive harnesses, or medical kits using the same engine and a modular YAML checklist.

### Visual Suggestions
* **Screenshots from Web App / Worker Station:**
  * Worker screen showing **"Fix it"** with red bounding box highlighting a missing/wrong component.
  * Blocked step: **"Close Box Lid"** showing locked state until all prior steps pass.

### Speaker Script (~30 seconds)
> *"Multilönd AI solves this through active workstation interlocks. In our primary demo — packing an accessory kit — the camera inspects each item placed into the box. If an accessory is missing or placed incorrectly, the worker instantly sees a 'Fix it' badge with a red bounding box. Most importantly, the system blocks the 'Close Box Lid' step until every component check passes. No mistake is ever buried again."*

---

## Slide 4: Architecture Built for Factory Deployment

### Slide Content (16:9 Layout)
* **Header:** **Cloud Evaluation, Factory GPU Production**
* **Tested Infrastructure:** Evaluated live on **AMD Token Factory (Radeon Cloud GPUs)** serving **Google Gemma-4-31B-IT** via OpenAI-compatible vLLM.
* **Production Deployment:** In production, the exact same open vision model runs on the factory's own local AMD GPU for complete air-gapping.
* **Edge Quality Gate:** Local OpenCV pre-filtering detects blurry or glare-saturated photos before model invocation, preventing wasted compute.

### System Flowchart
```text
[ Station Camera / Webcam ]
           │
           ▼
[ OpenCV Quality Gate ] ──── (Blur / Glare) ────► [ Retake Prompt ]
           │ (Sharp Photo)
           ▼
[ AMD Token Factory / Local AMD GPU ]
   (vLLM serving Gemma-4-31B-IT)
           │
           ▼
[ Step Verification & Bounding Box Overlap ]
           │
           ▼
[ SQLite Evidence Log ] ──────────────────────► [ Manager Dashboard ]
           │
           ▼
[ Worker Screen: Pass / Fix it + Red Box Overlay ]
```

### Speaker Script (~25 seconds)
> *"For this hackathon, we connected Multilönd AI directly to AMD Token Factory running Gemma-4-31B-IT on Radeon Cloud GPUs. Because Gemma 4 is an open-weight model, factories in production can deploy this exact same pipeline directly on their local AMD hardware — keeping proprietary product designs 100% on-premise without ever streaming photos to commercial public APIs."*

---

## Slide 5: Empirical Benchmark: The Power of Targeted Checklists

### Slide Content (16:9 Layout)
* **Header:** **Empirical Evaluation: MVTec AD Cable Benchmark (34 Samples)**
* **The Core Technical Discovery:** Why generic VLM prompts fail, and why Multilönd's structured checklist architecture wins:

| Inspection Metric | Generic Anomaly Prompt (*"Any defects?"*) | Multilönd Targeted Step Check | Engineering Impact |
| :--- | :--- | :--- | :--- |
| **Defect Catch Rate** | **8.3%** (2/24 caught) | **58.3%** (14/24 caught) | 🚀 **7× increase in defect detection** |
| **False Alarm Rate (Clean Units)** | **0.0%** (10/10 passed) | **0.0%** (10/10 passed) | ✅ **0% false alarms maintained** |
| **Cable Swap (`cable_swap`)** | 0/3 (0%) | **3/3 (100%!)** | 🎯 **100% precision on miswiring** |
| **Missing Cable (`missing_cable`)** | 0/3 (0%) | **3/3 (100%!)** | 🎯 **100% precision on missing parts** |
| **Cut Insulation (Inner/Outer)** | 1/6 (16%) | **4/6 (67%)** | 📈 **4× more physical cuts caught** |
| **Mean Bounding Box IoU** | 0.75 (only 2 detections) | **0.62** (across 14 detections) | 🎯 **Spatial grounding confirmed** |
| **Average Latency** | 5.71s | **5.65s** | ⚡ **Stable ~5.6s on AMD Cloud** |

### Key Takeaway
* General vision-language models fail when asked vague questions like *"is this defective?"*. 
* When Multilönd breaks assembly down into explicit, targeted verification checks (e.g., *"A correct cable has green-yellow, blue, and brown wires in order"*), Gemma 4 catches 100% of cable swaps and missing components with zero false alarms on clean units.

### Speaker Script (~35 seconds)
> *"We benchmarked Multilönd AI live against the official MVTec cable dataset on AMD Token Factory, and the data proved a vital engineering truth: generic vision prompts fail on industrial defects, catching only 8% of mistakes. But when Multilönd breaks the task into explicit checklist steps — describing exact wire sequences and insulation integrity — Gemma 4's catch rate jumps by seven times to 58%, hitting 100% accuracy on cable swaps and missing parts with zero false alarms on clean units."*

---

## Slide 6: Enterprise Audit Trail & Yield Visibility

### Slide Content (16:9 Layout)
* **Header:** **Audit Traceability & First-Pass Yield**
* **Key Enterprise Features:**
  * **Unit Evidence Record:** Every single assembly step stores the captured photo, timestamp, check identifier, and model verdict in SQLite.
  * **Supervisor Oversight:** If an operator needs to override a check, mandatory written rationale is captured in the audit trail.
  * **Yield Visibility:** Real-time visibility into first-pass yield and top mistake categories by step.
* **Visuals:** Screenshots of the Manager / Product dashboard showing defect counts by step and photo evidence viewer.

### Speaker Script (~25 seconds)
> *"Every check in Multilönd AI is logged to a local evidence store with the camera frame, timestamp, and AI verdict. Supervisors can log written overrides when necessary, ensuring zero unrecorded bypasses. Plant managers get clear visibility into step-by-step yield, pinpointing exactly which assembly steps cause the most errors on the line."*

---

## Slide 7: Roadmap & Team

### Slide Content (16:9 Layout)
* **Header:** **The Future of Zero-Defect Manufacturing**
* **Next Milestones:**
  * **GPIO Hardware Interlocks:** Wire direct electrical relays to physical pneumatic screwdrivers and box fixtures.
  * **Multi-Camera Station Sync:** Synchronize overhead wide-angle cameras and macro inspection lenses.
  * **Expanded YAML Checklists:** Deployable to PC manufacturing, automotive wire harnesses, and medical kits.
* **Team Multilönd AI:** Intelligent Industry Track · AMD Developer Hackathon: ACT III

### Speaker Script (~20 seconds)
> *"Looking forward, our extensible YAML checklist engine allows deploying Multilönd AI to medical packaging, automotive harnesses, or server assembly in minutes. Next, we are wiring direct GPIO relay interlocks to physical workbench tools. Thank you from team Multilönd AI — building the future of zero-defect assembly on AMD."*

---

## Appendix: Copy-Paste Descriptions for Lablab Submission

### Short Description (1–2 Sentences)
> *Multilönd AI is a visual inspection assistant for manual assembly and packaging that can run on a factory's own AMD GPU. Powered by Google Gemma 4 on AMD GPUs, it verifies each assembly step in real time and enforces a digital lock to catch mistakes before panels or box lids close.*

### Long Description (For Submission Form)
> *In electronics and hardware assembly, human fatigue inevitably leads to missed components, unseated connectors, and swapped wiring. Once the chassis panel is attached or the packing box lid is closed, these defects become hidden traps — costing 10× to 100× more to diagnose at end-of-line testing or through customer warranty returns.*
>
> *Multilönd AI solves this by introducing active workstation quality interlocks. As an operator packs or builds a unit, the station camera inspects each step against an extensible checklist. If a defect is detected, the operator instantly receives a visual "Fix it" badge with a localized red bounding box. Crucially, the system blocks the "Close Lid / Close Panel" step until all prerequisite checks pass.*
>
> *Evaluated live on AMD Token Factory using Google Gemma-4-31B-IT against the official MVTec industrial benchmark, Multilönd AI demonstrates that targeted checklist questions achieve a 7× higher defect catch rate (58.3% vs. 8.3% generic prompts), reaching 100% precision on cable swaps and missing parts with 0.0% false alarms on clean units. By serving open-weight models via vLLM, Multilönd AI enables factories to run confidential, air-gapped inspection directly on their own local AMD GPUs.*
