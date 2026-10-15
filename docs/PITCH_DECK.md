# Multilönd AI presentation

The updated twelve-slide PowerPoint, Multilond_AI_updated.pptx, is delivered separately to the user and is not stored in this repository. It is based on the supplied Multil_nd_AI_logo_directions.pptx. The original 16:9 size, cover artwork, Arial/Courier New fonts and black/white/red design remain.

[Speaker notes](SPEAKER_NOTES.md) are embedded in every slide. [Video script](DEMO_SCRIPT.md) and [lablab copy](LABLAB_DESCRIPTIONS.md) use the same claims.

## Slide order

1. Multilönd AI: catch mistakes before the next step covers them.
2. The problem: section divider.
3. Packing scenario: a missing charger becomes hidden when the lid closes.
4. The 1-10-100 rule: illustrative quality-management multipliers, not measured savings.
5. How it works: section divider.
6. Packing-box inspection: actual product-page screenshot with its illustration clearly labelled.
7. One check: worker photo, local quality gate, correct-state question, model response, deterministic rules.
8. Open vision on AMD: AMD Token Factory (Radeon Cloud GPUs), Gemma-4-31B-IT, factory deployment labelled as planned.
9. Same engine, new checklist: PC station screenshot in local demo mode and supported photo-evidence claims.
10. The results: section divider.
11. Same-set before/after results as an editable PowerPoint table.
12. Closing: packing-box focus and repository link.

## Results on slide 11

Same 34 MVTec AD cable photos: 24 defective and 10 clean.

| Metric | Generic | Targeted |
| --- | --- | --- |
| Defects caught | 2/24 (8.3%) | 14/24 (58.3%) |
| False alarms on clean photos | 0/10 | 0/10 |
| Reported mean box IoU | 0.75 | 0.62 |
| Average check time | 5.71 s | 5.65 s |

Seven times as many defects caught, with ten defective photos still missed. The current evaluator averages only positive-overlap detections for box IoU, excluding misses and zero-overlap boxes. This is a small cable experiment, not a factory or packing-box validation.

The team's rerun report and pitch-deck commit ad0c66e88bdd35f602c00ffaa5f11fc87b0c9439 are the source. Raw predictions were not supplied, and this update is not an independent rerun. The earlier 91.3% IoU and 97.1% mask coverage came from one photo and appear only as a qualification in speaker notes. Subtype 3/3 catch counts are not precision estimates.

## Remaining media

Replace the product-page illustration on slide 6 with actual packing-station footage when supplied: missing item and Fix it, corrected contents and Pass, then the lid step unlocked. Keep the PC screenshot as the secondary example. Its visible local-demo indicator must remain visible.

## Evidence and deployment boundaries

The implemented gate controls software progress. Physical tool interlocks are future work. Visual attempts save photos and results per unit in local SQLite plus image files. Written overrides remain in the active session; durable override history and manager reporting need further work. All reported model runs used AMD Token Factory (Radeon Cloud GPUs). Factory AMD GPU deployment is planned.
