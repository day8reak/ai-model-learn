#!/usr/bin/env python3
"""Generate one local daily lesson using the signed-in Codex CLI."""

import argparse
import fcntl
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Shanghai")


def codex_binary():
    configured = os.environ.get("AI_MODEL_LEARN_CODEX")
    if configured:
        executable = shutil.which(configured)
    else:
        # WSL may put a Windows npm shim before the native Linux installation.
        candidate = Path.home() / ".local/bin/codex"
        executable = (
            str(candidate) if candidate.is_file() and os.access(candidate, os.X_OK)
            else shutil.which("codex")
        )
    if not executable:
        raise RuntimeError("Codex CLI not found; install it and run codex login.")
    return executable


def validate_report(content, day):
    if not content.startswith(f"# {day} 大模型推理学习日报\n"):
        raise RuntimeError("Report title/date is invalid; inspect the run log.")
    for heading in ("今日知识", "最新动态", "自测", "来源"):
        if not re.search(rf"^## {heading}\s*$", content, re.MULTILINE):
            raise RuntimeError(f"Report section missing: {heading}")
    if len(content.strip()) < 500:
        raise RuntimeError("Report is too short; inspect the run log.")
    if not re.search(r"\[[^\]]+\]\(https?://[^\s)]+\)", content):
        raise RuntimeError("Report has no source links; inspect the run log.")


def sync_documents():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/sync_github.py")],
        timeout=300, check=False,
    )
    if result.returncode:
        raise RuntimeError("Report retained locally; GitHub sync failed. Retry sync_github.py.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check setup without generating")
    args = parser.parse_args()
    binary = codex_binary()
    prompt_file = ROOT / "prompts/daily-learning.md"
    if not prompt_file.is_file():
        raise RuntimeError(f"Missing prompt: {prompt_file}")
    if args.check:
        result = subprocess.run([binary, "login", "status"], timeout=30, check=False)
        if result.returncode:
            raise RuntimeError("Codex login is required.")
        print(f"Ready: {ROOT}; timezone=Asia/Shanghai; codex={binary}")
        return 0

    now = datetime.now(TIMEZONE)
    day = now.strftime("%Y-%m-%d")
    runtime = ROOT / ".automation"
    runtime.mkdir(exist_ok=True)
    with (runtime / "daily.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another daily run is active; skipped.")
            return 0
        report = ROOT / "daily" / now.strftime("%Y/%m") / f"{day}.md"
        if report.exists():
            print(f"Report already exists; preserved: {report}")
            sync_documents()
            return 0
        run_dir = runtime / "runs" / now.strftime("%Y-%m-%d_%H%M%S_%f")
        run_dir.mkdir(parents=True)
        draft = run_dir / "report.md"
        prompt = (
            f"本次日期：{day}；当前时间：{now.isoformat()}；时区：Asia/Shanghai。\n"
            f"工程根目录：{ROOT}\n\n"
            + prompt_file.read_text(encoding="utf-8")
        )
        command = [
            binary, "--search", "--ask-for-approval", "never", "exec",
            "--sandbox", "read-only", "--skip-git-repo-check",
            "--cd", str(ROOT), "--color", "never",
            "--output-last-message", str(draft), "-",
        ]
        print(f"Generating {day}; log: {run_dir / 'run.log'}", flush=True)
        with (run_dir / "run.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command, input=prompt, text=True, stdout=log,
                stderr=subprocess.STDOUT, timeout=1500, check=False,
            )
        if result.returncode:
            raise RuntimeError(f"Codex exited {result.returncode}; see {run_dir / 'run.log'}")
        content = draft.read_text(encoding="utf-8").strip() + "\n"
        validate_report(content, day)
        if datetime.now(TIMEZONE).strftime("%Y-%m-%d") != day:
            raise RuntimeError("Run crossed midnight; draft preserved, rerun for the new day.")
        draft.write_text(content, encoding="utf-8")
        report.parent.mkdir(parents=True, exist_ok=True)
        # Atomic creation without replacing a report written by another process.
        os.link(draft, report)
        print(f"Saved: {report}")
        sync_documents()
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"Daily learning failed: {error}", file=sys.stderr)
        sys.exit(1)
