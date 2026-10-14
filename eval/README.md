# Evaluation Pipeline (T60 + T61)

Measures core hackathon KPIs:
* **Catch Rate** $\ge 90\%$ on planted mistakes
* **False Alarm Rate** $\le 10\%$ on clean frames
* **P95 Latency** $< 5.0\text{s}$
* **Grounding Quality (Box vs. Mask Overlap)**: Bounding box IoU and pixel mask coverage

---

## 1. Quickstart

### Step 1: Generate Answer Key from Folders
```bash
# Auto-detects MVTec dataset or data/frames/:
python -m eval.make_answer_key

# Or specify an MVTec folder explicitly:
python -m eval.make_answer_key --mvtec data/mvtec/cable
```
This generates `eval/answer_key.csv` with:
- `image`: Relative image path
- `assembly`: Target assembly checklist (e.g. `assemblies/mvtec/cable.yaml`)
- `check_id`: Inspection check identifier
- `expected`: `pass` (clean) or `fix` (defect)
- `defect_type`: Specific defect category (`cable_swap`, `missing_wire`, etc.)
- `mask_path`: Path to ground truth defect mask PNG
- `gt_box`: Normalized 0–1000 bounding box `[ymin, xmin, ymax, xmax]` derived from mask

### Step 2: Run Evaluation & Generate Scorecard
```bash
# Run with offline Fake AI (default):
python -m eval.evaluate

# Run with real vLLM on AMD MI300X:
USE_FAKE_AI=false python -m eval.evaluate
```

---

## 2. Outputs

* **Terminal Scorecard:** Formatted ASCII summary table for pitch deck inclusion.
* **`eval/results.csv`:** Per-frame detailed predictions, latency, Box IoU, and mask coverage.
* **`eval/scorecard.json`:** Structured summary metrics consumed by the manager dashboard and pitch deck.

---

## 3. Box vs. Mask Overlap Metrics

For each defect sample:
* **Box IoU:** $\frac{\text{Area}(\text{Box}_{\text{pred}} \cap \text{Box}_{\text{gt}})}{\text{Area}(\text{Box}_{\text{pred}} \cup \text{Box}_{\text{gt}})}$
* **Mask Coverage:** Fraction of ground-truth defect pixels enclosed within the predicted bounding box.
* **Grounding Hit:** Flagged as a true grounding hit if $\text{Box IoU} \ge 0.25$ or $\text{Defect Coverage} \ge 0.30$.
