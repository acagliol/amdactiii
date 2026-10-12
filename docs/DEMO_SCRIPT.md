# 3-minute demo script (fake AI OK; mention AMD path)

## Setup before recording

```bash
USE_FAKE_AI=true streamlit run app/main.py
```

Have photos ready (phone or `data/frames/`):

1. blurry or dark → Retake  
2. `*_ok_*` RAM → Pass  
3. `*_bad_*` GPU → Fix it (+ red box)  
4. `*_ok_*` GPU → complete unit  

Open **Recent evidence** once so judges see the audit trail.

## Spoken flow (~3 min)

1. **Problem (30s)** — Hand assembly hides mistakes under the next panel. Fixing later is 10–100× more expensive.  
2. **Product (20s)** — Multilönd watches the station, checks the step while it’s visible, blocks “close panel” until critical checks pass.  
3. **Live (90s)** — Run the photo sequence above. Call out Pass / Fix it / Retake / evidence log.  
4. **AMD (30s)** — “Inspection runs on an open vision model via vLLM on AMD Instinct MI300X in the Developer Cloud — factory photos stay off public APIs.” (Show real mode if the tunnel is up; otherwise say it’s wired and show `USE_FAKE_AI=false` config.)  
5. **Close (20s)** — Worker + supervisor override + photo proof per unit. Intelligent Industry / downtime & quality.

## Don’t

- Don’t apologize for fake AI if AMD is down — say “deterministic demo path; production path is AMD.”  
- Don’t open Manager dashboards you didn’t build.  
- Don’t scroll the README on camera.  
