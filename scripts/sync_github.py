#!/usr/bin/env python3
"""Commit public learning documents and push an explicitly enabled GitHub remote."""

from datetime import datetime
import fcntl
import os
from pathlib import Path
import re
import subprocess
import sys
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [
    "README.md", ":(glob)docs/**/*.md", ":(glob)daily/**/*.md",
    ":(glob)notes/**/*.md",
]


def git(root, *args, check=True):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.setdefault(
        "GIT_SSH_COMMAND",
        "ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=yes",
    )
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True,
        timeout=120, env=env, check=False,
    )
    if check and result.returncode:
        raise RuntimeError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result


def github_remote(root):
    fetch = git(root, "remote", "get-url", "origin").stdout.strip()
    pushes = git(root, "remote", "get-url", "--push", "--all", "origin").stdout.splitlines()
    if pushes != [fetch] or not re.fullmatch(
        r"git@github\.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", fetch
    ):
        raise RuntimeError("origin must have one matching GitHub SSH fetch/push URL.")
    return fetch


def sync(root=ROOT):
    root = Path(root)
    if not (root / ".git").exists() or git(
        root, "config", "--local", "--get", "learning.syncGitHub", check=False
    ).stdout.strip().lower() != "true":
        print("GitHub sync disabled; local documents retained.")
        return 0
    runtime = root / ".automation"
    runtime.mkdir(exist_ok=True)
    with (runtime / "github.lock").open("a") as lock:
        # Wait for another bounded sync so this run cannot silently miss its files.
        fcntl.flock(lock, fcntl.LOCK_EX)
        remote = github_remote(root)
        if git(root, "branch", "--show-current").stdout.strip() != "main":
            raise RuntimeError("Automatic sync requires branch main.")
        for state in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "rebase-merge", "rebase-apply"):
            state_path = Path(git(root, "rev-parse", "--git-path", state).stdout.strip())
            if not state_path.is_absolute():
                state_path = root / state_path
            if state_path.exists():
                raise RuntimeError("Finish the active Git operation before syncing.")
        if git(root, "diff", "--cached", "--quiet", check=False).returncode:
            raise RuntimeError("Existing staged changes found; commit or unstage them first.")
        files = sorted(set(filter(None, git(
            root, "ls-files", "--cached", "--others", "--exclude-standard", "-z",
            "--", *DOCUMENTS,
        ).stdout.split("\0"))))
        for relative in files:
            path = root / relative
            if path.is_symlink() or root.resolve() not in path.resolve().parents:
                raise RuntimeError(f"Refusing linked/outside document: {relative}")
        if files:
            git(root, "add", "--", *(f":(literal){name}" for name in files))
            if git(root, "diff", "--cached", "--quiet", check=False).returncode:
                day = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
                git(root, "commit", "-m", f"Update learning documents for {day}")
        # A previous offline run may already have committed the same report.
        result = git(root, "push", "--porcelain", "origin", "HEAD:refs/heads/main")
        print(f"Synced learning documents: {remote}")
        if result.stdout.strip():
            print(result.stdout.strip())
        return 0


if __name__ == "__main__":
    try:
        sys.exit(sync())
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"GitHub sync failed; local files/commits retained: {error}", file=sys.stderr)
        sys.exit(1)
