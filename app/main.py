"""Multilönd AI — Multi-page Streamlit portal entry point.

Run: streamlit run app/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.shared import inject_custom_css  # noqa: E402


def main() -> None:
    st.set_page_config(
        page_title="Multilönd AI",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_custom_css()

    st.title("Multilönd AI")
    st.caption("Active computer vision inspection for precision hardware manufacturing.")

    st.markdown("<hr style='margin:16px 0 24px;border:none;border-top:1px solid rgba(128,128,128,0.12);'>", unsafe_allow_html=True)

    # ── Role Workspaces Overview ──
    st.subheader("Operational Workspaces")
    st.caption("Select a workspace from the sidebar navigation to begin.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            """
            <div class="ml-card">
                <div class="ml-card-header">
                    <span class="ml-card-title">Worker Station</span>
                    <span class="ml-card-meta">Operator</span>
                </div>
                <div style="font-size:0.83rem;color:var(--text-color, #475569);line-height:1.45;margin-top:6px;">
                    Step-by-step visual guidance with automated inspection. Compares live workstation captures against golden reference imagery before parts are enclosed.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="ml-card">
                <div class="ml-card-header">
                    <span class="ml-card-title">Manager Dashboard</span>
                    <span class="ml-card-meta">Quality Ops</span>
                </div>
                <div style="font-size:0.83rem;color:var(--text-color, #475569);line-height:1.45;margin-top:6px;">
                    Aggregated step failure rates, assembly line bottlenecks, serialized unit audit trails, and defect image inspection streams.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="ml-card">
                <div class="ml-card-header">
                    <span class="ml-card-title">Executive Summary</span>
                    <span class="ml-card-meta">Leadership</span>
                </div>
                <div style="font-size:0.83rem;color:var(--text-color, #475569);line-height:1.45;margin-top:6px;">
                    SLA benchmark compliance (catch rate vs. false alarms), downstream warranty cost avoidance calculations, and rollout readiness assessments.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            """
            <div class="ml-card">
                <div class="ml-card-header">
                    <span class="ml-card-title">Checklist Setup</span>
                    <span class="ml-card-meta">Supervisor</span>
                </div>
                <div style="font-size:0.83rem;color:var(--text-color, #475569);line-height:1.45;margin-top:6px;">
                    Author, validate, and publish assembly checklists, inspection prompts, camera guidance, and quality gates with real-time schema linting.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # ── System Data Stores Status ──
    st.subheader("Data Store Status")
    evidence_db = ROOT / "data" / "evidence" / "evidence.sqlite3"
    scorecard = ROOT / "eval" / "scorecard.json"

    s1, s2 = st.columns(2)
    with s1:
        if evidence_db.is_file():
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:8px;font-size:0.83rem;color:#166534;background:#f0fdf4;padding:8px 12px;border:1px solid #bbf7d0;border-radius:4px;">
                    <span style="width:7px;height:7px;border-radius:50%;background:#166534;"></span>
                    <span><strong>Live Evidence Database:</strong> Active and connected at <code>data/evidence/evidence.sqlite3</code></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:8px;font-size:0.83rem;color:#92400e;background:#fffbeb;padding:8px 12px;border:1px solid #fde68a;border-radius:4px;">
                    <span style="width:7px;height:7px;border-radius:50%;background:#92400e;"></span>
                    <span><strong>Live Evidence Database:</strong> Pending initial run (complete inspections on Worker Station to generate records).</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with s2:
        if scorecard.is_file():
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:8px;font-size:0.83rem;color:#166534;background:#f0fdf4;padding:8px 12px;border:1px solid #bbf7d0;border-radius:4px;">
                    <span style="width:7px;height:7px;border-radius:50%;background:#166534;"></span>
                    <span><strong>Evaluation Benchmark Scorecard:</strong> Available at <code>eval/scorecard.json</code></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:8px;font-size:0.83rem;color:#475569;background:#f8fafc;padding:8px 12px;border:1px solid #e2e8f0;border-radius:4px;">
                    <span style="width:7px;height:7px;border-radius:50%;background:#64748b;"></span>
                    <span><strong>Evaluation Benchmark Scorecard:</strong> Not yet generated (run <code>python eval/evaluate.py</code>).</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
