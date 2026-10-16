# Presentation handoff

[Multilond_AI_updated.pptx](Multilond_AI_updated.pptx) is the edited copy of the supplied twelve-slide PowerPoint. All slides include speaker notes. The results table on slide 11 remains editable.

- PITCH_DECK.md: slide order, claims, results and remaining media.
- SPEAKER_NOTES.md: notes matching the twelve-slide deck.
- DEMO_SCRIPT.md: timed packing-box video script.
- LABLAB_DESCRIPTIONS.md: short and long submission text.
- assets/product-page.jpg: actual product-page screenshot from web-frontend commit 3182b93afcfe0924672f3a7694afe9edfbc4df77. The box drawing is an illustration.
- assets/station-pc-example.jpg: actual PC worker-station screenshot from that frontend in local demo mode. It shows a quality-gate Retake on an uploaded reference illustration. Keep the visible Demo AI (offline) indicator. This is not benchmark evidence.

Slide 6 uses the product-page screenshot until the recording owner supplies real packing-station frames: missing item and Fix it, corrected contents and Pass, then the lid step unlocked. The repository snapshot lacks the actual packing checklist and those photos.

The before/after records are available as dated per-image CSVs and scorecards in [PR #9](https://github.com/acagliol/amdactiii/tree/7b9e5baaf56b1d8d30acccf876d91235f606c098/docs/results). Image paths and labels match across both 34-image CSVs. The generic IoU used in this presentation is 0.8554, recalculated from its two saved predicted/ground-truth box pairs. The targeted mean is 0.6211 across fourteen detections, displayed as 0.62. Source CSVs and scorecards remain unchanged. Retain the sample counts, ten missed defects and conditional overlap caveat.

This branch contains presentation materials only. Keep the evaluated cable checklist and application changes in their existing development branches.
