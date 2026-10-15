# Speaker notes for the seven-slide PowerPoint

Target: three minutes including brief pauses. The video script uses the same claims and gives the packing demo more screen time.

## Slide 1 / 0:00–0:15

Multilönd AI checks manual assembly and packing while the work is still visible. A missing accessory is easy to add when the box is open. Once the lid closes, finding it means reopening the unit or dealing with a customer return.

## Slide 2 / 0:15–0:35

The 1-10-100 rule of thumb explains why timing matters. Fixing a mistake at the station is simpler than finding it at final test or after delivery. These multipliers illustrate the principle. We have not measured cost savings. Our focus is the last visible checkpoint before the next step hides the work.

## Slide 3 / 0:35–1:10

Our demo is an accessory box. The worker shows the contents to the camera, and the model answers the current checklist question. A missing item produces Fix it and a box marking the problem area. The software keeps the lid step locked. After the worker corrects the contents and the check passes, the workflow advances. If the photo is unclear, the station asks for a retake. A person can override a check with a written reason.

## Slide 4 / 1:10–1:30

All our model runs used AMD Token Factory, on Radeon Cloud GPUs, with Gemma-4-31B-IT. OpenCV checks photo quality locally, and checklist rules decide what the model's response means. In production, the same open model runs on the factory's own AMD GPU. That is the deployment plan. Our current cloud checks take about six seconds.

## Slide 5 / 1:30–2:10

On the same 34 cable photos, the generic checklist caught two of 24 defects. It passed nearly everything, so zero false alarms alone was misleading. Describing a correct cable raised the reported catch count to 14 of 24, seven times as many. Both runs had zero false alarms on ten clean photos. Targeted checks averaged 5.65 seconds. The reported box IoU was 0.62 for positive-overlap detections. Ten defects still escaped, so this is an encouraging checklist experiment, not proof of production reliability.

## Slide 6 / 2:10–2:35

Each visual inspection attempt saves its photo and checker result with a unit ID, timestamp and check ID. That lets us review what happened for the unit we just demonstrated. The store is local SQLite plus image files. Manual confirmations and override reasons are available in the active session. Durable override records and manager reporting need further work.

## Slide 7 / 2:35–3:00

The checklist defines the product. The same engine also has a PC-build checklist for RAM clips and GPU power before the side panel closes. Next we want broader validation and deployment on a factory's AMD GPU. Physical tool interlocks are a future extension. Multilönd AI helps catch mistakes while the work is still visible. Thank you.

## Questions the presenter may get

**Did you measure this on factory hardware?** No. All reported model runs used AMD Token Factory (Radeon Cloud GPUs). Factory deployment is the proposed production path.

**Is the box physically locked?** The implemented gate controls software progress. Physical locks and tool relays are future work.

**Is 3/3 a precision result?** No. It is the catch count for three defective samples in each of the cable-swap and missing-cable subtypes.

**Why did box overlap fall?** The targeted run found more defects. Its reported mean uses a different subset of detections. That does not establish a localization improvement. The evaluator excludes zero-overlap boxes and missed defects.

**What do 91.3% and 97.1% mean?** Box IoU and mask coverage on one photo. They do not describe the full sample.

**Did you rerun these numbers for this script?** The team supplied the live rerun results. This script reflects that report. The repository does not include the raw result files.
