# AMD Developer Cloud → vLLM → Multilönd Worker

One-person checklist so the team can show a **real AMD** inference in the demo.

## 0. Accounts (do early — credits can take 2–3 days)

1. Join / sign in to the [AMD AI Developer Program](https://www.amd.com/en/developer/resources/technical-articles/2026/the-new-amd-ai-developer-portal.html).
2. Request **$100 AMD Developer Cloud** credits under [Member Perks](https://developer.amd.com/member-perks/).
3. Activate credits when the email arrives ([claim guide](https://www.amd.com/en/developer/resources/technical-articles/2026/how-to-claim-amd-cloud-credits.html)).

You do **not** need a local AMD GPU. Fake AI works until the VM is up.

## 1. Create a VM

1. Open [AMD Developer Cloud](https://www.amd.com/en/developer/resources/cloud-access/amd-developer-cloud.html).
2. Create a **single** Instinct **MI300X** instance (not 8× — credits burn 8× faster).
3. Use a ROCm-ready image if offered.
4. Note the **public IP** and SSH user.

**Billing tip:** destroy the VM when you stop for the day. Powered-off VMs can still consume reservation costs.

## 2. On the VM — start vLLM (vision model)

```bash
# example — adjust model id to whatever you pull for the hackathon
vllm serve google/gemma-4-26b-a4b-it \
  --host 127.0.0.1 \
  --port 8000 \
  --trust-remote-code
```

Leave this process running. Confirm locally on the VM:

```bash
curl -s http://127.0.0.1:8000/v1/models | head
```

## 3. On your laptop — SSH tunnel

```bash
ssh -L 8000:127.0.0.1:8000 USER@VM_PUBLIC_IP
```

Keep that session open while you demo.

## 4. Point Multilönd at it

From the repo root (copy `.env.example` → `.env` if needed):

```bash
# Windows PowerShell
$env:USE_FAKE_AI='false'
$env:VLLM_BASE_URL='http://localhost:8000/v1'
$env:VLLM_MODEL='google/gemma-4-26b-a4b-it'
$env:VLLM_FALLBACK_TO_FAKE='false'   # true only for emergency demos
# optional: $env:VLLM_DOUBLE_LOOK='true'
streamlit run app/main.py
```

Quick SDK smoke (no UI):

```bash
python - <<'PY'
from ai_client import look
print(look("path/to/photo.jpg", "Are both RAM clips closed?"))
PY
```

## 5. Demo safety

| Mode | When |
|------|------|
| `USE_FAKE_AI=true` | Default offline build / backup demo |
| Real vLLM | Recorded demo + judging |
| `VLLM_FALLBACK_TO_FAKE=true` | Only if the tunnel dies mid-pitch (reason shows `DEMO FALLBACK`) |

## Done when

- [ ] One Worker check returns Pass or Fix it with `USE_FAKE_AI=false`
- [ ] Evidence row saved for that attempt
- [ ] You can say in the pitch: “vision model on AMD Instinct via ROCm/vLLM”
