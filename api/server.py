"""HTTP API for the web worker station (web/).

A thin layer over the existing checker: every endpoint calls Session / run_check,
so the inspection rules stay in one place (checker/) for both Streamlit and the web app.

Run from the repo root:  uvicorn api.server:app --port 8000
If web/dist exists (npm run build), the same server also serves the frontend at /.
"""

from __future__ import annotations

import os
import re
import sqlite3
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api.custom_checklist import CustomChecklistError, build_custom_assembly, save_custom_assembly
from checker import Session, run_check
from checker.evidence import DEFAULT_ROOT, EvidenceLog
from checker.evidence_reader import EvidenceReader
from checker.loader import iter_checks, load_assembly

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLIES_DIR = ROOT / "assemblies"
WEB_BUILD_DIR = ROOT / "web" / "dist"
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # phone photos are a few MB; anything bigger is a mistake
SERIAL_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
SAVE_FAILED = "Could not save this check. Check disk space and folder permissions, then retry."


class StartUnitRequest(BaseModel):
    assembly: str = "pc_build.yaml"
    serial: str | None = None


class CustomUnitRequest(BaseModel):
    name: str = ""
    checks: list[str]  # what correct looks like, one check per line
    cover_step: str | None = None  # optional last step that hides earlier work (locked until all pass)
    serial: str | None = None


class ManualRequest(BaseModel):
    ok: bool
    note: str = ""


class OverrideRequest(BaseModel):
    reason: str


class UnitStore:
    """Units in progress, kept in memory for this server process (one demo station)."""

    def __init__(self, evidence_log: EvidenceLog):
        self.evidence_log = evidence_log
        self._sessions: dict[str, Session] = {}
        self._assembly_files: dict[str, str] = {}  # unit_id -> checklist file name
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()

    def start(self, assembly_path: Path, serial: str | None) -> Session:
        with self._guard:
            if serial is not None and serial in self._sessions:
                raise HTTPException(409, f"Unit {serial} is already in progress.")
            session = Session(assembly_path, unit_id=serial, evidence_log=self.evidence_log)
            self._sessions[session.unit_id] = session
            self._assembly_files[session.unit_id] = assembly_path.name
            self._locks[session.unit_id] = threading.Lock()
            return session

    def get(self, unit_id: str) -> Session:
        session = self._sessions.get(unit_id)
        if session is None:
            raise HTTPException(404, "Unknown unit. Start a new unit.")
        return session

    def assembly_file(self, unit_id: str) -> str:
        self.get(unit_id)
        return self._assembly_files[unit_id]

    def lock(self, unit_id: str) -> threading.Lock:
        """One action at a time per unit (an AI check can take many seconds)."""
        self.get(unit_id)
        return self._locks[unit_id]


# ---------- assemblies ----------

def list_assembly_files() -> list[Path]:
    """Top-level checklists only (assemblies/mvtec/* are benchmark checklists, not stations)."""
    return sorted(ASSEMBLIES_DIR.glob("*.yaml"))


def resolve_assembly(file_name: str) -> Path:
    for path in list_assembly_files():
        if path.name == file_name:
            return path
    raise HTTPException(404, f"Unknown assembly: {file_name}")


def reference_photo_path(check: dict[str, Any]) -> Path | None:
    """The check's reference photo, only if it exists inside assemblies/."""
    relative = check.get("reference_photo")
    if not relative:
        return None
    path = (ROOT / relative).resolve()
    if path.is_relative_to(ASSEMBLIES_DIR.resolve()) and path.is_file():
        return path
    return None


# ---------- JSON shapes sent to the browser ----------

def step_status(session: Session, index: int, check: dict[str, Any]) -> str:
    overridden = {item["check_id"] for item in session.overrides}
    if index < session.index:
        return "overridden" if check["check_id"] in overridden else "done"
    return "current" if index == session.index else "upcoming"


def current_check_state(session: Session, assembly_file: str) -> dict[str, Any] | None:
    check = session.current()
    if check is None:
        return None
    has_reference = reference_photo_path(check) is not None
    return {
        "check_id": check["check_id"],
        "step_id": check["step_id"],
        "kind": check["kind"],
        "instruction": check["instruction"],
        "question": check["question"],
        "show": check.get("show") or None,
        "hides": check.get("hides", False),
        "requires": check.get("requires", []),
        "gate": session.gate_status(check),
        "reference_url": (
            f"/api/assemblies/{assembly_file}/checks/{check['check_id']}/reference" if has_reference else None
        ),
    }


def unit_state(session: Session, assembly_file: str) -> dict[str, Any]:
    done, total = session.progress()
    return {
        "unit_id": session.unit_id,
        "assembly": session.assembly["assembly"],
        "assembly_file": assembly_file,
        "done": done,
        "total": total,
        "complete": session.current() is None,
        "retake_streak": session.retake_streak,
        "overrides": list(session.overrides),
        "steps": [
            {
                "check_id": check["check_id"],
                "step_id": check["step_id"],
                "instruction": check["instruction"],
                "kind": check["kind"],
                "hides": check.get("hides", False),
                "requires": check.get("requires", []),
                "status": step_status(session, index, check),
            }
            for index, check in enumerate(session.checks)
        ],
        "current": current_check_state(session, assembly_file),
    }


def evidence_photo_url(path: Path | None) -> str | None:
    return f"/api/evidence/photos/{path.name}" if path is not None else None


def clean_serial(serial: str | None) -> str | None:
    serial = serial.strip() if serial else None
    if serial and not SERIAL_PATTERN.match(serial):
        raise HTTPException(400, "Serial may use letters, digits, '.', '_' and '-' (max 64).")
    return serial or None


# ---------- running an action safely ----------

def save_upload(photo: UploadFile, directory: Path) -> Path:
    """Write the upload to a temp file, keeping its name (the fake AI reads filename keywords)."""
    data = photo.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Photo is too large (max 15 MB).")
    path = directory / Path(photo.filename or "camera_capture.jpg").name
    path.write_bytes(data)
    return path


def run_saving_evidence(action: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Storage must succeed before progress counts; report a clear error instead of a crash."""
    try:
        return action()
    except (OSError, sqlite3.Error):
        raise HTTPException(503, SAVE_FAILED) from None


def ai_mode() -> dict[str, Any]:
    """What the UI shows in its status badge. Never includes the API key."""
    fake = os.getenv("USE_FAKE_AI", "true").strip().lower() in {"1", "true", "yes", "on"}
    return {"ai": "fake" if fake else "real", "model": None if fake else os.getenv("VLLM_MODEL")}


# ---------- the app ----------

def create_app(evidence_root: str | Path = DEFAULT_ROOT) -> FastAPI:
    app = FastAPI(title="Multilönd API")
    store = UnitStore(EvidenceLog(evidence_root))
    reader = EvidenceReader(evidence_root)
    custom_folder = Path(evidence_root).parent / "custom_checklists"  # data/ is gitignored

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"ok": True, **ai_mode()}

    @app.get("/api/assemblies")
    def assemblies() -> list[dict[str, Any]]:
        listed = []
        for path in list_assembly_files():
            assembly = load_assembly(path)
            listed.append({"file": path.name, "name": assembly["assembly"], "checks": len(iter_checks(assembly))})
        return listed

    @app.get("/api/assemblies/{assembly_file}/checks/{check_id}/reference")
    def reference_photo(assembly_file: str, check_id: str) -> FileResponse:
        checks = iter_checks(load_assembly(resolve_assembly(assembly_file)))
        check = next((c for c in checks if c["check_id"] == check_id), None)
        path = reference_photo_path(check) if check else None
        if path is None:
            raise HTTPException(404, "No reference photo for this check.")
        return FileResponse(path)

    @app.post("/api/units")
    def start_unit(request: StartUnitRequest) -> dict[str, Any]:
        session = store.start(resolve_assembly(request.assembly), clean_serial(request.serial))
        return unit_state(session, request.assembly)

    @app.post("/api/units/custom")
    def start_custom_unit(request: CustomUnitRequest) -> dict[str, Any]:
        """A checklist the user wrote: one 'what correct looks like' line per check."""
        serial = clean_serial(request.serial)
        try:
            assembly = build_custom_assembly(request.name, request.checks, request.cover_step)
            path = save_custom_assembly(assembly, custom_folder)
        except CustomChecklistError as error:
            raise HTTPException(400, str(error)) from None
        session = store.start(path, serial)
        return unit_state(session, store.assembly_file(session.unit_id))

    @app.get("/api/units/{unit_id}")
    def get_unit(unit_id: str) -> dict[str, Any]:
        session = store.get(unit_id)
        return unit_state(session, store.assembly_file(unit_id))

    @app.post("/api/units/{unit_id}/check")
    def check_photo(unit_id: str, photo: UploadFile = File(...)) -> dict[str, Any]:
        session = store.get(unit_id)
        with store.lock(unit_id), tempfile.TemporaryDirectory() as temp_dir:
            path = save_upload(photo, Path(temp_dir))
            previous_photo = session.last_evidence_path
            result = run_saving_evidence(lambda: run_check(session, path))
        # Only link a photo if this attempt stored one (e.g. a manual step stores none).
        new_photo = session.last_evidence_path if session.last_evidence_path != previous_photo else None
        return {
            "result": {**result, "photo_url": evidence_photo_url(new_photo)},
            "unit": unit_state(session, store.assembly_file(unit_id)),
        }

    @app.post("/api/units/{unit_id}/manual")
    def confirm_manual(unit_id: str, request: ManualRequest) -> dict[str, Any]:
        session = store.get(unit_id)
        with store.lock(unit_id):
            result = run_saving_evidence(lambda: session.confirm_manual(request.ok, request.note))
        return {"result": {**result, "photo_url": None}, "unit": unit_state(session, store.assembly_file(unit_id))}

    @app.post("/api/units/{unit_id}/gate")
    def confirm_gate(unit_id: str) -> dict[str, Any]:
        session = store.get(unit_id)
        with store.lock(unit_id):
            result = run_saving_evidence(session.confirm_gate)
        return {"result": {**result, "photo_url": None}, "unit": unit_state(session, store.assembly_file(unit_id))}

    @app.post("/api/units/{unit_id}/override")
    def override(unit_id: str, request: OverrideRequest) -> dict[str, Any]:
        session = store.get(unit_id)
        with store.lock(unit_id):
            result = session.override_pass(request.reason)
        return {"result": {**result, "photo_url": None}, "unit": unit_state(session, store.assembly_file(unit_id))}

    @app.get("/api/evidence")
    def evidence(unit_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        try:
            records = reader.recent(unit_id=unit_id, limit=limit)
        except ValueError as error:
            raise HTTPException(400, str(error)) from None
        items = [
            {**{key: value for key, value in record.items() if key not in {"photo_path", "frame_path"}},
             "photo_url": evidence_photo_url(record["photo_path"])}
            for record in records
        ]
        return {"summary": reader.summary(unit_id=unit_id), "items": items}

    @app.get("/api/evidence/photos/{file_name}")
    def evidence_photo(file_name: str) -> FileResponse:
        frames_dir = store.evidence_log.frames_dir.resolve()
        path = (frames_dir / file_name).resolve()
        if path.parent != frames_dir or not path.is_file():
            raise HTTPException(404, "Photo not found.")
        return FileResponse(path)

    if WEB_BUILD_DIR.is_dir():
        app.mount("/", StaticFiles(directory=WEB_BUILD_DIR, html=True), name="web")
    return app


app = create_app()
