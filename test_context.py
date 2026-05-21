import unittest
from pathlib import Path

from context import build_context, build_planning_prompt, summarize_trajectory


def sample_state():
    return {
        "iteration": 0,
        "spec_path": "dummy_spec.md",
        "spec_text": "Build a CLI that prints hello world.",
        "plan": ["create main.py", "run tests"],
        "current_step_index": 0,
        "last_test_result": None,
        "recent_actions": [],
        "older_trajectory_summary": "",
    }


class ContextTests(unittest.TestCase):
    def test_build_planning_prompt_shape_and_spec(self):
        spec = "Build a CLI."
        system, user = build_planning_prompt(spec)

        self.assertIsInstance(system, str)
        self.assertIsInstance(user, str)
        self.assertTrue(system)
        self.assertTrue(user)
        self.assertIn(spec, user)

    def test_build_planning_prompt_mentions_steps(self):
        _, user = build_planning_prompt("Build something.")

        self.assertIn('"steps"', user)

    def test_build_context_shape_for_fresh_state(self):
        system, user = build_context(sample_state())

        self.assertTrue(system)
        self.assertTrue(user)

    def test_build_context_contains_section_headers(self):
        _, user = build_context(sample_state())

        for header in [
            "=== SPEC ===",
            "=== PLAN ===",
            "=== WORKSPACE ===",
            "=== LAST TEST RESULT ===",
            "=== RECENT ACTIONS ===",
        ]:
            self.assertIn(header, user)

    def test_trajectory_includes_recent_actions(self):
        state = sample_state()
        state["recent_actions"] = [
            {"iteration": 1, "action": "list_dir", "args": {}, "result_summary": "1 entry", "success": True},
            {"iteration": 2, "action": "read_file", "args": {"path": "main.py"}, "result_summary": "read", "success": True},
            {"iteration": 3, "action": "run_tests", "args": {}, "result_summary": "1 passed", "success": True},
        ]

        _, user = build_context(state)

        self.assertIn("iter 1: list_dir", user)
        self.assertIn("iter 2: read_file main.py", user)
        self.assertIn("iter 3: run_tests", user)

    def test_last_test_result_counts(self):
        state = sample_state()
        state["last_test_result"] = {
            "passed": 7,
            "failed": 3,
            "errors": 1,
            "failure_summary": "FAILED test_main.py::test_cli",
        }

        _, user = build_context(state)

        self.assertIn("7 passed, 3 failed, 1 errors", user)
        self.assertIn("FAILED test_main.py::test_cli", user)

    def test_no_test_result_message(self):
        _, user = build_context(sample_state())

        self.assertIn("no test run yet", user)

    def test_summarize_empty(self):
        summary = summarize_trajectory([])

        self.assertTrue(len(summary) < 500)

    def test_summarize_actions_short(self):
        actions = [
            {"action": "read_file", "args": {"path": "a.py"}, "result_summary": "read", "success": True},
            {"action": "edit_file", "args": {"path": "a.py"}, "result_summary": "wrote", "success": True},
            {"action": "run_tests", "args": {}, "result_summary": "1 passed", "success": True},
            {"action": "read_file", "args": {"path": "b.py"}, "result_summary": "read", "success": True},
            {"action": "edit_file", "args": {"path": "b.py"}, "result_summary": "wrote", "success": True},
        ]

        summary = summarize_trajectory(actions)

        self.assertTrue(summary)
        self.assertLessEqual(len(summary), 500)
        self.assertIn("Earlier: 5 actions.", summary)

    def test_prompt_templates_exist(self):
        for path in [
            Path("prompts/system.txt"),
            Path("prompts/plan.txt"),
            Path("prompts/decide.txt"),
        ]:
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
