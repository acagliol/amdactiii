# Evidence integration for Tiff

Thomas owns the evidence queries; Tiff owns the manager and CEO pages.
The Worker evidence panel already uses the shared reader. Dashboard pages
are not present on `main` yet; they can import this API when added.

```python
from datetime import datetime, timezone
import streamlit as st
from checker.evidence_reader import EvidenceReader

reader = EvidenceReader()  # Defaults to data/evidence/ in this checkout.
filters = {
    "assembly": "PC build",
    "start": datetime(2026, 10, 13, tzinfo=timezone.utc),
    "end": datetime(2026, 10, 14, tzinfo=timezone.utc),
}
totals = reader.summary(**filters)
rows = reader.recent(**filters, limit=50, offset=0)

# In a Streamlit page:
st.metric("Logged attempts", totals["attempts"])
st.metric("Units with evidence", totals["units_seen"])
for row in rows:
    st.write(row["unit_id"], row["action"], row["reason"])
    if row["photo_path"] is not None:
        st.image(str(row["photo_path"]))
```

Both methods accept optional exact-match
`unit_id`, `assembly`, and `action` filters, plus timezone-aware `start` and `end`.
Dates include the start and exclude the end. Local timezone boundaries are
converted to UTC. `recent` returns newest first, defaults to 100 rows, and accepts
limits from 1 to 500 plus a nonnegative offset. `summary` counts every match.

Rows contain all SQLite columns, decoded `problem_box` coordinates (0–1000),
and an absolute `photo_path` (`Path` or `None`). The original `frame_path` stays
relative to the evidence root. Missing or unsafe photo paths return `None`;
the record still counts. Use the normalized box to draw the defect overlay.

Summary keys: `attempts`, `units_seen`, `actions` (pass/fix/retake/supervisor),
`verdicts` (yes/no/cant_tell/no_verdict), `first_timestamp`, `last_timestamp`.
`no_verdict` counts SQL NULL, including quality and prerequisite gates.
`units_seen` counts distinct serials with matching evidence, across assemblies.

These are attempt metrics, not completed-unit totals, first-pass yield, defect
accuracy, or financial savings. Repeated checks count separately. Overrides and
manual checks without photos are not fully persisted. A gate can pass without
a vision verdict; a manual check with a photo can have a yes/no verdict.

Both pages must access the same evidence directory as the Worker, including
`frames/`. For another location, use `EvidenceReader(root=path_to_directory)`.
The reader opens SQLite in read-only mode and creates nothing. Missing stores
return empty rows and zero counts; database/schema errors raise `sqlite3.Error`
and should be shown as unavailable data. Reads are fresh on each call; rerun
or refresh the page for new records. Avoid caching without invalidation.

Run `python -m unittest tests.test_evidence_reader -v` to check the integration.
No new dependencies or database migrations are required.
