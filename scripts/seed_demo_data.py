"""Seed realistic demo evidence records for presentation and dashboard preview."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "data" / "evidence"
FRAMES_DIR = EVIDENCE_DIR / "frames"
DB_PATH = EVIDENCE_DIR / "evidence.sqlite3"

FRAMES_DIR.mkdir(parents=True, exist_ok=True)


def make_frame(color: tuple[int, int, int], text: str, box: list[int] | None = None) -> Image.Image:
    img = Image.new("RGB", (640, 480), color=color)
    draw = ImageDraw.Draw(img)
    draw.text((24, 24), text, fill=(255, 255, 255))
    if box:
        ymin, xmin, ymax, xmax = box
        draw.rectangle(
            [xmin * 640 // 1000, ymin * 480 // 1000, xmax * 640 // 1000, ymax * 480 // 1000],
            outline="#ef4444",
            width=4,
        )
        draw.text(
            (xmin * 640 // 1000 + 6, ymin * 480 // 1000 + 6),
            "DEFECT PINPOINTED",
            fill="#ef4444",
        )
    return img


def seed_database() -> int:
    base_ram_ok = ROOT / "assemblies" / "refs" / "ram_clips_ok.png"
    base_gpu_ok = ROOT / "assemblies" / "refs" / "gpu_power_ok.png"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            unit_id TEXT NOT NULL,
            assembly TEXT NOT NULL,
            step_id TEXT NOT NULL,
            check_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            frame_path TEXT NOT NULL,
            verdict TEXT CHECK (verdict IN ('yes', 'no', 'cant_tell')),
            action TEXT NOT NULL CHECK (action IN ('pass', 'fix', 'retake', 'supervisor')),
            reason TEXT NOT NULL,
            problem_box TEXT,
            hint TEXT
        )
        """
    )
    c.execute("DELETE FROM evidence")

    now = datetime.now(timezone.utc)

    records = [
        # Unit 1: UNIT-PC-101 (Fully assembled cleanly)
        {
            "unit_id": "UNIT-PC-101",
            "assembly": "PC build",
            "step_id": "ram",
            "check_id": "ram_clips",
            "action": "pass",
            "verdict": "yes",
            "reason": "Both RAM retention clips are fully engaged against the DIMM module.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 120,
            "img_source": base_ram_ok,
        },
        {
            "unit_id": "UNIT-PC-101",
            "assembly": "PC build",
            "step_id": "gpu_power",
            "check_id": "gpu_power_seated",
            "action": "pass",
            "verdict": "yes",
            "reason": "GPU 12VHPWR connector is fully seated with no gap visible.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 115,
            "img_source": base_gpu_ok,
        },
        {
            "unit_id": "UNIT-PC-101",
            "assembly": "PC build",
            "step_id": "cpu_cooler",
            "check_id": "cooler_film_removed",
            "action": "pass",
            "verdict": "yes",
            "reason": "Cooler base contact plate is bare copper; protective plastic peel film removed.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 110,
            "label": "CPU Cooler Base - Film Removed (OK)",
            "color": (40, 60, 80),
        },
        {
            "unit_id": "UNIT-PC-101",
            "assembly": "PC build",
            "step_id": "cables",
            "check_id": "cables_clear_of_fans",
            "action": "pass",
            "verdict": "yes",
            "reason": "Wiring harnesses tied back; clearance verified around all fans.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 105,
            "label": "Chassis Wiring Clearance (OK)",
            "color": (50, 70, 60),
        },
        {
            "unit_id": "UNIT-PC-101",
            "assembly": "PC build",
            "step_id": "cables",
            "check_id": "fan_header_connected",
            "action": "pass",
            "verdict": None,
            "reason": "Confirmed CPU_FAN header connected securely by hand.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 100,
            "label": "Manual Check: CPU Fan Header",
            "color": (60, 50, 70),
        },
        {
            "unit_id": "UNIT-PC-101",
            "assembly": "PC build",
            "step_id": "close_panel",
            "check_id": "close_panel",
            "action": "pass",
            "verdict": None,
            "reason": "All 5 prerequisite checks passed. Side panel closed and latched.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 95,
            "label": "Chassis Panel Enclosed (Gate Pass)",
            "color": (40, 40, 50),
        },
        # Unit 2: UNIT-PC-102 (Defect caught on GPU power, fixed on retake)
        {
            "unit_id": "UNIT-PC-102",
            "assembly": "PC build",
            "step_id": "ram",
            "check_id": "ram_clips",
            "action": "pass",
            "verdict": "yes",
            "reason": "RAM retention clips verified locked in position.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 90,
            "img_source": base_ram_ok,
        },
        {
            "unit_id": "UNIT-PC-102",
            "assembly": "PC build",
            "step_id": "gpu_power",
            "check_id": "gpu_power_seated",
            "action": "fix",
            "verdict": "no",
            "reason": "GPU power cable connector shows 2.5mm unseated gap on right latch. High risk of melting/thermal event.",
            "problem_box": [320, 410, 620, 750],
            "hint": "Firmly press 12VHPWR plug until locking tab audibly clicks.",
            "minutes_ago": 85,
            "label": "GPU Power Connector Loose (DEFECT)",
            "color": (80, 30, 30),
            "box": [320, 410, 620, 750],
        },
        {
            "unit_id": "UNIT-PC-102",
            "assembly": "PC build",
            "step_id": "gpu_power",
            "check_id": "gpu_power_seated",
            "action": "pass",
            "verdict": "yes",
            "reason": "Re-inspected: connector now fully seated, locking tab fully engaged.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 82,
            "img_source": base_gpu_ok,
        },
        {
            "unit_id": "UNIT-PC-102",
            "assembly": "PC build",
            "step_id": "cpu_cooler",
            "check_id": "cooler_film_removed",
            "action": "pass",
            "verdict": "yes",
            "reason": "Cooler copper cold-plate inspected clean.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 78,
            "label": "Cooler Contact Plate OK",
            "color": (40, 60, 80),
        },
        {
            "unit_id": "UNIT-PC-102",
            "assembly": "PC build",
            "step_id": "cables",
            "check_id": "cables_clear_of_fans",
            "action": "pass",
            "verdict": "yes",
            "reason": "Cables secured away from blades.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 74,
            "label": "Cable Clearance OK",
            "color": (50, 70, 60),
        },
        {
            "unit_id": "UNIT-PC-102",
            "assembly": "PC build",
            "step_id": "cables",
            "check_id": "fan_header_connected",
            "action": "pass",
            "verdict": None,
            "reason": "Operator confirmed CPU_FAN plugged into motherboard header.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 70,
            "label": "Fan Header Hand Confirmed",
            "color": (60, 50, 70),
        },
        {
            "unit_id": "UNIT-PC-102",
            "assembly": "PC build",
            "step_id": "close_panel",
            "check_id": "close_panel",
            "action": "pass",
            "verdict": None,
            "reason": "Prerequisites satisfied after rework. Panel locked.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 66,
            "label": "Chassis Panel Enclosed",
            "color": (40, 40, 50),
        },
        # Unit 3: UNIT-PC-103 (Defect caught on RAM clip not locked, fixed, retake on cooler due to blur)
        {
            "unit_id": "UNIT-PC-103",
            "assembly": "PC build",
            "step_id": "ram",
            "check_id": "ram_clips",
            "action": "fix",
            "verdict": "no",
            "reason": "Top RAM retention latch is open at 30-degree angle. DIMM not locked.",
            "problem_box": [150, 200, 450, 500],
            "hint": "Press DIMM firmly into slot until top clip snaps shut.",
            "minutes_ago": 60,
            "label": "RAM Clip Open (DEFECT)",
            "color": (90, 30, 40),
            "box": [150, 200, 450, 500],
        },
        {
            "unit_id": "UNIT-PC-103",
            "assembly": "PC build",
            "step_id": "ram",
            "check_id": "ram_clips",
            "action": "pass",
            "verdict": "yes",
            "reason": "DIMM re-seated, both clips locked.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 58,
            "img_source": base_ram_ok,
        },
        {
            "unit_id": "UNIT-PC-103",
            "assembly": "PC build",
            "step_id": "gpu_power",
            "check_id": "gpu_power_seated",
            "action": "pass",
            "verdict": "yes",
            "reason": "GPU power connector locked without gap.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 52,
            "img_source": base_gpu_ok,
        },
        {
            "unit_id": "UNIT-PC-103",
            "assembly": "PC build",
            "step_id": "cpu_cooler",
            "check_id": "cooler_film_removed",
            "action": "retake",
            "verdict": "cant_tell",
            "reason": "Frame motion blur exceeds quality threshold (Laplacian variance 8.2 < 12.0).",
            "problem_box": None,
            "hint": "Hold camera steady and ensure direct light on cooler base.",
            "minutes_ago": 48,
            "label": "Blurry Frame (RETAKE)",
            "color": (80, 60, 20),
        },
        {
            "unit_id": "UNIT-PC-103",
            "assembly": "PC build",
            "step_id": "cpu_cooler",
            "check_id": "cooler_film_removed",
            "action": "pass",
            "verdict": "yes",
            "reason": "Sharp frame captured: plastic film peel verified removed.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 46,
            "label": "Cooler Film Removed (OK)",
            "color": (40, 60, 80),
        },
        {
            "unit_id": "UNIT-PC-103",
            "assembly": "PC build",
            "step_id": "cables",
            "check_id": "cables_clear_of_fans",
            "action": "pass",
            "verdict": "yes",
            "reason": "All cable looms routed through grommets.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 40,
            "label": "Cables Clear",
            "color": (50, 70, 60),
        },
        {
            "unit_id": "UNIT-PC-103",
            "assembly": "PC build",
            "step_id": "cables",
            "check_id": "fan_header_connected",
            "action": "pass",
            "verdict": None,
            "reason": "Confirmed by technician.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 36,
            "label": "Header Connected",
            "color": (60, 50, 70),
        },
        {
            "unit_id": "UNIT-PC-103",
            "assembly": "PC build",
            "step_id": "close_panel",
            "check_id": "close_panel",
            "action": "pass",
            "verdict": None,
            "reason": "All checks verified. Enclosure closed.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 32,
            "label": "Enclosure Gate Completed",
            "color": (40, 40, 50),
        },
        # Unit 4: UNIT-PC-104 (Planted defect caught: cable pinched in fan blade)
        {
            "unit_id": "UNIT-PC-104",
            "assembly": "PC build",
            "step_id": "ram",
            "check_id": "ram_clips",
            "action": "pass",
            "verdict": "yes",
            "reason": "RAM clips verified seated.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 28,
            "img_source": base_ram_ok,
        },
        {
            "unit_id": "UNIT-PC-104",
            "assembly": "PC build",
            "step_id": "gpu_power",
            "check_id": "gpu_power_seated",
            "action": "pass",
            "verdict": "yes",
            "reason": "Power connector fully clicked in.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 24,
            "img_source": base_gpu_ok,
        },
        {
            "unit_id": "UNIT-PC-104",
            "assembly": "PC build",
            "step_id": "cpu_cooler",
            "check_id": "cooler_film_removed",
            "action": "pass",
            "verdict": "yes",
            "reason": "No film present on cooler base plate.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 20,
            "label": "Cooler Plate Clean",
            "color": (40, 60, 80),
        },
        {
            "unit_id": "UNIT-PC-104",
            "assembly": "PC build",
            "step_id": "cables",
            "check_id": "cables_clear_of_fans",
            "action": "fix",
            "verdict": "no",
            "reason": "SATA power cable is caught against top intake fan blade. Fan obstruction will cause thermal shutdown.",
            "problem_box": [280, 520, 590, 880],
            "hint": "Tie cable back using zip-tie anchor on motherboard tray.",
            "minutes_ago": 15,
            "label": "Cable In Fan Blades (DEFECT)",
            "color": (95, 25, 25),
            "box": [280, 520, 590, 880],
        },
        {
            "unit_id": "UNIT-PC-104",
            "assembly": "PC build",
            "step_id": "cables",
            "check_id": "cables_clear_of_fans",
            "action": "pass",
            "verdict": "yes",
            "reason": "Cable tied back to chassis tray; full 40mm blade clearance verified.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 12,
            "label": "Cable Cleared and Tied",
            "color": (50, 70, 60),
        },
        {
            "unit_id": "UNIT-PC-104",
            "assembly": "PC build",
            "step_id": "cables",
            "check_id": "fan_header_connected",
            "action": "pass",
            "verdict": None,
            "reason": "CPU_FAN header locked in place.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 8,
            "label": "Header Verified",
            "color": (60, 50, 70),
        },
        {
            "unit_id": "UNIT-PC-104",
            "assembly": "PC build",
            "step_id": "close_panel",
            "check_id": "close_panel",
            "action": "pass",
            "verdict": None,
            "reason": "Gate checks confirmed. Side cover sealed.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 5,
            "label": "Chassis Closed",
            "color": (40, 40, 50),
        },
        # Unit 5: UNIT-PC-105 (In progress on the line right now)
        {
            "unit_id": "UNIT-PC-105",
            "assembly": "PC build",
            "step_id": "ram",
            "check_id": "ram_clips",
            "action": "pass",
            "verdict": "yes",
            "reason": "RAM clips verified locked.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 3,
            "img_source": base_ram_ok,
        },
        {
            "unit_id": "UNIT-PC-105",
            "assembly": "PC build",
            "step_id": "gpu_power",
            "check_id": "gpu_power_seated",
            "action": "pass",
            "verdict": "yes",
            "reason": "GPU power connection clean and tight.",
            "problem_box": None,
            "hint": None,
            "minutes_ago": 1,
            "img_source": base_gpu_ok,
        },
    ]

    for r in records:
        rec_id = uuid4().hex
        rel_path = f"frames/{rec_id}.png"
        target_path = EVIDENCE_DIR / rel_path

        if r.get("img_source") and Path(r["img_source"]).is_file():
            shutil.copyfile(r["img_source"], target_path)
        else:
            color = r.get("color", (50, 50, 50))
            label = r.get("label", f"{r['step_id']} - {r['check_id']}")
            box = r.get("box")
            img = make_frame(color, label, box)
            img.save(target_path)

        ts = (now - timedelta(minutes=r["minutes_ago"])).isoformat()
        box_json = json.dumps(r["problem_box"]) if r.get("problem_box") else None

        c.execute(
            """
            INSERT INTO evidence (
                id, unit_id, assembly, step_id, check_id, timestamp,
                frame_path, verdict, action, reason, problem_box, hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec_id,
                r["unit_id"],
                r["assembly"],
                r["step_id"],
                r["check_id"],
                ts,
                rel_path,
                r["verdict"],
                r["action"],
                r["reason"],
                box_json,
                r.get("hint"),
            ),
        )

    conn.commit()
    conn.close()
    return len(records)


if __name__ == "__main__":
    count = seed_database()
    print(f"Successfully seeded {count} records into evidence database.")
