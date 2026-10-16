"""Real SDK requests against an in-memory vLLM transport; no GPU or network."""

from __future__ import annotations

import base64
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

try:
    import httpx2 as httpx
except ImportError:
    import httpx
from openai import OpenAI
from PIL import Image

from ai_client import look, vllm
from ai_client.vllm import parse_result
from checker import Session, run_check
from checker.evidence import EvidenceLog
from tests.foundation._images import write_sharp

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLY = ROOT / "assemblies" / "pc_build.yaml"


def inspection(verdict="yes", box=None):
    return {"verdict": verdict, "reason": "Visible inspection result.", "problem_box": box}


def completion(content=None, *, finish="stop", refusal=None):
    return {
        "id": "local-test",
        "object": "chat.completion",
        "created": 0,
        "model": "test-vision",
        "choices": [{
            "index": 0,
            "finish_reason": finish,
            "message": {"role": "assistant", "content": content, "refusal": refusal},
        }],
    }


class AIClientTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.frame = write_sharp("part_ok_01.png", self.work)
        env = patch.dict(os.environ, {
            "USE_FAKE_AI": "false",
            "VLLM_BASE_URL": "http://vllm.test:8000/v1",
            "VLLM_MODEL": "test-vision",
            "VLLM_API_KEY": "local-test-key",
            "VLLM_TIMEOUT_SECONDS": "7.5",
            "VLLM_FALLBACK_TO_FAKE": "false",
            "OPENAI_API_KEY": "must-not-be-used",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
        })
        env.start()
        self.addCleanup(env.stop)
        self.requests = []
        self.clients = []
        self.reply = completion(json.dumps(inspection()))
        self.status = 200
        self.status_sequence = []  # optional per-request statuses, e.g. [429, 200]
        self.retry_after = None
        self.transport_error = None
        factory = patch("ai_client.vllm.OpenAI", side_effect=self.make_client)
        self.factory = factory.start()
        self.addCleanup(factory.stop)
        # Retries wait between attempts; tests record the waits instead of sleeping.
        sleep = patch("ai_client.vllm.time.sleep")
        self.sleep = sleep.start()
        self.addCleanup(sleep.stop)

    def make_client(self, **settings):
        client = OpenAI(**settings, http_client=httpx.Client(transport=httpx.MockTransport(self.respond)))
        self.clients.append(client)
        return client

    def respond(self, request):
        self.requests.append(request)
        if self.transport_error:
            raise self.transport_error("Private error text must not reach the UI.", request=request)
        status = self.status_sequence.pop(0) if self.status_sequence else self.status
        reply = self.reply if status == 200 else {"error": {"message": "Private error local-test-key", "type": "test_error"}}
        headers = {"retry-after": self.retry_after} if self.retry_after else {}
        return httpx.Response(status, json=reply, headers=headers)

    def check_uncertain(self, result):
        self.assertEqual(set(result), {"verdict", "reason", "problem_box"})
        self.assertEqual(result["verdict"], "cant_tell")
        self.assertIsNone(result["problem_box"])
        self.assertTrue(result["reason"])
        self.assertNotIn("Private error", result["reason"])
        self.assertNotIn("local-test-key", result["reason"])

    def test_default_fake_mode_never_constructs_a_real_client(self):
        os.environ.pop("USE_FAKE_AI")
        os.environ["VLLM_BASE_URL"] = "invalid"
        os.environ["VLLM_TIMEOUT_SECONDS"] = "invalid"
        for filename, verdict in (("a_ok_.jpg", "yes"), ("a_bad_.jpg", "no"), ("a_blur_.jpg", "cant_tell")):
            self.assertEqual(look(filename, "Inspect the clip.")["verdict"], verdict)
        self.factory.assert_not_called()

    def test_boolean_forms_select_fake_or_real_mode(self):
        for flag in ("true", "1", "YES", " on "):
            with patch.dict(os.environ, {"USE_FAKE_AI": flag}):
                self.assertEqual(look("part_bad_.png", "Inspect the clip.")["verdict"], "no")
        self.factory.assert_not_called()
        for flag in ("false", "0", "NO", " off "):
            with patch.dict(os.environ, {"USE_FAKE_AI": flag}):
                self.assertEqual(look(self.frame, "Inspect the clip.")["verdict"], "yes")
        self.assertEqual(len(self.requests), 4)

    def test_invalid_configuration_makes_no_requests(self):
        cases = [
            ("USE_FAKE_AI", "maybe"), ("VLLM_FALLBACK_TO_FAKE", "maybe"),
            ("VLLM_BASE_URL", ""), ("VLLM_BASE_URL", "ftp://host/v1"),
            ("VLLM_BASE_URL", "http://host:bad/v1"),
            ("VLLM_BASE_URL", "http://user:password@host/v1"),
            ("VLLM_BASE_URL", "http://host/v1?query=yes"),
            ("VLLM_MODEL", " "), ("VLLM_TIMEOUT_SECONDS", "bad"),
            ("VLLM_TIMEOUT_SECONDS", "0"), ("VLLM_TIMEOUT_SECONDS", "-1"),
            ("VLLM_TIMEOUT_SECONDS", "nan"), ("VLLM_TIMEOUT_SECONDS", "inf"),
        ]
        for name, value in cases:
            with self.subTest(name=name, value=value), patch.dict(os.environ, {name: value}):
                result = look(self.frame, "Inspect the clip.")
                self.check_uncertain(result)
                self.assertIn(name, result["reason"])
        self.factory.assert_not_called()

    def test_dotenv_uses_repo_root_and_preserves_shell_precedence(self):
        mirror = self.work / "mirror"
        package = mirror / "ai_client"
        package.mkdir(parents=True)
        for name in ("__init__.py", "client.py", "fake_ai.py"):
            shutil.copyfile(ROOT / "ai_client" / name, package / name)
        (mirror / ".env").write_text("USE_FAKE_AI=true\nVLLM_MODEL=dotenv-model\n", encoding="utf-8")
        script = (
            "import json, os, sys; from ai_client import look; "
            "print(json.dumps({'model': os.getenv('VLLM_MODEL'), "
            "'verdict': look('part_bad_.jpg', 'Inspect the clip.')['verdict'], "
            "'sdk_imported': 'openai' in sys.modules}))"
        )
        env = dict(os.environ, PYTHONPATH=str(mirror))
        for name in tuple(env):
            if name == "USE_FAKE_AI" or name.startswith("VLLM_"):
                del env[name]
        for shell_model, expected in ((None, "dotenv-model"), ("shell-model", "shell-model")):
            if shell_model:
                env["VLLM_MODEL"] = shell_model
            result = json.loads(subprocess.check_output(
                [sys.executable, "-c", script], cwd=self.work, env=env, text=True,
            ))
            self.assertEqual(result, {"model": expected, "verdict": "no", "sdk_imported": False})

    def test_request_sends_small_jpeg_in_json_mode_with_explicit_settings(self):
        for image_format in ("PNG", "JPEG"):
            # The extension intentionally differs from the image's actual format.
            path = self.work / "capture.bin"
            with Image.open(self.frame) as image:
                image.save(path, format=image_format)
                original_size = image.size
            self.assertEqual(look(path, "Are both RAM clips closed?")["verdict"], "yes")
            request = self.requests[-1]
            self.assertEqual(request.method, "POST")
            self.assertEqual(str(request.url), "http://vllm.test:8000/v1/chat/completions")
            self.assertEqual(request.headers["authorization"], "Bearer local-test-key")
            payload = json.loads(request.content)
            self.assertEqual(payload["model"], "test-vision")
            self.assertEqual(payload["temperature"], 0)
            self.assertEqual(payload["max_tokens"], 256)
            self.assertEqual(payload["response_format"], {"type": "json_object"})
            content = payload["messages"][1]["content"]
            self.assertEqual(content[0], {"type": "text", "text": "Are both RAM clips closed?"})
            # Whatever comes in, a JPEG goes out (small upload, same 0-1000 box scale).
            prefix, encoded = content[1]["image_url"]["url"].split(",", 1)
            self.assertEqual(prefix, "data:image/jpeg;base64")
            with Image.open(io.BytesIO(base64.b64decode(encoded))) as sent:
                self.assertEqual(sent.format, "JPEG")
                self.assertEqual(sent.size, original_size)  # 640x480 is already small: not resized
            self.assertEqual(self.factory.call_args.kwargs["timeout"], 7.5)
            self.assertEqual(self.factory.call_args.kwargs["max_retries"], 0)
            self.assertTrue(self.clients[-1].is_closed())

    def test_real_mode_defaults_use_the_local_endpoint_and_placeholder_key(self):
        for name in ("VLLM_BASE_URL", "VLLM_MODEL", "VLLM_API_KEY", "VLLM_TIMEOUT_SECONDS"):
            os.environ.pop(name)
        self.assertEqual(look(self.frame, "Inspect the clip.")["verdict"], "yes")
        self.assertEqual(str(self.requests[0].url), "http://localhost:8000/v1/chat/completions")
        self.assertEqual(self.requests[0].headers["authorization"], "Bearer EMPTY")
        self.assertEqual(json.loads(self.requests[0].content)["model"], "google/gemma-4-26b-a4b-it")
        self.assertEqual(self.factory.call_args.kwargs["timeout"], 10)

    def test_valid_contract_results_and_json_fence(self):
        results = [inspection(), inspection("no"), inspection("cant_tell"), inspection("no", [10, 20.5, 900, 1000])]
        for expected in results:
            for content in (json.dumps(expected), "```json\n" + json.dumps(expected) + "\n```"):
                with self.subTest(expected=expected, fenced=content.startswith("```")):
                    self.reply = completion(content)
                    self.assertEqual(look(self.frame, "Inspect the clip."), expected)

    def test_invalid_json_and_fields_are_rejected(self):
        invalid = ["", "not JSON", "[]", "null", "{}", "{} {}", "text " + json.dumps(inspection()),
                   '```json\n{}\n```\nextra',
                   '{"verdict":"no","verdict":"yes","reason":"ok","problem_box":null}']
        for updates in (
            {"verdict": "pass"}, {"verdict": []}, {"reason": " "}, {"reason": 12},
            {"extra": True}, {"problem_box": [0, 0, 100, 100]},
        ):
            invalid.append(json.dumps(dict(inspection(), **updates)))
        for text in invalid:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_result(text)
                self.reply = completion(text)
                self.check_uncertain(look(self.frame, "Inspect the clip."))

    def test_invalid_boxes_are_rejected_without_repair(self):
        boxes = [
            [], [1, 2, 3], "1,2,3,4", [True, 0, 10, 10], [0, "0", 10, 10],
            [-1, 0, 10, 10], [0, 0, 1001, 100], [20, 0, 10, 10],
            [0, 20, 10, 10], [0, 0, 0, 10], [0, 0, 10, 0],
            [float("nan"), 0, 10, 10], [0, 0, float("inf"), 10], [0, 0, 10**500, 10],
        ]
        for box in boxes:
            with self.subTest(box=box):
                with self.assertRaises(ValueError):
                    parse_result(json.dumps(inspection("no", box)))

    def test_incomplete_empty_and_refused_completions_are_uncertain(self):
        replies = [
            {}, dict(completion(), choices=[]), dict(completion(), choices=[None]),
            completion(), completion(json.dumps(inspection()), finish="length"),
            completion(json.dumps(inspection()), refusal="Cannot answer"),
        ]
        for reply in replies:
            with self.subTest(reply=reply):
                self.reply = reply
                self.check_uncertain(look(self.frame, "Inspect the clip."))

    def test_non_json_http_response_is_uncertain(self):
        with patch.object(self, "respond", return_value=httpx.Response(
            200, content=b"not JSON", headers={"content-type": "application/json"},
        )):
            self.check_uncertain(look(self.frame, "Inspect the clip."))

    def test_permanent_http_errors_are_uncertain_and_not_retried(self):
        for status in (400, 401, 403, 404, 408, 500):
            with self.subTest(status=status):
                self.status = status
                before = len(self.requests)
                self.check_uncertain(look(self.frame, "Inspect the clip."))
                self.assertEqual(len(self.requests), before + 1)
                self.assertTrue(self.clients[-1].is_closed())
        self.sleep.assert_not_called()

    def test_busy_errors_are_retried_then_uncertain(self):
        for status in sorted(vllm.RETRY_STATUS_CODES):
            with self.subTest(status=status):
                self.status = status
                self.sleep.reset_mock()
                before = len(self.requests)
                self.check_uncertain(look(self.frame, "Inspect the clip."))
                self.assertEqual(len(self.requests), before + vllm.MAX_ATTEMPTS)
                self.assertEqual(self.sleep.call_count, vllm.MAX_ATTEMPTS - 1)
                self.assertTrue(self.clients[-1].is_closed())

    def test_busy_then_ok_returns_the_real_answer(self):
        self.status_sequence = [429, 503]
        self.reply = completion(json.dumps(inspection("no", [10, 20, 300, 400])))
        self.assertEqual(look(self.frame, "Inspect the clip."), inspection("no", [10, 20, 300, 400]))
        self.assertEqual(len(self.requests), 3)

    def test_retry_follows_server_hint_but_waits_at_most_the_cap(self):
        for retry_after, expected_wait in (("1", 1.0), ("60", vllm.MAX_RETRY_WAIT_SECONDS)):
            with self.subTest(retry_after=retry_after):
                self.retry_after = retry_after
                self.status_sequence = [429]
                self.sleep.reset_mock()
                look(self.frame, "Inspect the clip.")
                wait = self.sleep.call_args.args[0]
                self.assertGreaterEqual(wait, expected_wait)
                self.assertLessEqual(wait, expected_wait + 0.5)  # plus a little random jitter

    def test_transport_errors_are_uncertain_and_never_retried(self):
        for error in (httpx.ReadTimeout, httpx.ConnectError):
            with self.subTest(error=error):
                self.transport_error = error
                before = len(self.requests)
                self.check_uncertain(look(self.frame, "Inspect the clip."))
                self.assertEqual(len(self.requests), before + 1)
                self.assertTrue(self.clients[-1].is_closed())

    def test_demo_fallback_only_handles_availability_failures(self):
        os.environ["VLLM_FALLBACK_TO_FAKE"] = "true"
        for error in (httpx.ReadTimeout, httpx.ConnectError, None):
            with self.subTest(error=error):
                self.transport_error = error
                self.status = 503
                result = look(self.frame, "Inspect the clip.")
                self.assertEqual(result["verdict"], "yes")
                self.assertTrue(result["reason"].startswith("DEMO FALLBACK"))
        self.transport_error = None
        for status in (400, 401, 403, 404, 429):
            self.status = status
            self.check_uncertain(look(self.frame, "Inspect the clip."))
        self.status = 200
        self.reply = completion("invalid JSON")
        self.check_uncertain(look(self.frame, "Inspect the clip."))

    def test_bad_input_makes_no_request_or_demo_fallback(self):
        os.environ["VLLM_FALLBACK_TO_FAKE"] = "true"
        bad = self.work / "broken_ok_.png"
        bad.write_bytes(b"invalid image")
        corrupt = self.work / "corrupt_ok_.png"
        data = bytearray(self.frame.read_bytes())
        data[data.index(b"IDAT") + 4] ^= 1
        corrupt.write_bytes(data)
        gif = self.work / "capture_ok_.gif"
        Image.new("RGB", (20, 20)).save(gif)
        for path, question in ((bad, "Inspect."), (corrupt, "Inspect."), (gif, "Inspect."), (self.work / "missing_ok_.png", "Inspect."),
                               (self.frame, " ")):
            self.check_uncertain(look(path, question))
        self.factory.assert_not_called()

    def test_unexpected_programming_errors_remain_visible(self):
        with patch("ai_client.vllm.parse_result", side_effect=RuntimeError("Programming bug")):
            with self.assertRaisesRegex(RuntimeError, "Programming bug"):
                look(self.frame, "Inspect the clip.")

    def test_checker_flow_records_real_results(self):
        evidence = EvidenceLog(self.work / "evidence")
        session = Session(ASSEMBLY, unit_id="REAL-001", evidence_log=evidence)
        cases = [
            (inspection(), "pass"), (inspection("no", [20, 30, 800, 900]), "fix"),
            (inspection("cant_tell"), "retake"), (inspection("cant_tell"), "retake"),
            (inspection("cant_tell"), "supervisor"), (inspection(), "pass"),
        ]
        for ai_result, expected_action in cases:
            self.reply = completion(json.dumps(ai_result))
            self.assertEqual(run_check(session, self.frame)["action"], expected_action)
        with closing(sqlite3.connect(evidence.db_path)) as connection:
            rows = connection.execute("SELECT unit_id, verdict, action, problem_box FROM evidence ORDER BY rowid").fetchall()
        self.assertEqual([row[1] for row in rows], [result["verdict"] for result, _ in cases])
        self.assertEqual([row[2] for row in rows], [action for _, action in cases])
        self.assertEqual({row[0] for row in rows}, {"REAL-001"})
        self.assertEqual(json.loads(rows[1][3]), [20, 30, 800, 900])
        self.assertEqual(session.current()["check_id"], "cooler_film_removed")
        self.assertEqual(len(list(evidence.frames_dir.iterdir())), len(cases))

    def test_server_failure_does_not_unlock_and_escalates_with_evidence(self):
        evidence = EvidenceLog(self.work / "evidence")
        session = Session(ASSEMBLY, evidence_log=evidence)
        self.status = 503
        for action in ("retake", "retake", "supervisor"):
            self.assertEqual(run_check(session, self.frame)["action"], action)
        self.assertEqual(session.index, 0)
        self.assertEqual(session.passed, set())
        with closing(sqlite3.connect(evidence.db_path)) as connection:
            verdicts = connection.execute("SELECT verdict FROM evidence").fetchall()
        self.assertEqual(verdicts, [("cant_tell",)] * 3)

    def test_demo_fallback_is_marked_in_evidence(self):
        os.environ["VLLM_FALLBACK_TO_FAKE"] = "true"
        evidence = EvidenceLog(self.work / "evidence")
        session = Session(ASSEMBLY, evidence_log=evidence)
        self.status = 503
        bad = write_sharp("part_bad_01.png", self.work)
        self.assertEqual(run_check(session, bad)["action"], "fix")
        with closing(sqlite3.connect(evidence.db_path)) as connection:
            verdict, reason = connection.execute("SELECT verdict, reason FROM evidence").fetchone()
        self.assertEqual(verdict, "no")
        self.assertTrue(reason.startswith("DEMO FALLBACK"))


if __name__ == "__main__":
    unittest.main()
