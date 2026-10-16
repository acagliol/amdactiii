"""Manager Dashboard — Quality operations & unit audit view.

Designed for Quality Operations Managers and Line Supervisors:
- High-density KPI metric overview
- Check-level failure rates and bottleneck identification
- Serialized unit audit trail with step history and photo records
- Defect photo inspection stream
"""

from __future__ import annotations

import sys
from datetime import datetime, time, timezone
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.shared import (  # noqa: E402
    BADGE_PALETTE,
    available_assemblies,
    create_reader,
    fmt_pct,
    fmt_timestamp,
    inject_custom_css,
    is_seeded_db,
    render_badge_html,
    render_sample_data_banner,
    safe_by_check,
    safe_by_unit,
    safe_recent,
    safe_summary,
)


def _build_filters() -> dict:
    """Render sidebar filters and return kwargs for EvidenceReader queries."""
    st.sidebar.subheader("Filter Scope")
    filters: dict = {}

    assemblies = available_assemblies()
    if assemblies:
        options = ["All Assemblies"] + [
            f.replace(".yaml", "").replace("_", " ").title() for f in assemblies
        ]
        choice = st.sidebar.selectbox("Assembly Model", options, index=0)
        if choice != "All Assemblies":
            idx = options.index(choice) - 1
            import yaml
            yaml_path = ROOT / "assemblies" / assemblies[idx]
            try:
                with yaml_path.open() as f:
                    doc = yaml.safe_load(f)
                filters["assembly"] = doc.get("assembly", choice)
            except Exception:
                filters["assembly"] = choice

    action_options = ["All Actions", "pass", "fix", "retake", "supervisor"]
    action_choice = st.sidebar.selectbox(
        "Action Type",
        action_options,
        index=0,
        format_func=lambda x: "All Actions" if x == "All Actions" else x.capitalize(),
    )
    if action_choice != "All Actions":
        filters["action"] = action_choice

    col_s, col_e = st.sidebar.columns(2)
    with col_s:
        start_date = st.date_input("From", value=None, key="mgr_start")
    with col_e:
        end_date = st.date_input("To", value=None, key="mgr_end")
    if start_date:
        filters["start"] = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
    if end_date:
        filters["end"] = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)

    return filters


def _render_kpis(totals: dict) -> None:
    """High-level summary metrics bar."""
    attempts = totals["attempts"]
    units = totals["units_seen"]
    pass_count = totals["actions"]["pass"]
    fix_count = totals["actions"]["fix"]
    sup_count = totals["actions"]["supervisor"]

    pass_rate = pass_count / attempts if attempts else 0.0
    defect_rate = fix_count / attempts if attempts else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Inspections", f"{attempts:,}")
    with c2:
        st.metric("Units Inspected", f"{units:,}")
    with c3:
        st.metric("Overall Pass Rate", fmt_pct(pass_rate))
    with c4:
        st.metric("Defects Flagged", f"{fix_count:,}", delta=f"{fmt_pct(defect_rate)} failure rate")
    with c5:
        st.metric("Supervisor Escalations", f"{sup_count:,}")


def _render_check_table(checks: list[dict]) -> None:
    """Industrial data table showing per-check quality performance."""
    st.subheader("Step-Level Quality Analysis")
    st.caption("Aggregated failure rates by assembly step. Sorted by lowest pass rate first.")

    if not checks:
        st.info("No check-level records found for the selected scope.")
        return

    rows_html = []
    for c in checks:
        pr = c["pass_rate"]
        if pr < 0.80:
            badge_style = "background:#fef2f2;color:#991b1b;border:1px solid #fecaca;"
        elif pr < 0.95:
            badge_style = "background:#fffbeb;color:#92400e;border:1px solid #fde68a;"
        else:
            badge_style = "background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;"

        rows_html.append(
            f"<tr>"
            f"<td style='font-weight:600;'>{c['step_id']}</td>"
            f"<td><code style='font-size:0.8rem;'>{c['check_id']}</code></td>"
            f"<td style='text-align:right;'>{c['units_seen']:,}</td>"
            f"<td style='text-align:right;'>{c['attempts']:,}</td>"
            f"<td style='text-align:center;'><span style='display:inline-block;padding:2px 8px;border-radius:4px;font-weight:700;font-size:0.75rem;{badge_style}'>{fmt_pct(pr)}</span></td>"
            f"<td style='text-align:right;color:#b91c1c;font-weight:600;'>{c['actions']['fix']:,}</td>"
            f"<td style='text-align:right;'>{c['actions']['retake']:,}</td>"
            f"<td style='text-align:right;'>{c['actions']['supervisor']:,}</td>"
            f"<td style='color:#64748b;font-size:0.78rem;'>{fmt_timestamp(c.get('last_timestamp'))}</td>"
            f"</tr>"
        )

    table_html = f"""
    <table class="ml-table">
        <thead>
            <tr>
                <th>Step</th>
                <th>Check ID</th>
                <th style="text-align:right;">Units</th>
                <th style="text-align:right;">Attempts</th>
                <th style="text-align:center;">Pass Rate</th>
                <th style="text-align:right;">Defects</th>
                <th style="text-align:right;">Retakes</th>
                <th style="text-align:right;">Escalated</th>
                <th>Last Inspected</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def _render_unit_audit_trail(reader, filters: dict) -> None:
    """Per-unit chronological inspection records with side-by-side photo review."""
    st.subheader("Unit Inspection Audit Trail")
    st.caption("Chronological ledger of serialized units with expandable check attempts and imagery.")

    units = safe_by_unit(reader, **filters, limit=50)
    if not units:
        st.info("No unit records found for the selected filter criteria.")
        return

    for unit in units:
        uid = unit["unit_id"]
        actions = unit["actions"]
        pills = []
        for key in ("pass", "fix", "retake", "supervisor"):
            count = actions.get(key, 0)
            if count > 0:
                p = BADGE_PALETTE[key]
                pills.append(
                    f"<span style='display:inline-flex;align-items:center;gap:4px;padding:1px 6px;"
                    f"border-radius:3px;font-size:0.72rem;font-weight:600;background:{p['bg']};"
                    f"color:{p['fg']};border:1px solid {p['border']};'>"
                    f"{p['label']}: {count}</span>"
                )
        pills_html = " ".join(pills)

        header_label = (
            f"Unit {uid} · {unit['assembly']} · {unit['checks_passed']} passed · "
            f"{unit['attempts']} attempts"
        )

        with st.expander(header_label, expanded=False):
            st.markdown(f"<div style='margin-bottom:8px;'>{pills_html}</div>", unsafe_allow_html=True)
            attempts = safe_recent(reader, unit_id=uid, limit=50)
            if not attempts:
                st.caption("No attempt records found.")
                continue

            for row in attempts:
                c_details, c_photo = st.columns([3, 1])
                with c_details:
                    st.markdown(
                        f"{render_badge_html(row['action'])} "
                        f"<strong><code>{row['check_id']}</code></strong> · "
                        f"<span style='color:#64748b;font-size:0.8rem;'>{fmt_timestamp(row.get('timestamp'))}</span>",
                        unsafe_allow_html=True,
                    )
                    reason = row.get("reason")
                    if reason:
                        st.markdown(
                            f"<div style='margin-top:4px;font-size:0.84rem;color:#334155;line-height:1.4;'>"
                            f"{reason}</div>",
                            unsafe_allow_html=True,
                        )
                with c_photo:
                    photo_path = row.get("photo_path")
                    if photo_path and Path(photo_path).exists():
                        st.image(str(photo_path), width=150)
                    else:
                        st.caption("No photo captured")
                st.markdown("<hr style='margin:8px 0;border:none;border-top:1px solid rgba(128,128,128,0.1);'>", unsafe_allow_html=True)


def _render_evidence_stream(reader, filters: dict) -> None:
    """Inspection photo stream with defect isolation."""
    st.subheader("Photo Evidence Stream")

    col_toggle, _ = st.columns([1, 3])
    with col_toggle:
        defects_only = st.toggle("Show defects only", value=False, key="mgr_defects_toggle")

    stream_filters = dict(filters)
    if defects_only:
        stream_filters["action"] = "fix"

    rows = safe_recent(reader, **stream_filters, limit=24)
    if not rows:
        st.info("No photographic records available for current filter selection.")
        return

    cols_per_row = 4
    for i in range(0, len(rows), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(rows):
                break
            record = rows[idx]
            with col:
                photo_path = record.get("photo_path")
                if photo_path and Path(photo_path).exists():
                    st.image(str(photo_path), use_container_width=True)
                else:
                    st.markdown(
                        "<div style='height:120px;border:1px dashed rgba(128,128,128,0.25);border-radius:4px;"
                        "display:flex;align-items:center;justify-content:center;color:#64748b;font-size:0.75rem;'>"
                        "Photo unavailable</div>",
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f"<div style='margin-top:4px;'>{render_badge_html(record['action'])} "
                    f"<code style='font-size:0.75rem;'>{record['check_id']}</code></div>"
                    f"<div style='font-size:0.72rem;color:#64748b;margin-top:2px;font-variant-numeric:tabular-nums;'>"
                    f"Unit: {record['unit_id'][:12]} · {fmt_timestamp(record.get('timestamp'))}</div>",
                    unsafe_allow_html=True,
                )


def main() -> None:
    inject_custom_css()

    st.title("Manager Dashboard")
    st.caption("Assembly line quality monitoring, bottleneck detection, and serialized audit history.")

    reader = create_reader()
    filters = _build_filters()

    if not reader.db_path.is_file():
        st.warning(
            "No active evidence database located. "
            "Complete inspection checks on the Worker Station to populate real-time quality records."
        )
        return

    if is_seeded_db(reader):
        render_sample_data_banner()

    totals = safe_summary(reader, **filters)
    if totals["attempts"] == 0:
        st.info("No inspection records match the selected scope. Adjust the filter criteria.")
        return

    _render_kpis(totals)

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    tab_checks, tab_audit, tab_stream = st.tabs([
        "Step Failure Rates", "Unit Audit Trail", "Photo Evidence Stream"
    ])

    with tab_checks:
        checks = safe_by_check(reader, **filters)
        _render_check_table(checks)

    with tab_audit:
        _render_unit_audit_trail(reader, filters)

    with tab_stream:
        _render_evidence_stream(reader, filters)


main()
