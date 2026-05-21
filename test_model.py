import json
import os
import shutil
import unittest
from pathlib import Path

from model import _extract_json, call_model


class ModelUnitTests(unittest.TestCase):
    def setUp(self):
        shutil.rmtree("agent_logs", ignore_errors=True)
        Path("agent_logs").mkdir(exist_ok=True)

    def test_extract_plain_json(self):
        self.assertEqual(_extract_json('{"foo": 1}'), '{"foo": 1}')

    def test_extract_fenced_json(self):
        self.assertEqual(_extract_json('```json\n{"foo": 1}\n```'), '{"foo": 1}')

    def test_extract_fenced_json_without_language(self):
        self.assertEqual(_extract_json('```\n{"foo": 1}\n```'), '{"foo": 1}')

    def test_extract_prose_wrapped_json(self):
        text = 'Sure, here you go:\n{"foo": 1}\nLet me know.'
        self.assertEqual(_extract_json(text), '{"foo": 1}')

    def test_extract_no_json_raises(self):
        with self.assertRaises(ValueError):
            _extract_json("no structured data here")

    def test_extract_nested_objects_and_arrays(self):
        text = 'prefix {"items": [{"ok": true}], "meta": {"n": 1}} suffix'
        extracted = _extract_json(text)
        self.assertEqual(json.loads(extracted)["items"][0]["ok"], True)

    def test_no_api_key_strings_in_logs_after_unit_tests(self):
        for path in Path("agent_logs").rglob("*"):
            if path.is_file():
                content = path.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("AIzaSy", content)
                self.assertNotIn("gsk_", content)


@unittest.skipUnless(
    os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY"),
    "integration tests require GEMINI_API_KEY or GROQ_API_KEY",
)
class ModelIntegrationTests(unittest.TestCase):
    def test_call_model_text(self):
        response = call_model("You are helpful.", "Say hello in one word.", expect_json=False)
        self.assertIsInstance(response, str)
        self.assertTrue(response.strip())

    def test_call_model_json(self):
        response = call_model(
            "Respond only with JSON.",
            'Return {"ok": true}',
            expect_json=True,
        )
        self.assertTrue(json.loads(response)["ok"])

    def test_call_files_created_and_no_key_leakage(self):
        call_model("Be concise.", "Say hi.", expect_json=False)
        calls_dir = Path("agent_logs/calls")
        self.assertTrue(calls_dir.is_dir())
        self.assertTrue(any(calls_dir.iterdir()))

        for path in Path("agent_logs").rglob("*"):
            if path.is_file():
                content = path.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn(os.environ.get("GEMINI_API_KEY", "not-set"), content)
                self.assertNotIn(os.environ.get("GROQ_API_KEY", "not-set"), content)


if __name__ == "__main__":
    unittest.main()
