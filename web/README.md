# Multilönd web worker station

React + Vite + TypeScript frontend for the worker screen. It talks to a small Python API
(`api/server.py`) that calls the same checker as the Streamlit app, so the inspection rules
live in one place (`checker/`). Streamlit (`app/main.py`) still works as a fallback.

```
browser (web/)  →  /api/...  →  api/server.py  →  checker (Session, run_check)  →  ai_client  →  AMD
```

## Run it (one server)

From the repo root, after `pip install -r requirements.txt`:

```bash
cd web && npm install && npm run build && cd ..
uvicorn api.server:app --port 8000
```

Open http://localhost:8000. The server serves the built frontend and the API together.
AI settings come from `.env` as usual (`USE_FAKE_AI=true` for offline demos).
The browser only allows the camera on `localhost` or `https://`.

## Develop the frontend (hot reload)

Two terminals:

```bash
uvicorn api.server:app --port 8000 --reload      # repo root
cd web && npm run dev                             # http://localhost:5173, forwards /api to :8000
```

## Where things are

| File | What it does |
|---|---|
| `src/components/Station.tsx` | One unit in progress: camera → check → result, manual and gate steps, override |
| `src/components/CaptureStage.tsx` | Live camera, frozen photo, "Checking…" ring |
| `src/components/PhotoWithBox.tsx` | Draws the AI's red box exactly on the photo |
| `src/components/Logo.tsx` | Brand mark; its ring shows the check status |
| `src/api.ts`, `src/types.ts` | Calls to `api/server.py` and the shapes it returns |
| `src/hooks/useCamera.ts` | Browser camera + freezing a frame as a JPEG |
