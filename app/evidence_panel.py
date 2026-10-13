"""Read-only recent evidence list for the Worker UI (does not write to the DB)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import streamlit as st

from checker.evidence import DEFAULT_ROOT
from checker.evidence_reader import EvidenceReader


def render_recent_evidence(
    unit_id: str | None = None, *, limit: int = 8, root: str | Path = DEFAULT_ROOT,
) -> None:
    """Show latest evidence rows; optional filter to the current unit."""
    reader = EvidenceReader(root)
    with st.expander("Recent evidence", expanded=False):
        if not reader.db_path.is_file():
            st.caption("No evidence database yet — run a check first.")
            return

        try:
            rows = reader.recent(unit_id=unit_id, limit=limit)
        except sqlite3.Error as exc:
            st.caption(f"Could not read evidence DB: {exc}")
            return

        if not rows:
            st.caption("No rows for this unit yet.")
            return

        for row in rows:
            st.markdown(
                f"**{row['action']}** · `{row['check_id']}` · {row['verdict'] or '—'} · `{row['unit_id']}`"
            )
            st.caption(row["timestamp"])
            st.caption(row["reason"][:160])
            if row["photo_path"] is not None:
                st.image(str(row["photo_path"]), width=220)
            else:
                st.caption("Photo unavailable.")
            st.divider()
