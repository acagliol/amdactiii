"""Web API over the checker: full worker flow with the fake AI; no GPU, network, or real evidence."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.server import create_app
from tests.foundation._images import write_sharp


class WorkerApiTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        env = patch.dict(os.environ, {"USE_FAKE_AI": "true"})
        env.start()
        self.addCleanup(env.stop)
        self.client = TestClient(create_app(evidence_root=self.work / "evidence"))
        self.good = write_sharp("part_ok_01.png", self.work)
        self.bad = write_sharp("part_bad_01.png", self.work)

    def start_unit(self, **body) -> dict:
        response = self.client.post("/api/units", json={"assembly": "pc_build.yaml", **body})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def check(self, unit_id: str, photo: Path) -> dict:
        with photo.open("rb") as handle:
            response = self.client.post(f"/api/units/{unit_id}/check", files={"photo": (photo.name, handle, "image/png")})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_health_reports_fake_mode_without_secrets(self):
        body = self.client.get("/api/health").json()
        self.assertEqual(body, {"ok": True, "ai": "fake", "model": None})

    def test_assemblies_lists_station_checklists_only(self):
        files = [item["file"] for item in self.client.get("/api/assemblies").json()]
        self.assertIn("pc_build.yaml", files)
        self.assertFalse(any("/" in name for name in files))  # mvtec benchmark folder is not a station

    def test_full_pc_build_flow_ends_complete_with_evidence(self):
        unit = self.start_unit()
        unit_id = unit["unit_id"]
        self.assertEqual(unit["current"]["check_id"], "ram_clips")
        self.assertEqual(unit["steps"][0]["status"], "current")

        # A planted mistake: Fix it, a red box, a stored photo, and no progress.
        fix = self.check(unit_id, self.bad)
        self.assertEqual(fix["result"]["action"], "fix")
        self.assertIsNotNone(fix["result"]["problem_box"])
        self.assertEqual(fix["unit"]["done"], 0)
        self.assertEqual(self.client.get(fix["result"]["photo_url"]).status_code, 200)

        for _ in range(4):  # four visual checks pass
            self.assertEqual(self.check(unit_id, self.good)["result"]["action"], "pass")

        unit = self.client.get(f"/api/units/{unit_id}").json()
        self.assertEqual(unit["current"]["kind"], "manual")
        manual = self.client.post(f"/api/units/{unit_id}/manual", json={"ok": True}).json()
        self.assertEqual(manual["result"]["action"], "pass")

        self.assertEqual(manual["unit"]["current"]["kind"], "gate")
        self.assertTrue(manual["unit"]["current"]["hides"])
        gate = self.client.post(f"/api/units/{unit_id}/gate").json()
        self.assertEqual(gate["result"]["action"], "pass")
        self.assertTrue(gate["unit"]["complete"])
        self.assertIsNone(gate["unit"]["current"])

        evidence = self.client.get("/api/evidence", params={"unit_id": unit_id}).json()
        self.assertEqual(evidence["summary"]["attempts"], len(evidence["items"]))
        self.assertGreaterEqual(evidence["summary"]["attempts"], 5)
        self.assertTrue(all("frame_path" not in item for item in evidence["items"]))

    def test_manual_step_via_photo_check_stores_no_photo(self):
        unit_id = self.start_unit()["unit_id"]
        for _ in range(4):
            self.check(unit_id, self.good)
        attempt = self.check(unit_id, self.good)  # manual step: camera is not the right tool
        self.assertEqual(attempt["result"]["action"], "retake")
        self.assertIsNone(attempt["result"]["photo_url"])

    def test_override_needs_a_written_reason(self):
        unit_id = self.start_unit()["unit_id"]
        short = self.client.post(f"/api/units/{unit_id}/override", json={"reason": "ok"}).json()
        self.assertEqual(short["result"]["action"], "retake")
        accepted = self.client.post(f"/api/units/{unit_id}/override", json={"reason": "verified by hand, clips seated"}).json()
        self.assertEqual(accepted["result"]["action"], "pass")
        self.assertEqual(accepted["unit"]["steps"][0]["status"], "overridden")

    def test_reference_photo_is_served_for_checks_that_have_one(self):
        unit = self.start_unit()
        reference_url = unit["current"]["reference_url"]
        self.assertIsNotNone(reference_url)
        self.assertEqual(self.client.get(reference_url).status_code, 200)
        missing = self.client.get("/api/assemblies/pc_build.yaml/checks/cooler_film_removed/reference")
        self.assertEqual(missing.status_code, 404)

    def test_serials_are_validated_and_unique(self):
        self.assertEqual(self.start_unit(serial="UNIT-1042")["unit_id"], "UNIT-1042")
        duplicate = self.client.post("/api/units", json={"assembly": "pc_build.yaml", "serial": "UNIT-1042"})
        self.assertEqual(duplicate.status_code, 409)
        bad = self.client.post("/api/units", json={"assembly": "pc_build.yaml", "serial": "../etc"})
        self.assertEqual(bad.status_code, 400)

    def test_unknown_or_unsafe_names_are_rejected(self):
        self.assertEqual(self.client.post("/api/units", json={"assembly": "../README.md"}).status_code, 404)
        self.assertEqual(self.client.get("/api/units/nope").status_code, 404)
        self.assertEqual(self.client.get("/api/evidence/photos/..%2Fevidence.sqlite3").status_code, 404)
        self.assertEqual(self.client.get("/api/evidence", params={"limit": 0}).status_code, 400)

    def test_oversized_upload_is_rejected(self):
        unit_id = self.start_unit()["unit_id"]
        with patch("api.server.MAX_UPLOAD_BYTES", 10):
            response = self.client.post(
                f"/api/units/{unit_id}/check", files={"photo": ("big_ok_.png", self.good.read_bytes(), "image/png")}
            )
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
