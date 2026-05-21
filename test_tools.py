import json
import shutil
import sys
import unittest
from pathlib import Path

from tools import edit_file, list_dir, read_file, run_shell, run_tests


class ToolsTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("workspace/test_sandbox")
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True)
        self.manifest = Path("agent_manifest.json")
        self.old_manifest = None
        if self.manifest.exists():
            self.old_manifest = self.manifest.read_text(encoding="utf-8")
            self.manifest.unlink()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)
        if self.manifest.exists():
            self.manifest.unlink()
        if self.old_manifest is not None:
            self.manifest.write_text(self.old_manifest, encoding="utf-8")

    def test_read_file_happy_path(self):
        path = self.root / "hello.txt"
        path.write_text("alpha\nbeta\n", encoding="utf-8")

        self.assertEqual(read_file("test_sandbox/hello.txt"), "   1\talpha\n   2\tbeta\n")

    def test_read_file_missing(self):
        with self.assertRaises(FileNotFoundError):
            read_file("test_sandbox/missing.txt")

    def test_edit_file_create(self):
        result = edit_file("test_sandbox/nested/new.txt", "content")

        self.assertTrue(result["success"])
        self.assertEqual((self.root / "nested/new.txt").read_text(encoding="utf-8"), "content")
        self.assertIn("created new file", result["diff_summary"])

    def test_edit_file_overwrite(self):
        edit_file("test_sandbox/overwrite.txt", "old")
        result = edit_file("test_sandbox/overwrite.txt", "new")

        self.assertEqual((self.root / "overwrite.txt").read_text(encoding="utf-8"), "new")
        self.assertIn("overwrote existing file", result["diff_summary"])

    def test_list_dir_sorted_and_skips_hidden(self):
        (self.root / "b.txt").write_text("b", encoding="utf-8")
        (self.root / "a.txt").write_text("a", encoding="utf-8")
        (self.root / ".hidden").write_text("x", encoding="utf-8")

        self.assertEqual(list_dir("test_sandbox"), ["a.txt", "b.txt"])

    def test_run_shell_happy_path(self):
        result = run_shell("echo hello")

        self.assertEqual(result["stdout"], "hello\n")
        self.assertEqual(result["stderr"], "")
        self.assertEqual(result["exit_code"], 0)
        self.assertGreaterEqual(result["duration_s"], 0)

    def test_run_shell_timeout(self):
        result = run_shell("sleep 5", timeout=1)

        self.assertEqual(result["exit_code"], -1)
        self.assertIn("timeout after 1s", result["stderr"])

    def test_run_shell_stderr_capture(self):
        result = run_shell(
            f"{sys.executable} -c \"import sys; sys.stderr.write('oops\\\\n')\""
        )

        self.assertEqual(result["stderr"], "oops\n")
        self.assertEqual(result["exit_code"], 0)

    def test_run_tests_no_pytest(self):
        result = run_tests()

        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["failure_summary"], "test runner not found")

    def test_run_tests_happy_path(self):
        test_file = self.root / "test_sample.py"
        test_file.write_text(
            "import unittest\n\n"
            "class SampleTest(unittest.TestCase):\n"
            "    def test_ok(self):\n"
            "        self.assertEqual(1 + 1, 2)\n",
            encoding="utf-8",
        )
        self.manifest.write_text(
            json.dumps(
                {
                    "test_command": (
                        f"{sys.executable} -m unittest discover "
                        "-s test_sandbox -p 'test_*.py'"
                    )
                }
            ),
            encoding="utf-8",
        )

        result = run_tests()

        self.assertGreater(result["passed"], 0)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["errors"], 0)

    def test_sandbox_read_escape(self):
        with self.assertRaises(PermissionError):
            read_file("../agent.py")

    def test_sandbox_edit_absolute_escape(self):
        with self.assertRaises(PermissionError):
            edit_file("/tmp/evil.txt", "x")

    def test_sandbox_list_absolute_escape(self):
        with self.assertRaises(PermissionError):
            list_dir("/etc")

    def test_sandbox_shell_parent_escape(self):
        with self.assertRaises(PermissionError):
            run_shell("cat ../agent.py")

    def test_sandbox_shell_rm_root(self):
        with self.assertRaises(PermissionError):
            run_shell("rm -rf /")

    def test_sandbox_symlink_escape(self):
        link = self.root / "outside_link"
        if not hasattr(link, "symlink_to"):
            self.skipTest("symlinks unsupported")
        try:
            link.symlink_to(Path("agent.py").resolve())
        except OSError as exc:
            self.skipTest(f"could not create symlink: {exc}")

        with self.assertRaises(PermissionError):
            read_file("test_sandbox/outside_link")

    def test_list_missing_returns_empty(self):
        self.assertEqual(list_dir("test_sandbox/nope"), [])


if __name__ == "__main__":
    unittest.main()
