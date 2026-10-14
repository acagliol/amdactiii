# Eval (T60 + T61)

Measures the KPI from BUILD_PLAN: **catch >= 90% planted mistakes, false alarm <= 10% on clean, latency < 5s**.

1. Put frames in `data/frames/` (T45). Name them so the label is obvious:
   `<check_id>_ok_01.jpg` (clean) or `<check_id>_bad_01.jpg` (planted mistake).
   e.g. `ram_clips_ok_01.jpg`, `gpu_power_seated_bad_02.jpg`.
2. Build the answer key (review it by hand after):
   `python -m eval.make_answer_key`  -> `eval/answer_key.csv`
   MVTec AD too: `python -m eval.make_answer_key --mvtec path/to/mvtec_ad`
   (`<category>/test/good/*` = pass, other defect folders = fix; one checklist per category).
3. Score:
   `python -m eval.evaluate`            (uses USE_FAKE_AI from env, default true)
   `USE_FAKE_AI=false python -m eval.evaluate`  (real model on AMD)
   Writes `eval/results.csv` and prints the summary (plus a per-checklist table when several are scored). Exit 1 if a KPI misses.

answer_key.csv columns: `image,assembly,check_id,expected` where expected is `pass` or `fix`.
