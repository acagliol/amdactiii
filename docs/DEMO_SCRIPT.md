# Three-minute packing-box video script

## Recording setup

Use the accessory-box checklist and the same box, camera angle and items throughout. Record the real station using DeepSeek V4.1 Flash (open-weight) on AMD Token Factory with fake fallback disabled. Keep the model-mode indicator visible. Have the missing-item photo, corrected photo and a genuinely poor-quality photo ready.

Use Multilond_AI_updated.pptx as the deck, based on the supplied PowerPoint. [PITCH_DECK.md](PITCH_DECK.md) is the team's slide blueprint. [SPEAKER_NOTES.md](SPEAKER_NOTES.md) matches this twelve-slide PowerPoint.

The repository snapshot does not contain packing_box.yaml or the actual packing-demo footage. Take the packing-station shots from the recording owner's working setup. Match the spoken item names to what that checklist actually checks. The supplied PC station screenshot is only for the secondary example.

## 0:00–0:15 / Product-page screenshot

Show [the product-page hero](assets/product-page.jpg), then cut to the open accessory box.

**Voiceover:** A charger left out of a box is easy to add while the box is open. After the lid closes, the same mistake becomes rework or a customer return. Multilönd AI checks the work before the next step covers it.

## 0:15–0:30 / Problem slide

Show the 1-10-100 slide. Label it a rule of thumb.

**Voiceover:** The 1-10-100 quality rule captures why early checks matter. Fix it at the station, before it reaches final test or the customer. These are illustrative multipliers, not savings we have measured.

## 0:30–1:30 / Packing-box station

Show the real station and unit serial. Submit the box with an item missing. Leave the actual Checking state on screen. Show Fix it, its problem box and the uncompleted lid step. Add the item and run the check again. Show Pass and the lid step becoming available. Finish with the poor-quality photo and Retake.

**Voiceover:** Here is the accessory-box station. The worker shows the contents to the camera, and the checklist describes what a correct box should contain. This box is missing an item. The station returns Fix it and marks the area to inspect. The lid step stays locked in the software. We add the item and check again. Now it passes, and the workflow allows the closing step. An unclear photo gets Retake so the worker can improve the view. Physical locks are a future extension. This prototype controls the checklist workflow.

Editing: let each result appear before describing it. If trimming waiting time, show a visible **wait shortened** caption. Do not present a shortened clip as the measured latency.

## 1:30–2:00 / Same-set results slide

Show the full before/after table with sample counts and the visible label **Measured with Gemma 4**. These results belong to the earlier Gemma-4-31B-IT runs, not the current DeepSeek demo.

**Voiceover:** In the historical benchmark measured with Gemma 4 on the same 34 MVTec cable photos, the generic question caught two of 24 defects. A question describing a correct cable caught 14, seven times as many. Both runs had zero false alarms on ten clean photos. Targeted checks averaged 5.65 seconds, with reported box IoU of 0.62 on positive-overlap detections. Ten defects still escaped, so more validation is needed.

## 2:00–2:20 / AMD slide

Show **DeepSeek V4.1 Flash (open-weight) on AMD Token Factory** as the current demo model, with factory deployment labelled as planned.

**Voiceover:** Our current demo uses DeepSeek V4.1 Flash, an open-weight model, on AMD Token Factory. The cable benchmark was measured with Gemma 4. Local photo-quality checks and fixed checklist rules surround the model. In production, the same open model runs on the factory's own AMD GPU. That is our planned deployment path.

## 2:20–2:40 / Evidence for this unit

Show the actual Recent evidence view and a saved photo from the packing session.

**Voiceover:** Each visual attempt saves the photo, unit ID, timestamp, check ID and checker result in a local evidence store. We can review the exact attempt for this unit. Manual confirmations and override reasons remain available in the active session. Durable override records need further work.

## 2:40–3:00 / Same engine, new checklist

Show [the PC station example](assets/station-pc-example.jpg), visibly labelled **PC build example / local demo mode**, then return to the corrected packing box and closing slide.

**Voiceover:** A new product uses a new checklist. The same engine also checks RAM clips and GPU power in a PC build before the side panel closes. Our next work is broader validation and factory deployment on AMD. Multilönd AI helps catch mistakes while they are still visible.

## Recording fallback

If the live endpoint is unavailable, use a previously recorded real packing check and label it with its actual model and **recorded AMD Token Factory run**. Only label footage as DeepSeek when its model configuration confirms that. Label any fake-AI footage **local demo mode** and keep it out of benchmark evidence. Do not imply that the product-page illustration is a real model prediction.
