# Speaker notes for the twelve-slide PowerPoint

Three-minute timing. These notes are embedded in Multilond_AI_updated.pptx.

## Slide 1: Multilönd AI

0:00–0:12. Multilönd AI checks manual assembly and packing while the work is still visible. A missing accessory is easy to add when the box is open. After the lid closes, it becomes rework or a customer return.

## Slide 2: The problem

0:12–0:15. The problem is the moment a later step hides earlier work.

## Slide 3: The packing-box mistake

0:15–0:27. Our main example is an accessory box. A worker leaves out a charger. Closing the lid hides the contents, and the customer receives an incomplete kit. This is an illustrative scenario, not a measured customer incident.

## Slide 4: The 1-10-100 rule

0:27–0:41. The 1-10-100 rule of thumb explains why timing matters. Fixing a mistake at the station is simpler than finding it at final test or after delivery. These multipliers illustrate the principle. We have not measured savings.

## Slide 5: How it works

0:41–0:44. The camera checks the contents before the workflow reaches the closing step.

## Slide 6: Packing-box inspection

0:44–1:14. This is the product page, with an accessory-box illustration. In the live packing demo, the worker shows the contents to the camera. Fix it marks a problem area. Pass advances the workflow. Retake asks for a clearer view. The software keeps the lid step locked until required checks pass or a person provides an override reason. Physical interlocks are future work. Replace this illustrative product-page screenshot with real packing-station footage when the recording owner supplies it.

## Slide 7: One check, step by step

1:14–1:26. The worker captures a photo. OpenCV checks image quality locally. A checklist question describes what correct looks like. The model returns a verdict and, for a visible problem, a box. Fixed rules decide what happens next and save visual inspection attempts.

## Slide 8: Open vision on AMD

1:26–1:44. The current demo uses DeepSeek V4.1 Flash (open-weight) on AMD Token Factory through an OpenAI-compatible API. The 14/24 cable benchmark and its roughly six-second checks were measured with Gemma 4. Those figures do not establish DeepSeek performance. In production, the same open model runs on the factory’s own AMD GPU. That deployment is planned, not demonstrated here.

## Slide 9: Same engine, new checklist

1:44–2:02. A new product uses a new checklist. This screenshot shows the existing PC-build workflow in local demo mode. The image-quality gate requested a retake, and the panel step remains locked. Visual attempts save photo evidence by unit with a timestamp, check ID and checker result. Override reasons remain in the active session. Durable override records need further work.

## Slide 10: The results

2:02–2:05. The historical cable benchmark was measured with Gemma 4, comparing generic and targeted questions on the same photo set.

## Slide 11: 2/24 to 14/24 defects caught

2:05–2:45. In the historical benchmark measured with Gemma 4 (Gemma-4-31B-IT) on the same 34 MVTec AD cable photos, the generic checklist caught two of 24 defects. It passed almost everything, so zero false alarms alone was misleading. Describing a correct cable raised the catch count to 14, seven times as many. Both runs had zero false alarms on ten clean photos. Targeted checks averaged 5.65 seconds. Generic mean box IoU is 0.8554, recalculated from its two detected boxes. Targeted mean box IoU is 0.6211 across fourteen detected boxes, shown rounded to 0.62. Both means use positive-overlap detections only. Ten defects still escaped. This small cable experiment does not establish packing-box or factory reliability. The targeted run caught 3/3 cable swaps and 3/3 missing cables in this set; these are subtype catch counts, not precision. The earlier 91.3% IoU and 97.1% mask coverage were from one photo, not sample averages. Sources: team rerun report supplied by the user; https://github.com/acagliol/amdactiii/commit/ad0c66e88bdd35f602c00ffaa5f11fc87b0c9439 ; evaluator averaging behavior in eval/evaluate.py. Both per-image CSVs are now available in PR #9 and have been checked for matching image paths and labels. Counts, latency averages and box IoU were recalculated from those records; this is not an independent model rerun. The generic CSV and scorecard store 0.75, but their saved boxes yield 0.8160 and 0.8948, averaging 0.8554. The original CSV and scorecard remain unchanged. Source: https://github.com/acagliol/amdactiii/tree/7b9e5baaf56b1d8d30acccf876d91235f606c098/docs/results . Pixel-mask coverage and endpoint/model settings have not been independently verified.

## Slide 12: Thank you

2:45–3:00. Multilönd AI helps catch mistakes while the work is still visible. Next we want broader validation and deployment on a factory AMD GPU. The packing box is our main demo. PC build shows how the same engine uses another checklist. Thank you.

