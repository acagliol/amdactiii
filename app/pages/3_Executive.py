"""Executive Summary — High-level defect prevention and business impact.

Designed for Operations Leadership, COO, and Executive Stakeholders:
- Verification against critical quality SLAs (Catch rate, False alarm rate, Latency)
- Live factory floor throughput and defect interception metrics
- Financial ROI model based on the 1-10-100 quality rule
- Defect category breakdown and rollout readiness assessment
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.shared import (  # noqa: E402
    DEFAULT_COST_PER_HIDDEN_DEFECT,
    create_reader,
    fmt_pct,
    inject_custom_css,
    is_seeded_db,
    load_scorecard,
    render_kpi_target,
    render_sample_data_banner,
    safe_summary,
)


def _render_scorecard(sc: dict) -> None:
    """Evaluation KPI scorecard from eval/scorecard.json."""
    st.subheader("Model Performance & SLA Compliance")
    frames = sc.get("frames", 0)
    clean = sc.get("clean_frames", 0)
    defect = sc.get("defect_frames", 0)
    st.caption(
        f"Benchmarked on {frames} standardized test frames "
        f"({clean} defect-free baseline, {defect} seeded defect conditions)."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_target(
            "Defect Catch Rate",
            sc.get("catch_rate"),
            target=0.90,
            higher_is_better=True,
        )
    with c2:
        render_kpi_target(
            "False Alarm Rate",
            sc.get("false_alarm_rate"),
            target=0.10,
            higher_is_better=False,
        )
    with c3:
        render_kpi_target(
            "Latency (P95)",
            sc.get("p95_latency_s"),
            target=5.0,
            higher_is_better=False,
            fmt="time",
        )
    with c4:
        render_kpi_target(
            "Grounding Hit Rate",
            sc.get("grounding_hit_rate"),
            target=0.75,
            higher_is_better=True,
        )


def _render_production_summary(totals: dict) -> None:
    """Live production throughput from the workstation evidence store."""
    st.subheader("Factory Floor Production Throughput")
    st.caption("Active data stream from assembly line inspection stations.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Serialized Units", f"{totals['units_seen']:,}")
    with c2:
        st.metric("Defects Intercepted", f"{totals['actions']['fix']:,}")
    with c3:
        st.metric("Checks Completed", f"{totals['attempts']:,}")
    with c4:
        pass_count = totals["actions"]["pass"]
        fix_count = totals["actions"]["fix"]
        decisive = pass_count + fix_count
        fpy = pass_count / decisive if decisive else 0.0
        st.metric(
            "First-Pass Yield (est.)",
            fmt_pct(fpy),
            help="Estimated as pass / (pass + fix). Retakes are resolved on-station.",
        )


def _render_savings_model(totals: dict) -> None:
    """Estimated warranty and rework cost avoidance based on the 1-10-100 rule."""
    st.subheader("Warranty & Rework Cost Avoidance Model")
    st.caption(
        "Based on the industrial 1-10-100 quality rule: intercepting an assembly defect on-station "
        "avoids $10 to $100+ in downstream testing, rework, RMA warranty, and field recall costs."
    )

    defects_caught = totals["actions"]["fix"]

    col_slider, col_display = st.columns([2, 3])
    with col_slider:
        cost_per = st.slider(
            "Average downstream escape cost ($ / defect)",
            min_value=10,
            max_value=200,
            value=DEFAULT_COST_PER_HIDDEN_DEFECT,
            step=10,
            key="ceo_cost_slider",
            help="Conservative blended estimate of downstream rework, technician diagnostics, and warranty claims.",
        )

    savings = defects_caught * cost_per

    with col_display:
        c_a, c_b, c_c = st.columns(3)
        with c_a:
            st.metric("Escapes Prevented", f"{defects_caught:,}")
        with c_b:
            st.metric("Cost per Escape", f"${cost_per:,}")
        with c_c:
            st.metric("Net Cost Avoidance", f"${savings:,.0f}")


def _render_category_breakdown(sc: dict) -> None:
    """Breakdown of detection rate across defect categories."""
    by_cat = sc.get("by_category", {})
    if not by_cat:
        return

    st.subheader("Detection Accuracy by Defect Typology")
    st.caption("Verification of detection reliability across specific defect classes.")

    rows_html = []
    for cat, data in by_cat.items():
        rate = data.get("rate", 0.0)
        caught = data.get("caught", 0)
        total = data.get("total", 0)

        if cat == "good":
            label = "Defect-free baseline (Pass accuracy)"
            status_style = "background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;" if rate >= 0.90 else "background:#fef2f2;color:#991b1b;border:1px solid #fecaca;"
        else:
            label = cat.replace("_", " ").title()
            if rate >= 0.90:
                status_style = "background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;"
            elif rate >= 0.75:
                status_style = "background:#fffbeb;color:#92400e;border:1px solid #fde68a;"
            else:
                status_style = "background:#fef2f2;color:#991b1b;border:1px solid #fecaca;"

        rows_html.append(
            f"<tr>"
            f"<td style='font-weight:600;'>{label}</td>"
            f"<td style='text-align:right;'>{total}</td>"
            f"<td style='text-align:right;'>{caught}</td>"
            f"<td style='text-align:center;'><span style='display:inline-block;padding:2px 8px;border-radius:4px;font-weight:700;font-size:0.75rem;{status_style}'>{fmt_pct(rate)}</span></td>"
            f"</tr>"
        )

    table_html = f"""
    <table class="ml-table">
        <thead>
            <tr>
                <th>Defect Category</th>
                <th style="text-align:right;">Sample Count</th>
                <th style="text-align:right;">Detected</th>
                <th style="text-align:center;">Detection Rate</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def _render_readiness_assessment(sc: dict, totals: dict) -> None:
    """Operational deployment recommendations based on benchmark and factory metrics."""
    st.subheader("Deployment Readiness Assessment")

    catch = sc.get("catch_rate")
    false_alarm = sc.get("false_alarm_rate")
    defects = totals["actions"]["fix"]
    supervisors = totals["actions"]["supervisor"]

    points = []
    if catch is not None:
        if catch >= 0.90:
            points.append(
                f"<strong>Detection Reliability Met:</strong> Intercepting {fmt_pct(catch)} of seeded defect states, "
                f"satisfying the ≥90.0% deployment threshold."
            )
        else:
            points.append(
                f"<strong>Detection Under Target:</strong> Current catch rate is {fmt_pct(catch)} (target: 90.0%). "
                f"Recommend prompt refinement or fine-tuning before line rollout."
            )

    if false_alarm is not None:
        if false_alarm <= 0.10:
            points.append(
                f"<strong>Worker Friction Contained:</strong> False alarm rate is {fmt_pct(false_alarm)} (target ≤ 10.0%), "
                f"ensuring line operators do not face frequent unwarranted interruptions."
            )
        else:
            points.append(
                f"<strong>High False Alarm Warning:</strong> False alarm rate of {fmt_pct(false_alarm)} exceeds the 10.0% target. "
                f"Worker fatigue risk is elevated."
            )

    if defects > 0:
        points.append(
            f"<strong>Interception In Action:</strong> {defects:,} defects were caught before assembly enclosure, "
            f"preventing expensive tear-down rework."
        )

    if supervisors > 0:
        points.append(
            f"<strong>Escalation Tracking:</strong> {supervisors:,} inspections required supervisor review. "
            f"Review edge-case imagery to refine inspection criteria."
        )

    if not points:
        points.append("Awaiting evaluation benchmark data and line inspection records.")

    for p in points:
        st.markdown(
            f"<div style='display:flex;gap:8px;margin-bottom:6px;font-size:0.85rem;line-height:1.45;color:#334155;'>"
            f"<span style='color:#64748b;line-height:1.45;'>•</span><span>{p}</span></div>",
            unsafe_allow_html=True,
        )


def main() -> None:
    inject_custom_css()

    st.title("Executive Summary")
    st.caption("AI-assisted inspection performance, defect avoidance economics, and production rollout status.")

    sc = load_scorecard()
    reader = create_reader()
    totals = safe_summary(reader)

    if is_seeded_db(reader):
        render_sample_data_banner()

    if sc:
        _render_scorecard(sc)
    else:
        st.info(
            "Evaluation scorecard not yet generated. "
            "Execute `python eval/evaluate.py` to produce benchmark SLA validation records at `eval/scorecard.json`."
        )

    st.markdown("<hr style='margin:20px 0;border:none;border-top:1px solid rgba(128,128,128,0.12);'>", unsafe_allow_html=True)

    has_evidence = reader.db_path.is_file() and totals["attempts"] > 0
    if has_evidence:
        _render_production_summary(totals)
        st.markdown("<hr style='margin:20px 0;border:none;border-top:1px solid rgba(128,128,128,0.12);'>", unsafe_allow_html=True)
        _render_savings_model(totals)
    else:
        st.info(
            "No live production records found in `data/evidence/`. "
            "Once assembly checks are executed on the Worker Station, live throughput and financial avoidance will display here."
        )

    st.markdown("<hr style='margin:20px 0;border:none;border-top:1px solid rgba(128,128,128,0.12);'>", unsafe_allow_html=True)

    if sc and sc.get("by_category"):
        _render_category_breakdown(sc)
        st.markdown("<hr style='margin:20px 0;border:none;border-top:1px solid rgba(128,128,128,0.12);'>", unsafe_allow_html=True)

    _render_readiness_assessment(sc, totals)


main()
