# Multilönd AI pitch deck

Seven slides for the existing 16:9 PowerPoint. Keep Ilyas's cover and visual identity. The accessory-box pack-out is the main demo. PC build is the "same engine, new checklist" example.

Spoken copy: [speaker notes](SPEAKER_NOTES.md). Recording plan: [video script](DEMO_SCRIPT.md). Submission copy: [lablab descriptions](LABLAB_DESCRIPTIONS.md).

## 1. Multilönd AI

**Catch mistakes before the next step covers them**

Visual inspection for manual assembly and packing.

Visual: official cover. Footer: AMD Developer Hackathon: ACT III / Intelligent Industry.

## 2. The cost of a hidden mistake

| At the station | At final test | At the customer |
| --- | --- | --- |
| 1× | 10× | 100× |
| Add the missing item while the box is open | Reopen, inspect, fix, retest | Return, repair, replace |

Visible footnote: **The 1-10-100 rule is a quality-management rule of thumb, not measured savings.**

## 3. The packing-box station

**Check the contents before closing the lid**

- A camera photo answers the active checklist question.
- Pass advances. Fix it shows the problem. Retake asks for a clearer view.
- The software keeps the lid step locked until prerequisites pass or a person records an override reason.

Visual: a real frame from the packing-box video showing Fix it and the uncompleted checklist. Follow with the corrected box and unlocked lid step. Match the video's actual items and step names.

Supporting visual: [product page](assets/product-page.jpg). Its box drawing illustrates the product and is not an inference result.

## 4. Open vision on AMD

**Prototype and evaluation: AMD Token Factory (Radeon Cloud GPUs)**

Gemma-4-31B-IT through an OpenAI-compatible API.

Camera photo / local OpenCV quality check / model response / checklist rules / worker feedback and local evidence.

**Production plan:** In production, the same open model runs on the factory's own AMD GPU.

Visible footnote: The production deployment is a proposed next step. Current cloud checks average about six seconds.

## 5. A correct-state checklist catches more defects

**Same 34 MVTec AD cable photos: 24 defective, 10 clean**

| Metric | Generic checklist | Targeted checklist |
| --- | --- | --- |
| Defects caught | 2/24 (8.3%) | **14/24 (58.3%)** |
| False alarms on clean photos | 0/10 | **0/10** |
| Reported mean box overlap (IoU)* | 0.75 | **0.62** |
| Average check time | 5.71 s | **5.65 s** |

**7× as many defects caught. 10/24 defects still missed.**

Visible footnote: Team-reported runs on AMD Token Factory (Radeon Cloud GPUs), Gemma-4-31B-IT. Small sample, not a factory validation. *Current evaluator averages positive-overlap detections only and excludes misses and zero-overlap boxes.

Speaker detail: The generic prompt passed 22/24 defective photos. Its zero false alarms are therefore not evidence of a strong detector. The targeted run caught 3/3 cable swaps and 3/3 missing cables in this set. These are subtype catch counts, not a precision estimate. Do not call them general 100% accuracy.

Prompt change: The generic question lists defect category names. The targeted question describes intact insulation and the expected green-yellow, blue, and brown wires. See [the evaluated checklist](https://github.com/acagliol/amdactiii/blob/ad0c66e88bdd35f602c00ffaa5f11fc87b0c9439/assemblies/mvtec/cable.yaml).

Evidence source: team rerun report supplied with this update and commit ad0c66e88bdd35f602c00ffaa5f11fc87b0c9439. Raw predictions and scorecards are local-only and absent from the repository. Preserve these reported numbers as reported, without claiming a new independent rerun.

## 6. Photo evidence per unit

**Review what the camera saw and what the checker decided**

- Visual attempts save the photo, unit ID, timestamp, check ID, verdict and result in SQLite with local image files.
- Review recent evidence for the demonstrated unit.
- Manual confirmations and written overrides remain part of the active session.

Visual: the actual Recent evidence view for the packing demo. Use a unit serial, not a worker identifier.

Presenter detail: The current web override path stores its reason in session memory. Do not promise durable override history or authenticated supervisor approval. Dashboard and yield reporting remain next steps.

## 7. Same engine, new checklist

**Accessory-box pack-out today. PC build as the next example.**

The existing PC checklist asks about RAM clips and GPU power before the side-panel step.

Next: validate more products and lighting conditions, deploy the model on a factory AMD GPU, and evaluate physical tool interlocks.

Visual: [worker station with the PC checklist](assets/station-pc-example.jpg), labelled **PC build example / local demo mode**. Keep this secondary to the packing-box video.

## Appendix: one-photo localization example

91.3% box IoU and 97.1% defect-mask coverage describe one cable-swap photo. They are not averages over the 34 photos, and neither metric measures defect catch rate. Use only with that photo and its prediction/mask pair, clearly labelled **one photo**.

## Appendix: submission descriptions

Copy from [LABLAB_DESCRIPTIONS.md](LABLAB_DESCRIPTIONS.md).
