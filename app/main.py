"""Worker screen. Run: streamlit run app/main.py"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evidence_panel import render_recent_evidence  # noqa: E402
from checker import Session, run_check  # noqa: E402

ASSEMBLY = ROOT / "assemblies" / "pc_build.yaml"

BADGE_STYLE = {
    "pass": ("Pass", "#0b6e4f", "#d8f3e7"),
    "fix": ("Fix it", "#9b2226", "#fde2e1"),
    "retake": ("Retake", "#bb4d00", "#ffe8cc"),
    "supervisor": ("Supervisor", "#5a189a", "#efe2ff"),
}


def draw_box(img: Image.Image, box: list[int] | None) -> Image.Image:
    if not box or len(box) != 4:
        return img
    out = img.copy()
    draw = ImageDraw.Draw(out)
    w, h = out.size
    ymin, xmin, ymax, xmax = box
    left = int(xmin / 1000 * w)
    top = int(ymin / 1000 * h)
    right = int(xmax / 1000 * w)
    bottom = int(ymax / 1000 * h)
    draw.rectangle([left, top, right, bottom], outline="red", width=4)
    return out


def render_badge(action: str) -> None:
    label, fg, bg = BADGE_STYLE.get(action, (action, "#222", "#eee"))
    st.markdown(
        f"""
        <div style="
            margin: 0.75rem 0 1rem 0;
            padding: 1rem 1.25rem;
            border-radius: 12px;
            background: {bg};
            color: {fg};
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            text-align: center;
            border: 2px solid {fg};
        ">{label}</div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Multilönd AI — Worker", layout="wide")
    st.title("Multilönd AI")
    st.caption("Catch assembly mistakes while they are still visible.")

    assemblies_dir = ROOT / "assemblies"
    yaml_files = sorted([f.name for f in assemblies_dir.glob("*.yaml")])
    active_assembly = ASSEMBLY
    if yaml_files:
        default_idx = yaml_files.index("pc_build.yaml") if "pc_build.yaml" in yaml_files else 0
        chosen_yaml = st.sidebar.selectbox("Active Checklist", yaml_files, index=default_idx)
        active_assembly = assemblies_dir / chosen_yaml

    if "current_assembly_path" not in st.session_state or st.session_state.current_assembly_path != active_assembly:
        st.session_state.current_assembly_path = active_assembly
        st.session_state.session = Session(active_assembly)
        st.session_state.pop("last_result", None)
        st.session_state.pop("last_image", None)

    session: Session = st.session_state.session
    if "unit_id" not in st.session_state:
        st.session_state.unit_id = st.session_state.session.unit_id

    done, total = session.progress()
    st.progress(done / total if total else 1.0, text=f"Check {min(done + 1, total)} / {total}")

    serial = st.text_input(
        "Unit serial",
        key="unit_id",
        disabled=session.last_evidence_path is not None or bool(session.passed),
    )
    session.unit_id = serial.strip() or session.unit_id
    render_recent_evidence(session.unit_id, root=session.evidence_log.root)

    current = session.current()
    if current is None:
        st.success("All checks complete for this unit.")
        if session.overrides:
            st.caption(f"Overrides logged: {len(session.overrides)}")
        if st.button("Start new unit", type="primary"):
            st.session_state.session = Session(st.session_state.get("current_assembly_path", ASSEMBLY))
            st.session_state.pop("last_result", None)
            st.session_state.pop("last_image", None)
            st.session_state.pop("unit_id", None)
            st.rerun()
        return

    # Side-by-side comparison: Golden Reference on Left vs. Workstation on Right
    col_ref, col_inspect = st.columns([1, 1], gap="large")

    with col_ref:
        st.subheader("📌 What CORRECT looks like")
        st.markdown(f"**Step:** `{current['step_id']}` · `{current['check_id']}`")
        st.write(current["instruction"])
        st.info(f"**Question:** {current['question']}")
        if current.get("show"):
            st.caption(f"📐 **Camera Hint:** {current['show']}")

        ref_path_str = current.get("reference_photo")
        if ref_path_str:
            ref_path = ROOT / ref_path_str if not Path(ref_path_str).is_absolute() else Path(ref_path_str)
            if ref_path.exists():
                st.image(str(ref_path), caption="Golden Reference (Correct Standard)", use_container_width=True)
            else:
                st.caption(f"Reference file not found at: {ref_path_str}")
        else:
            st.caption("No reference photo specified for this step.")

    with col_inspect:
        st.subheader("🔬 Workstation (Unit under test)")
        st.caption(f"Passed: {sorted(session.passed) or '—'} · Retake streak: {session.retake_streak}")

        tab_upload, tab_camera = st.tabs(["Upload photo", "Camera"])
        image_file = None
        with tab_upload:
            image_file = st.file_uploader(
                "Workstation photo",
                type=["jpg", "jpeg", "png"],
                label_visibility="collapsed",
            )
            st.caption("Demo filenames: `*_ok_*`, `*_bad_*`, `*_blur_*`, or MVTec dataset `*defect*` (fake AI).")
        with tab_camera:
            camera = st.camera_input("Capture workstation")
            if camera is not None:
                image_file = camera

        col_check, col_override = st.columns([1, 1])
        with col_check:
            check_clicked = st.button(
                "Check photo",
                type="primary",
                use_container_width=True,
                disabled=image_file is None,
            )
        with col_override:
            with st.expander("Override (needs reason)"):
                override_reason = st.text_area(
                    "Why skip / accept this check?",
                    placeholder="e.g. verified by hand — clips fully seated",
                    height=80,
                )
                override_clicked = st.button("Accept override", use_container_width=True)

        if check_clicked and image_file is not None:
            name = getattr(image_file, "name", None) or "camera_capture.jpg"
            # Isolate uploads while preserving filename keywords for fake_ai.
            with tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / Path(name).name
                path.write_bytes(image_file.getvalue())
                try:
                    result = run_check(session, path)
                except (OSError, sqlite3.Error):
                    st.error(
                        "Could not save this check. Check disk space and folder permissions, then retry."
                    )
                    st.stop()
            st.session_state.last_result = result
            st.session_state.last_image = session.last_evidence_path
            if result["action"] == "pass":
                st.rerun()

        if override_clicked:
            result = session.override_pass(override_reason)
            st.session_state.last_result = result
            if result["action"] == "pass":
                st.rerun()

        if "last_result" in st.session_state:
            result = st.session_state.last_result
            render_badge(result["action"])
            st.write(result["reason"])
            if result.get("hint"):
                st.warning(result["hint"])

            img_path = st.session_state.get("last_image")
            if img_path and Path(img_path).exists():
                img = Image.open(img_path).convert("RGB")
                st.image(
                    draw_box(img, result.get("problem_box")),
                    caption="Checked frame (Defect highlighted with red box)" if result.get("problem_box") else "Checked frame",
                    use_container_width=True,
                )


if __name__ == "__main__":
    main()
