"""Double-look agreement helpers (L-AI). Does not require a live GPU."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import httpx2 as httpx
except ImportError:
    import httpx
from openai import OpenAI

from ai_client import look
from ai_client.agreement import reconcile
from tests.foundation._images import write_sharp


def _inspection(verdict="yes", box=None, reason="Visible inspection result."):
    return {"verdict": verdict, "reason": reason, "problem_box": box}


def _completion(content):
    return {
        "id": "local-test",
        "object": "chat.completion",
        "created": 0,
        "model": "test-vision",
        "choices": [{
            "index": 0,
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": content, "refusal": None},
        }],
    }


class AgreementUnitTests(unittest.TestCase):
    def test_reconcile_yes_yes(self):
        out = reconcile(_inspection("yes"), _inspection("yes", reason="Also ok."))
        self.assertEqual(out["verdict"], "yes")
        self.assertIsNone(out["problem_box"])

    def test_reconcile_no_no_keeps_box(self):
        out = reconcile(
            _inspection("no", [10, 20, 100, 200], "open clip"),
            _inspection("no", None, "latch up"),
        )
        self.assertEqual(out["verdict"], "no")
        self.assertEqual(out["problem_box"], [10, 20, 100, 200])
        self.assertIn("latch up", out["reason"])

    def test_reconcile_disagree_is_uncertain(self):
        out = reconcile(_inspection("yes"), _inspection("no", [1, 2, 3, 4]))
        self.assertEqual(out["verdict"], "cant_tell")
        self.assertIsNone(out["problem_box"])
        self.assertIn("disagreed", out["reason"].lower())


class DoubleLookClientTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.frame = write_sharp("part_ok_01.png", self.work)
        self.queue: list[dict] = []
        env = patch.dict(os.environ, {
            "USE_FAKE_AI": "false",
            "VLLM_BASE_URL": "http://vllm.test:8000/v1",
            "VLLM_MODEL": "test-vision",
            "VLLM_API_KEY": "local-test-key",
            "VLLM_TIMEOUT_SECONDS": "7.5",
            "VLLM_FALLBACK_TO_FAKE": "false",
            "VLLM_DOUBLE_LOOK": "true",
        })
        env.start()
        self.addCleanup(env.stop)
        self.requests = []
        factory = patch("ai_client.vllm.OpenAI", side_effect=self.make_client)
        factory.start()
        self.addCleanup(factory.stop)

    def make_client(self, **settings):
        return OpenAI(**settings, http_client=httpx.Client(transport=httpx.MockTransport(self.respond)))

    def respond(self, request):
        self.requests.append(request)
        payload = self.queue.pop(0) if self.queue else _completion(json.dumps(_inspection()))
        return httpx.Response(200, json=payload)

    def test_double_look_agree_yes_makes_two_requests(self):
        self.queue = [
            _completion(json.dumps(_inspection("yes", reason="first"))),
            _completion(json.dumps(_inspection("yes", reason="second"))),
        ]
        result = look(self.frame, "Inspect the clip.")
        self.assertEqual(result["verdict"], "yes")
        self.assertEqual(len(self.requests), 2)

    def test_double_look_disagree_is_cant_tell(self):
        self.queue = [
            _completion(json.dumps(_inspection("yes"))),
            _completion(json.dumps(_inspection("no", [10, 20, 300, 400]))),
        ]
        result = look(self.frame, "Inspect the clip.")
        self.assertEqual(result["verdict"], "cant_tell")
        self.assertEqual(len(self.requests), 2)

    def test_first_cant_tell_skips_second_call(self):
        self.queue = [
            _completion(json.dumps(_inspection("cant_tell", reason="too dark"))),
            _completion(json.dumps(_inspection("yes"))),
        ]
        result = look(self.frame, "Inspect the clip.")
        self.assertEqual(result["verdict"], "cant_tell")
        self.assertEqual(len(self.requests), 1)

    def test_double_look_off_still_one_request(self):
        os.environ["VLLM_DOUBLE_LOOK"] = "false"
        self.queue = [_completion(json.dumps(_inspection("yes")))]
        result = look(self.frame, "Inspect the clip.")
        self.assertEqual(result["verdict"], "yes")
        self.assertEqual(len(self.requests), 1)


if __name__ == "__main__":
    unittest.main()
