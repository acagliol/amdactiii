"""Shared design system tokens, helpers, and data connectors for Multilönd AI."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "data" / "evidence"
SCORECARD_PATH = ROOT / "eval" / "scorecard.json"
ASSEMBLIES_DIR = ROOT / "assemblies"

# Design tokens: restrained, enterprise-grade semantic colors
BADGE_PALETTE = {
    "pass": {
        "label": "Pass",
        "fg": "#15803d",
        "bg": "#f0fdf4",
        "border": "#bbf7d0",
    },
    "fix": {
        "label": "Defect",
        "fg": "#b91c1c",
        "bg": "#fef2f2",
        "border": "#fecaca",
    },
    "retake": {
        "label": "Retake",
        "fg": "#b45309",
        "bg": "#fffbeb",
        "border": "#fde68a",
    },
    "supervisor": {
        "label": "Escalated",
        "fg": "#4338ca",
        "bg": "#eef2ff",
        "border": "#c7d2fe",
    },
}

# Cost-per-defect assumption for the 1-10-100 rule savings calculation
DEFAULT_COST_PER_HIDDEN_DEFECT = 50  # dollars


def inject_custom_css() -> None:
    """Inject understated, cohesive typography, table, and spacing styles."""
    st.markdown(
        """
        <style>
        /* Base typography & density */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            letter-spacing: -0.01em;
        }

        /* Metric card styling: crisp, restrained, no huge gaps */
        [data-testid="stMetric"] {
            background-color: var(--secondary-background-color, rgba(128, 128, 128, 0.05));
            border: 1px solid var(--border-color, rgba(128, 128, 128, 0.15));
            border-radius: 6px;
            padding: 10px 14px;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            color: var(--text-color, #475569) !important;
            opacity: 0.8;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.45rem !important;
            font-weight: 700 !important;
            font-variant-numeric: tabular-nums;
            color: var(--text-color, #0f172a) !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.72rem !important;
            font-weight: 500 !important;
        }

        /* Cleaner tabs: underline style instead of pill bloat */
        .stTabs [data-baseweb="tab-list"] {
            gap: 16px;
            border-bottom: 1px solid var(--border-color, rgba(128, 128, 128, 0.15));
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 4px;
            font-size: 0.85rem;
            font-weight: 500;
        }

        /* Tables & data frames */
        table.ml-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.85rem;
            border: 1px solid var(--border-color, rgba(128, 128, 128, 0.15));
            border-radius: 6px;
            overflow: hidden;
            margin: 8px 0;
        }
        table.ml-table th {
            background-color: var(--secondary-background-color, rgba(128, 128, 128, 0.06));
            padding: 8px 12px;
            font-weight: 600;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-color, #475569);
            border-bottom: 1px solid var(--border-color, rgba(128, 128, 128, 0.15));
            text-align: left;
        }
        table.ml-table td {
            padding: 8px 12px;
            border-bottom: 1px solid var(--border-color, rgba(128, 128, 128, 0.08));
            vertical-align: middle;
            font-variant-numeric: tabular-nums;
        }
        table.ml-table tr:last-child td {
            border-bottom: none;
        }
        table.ml-table tr:hover td {
            background-color: var(--secondary-background-color, rgba(128, 128, 128, 0.04));
        }

        /* Clean callout banner without neon gradients */
        .ml-banner {
            border: 1px solid var(--border-color, rgba(128, 128, 128, 0.15));
            border-radius: 6px;
            padding: 12px 16px;
            margin-bottom: 16px;
            background-color: var(--secondary-background-color, rgba(128, 128, 128, 0.04));
        }
        .ml-banner-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-color, #0f172a);
            margin: 0;
        }
        .ml-banner-desc {
            font-size: 0.78rem;
            color: var(--text-color, #64748b);
            opacity: 0.85;
            margin: 2px 0 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_reader(root: str | Path | None = None):
    """Return an EvidenceReader; import here to avoid circular deps at module level."""
    from checker.evidence_reader import EvidenceReader
    if root is None:
        try:
            root = st.session_state.get("evidence_root", EVIDENCE_ROOT)
        except Exception:
            root = EVIDENCE_ROOT
    return EvidenceReader(root)


def load_scorecard(path: str | Path | None = None) -> dict[str, Any]:
    """Load eval/scorecard.json, returning {} if missing or invalid."""
    if path is None:
        try:
            path = st.session_state.get("scorecard_path", SCORECARD_PATH)
        except Exception:
            path = SCORECARD_PATH
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        with p.open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def available_assemblies() -> list[str]:
    """List YAML assembly files in assemblies/."""
    return sorted([f.name for f in ASSEMBLIES_DIR.glob("*.yaml")])


def safe_summary(reader, **filters) -> dict[str, Any]:
    """Call reader.summary() with sqlite error handling."""
    try:
        return reader.summary(**filters)
    except sqlite3.Error:
        return {
            "attempts": 0, "units_seen": 0,
            "actions": {"pass": 0, "fix": 0, "retake": 0, "supervisor": 0},
            "verdicts": {"yes": 0, "no": 0, "cant_tell": 0, "no_verdict": 0},
            "first_timestamp": None, "last_timestamp": None,
        }


def safe_by_check(reader, **filters) -> list[dict[str, Any]]:
    """Call reader.by_check() with sqlite error handling."""
    try:
        return reader.by_check(**filters)
    except sqlite3.Error:
        return []


def safe_by_unit(reader, **filters) -> list[dict[str, Any]]:
    """Call reader.by_unit() with sqlite error handling."""
    try:
        return reader.by_unit(**filters)
    except sqlite3.Error:
        return []


def safe_recent(reader, **filters) -> list[dict[str, Any]]:
    """Call reader.recent() with sqlite error handling."""
    try:
        return reader.recent(**filters)
    except sqlite3.Error:
        return []


def fmt_pct(value: float | None, decimals: int = 1) -> str:
    """Format a 0-1 float as a percentage string."""
    if value is None:
        return "n/a"
    return f"{value * 100:.{decimals}f}%"


def fmt_timestamp(ts: str | None) -> str:
    """Format an ISO timestamp string for display."""
    if not ts:
        return "—"
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%b %d, %H:%M UTC")
    except (ValueError, TypeError):
        return ts[:19] if ts else "—"


def render_badge_html(action: str) -> str:
    """Return HTML for an understated status pill badge."""
    style = BADGE_PALETTE.get(
        action,
        {"label": action.upper(), "fg": "#475569", "bg": "#f1f5f9", "border": "#cbd5e1"},
    )
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;padding:2px 8px;'
        f'border-radius:4px;font-size:0.75rem;font-weight:600;letter-spacing:0.02em;'
        f'background:{style["bg"]};color:{style["fg"]};border:1px solid {style["border"]}">'
        f'<span style="width:5px;height:5px;border-radius:50%;background:{style["fg"]}"></span>'
        f'{style["label"]}</span>'
    )


def render_kpi_target(
    label: str,
    value: float | None,
    target: float,
    higher_is_better: bool = True,
    fmt: str = "pct",
) -> None:
    """Render a KPI metric with target compliance indicator."""
    if value is None:
        st.metric(label, "n/a")
        return
    if fmt == "pct":
        display = fmt_pct(value)
        target_str = fmt_pct(target)
    else:
        display = f"{value:.2f}s"
        target_str = f"{target:.1f}s"

    if higher_is_better:
        hit = value >= target
    else:
        hit = value <= target

    status = "Target met" if hit else "Below target"
    st.metric(
        label,
        display,
        delta=f"{status} (target: {target_str})",
        delta_color="normal" if hit else "inverse",
    )
