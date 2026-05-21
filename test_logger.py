import importlib
import re
import shutil
import sys
import unittest
from pathlib import Path


ISO_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")


class LoggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        shutil.rmtree("agent_logs", ignore_errors=True)
        sys.modules.pop("logger", None)
        cls.logger_module = importlib.import_module("logger")

    def test_log_directory_created_on_import(self):
        self.assertTrue(Path("agent_logs").is_dir())

    def test_iteration_format_and_readback(self):
        log = self.logger_module.get_logger("prompts")
        log.info("first test message")

        lines = Path("agent_logs/prompts.log").read_text(encoding="utf-8").splitlines()
        self.assertRegex(lines[-1], ISO_PATTERN)
        self.assertIn("[iter -]", lines[-1])
        self.assertIn("first test message", lines[-1])

        self.logger_module.set_iteration(5)
        log.info("second test message")

        lines = Path("agent_logs/prompts.log").read_text(encoding="utf-8").splitlines()
        self.assertIn("[iter 5]", lines[-1])
        self.assertIn("second test message", lines[-1])

    def test_logger_cache_prevents_duplicate_handlers(self):
        first = self.logger_module.get_logger("prompts")
        before = Path("agent_logs/prompts.log").read_text(encoding="utf-8").splitlines()

        second = self.logger_module.get_logger("prompts")
        self.assertIs(first, second)

        second.info("single cached write")
        after = Path("agent_logs/prompts.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(after), len(before) + 1)
        self.assertIn("single cached write", after[-1])

    def test_human_intervention_format(self):
        self.logger_module.log_intervention("test message")

        lines = Path("agent_logs/human_interventions.log").read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertRegex(lines[-1], ISO_PATTERN)
        self.assertIn("test message", lines[-1])
        self.assertNotIn("[iter", lines[-1])

    def test_invalid_logger_name(self):
        with self.assertRaises(ValueError):
            self.logger_module.get_logger("invalid_name")

    def test_exception_traceback_logging(self):
        log = self.logger_module.get_logger("errors")
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            log.exception("caught test exception")

        content = Path("agent_logs/errors.log").read_text(encoding="utf-8")
        self.assertIn("caught test exception", content)
        self.assertIn("Traceback (most recent call last):", content)
        self.assertIn("RuntimeError: boom", content)


if __name__ == "__main__":
    unittest.main()
