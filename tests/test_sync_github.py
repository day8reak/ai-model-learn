"""Exercise backup and recovery against disposable local Git repositories."""

from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "sync_github", Path(__file__).resolve().parents[1] / "scripts/sync_github.py"
)
backup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup)


class GitHubSyncTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root = base / "working"
        self.remote = base / "remote.git"
        self.root.mkdir()
        self.git(self.root, "init", "-b", "main")
        self.git(self.root, "config", "user.name", "Test Author")
        self.git(self.root, "config", "user.email", "test@example.invalid")
        (self.root / ".gitignore").write_text(".automation/\n.env\n")
        (self.root / "README.md").write_text("Learning repository\n")
        self.git(self.root, "add", "README.md", ".gitignore")
        self.git(self.root, "commit", "-m", "Initialize test repository")
        self.git(base, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.git(self.root, "remote", "add", "origin", str(self.remote))
        self.git(self.root, "push", "origin", "main")
        self.git(self.root, "config", "--local", "learning.syncGitHub", "true")

    @staticmethod
    def git(root, *args):
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True,
            text=True, timeout=15,
        ).stdout.strip()

    def document(self, relative, content="A lesson with sources.\n"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def sync(self):
        # Only remote validation is substituted: commits and pushes use real Git.
        with patch.object(backup, "github_remote", return_value=str(self.remote)), \
                redirect_stdout(io.StringIO()):
            return backup.sync(self.root)

    def test_commits_only_public_documents_and_is_idempotent(self):
        self.document("daily/2026/10/2026-10-09.md")
        self.document("notes/foundations/T001-transformer.md")
        self.document("docs/progress.md")
        self.document("scripts/local.py", "private implementation")
        self.document(".env", "LOCAL_SECRET=fake-test-value")
        self.document(".automation/run.log", "local log")
        self.assertEqual(self.sync(), 0)
        head = self.git(self.root, "rev-parse", "HEAD")
        self.assertEqual(head, self.git(self.remote, "rev-parse", "main"))
        names = self.git(self.remote, "ls-tree", "-r", "--name-only", "main").splitlines()
        self.assertIn("daily/2026/10/2026-10-09.md", names)
        self.assertIn("notes/foundations/T001-transformer.md", names)
        self.assertIn("docs/progress.md", names)
        self.assertNotIn("scripts/local.py", names)
        self.assertNotIn(".env", names)
        self.assertNotIn(".automation/run.log", names)
        self.sync()
        self.assertEqual(head, self.git(self.root, "rev-parse", "HEAD"))

    def test_disabled_does_not_commit_or_push(self):
        self.git(self.root, "config", "learning.syncGitHub", "false")
        head = self.git(self.root, "rev-parse", "HEAD")
        self.document("docs/progress.md")
        self.sync()
        self.assertEqual(head, self.git(self.root, "rev-parse", "HEAD"))
        self.assertEqual(head, self.git(self.remote, "rev-parse", "main"))

    def test_existing_staged_changes_are_preserved(self):
        self.document("scripts/local.py")
        self.git(self.root, "add", "scripts/local.py")
        self.document("docs/progress.md")
        with self.assertRaisesRegex(RuntimeError, "staged changes"):
            self.sync()
        self.assertEqual(
            self.git(self.root, "diff", "--cached", "--name-only"), "scripts/local.py"
        )

    def test_push_failure_keeps_commit_and_retries_without_duplicate(self):
        path = self.document("docs/progress.md")
        self.git(self.root, "remote", "set-url", "origin", str(self.remote) + ".missing")
        with self.assertRaisesRegex(RuntimeError, "push failed"):
            self.sync()
        committed = self.git(self.root, "rev-parse", "HEAD")
        self.assertTrue(path.exists())
        self.assertNotEqual(committed, self.git(self.remote, "rev-parse", "main"))
        self.git(self.root, "remote", "set-url", "origin", str(self.remote))
        self.sync()
        self.assertEqual(committed, self.git(self.remote, "rev-parse", "main"))
        self.assertEqual(committed, self.git(self.root, "rev-parse", "HEAD"))

    def test_remote_divergence_is_not_overwritten(self):
        other = self.root.parent / "other"
        self.git(self.root.parent, "clone", str(self.remote), str(other))
        self.git(other, "config", "user.name", "Other")
        self.git(other, "config", "user.email", "other@example.invalid")
        (other / "README.md").write_text("Remote edit\n")
        self.git(other, "commit", "-am", "Edit remote")
        self.git(other, "push", "origin", "main")
        remote_head = self.git(self.remote, "rev-parse", "main")
        self.document("docs/progress.md")
        with self.assertRaisesRegex(RuntimeError, "push failed"):
            self.sync()
        self.assertEqual(remote_head, self.git(self.remote, "rev-parse", "main"))
        self.assertTrue((self.root / "docs/progress.md").exists())

    def test_rejects_document_symlinks(self):
        outside = self.root.parent / "private.md"
        outside.write_text("Do not publish")
        (self.root / "docs").mkdir()
        (self.root / "docs/leak.md").symlink_to(outside)
        with self.assertRaisesRegex(RuntimeError, "linked/outside"):
            self.sync()

    def test_rejects_unexpected_remote(self):
        with self.assertRaisesRegex(RuntimeError, "GitHub SSH"):
            backup.sync(self.root)


if __name__ == "__main__":
    unittest.main()
