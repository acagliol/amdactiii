# Hosting the judges’ demo link

One process serves the API and the built React app (`api.server` + `web/dist`).

## Local (same as production command)

```bash
cd web && npm ci && npm run build && cd ..
uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8000}
```

Open `http://localhost:8000`. Camera needs **https** or **localhost**.

## Environment (put the key in the host’s secret store — never commit)

| Variable | Judges / live | Offline demo |
|----------|---------------|--------------|
| `USE_FAKE_AI` | `false` | `true` |
| `VLLM_BASE_URL` | `https://developer.amd.com.cn/radeon/api/v1` | unused if fake |
| `VLLM_MODEL` | `DeepSeek-V4.1-Flash` | unused if fake |
| `VLLM_API_KEY` | team Token Factory secret | `EMPTY` |
| `VLLM_TIMEOUT_SECONDS` | `60` | `10` |
| `VLLM_FALLBACK_TO_FAKE` | `false` | optional |

Gemma 4 was removed from AMD Token Factory — use **DeepSeek-V4.1-Flash**.

## Docker

```bash
docker build -t multilond .
docker run --rm -p 8000:8000 \
  -e USE_FAKE_AI=false \
  -e VLLM_BASE_URL=https://developer.amd.com.cn/radeon/api/v1 \
  -e VLLM_MODEL=DeepSeek-V4.1-Flash \
  -e VLLM_API_KEY="$VLLM_API_KEY" \
  -e VLLM_TIMEOUT_SECONDS=60 \
  multilond
```

## Render (recommended path in-repo)

1. Push this repo (public or private connected to Render).
2. **New → Blueprint** and select `render.yaml`, or **New Web Service** → Docker.
3. Set **`VLLM_API_KEY`** in the dashboard (secret). Other vars are in `render.yaml`.
4. Deploy. Copy the `https://….onrender.com` URL into lablab.
5. **Sleep:** free instances spin down when idle. For a link that must stay up after Oct 18, use a paid/starter always-on plan (Blueprint uses `starter`).

## Checklist before sharing the link

- [ ] `web/dist` present (build step succeeded)
- [ ] HTTPS URL works on phone + laptop
- [ ] Camera allowed (or use Upload / recorded video in live-mode)
- [ ] One Pass and one Fix it with red box on a real/fake check
- [ ] No API key in git history (`git log -p | findstr /i api_key` clean)
- [ ] Repo public + MIT `LICENSE` for lablab MIT-compliant submissions
