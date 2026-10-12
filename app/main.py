"""Worker screen — foundation UI. Run: streamlit run app/main.py"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw

# Repo root on path so `checker` / `ai_client` import cleanly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from checker import Session, run_check  # noqa: E402

ASSEMBLY = ROOT / "assemblies" / "pc_build.yaml"
BADGE = {
    "pass": ("✅ Pass", "green"),
    "fix": ("🔧 Fix it", "red"),
    "retake": ("📷 Retake", "orange"),
    "supervisor": ("🚨 Supervisor", "violet"),
}


def draw_box(img: Image.Image, box: list[int] | None) -> Image.Image:
    if not box or len(box) != 4:
        return img
    out = img.copy()
    draw = ImageDraw.Draw(out)
    w, h = out.size
    ymin, xmin, ymax, xmax = box
    # CONTRACT boxes are 0–1000 normalized
    left = int(xmin / 1000 * w)
    top = int(ymin / 1000 * h)
    right = int(xmax / 1000 * w)
    bottom = int(ymax / 1000 * h)
    draw.rectangle([left, top, right, bottom], outline="red", width=4)
    return out


def main() -> None:
    st.set_page_config(page_title="Multilönd AI — Worker", layout="centered")
    st.title("Multilönd AI")
    st.caption("Catch assembly mistakes while they are still visible.")

    if "session" not in st.session_state:
        st.session_state.session = Session(ASSEMBLY)

    session: Session = st.session_state.session
    current = session.current()

    if current is None:
        st.success("All checks complete for this unit.")
        if st.button("Start new unit"):
            st.session_state.session = Session(ASSEMBLY)
            st.rerun()
        return

    st.subheader(f"Step: `{current['step_id']}` · Check: `{current['check_id']}`")
    st.write(current["instruction"])
    st.info(current.get("show") or current["question"])
    st.write(f"**Question:** {current['question']}")
    st.caption(f"Passed so far: {sorted(session.passed) or '—'}")

    uploaded = st.file_uploader("Upload workstation photo", type=["jpg", "jpeg", "png"])
    st.caption(
        "Demo tip: name files with `_ok_`, `_bad_`, or `_blur_` "
        "(fake AI keys off the filename)."
    )

    if uploaded and st.button("Check photo", type="primary"):
        suffix = Path(uploaded.name).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = Path(tmp.name)

        # Preserve original name keywords for fake_ai
        named = tmp_path.with_name(uploaded.name)
        tmp_path.replace(named)

        result = run_check(session, named)
        st.session_state.last_result = result
        st.session_state.last_image = named

    if "last_result" in st.session_state:
        result = st.session_state.last_result
        label, color = BADGE.get(result["action"], (result["action"], "gray"))
        st.markdown(f"### :{color}[{label}]")
        st.write(result["reason"])
        if result.get("hint"):
            st.warning(result["hint"])

        img_path = st.session_state.get("last_image")
        if img_path and Path(img_path).exists():
            img = Image.open(img_path).convert("RGB")
            st.image(draw_box(img, result.get("problem_box")), caption="Checked frame")

        if result["action"] == "pass":
            st.rerun()


if __name__ == "__main__":
    main()
