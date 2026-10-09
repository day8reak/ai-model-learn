"""Check unattended generation without calling a model or using the network."""

from contextlib import redirect_stdout
from datetime import datetime
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "daily_learning", Path(__file__).resolve().parents[1] / "scripts/daily_learning.py"
)
daily = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(daily)


class DailyLearningTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "prompts").mkdir()
        (self.root / "prompts/daily-learning.md").write_text("Generate a lesson.")
        now = datetime.now(daily.TIMEZONE)
        self.day = now.strftime("%Y-%m-%d")
        self.report = self.root / "daily" / now.strftime("%Y/%m") / f"{self.day}.md"
        self.content = (
            f"# {self.day} 大模型推理学习日报\n\n"
            "## 今日知识\n" + "有来源的基础知识解释。" * 60
            + "\n## 最新动态\n今日动态检索失败：测试环境无网络。\n"
            "## 自测\n训练与推理的区别是什么？\n"
            "## 来源\n[资料](https://example.com/reference)\n"
        )
        for relative in ("AGENTS.md", "docs/progress.md"):
            path = self.root / relative
            path.parent.mkdir(exist_ok=True)
            path.write_text("preserve me", encoding="utf-8")

    def invoke(self, generated=None, returncode=0, sync_error=None):
        def fake_run(command, **kwargs):
            self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
            self.assertIn("--search", command)
            if generated is not None:
                output = Path(command[command.index("--output-last-message") + 1])
                output.write_text(generated, encoding="utf-8")
            return subprocess.CompletedProcess(command, returncode)

        with patch.object(daily, "ROOT", self.root), \
                patch.object(daily, "codex_binary", return_value="fake-codex"), \
                patch.object(daily.sys, "argv", ["daily_learning.py"]), \
                patch.object(daily, "sync_documents", side_effect=sync_error) as sync, \
                patch.object(daily.subprocess, "run", side_effect=fake_run) as run, \
                redirect_stdout(io.StringIO()):
            result = daily.main()
            sync.assert_called_once_with()
            return result, run.call_count

    def test_success_saves_report_without_changing_progress(self):
        self.assertEqual(self.invoke(self.content), (0, 1))
        self.assertEqual(self.report.read_text(encoding="utf-8"), self.content)
        for relative in ("AGENTS.md", "docs/progress.md"):
            self.assertEqual((self.root / relative).read_text(), "preserve me")

    def test_existing_report_is_preserved_without_model_call(self):
        self.report.parent.mkdir(parents=True)
        self.report.write_text("manual edits", encoding="utf-8")
        self.assertEqual(self.invoke(), (0, 0))
        self.assertEqual(self.report.read_text(), "manual edits")

    def test_model_failure_does_not_publish_report(self):
        with self.assertRaisesRegex(RuntimeError, "Codex exited"):
            self.invoke(returncode=1)
        self.assertFalse(self.report.exists())

    def test_sync_failure_keeps_saved_report_for_retry(self):
        with self.assertRaisesRegex(RuntimeError, "offline"):
            self.invoke(self.content, sync_error=RuntimeError("offline"))
        self.assertEqual(self.report.read_text(encoding="utf-8"), self.content)
        self.assertEqual(self.invoke(), (0, 0))

    def test_wrong_date_is_retained_only_as_a_draft(self):
        with self.assertRaisesRegex(RuntimeError, "title/date"):
            self.invoke(self.content.replace(self.day, "2000-01-01", 1))
        self.assertFalse(self.report.exists())
        self.assertEqual(len(list((self.root / ".automation/runs").glob("*/report.md"))), 1)


if __name__ == "__main__":
    unittest.main()
