"""Read-only recent evidence list for the Worker UI (does not write to the DB)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import streamlit as st

from checker.evidence import DEFAULT_ROOT


def render_recent_evidence(unit_id: str | None = None, *, limit: int = 8) -> None:
    """Show latest evidence rows; optional filter to the current unit."""
    db_path = Path(DEFAULT_ROOT) / "evidence.sqlite3"
    with st.expander("Recent evidence", expanded=False):
        if not db_path.is_file():
            st.caption("No evidence database yet — run a check first.")
            return

        query = (
            "SELECT timestamp, unit_id, check_id, action, verdict, reason, frame_path "
            "FROM evidence"
        )
        params: tuple = ()
        if unit_id:
            query += " WHERE unit_id = ?"
            params = (unit_id,)
        query += " ORDER BY rowid DESC LIMIT ?"
        params = params + (limit,)

        try:
            with closing(sqlite3.connect(db_path)) as connection:
                rows = connection.execute(query, params).fetchall()
        except sqlite3.Error as exc:
            st.caption(f"Could not read evidence DB: {exc}")
            return

        if not rows:
            st.caption("No rows for this unit yet.")
            return

        for ts, uid, check_id, action, verdict, reason, frame_path in rows:
            st.markdown(
                f"**{action}** · `{check_id}` · {verdict or '—'} · `{uid}`  \n"
                f"<span style='color:#666;font-size:0.85rem'>{ts}</span>",
                unsafe_allow_html=True,
            )
            st.caption((reason or "")[:160])
            full = Path(DEFAULT_ROOT) / frame_path
            if full.is_file():
                st.image(str(full), width=220)
            st.divider()
