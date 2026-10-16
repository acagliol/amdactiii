# Lablab submission copy

## Short description

Multilönd AI uses a camera and a product checklist to catch manual assembly and packing mistakes before the next step hides them. Our accessory-box prototype uses DeepSeek V4.1 Flash (open-weight) on AMD Token Factory, marks problems for the worker and keeps the closing step locked in software until required checks pass or a person records an override reason.

## Long description

A missing charger is easy to add while a packing box is open. An assembly mistake becomes harder to find once a lid or panel covers it. The 1-10-100 quality-management rule of thumb illustrates why checking earlier matters, without assuming measured cost savings.

Multilönd AI checks work at those visible checkpoints. A station camera captures the current step, and an open vision model compares it with a product checklist. Pass advances the workflow. Fix it identifies the problem area with a bounding box. Retake asks for a clearer view. The software keeps a step that hides earlier work locked until its prerequisites pass or a person supplies a written override reason.

The live demo focuses on accessory-box pack-out. The same engine also supports a PC-build checklist for RAM clips and GPU power before the side panel closes. Product setup lives in YAML, so the checklist defines the inspection questions and prerequisites.

The current prototype uses DeepSeek V4.1 Flash (open-weight) on AMD Token Factory through an OpenAI-compatible API. The historical cable benchmark used Gemma 4 (Gemma-4-31B-IT) on AMD Token Factory (Radeon Cloud GPUs). In that comparison on the same 34 MVTec AD cable photos, a generic question caught 2/24 defects. Describing a correct cable caught 14/24, seven times as many. Both runs produced zero false alarms on ten clean photos. The targeted run averaged 5.65 seconds per check and a reported box IoU of 0.62 on positive-overlap detections. Ten defects still escaped. These results describe the earlier Gemma 4 cable experiment. They do not establish DeepSeek performance, production reliability or packing-box accuracy.

Visual inspection attempts save photos and checker results by unit in a local SQLite evidence store. Next steps include broader validation and durable override records. In production, the same open model runs on the factory's own AMD GPU. That deployment is planned.

## Copy notes

Current-model wording follows the team's DeepSeek update. The 14/24 result and its timing/overlap values belong to the historical Gemma 4 benchmark. No DeepSeek rerun is claimed. The 3/3 cable-swap and 3/3 missing-cable results are subtype catch counts, not precision estimates. The reported mean box IoU excludes missed defects and zero-overlap boxes under the current evaluator. Do not substitute the one-photo 91.3% IoU or 97.1% coverage values for a sample average.
