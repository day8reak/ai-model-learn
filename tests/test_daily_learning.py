"""Verify course/date separation without a model, network or real repository."""

from contextlib import redirect_stdout
from datetime import datetime, timedelta
import importlib.util
import io
import json
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
        (self.root / "prompts/daily-learning.md").write_text("Generate requested parts.")
        (self.root / "docs").mkdir()
        (self.root / "AGENTS.md").write_text("preserve me")
        self.progress_file = self.root / "docs/progress.md"
        self.study_log = self.root / "study-log/2026/10/2026-10-12.md"
        self.save(self.study_log, "User feedback must remain unchanged.\n")
        self.now = datetime(2026, 10, 12, 9, tzinfo=daily.TIMEZONE)
        self.day = self.now.strftime("%Y-%m-%d")
        self.lesson_id = "T002-1"
        self.set_progress()
        self.report = self.report_path()
        self.lesson = self.root / "lessons/T002-1.md"
        self.lesson_text = (
            "# T002-1 — Token、token ID 与词表\n\n"
            "## 知识讲解\n" + "解释身份编号与序列位置的不同。" * 45
            + "\n## 自测\n编号改变会改变哪些对应关系？\n"
            "## 来源\n[资料](https://example.com/reference)\n"
        )
        self.news_text = self.news()

    def set_progress(self, identifier="T002-1", state="学习中", day=None):
        self.progress_file.write_text(
            f"- 当前知识点：{identifier} — Token、token ID 与词表\n"
            f"- 当前状态：{state}\n- 计划开始：{day or self.day}\n",
            encoding="utf-8",
        )

    def report_path(self):
        return self.root / "daily" / self.now.strftime("%Y/%m") / f"{self.now:%Y-%m-%d}.md"

    def news(self):
        return (
            f"# {self.now:%Y-%m-%d} 大模型动态\n\n## 最新动态\n"
            + "今日动态检索失败：离线测试环境不能访问网络。" * 10
            + "\n## 来源\n本次未使用外部来源，不编造新闻。\n"
        )

    @staticmethod
    def save(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def invoke(self, lesson=None, news=None, *, raw=None, returncode=0,
               sync_error=None, during_run=None, crossed_midnight=False):
        def fake_run(command, **kwargs):
            self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
            self.assertIn("--search", command)
            self.request = kwargs["input"]
            if during_run:
                during_run()
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text(
                raw if raw is not None else json.dumps({"lesson": lesson, "news": news}),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, returncode)

        with patch.object(daily, "ROOT", self.root), \
                patch.object(daily, "codex_binary", return_value="fake-codex"), \
                patch.object(daily.sys, "argv", ["daily_learning.py"]), \
                patch.object(daily, "datetime", wraps=datetime) as clock, \
                patch.object(daily, "sync_documents", side_effect=sync_error) as sync, \
                patch.object(daily.subprocess, "run", side_effect=fake_run) as run, \
                redirect_stdout(io.StringIO()):
            clock.now.side_effect = [self.now, self.now + timedelta(days=int(crossed_midnight))]
            result = daily.main()
            sync.assert_called_once_with()
            return result, run.call_count

    def test_new_course_and_news_have_independent_paths_and_keep_progress(self):
        progress = self.progress_file.read_text()
        self.assertEqual(self.invoke(self.lesson_text, self.news_text), (0, 1))
        self.assertEqual(self.lesson.read_text(), self.lesson_text)
        self.assertIn(self.news_text.split("## 最新动态", 1)[1], self.report.read_text())
        self.assertIn("../../../lessons/T002-1.md", self.report.read_text())
        self.assertIn("[T002-1 — Token、token ID 与词表](T002-1.md)",
                      (self.root / "lessons/README.md").read_text())
        self.assertEqual(self.progress_file.read_text(), progress)
        self.assertEqual((self.root / "AGENTS.md").read_text(), "preserve me")
        self.assertEqual(self.study_log.read_text(), "User feedback must remain unchanged.\n")

    def test_existing_documents_are_preserved_without_model_call(self):
        self.save(self.lesson, "# T002-1 — Manual course\nfeedback\n")
        self.save(self.report, "manual news")
        self.assertEqual(self.invoke(), (0, 0))
        self.assertIn("feedback", self.lesson.read_text())
        self.assertEqual(self.report.read_text(), "manual news")

    def test_break_for_several_days_reuses_same_course(self):
        self.save(self.lesson, "# T002-1 — Manual course\nquiz answers\n")
        self.save(self.report, "previous day's news")
        self.now += timedelta(days=4)
        self.assertEqual(self.invoke(news=self.news()), (0, 1))
        self.assertIn('"generate_lesson": false', self.request)
        self.assertEqual(self.lesson.read_text(), "# T002-1 — Manual course\nquiz answers\n")
        self.assertTrue(self.report_path().is_file())
        self.assertEqual(self.report.read_text(), "previous day's news")
        self.assertFalse((self.root / "lessons/T002-2.md").exists())

    def test_second_course_same_day_does_not_require_new_news(self):
        self.save(self.lesson, self.lesson_text)
        self.save(self.report, "existing edited news")
        self.set_progress("T002-2")
        next_lesson = self.lesson_text.replace("T002-1", "T002-2", 1)
        self.assertEqual(self.invoke(lesson=next_lesson), (0, 1))
        self.assertEqual((self.root / "lessons/T002-2.md").read_text(), next_lesson)
        self.assertEqual(self.lesson.read_text(), self.lesson_text)
        self.assertEqual(self.report.read_text(), "existing edited news")
        self.assertIn('"generate_news": false', self.request)

    def test_future_course_waits_while_news_is_generated(self):
        self.set_progress(day="2026-10-13", state="待学习")
        self.assertEqual(self.invoke(news=self.news_text), (0, 1))
        self.assertFalse(self.lesson.exists())
        self.assertNotIn("../../../lessons/T002-1.md", self.report.read_text())

    def test_paused_course_does_not_advance(self):
        self.set_progress(state="暂缓")
        self.assertEqual(self.invoke(news=self.news_text), (0, 1))
        self.assertFalse(self.lesson.exists())

    def test_model_failure_does_not_publish_any_document(self):
        with self.assertRaisesRegex(RuntimeError, "Codex exited"):
            self.invoke(returncode=1)
        self.assertFalse(self.lesson.exists())
        self.assertFalse(self.report.exists())

    def test_sync_failure_retains_both_documents_and_retries_without_model(self):
        with self.assertRaisesRegex(RuntimeError, "offline"):
            self.invoke(self.lesson_text, self.news_text, sync_error=RuntimeError("offline"))
        self.assertEqual(self.lesson.read_text(), self.lesson_text)
        self.assertTrue(self.report.exists())
        self.assertEqual(self.invoke(), (0, 0))

    def test_wrong_date_rejects_entire_bundle_and_retains_draft(self):
        with self.assertRaisesRegex(RuntimeError, "title/identifier"):
            self.invoke(self.lesson_text, self.news_text.replace(self.day, "2000-01-01", 1))
        self.assertFalse(self.lesson.exists())
        self.assertFalse(self.report.exists())
        self.assertEqual(len(list((self.root / ".automation/runs").glob("*/bundle.json"))), 1)

    def test_wrong_course_rejects_entire_bundle(self):
        with self.assertRaisesRegex(RuntimeError, "title/identifier"):
            self.invoke(self.lesson_text.replace("T002-1", "T002-2", 1), self.news_text)
        self.assertFalse(self.lesson.exists())
        self.assertFalse(self.report.exists())

    def test_invalid_json_is_not_published(self):
        with self.assertRaisesRegex(RuntimeError, "JSON object"):
            self.invoke(raw="not JSON")
        self.assertFalse(self.lesson.exists())
        self.assertFalse(self.report.exists())

    def test_unrequested_course_cannot_replace_existing_feedback(self):
        self.save(self.lesson, "# T002-1 — Manual course\nquiz answers\n")
        with self.assertRaisesRegex(RuntimeError, "Unexpected lesson"):
            self.invoke(self.lesson_text, self.news_text)
        self.assertIn("quiz answers", self.lesson.read_text())
        self.assertFalse(self.report.exists())

    def test_interactive_lesson_written_during_generation_wins(self):
        def concurrent_edit():
            self.save(self.lesson, "# T002-1 — Interactive lesson\nmanual feedback\n")
        self.assertEqual(self.invoke(self.lesson_text, self.news_text, during_run=concurrent_edit), (0, 1))
        self.assertIn("manual feedback", self.lesson.read_text())
        self.assertTrue(self.report.exists())

    def test_progress_change_during_generation_does_not_publish_stale_course(self):
        with self.assertRaisesRegex(RuntimeError, "progress changed"):
            self.invoke(self.lesson_text, self.news_text, during_run=lambda: self.set_progress("T002-2"))
        self.assertFalse(self.lesson.exists())
        self.assertFalse(self.report.exists())

    def test_course_id_cannot_escape_lesson_directory(self):
        self.set_progress("../outside")
        with self.assertRaisesRegex(RuntimeError, "course ID"):
            self.invoke(self.lesson_text, self.news_text)
        self.assertFalse(self.lesson.exists())

    def test_invalid_planned_date_does_not_publish_documents(self):
        self.set_progress(day="2026-02-30")
        with self.assertRaisesRegex(RuntimeError, "invalid planned date"):
            self.invoke(self.lesson_text, self.news_text)
        self.assertFalse(self.lesson.exists())
        self.assertFalse(self.report.exists())

    def test_midnight_does_not_publish_yesterdays_news(self):
        with self.assertRaisesRegex(RuntimeError, "crossed midnight"):
            self.invoke(self.lesson_text, self.news_text, crossed_midnight=True)
        self.assertFalse(self.lesson.exists())
        self.assertFalse(self.report.exists())

    def test_index_preserves_manual_text_outside_table(self):
        self.save(self.root / "lessons/README.md",
                  "# Custom introduction\n<!-- courses:start -->\nold\n<!-- courses:end -->\nCustom footer\n")
        self.invoke(self.lesson_text, self.news_text)
        index = (self.root / "lessons/README.md").read_text()
        self.assertTrue(index.startswith("# Custom introduction\n"))
        self.assertTrue(index.endswith("Custom footer\n"))
        self.assertIn("T002-1.md", index)


if __name__ == "__main__":
    unittest.main()
