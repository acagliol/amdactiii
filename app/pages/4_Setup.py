"""Checklist Setup — Author, validate, and publish assembly checklists.

Designed for Manufacturing Supervisors and Quality Engineers:
- Visual step and check authoring (visual AI inspections, manual checks, gate steps)
- Direct YAML specification editor with two-way sync
- Real-time linting and validation via checker.lint
- Reference image attachment management
- Direct publishing to the assemblies directory
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.shared import available_assemblies, inject_custom_css  # noqa: E402
from checker.lint import lint_data  # noqa: E402
from checker.loader import load_assembly  # noqa: E402

ASSEMBLIES_DIR = ROOT / "assemblies"
REFS_DIR = ASSEMBLIES_DIR / "refs"


def _get_available_ref_photos() -> list[str]:
    """List relative paths of existing reference photos."""
    if not REFS_DIR.is_dir():
        return []
    valid_exts = {".png", ".jpg", ".jpeg"}
    photos = [
        f"assemblies/refs/{p.name}"
        for p in REFS_DIR.iterdir()
        if p.suffix.lower() in valid_exts
    ]
    return sorted(photos)


def _init_session_state() -> None:
    """Initialize checklist authoring session state."""
    if "setup_assembly_data" not in st.session_state:
        # Default to pc_build.yaml if present
        default_file = ASSEMBLIES_DIR / "pc_build.yaml"
        if default_file.is_file():
            try:
                st.session_state.setup_assembly_data = load_assembly(default_file)
                st.session_state.setup_filename = "pc_build.yaml"
            except Exception:
                st.session_state.setup_assembly_data = _blank_template()
                st.session_state.setup_filename = "new_assembly.yaml"
        else:
            st.session_state.setup_assembly_data = _blank_template()
            st.session_state.setup_filename = "new_assembly.yaml"


def _blank_template() -> dict[str, Any]:
    """Return an empty valid assembly template."""
    return {
        "assembly": "New Assembly",
        "steps": [
            {
                "id": "step_1",
                "instruction": "Assemble primary sub-component.",
                "checks": [
                    {
                        "id": "check_1",
                        "type": "visual",
                        "question": "Is the component seated correctly with no visible gap?",
                        "show": "Point camera directly at the connection interface, ~20 cm away.",
                        "reference_photo": "",
                    }
                ],
            }
        ],
    }


def _render_sidebar_controls() -> tuple[str, bool]:
    """Render sidebar for checklist loading, file management, and mode selection."""
    st.sidebar.subheader("Checklist Source")

    existing_files = available_assemblies()
    options = ["Create New Checklist"] + existing_files

    current_file = st.session_state.get("setup_filename", "pc_build.yaml")
    default_idx = options.index(current_file) if current_file in options else 0

    selected = st.sidebar.selectbox("Active File", options, index=default_idx)

    load_clicked = st.sidebar.button("Load Checklist", use_container_width=True)
    if load_clicked:
        if selected == "Create New Checklist":
            st.session_state.setup_assembly_data = _blank_template()
            st.session_state.setup_filename = "new_assembly.yaml"
            st.session_state.pop("setup_yaml_text", None)
            st.rerun()
        else:
            file_path = ASSEMBLIES_DIR / selected
            try:
                st.session_state.setup_assembly_data = load_assembly(file_path)
                st.session_state.setup_filename = selected
                st.session_state.pop("setup_yaml_text", None)
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Failed to load checklist: {e}")

    st.sidebar.markdown("<hr style='margin:12px 0;border:none;border-top:1px solid rgba(128,128,128,0.15);'>", unsafe_allow_html=True)
    st.sidebar.subheader("Editor Mode")
    editor_mode = st.sidebar.radio(
        "Interface",
        ["Structured Builder", "YAML Source Editor"],
        label_visibility="collapsed",
    )

    return editor_mode, selected == "Create New Checklist"


def _render_lint_status(data: Any) -> list[str]:
    """Run lint_data and display understated status banner."""
    errors = lint_data(data, root=ROOT)
    if not errors:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;
            background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;border-radius:4px;
            font-size:0.83rem;margin-bottom:16px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#166534;"></span>
                <span><strong>Specification Valid:</strong> Checklist satisfies all schema and prerequisite validation rules.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        errors_html = "".join(f"<li>{err}</li>" for err in errors)
        st.markdown(
            f"""
            <div style="padding:10px 14px;background:#fef2f2;color:#991b1b;
            border:1px solid #fecaca;border-radius:4px;font-size:0.83rem;margin-bottom:16px;">
                <div style="font-weight:600;margin-bottom:4px;">Validation Issues ({len(errors)})</div>
                <ul style="margin:0;padding-left:18px;line-height:1.4;">
                    {errors_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return errors


def _render_structured_builder(data: dict[str, Any]) -> dict[str, Any]:
    """Form-based checklist builder."""
    st.subheader("Assembly Metadata")

    c_name, c_file = st.columns([2, 1])
    with c_name:
        assembly_name = st.text_input(
            "Assembly Name",
            value=data.get("assembly", ""),
            help="Human-readable title displayed to line operators.",
        )
        data["assembly"] = assembly_name.strip()

    with c_file:
        current_fn = st.session_state.get("setup_filename", "custom_assembly.yaml")
        filename_input = st.text_input("Target Filename", value=current_fn)
        if filename_input.strip():
            if not filename_input.endswith(".yaml") and not filename_input.endswith(".yml"):
                filename_input += ".yaml"
            st.session_state.setup_filename = filename_input.strip()

    st.markdown("<hr style='margin:16px 0;border:none;border-top:1px solid rgba(128,128,128,0.12);'>", unsafe_allow_html=True)
    st.subheader("Assembly Steps & Checkpoints")
    st.caption("Define the sequential inspection steps, binary AI verification questions, manual actions, and gate closures.")

    steps = data.get("steps", [])
    if not isinstance(steps, list):
        steps = []
        data["steps"] = steps

    # Collect all known check IDs up to this point for prerequisite selectboxes
    defined_check_ids: list[str] = []
    for s in steps:
        if isinstance(s, dict):
            for c in s.get("checks", []) or []:
                if isinstance(c, dict) and c.get("id"):
                    defined_check_ids.append(c["id"])

    updated_steps = []
    for s_idx, step in enumerate(steps):
        s_id = step.get("id", f"step_{s_idx + 1}")
        instruction = step.get("instruction", "")
        is_gate = bool(step.get("requires") and not step.get("checks"))
        step_type = "Quality Gate" if is_gate else "Inspection Step"

        header = f"Step {s_idx + 1}: {s_id} ({step_type})"
        with st.expander(header, expanded=True):
            col_id, col_type = st.columns([2, 1])
            with col_id:
                new_sid = st.text_input(
                    "Step Identifier",
                    value=s_id,
                    key=f"sid_{s_idx}",
                    help="Unique machine identifier for this assembly stage.",
                )
            with col_type:
                kind_choice = st.selectbox(
                    "Step Category",
                    ["Inspection Step", "Quality Gate (Enclosure)"],
                    index=1 if is_gate else 0,
                    key=f"skind_{s_idx}",
                )

            new_instr = st.text_area(
                "Operator Instruction",
                value=instruction,
                height=68,
                key=f"sinstr_{s_idx}",
                help="Clear directive displayed on the worker screen.",
            )

            current_step_dict: dict[str, Any] = {
                "id": new_sid.strip(),
                "instruction": new_instr.strip(),
            }

            if kind_choice == "Quality Gate (Enclosure)":
                current_step_dict["hides"] = True
                # Gate steps require prerequisite checks
                available_prereqs = [c for c in defined_check_ids if c != new_sid]
                current_reqs = step.get("requires", [])
                selected_reqs = st.multiselect(
                    "Prerequisite Checks (Must Pass Before Enclosure)",
                    options=available_prereqs,
                    default=[r for r in current_reqs if r in available_prereqs],
                    key=f"sreqs_{s_idx}",
                    help="All selected checks must be verified before the operator can close or seal the component.",
                )
                current_step_dict["requires"] = selected_reqs
            else:
                checks = step.get("checks", [])
                if not checks:
                    checks = [
                        {
                            "id": f"{new_sid}_check",
                            "type": "visual",
                            "question": "Is the part assembled correctly?",
                            "show": "",
                            "reference_photo": "",
                        }
                    ]

                updated_checks = []
                for c_idx, check in enumerate(checks):
                    st.markdown(
                        f"<div style='font-size:0.8rem;font-weight:600;color:#475569;margin-top:10px;'>"
                        f"Check {c_idx + 1}</div>",
                        unsafe_allow_html=True,
                    )
                    c_id = check.get("id", f"{new_sid}_check_{c_idx + 1}")
                    c_type = check.get("type", "visual")
                    c_q = check.get("question", "")
                    c_show = check.get("show", "")
                    c_ref = check.get("reference_photo", "")

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        new_cid = st.text_input(
                            "Check Identifier",
                            value=c_id,
                            key=f"cid_{s_idx}_{c_idx}",
                        )
                    with c2:
                        new_ctype = st.selectbox(
                            "Verification Mode",
                            ["visual", "manual"],
                            index=0 if c_type == "visual" else 1,
                            key=f"ctype_{s_idx}_{c_idx}",
                            format_func=lambda x: "Visual AI Inspection" if x == "visual" else "Manual Confirmation",
                        )

                    new_q = st.text_input(
                        "Verification Question",
                        value=c_q,
                        key=f"cq_{s_idx}_{c_idx}",
                        help="Exact yes/no question evaluated by the vision AI or confirmed by hand.",
                    )

                    new_show = ""
                    new_ref = ""
                    if new_ctype == "visual":
                        c_cam, c_photo = st.columns([1, 1])
                        with c_cam:
                            new_show = st.text_input(
                                "Camera Guidance Hint",
                                value=c_show,
                                key=f"cshow_{s_idx}_{c_idx}",
                                placeholder="e.g. Point camera at RAM slot, ~20 cm away.",
                            )
                        with c_photo:
                            avail_refs = ["None"] + _get_available_ref_photos()
                            ref_idx = avail_refs.index(c_ref) if c_ref in avail_refs else 0
                            ref_choice = st.selectbox(
                                "Golden Reference Photo",
                                avail_refs,
                                index=ref_idx,
                                key=f"cref_{s_idx}_{c_idx}",
                            )
                            new_ref = "" if ref_choice == "None" else ref_choice

                    check_obj: dict[str, Any] = {
                        "id": new_cid.strip(),
                        "type": new_ctype,
                        "question": new_q.strip(),
                    }
                    if new_show.strip():
                        check_obj["show"] = new_show.strip()
                    if new_ref.strip():
                        check_obj["reference_photo"] = new_ref.strip()

                    updated_checks.append(check_obj)
                    if new_cid.strip() not in defined_check_ids:
                        defined_check_ids.append(new_cid.strip())

                current_step_dict["checks"] = updated_checks

            col_del, _ = st.columns([1, 5])
            with col_del:
                if st.button("Delete Step", key=f"del_step_{s_idx}", type="secondary"):
                    steps.pop(s_idx)
                    st.rerun()

            updated_steps.append(current_step_dict)

    data["steps"] = updated_steps

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    if st.button("Add Assembly Step", type="secondary"):
        new_idx = len(steps) + 1
        steps.append({
            "id": f"step_{new_idx}",
            "instruction": "New assembly operation instruction.",
            "checks": [
                {
                    "id": f"step_{new_idx}_check",
                    "type": "visual",
                    "question": "Is the part properly positioned?",
                    "show": "",
                    "reference_photo": "",
                }
            ],
        })
        st.rerun()

    return data


def _render_yaml_editor(data: dict[str, Any]) -> dict[str, Any]:
    """Direct YAML text editor with real-time validation."""
    st.subheader("YAML Specification Source")
    st.caption("Directly modify the assembly YAML specification.")

    if "setup_yaml_text" not in st.session_state:
        st.session_state.setup_yaml_text = yaml.dump(data, sort_keys=False, allow_unicode=True)

    yaml_text = st.text_area(
        "YAML Content",
        value=st.session_state.setup_yaml_text,
        height=450,
        label_visibility="collapsed",
    )
    st.session_state.setup_yaml_text = yaml_text

    try:
        parsed = yaml.safe_load(yaml_text)
        if isinstance(parsed, dict):
            return parsed
        else:
            st.error("YAML root must be a mapping dictionary.")
            return data
    except yaml.YAMLError as exc:
        st.error(f"YAML Syntax Error: {exc}")
        return data


def _render_ref_photo_uploader() -> None:
    """Upload reference photo to assemblies/refs/."""
    st.markdown("<hr style='margin:20px 0;border:none;border-top:1px solid rgba(128,128,128,0.12);'>", unsafe_allow_html=True)
    st.subheader("Reference Photo Management")
    st.caption("Upload golden reference images stored at assemblies/refs/ for worker side-by-side comparison.")

    uploaded_photo = st.file_uploader(
        "Upload Golden Reference Photo",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
        key="setup_ref_uploader",
    )

    if uploaded_photo is not None:
        REFS_DIR.mkdir(parents=True, exist_ok=True)
        target_path = REFS_DIR / Path(uploaded_photo.name).name
        target_path.write_bytes(uploaded_photo.getvalue())
        st.success(f"Uploaded reference photo saved to assemblies/refs/{target_path.name}")


def main() -> None:
    inject_custom_css()
    _init_session_state()

    st.title("Checklist Setup")
    st.caption("Author, validate, and publish assembly checklists and quality gate specifications.")

    editor_mode, is_new = _render_sidebar_controls()

    data = st.session_state.setup_assembly_data

    # Main authoring interface
    if editor_mode == "Structured Builder":
        data = _render_structured_builder(data)
        st.session_state.setup_assembly_data = data
        st.session_state.setup_yaml_text = yaml.dump(data, sort_keys=False, allow_unicode=True)
    else:
        data = _render_yaml_editor(data)
        st.session_state.setup_assembly_data = data

    st.markdown("<hr style='margin:20px 0;border:none;border-top:1px solid rgba(128,128,128,0.12);'>", unsafe_allow_html=True)

    # Real-time Linter execution
    errors = _render_lint_status(data)

    # Save & Publish section
    col_save, col_info = st.columns([1, 2])
    with col_save:
        target_filename = st.session_state.get("setup_filename", "custom_assembly.yaml")
        save_disabled = bool(errors)
        if st.button("Save and Publish Checklist", type="primary", disabled=save_disabled, use_container_width=True):
            save_path = ASSEMBLIES_DIR / target_filename
            try:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with save_path.open("w", encoding="utf-8") as f:
                    yaml.dump(data, f, sort_keys=False, allow_unicode=True)
                st.success(f"Checklist published to assemblies/{target_filename}. Available immediately on the Worker Station.")
            except Exception as e:
                st.error(f"Failed to write checklist file: {e}")

    with col_info:
        if errors:
            st.caption("Resolve all validation issues above to enable publishing.")
        else:
            st.caption(f"Ready to publish to assemblies/{st.session_state.get('setup_filename', 'custom_assembly.yaml')}")

    # Reference Photo Manager
    _render_ref_photo_uploader()


main()
