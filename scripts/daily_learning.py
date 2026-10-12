#!/usr/bin/env python3
"""Prepare the current numbered lesson and dated news independently."""

import argparse
import fcntl
import json
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


def current_course(progress, day):
    match = re.search(
        r"^- 当前知识点：([A-Z]+[0-9]+(?:-[0-9]+)*) — (.+)$",
        progress, re.MULTILINE,
    )
    state = re.search(r"^- 当前状态：(.+)$", progress, re.MULTILINE)
    start = re.search(r"^- 计划开始：(\d{4}-\d{2}-\d{2})", progress, re.MULTILINE)
    if not (match and state and start):
        raise RuntimeError("Progress must declare a course ID, status and planned date.")
    try:
        planned_day = datetime.strptime(start[1], "%Y-%m-%d").date().isoformat()
    except ValueError as error:
        raise RuntimeError("Progress has an invalid planned date.") from error
    eligible = state[1].strip() in ("待学习", "学习中") and planned_day <= day
    return match[1], match[2], eligible


def validate_document(content, kind, identifier):
    if not isinstance(content, str):
        raise RuntimeError(f"Missing {kind} Markdown; inspect the run log.")
    content = content.strip() + "\n"
    if kind == "lesson":
        valid_title = re.match(rf"^# {re.escape(identifier)} — [^\n]+\n", content)
        headings = ("知识讲解", "自测", "来源")
        minimum = 500
    else:
        valid_title = content.startswith(f"# {identifier} 大模型动态\n")
        headings = ("最新动态", "来源")
        minimum = 150
    if not valid_title:
        raise RuntimeError(f"{kind} title/identifier is invalid; inspect the run log.")
    for heading in headings:
        if not re.search(rf"^## {heading}\s*$", content, re.MULTILINE):
            raise RuntimeError(f"{kind} section missing: {heading}")
    if len(content.strip()) < minimum:
        raise RuntimeError(f"{kind} is too short; inspect the run log.")
    no_news = kind == "news" and (
        "检索失败" in content or "未找到可核实的新动态" in content
    )
    if not no_news and not re.search(r"\[[^\]]+\]\(https?://[^\s)]+\)", content):
        raise RuntimeError(f"{kind} has no source links; inspect the run log.")
    return content


def validate_bundle(raw, lesson_id, day, need_lesson, need_news):
    try:
        bundle = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("Output must be a JSON object; inspect the run log.") from error
    if not isinstance(bundle, dict) or set(bundle) != {"lesson", "news"}:
        raise RuntimeError("Output must contain exactly lesson and news.")
    for kind, needed, identifier in (
        ("lesson", need_lesson, lesson_id), ("news", need_news, day),
    ):
        if needed:
            bundle[kind] = validate_document(bundle[kind], kind, identifier)
        elif bundle[kind] is not None:
            raise RuntimeError(f"Unexpected {kind}; existing documents must be preserved.")
    return bundle


def publish_document(draft, target, content):
    draft.write_text(content, encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Atomic creation: a concurrent interactive lesson always wins.
        os.link(draft, target)
    except FileExistsError:
        print(f"Existing document preserved: {target}")
    else:
        print(f"Saved: {target}")


def refresh_lesson_index():
    directory = ROOT / "lessons"
    directory.mkdir(exist_ok=True)
    index = directory / "README.md"
    begin, end = "<!-- courses:start -->", "<!-- courses:end -->"
    if index.exists():
        content = index.read_text(encoding="utf-8")
        if content.count(begin) != 1 or content.count(end) != 1:
            raise RuntimeError("Lesson index markers are missing; index preserved.")
        prefix, rest = content.split(begin)
        _, suffix = rest.split(end)
    else:
        prefix = (
            "# 课程讲义\n\n每个课号对应一份讲义，讲解、例子和自测题集中维护。\n\n"
            "学习状态以[进度](../docs/progress.md)为准；顺序见[路线](../docs/roadmap.md)。"
            "日期、答题反馈和暂停位置记入[学习日志](../study-log/README.md)。"
            "已掌握或跳过后的总结见[知识索引](../notes/README.md)。\n\n"
            "下表自动维护，文件存在不代表已经学习或掌握。\n\n"
        )
        suffix = "\n"
    rows = ["| 课号 | 讲义 |", "| --- | --- |"]
    for path in sorted(directory.glob("*.md")):
        if not re.fullmatch(r"[A-Z]+[0-9]+(?:-[0-9]+)*", path.stem):
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        title = lines[0].removeprefix("# ") if lines else path.stem
        title = title.replace("|", r"\|").replace("[", r"\[").replace("]", r"\]")
        rows.append(f"| {path.stem} | [{title}]({path.name}) |")
    updated = prefix + begin + "\n" + "\n".join(rows) + "\n" + end + suffix
    if not index.exists() or content != updated:
        draft = ROOT / ".automation" / "lesson-index.md"
        draft.write_text(updated, encoding="utf-8")
        os.replace(draft, index)


def learning_entry(lesson_id, available):
    links = (
        "[当前进度](../../../docs/progress.md) · [课程目录](../../../lessons/README.md)"
        " · [学习日志](../../../study-log/README.md)"
    )
    if available:
        links += f" · [本次课程 {lesson_id}](../../../lessons/{lesson_id}.md)"
    return "## 学习入口\n\n" + links + "\n\n课程按课号保存，学习进度不随日期自动推进。\n\n"


def sync_documents():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/sync_github.py")],
        timeout=300, check=False,
    )
    if result.returncode:
        raise RuntimeError("Documents retained locally; GitHub sync failed. Retry sync_github.py.")


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
        progress_file = ROOT / "docs/progress.md"
        progress = progress_file.read_text(encoding="utf-8")
        lesson_id, lesson_title, eligible = current_course(progress, day)
        lesson = ROOT / "lessons" / f"{lesson_id}.md"
        report = ROOT / "daily" / now.strftime("%Y/%m") / f"{day}.md"
        for path in (lesson, report, ROOT / "lessons/README.md"):
            if path.is_symlink() or ROOT.resolve() not in path.resolve().parents:
                raise RuntimeError(f"Refusing linked/outside document: {path}")
        need_lesson, need_news = eligible and not lesson.exists(), not report.exists()
        if not need_lesson and not need_news:
            print("Current lesson and dated news preserved; nothing to generate.")
            refresh_lesson_index()
            sync_documents()
            return 0
        run_dir = runtime / "runs" / now.strftime("%Y-%m-%d_%H%M%S_%f")
        run_dir.mkdir(parents=True)
        draft = run_dir / "bundle.json"
        prompt = (
            f"本次日期：{day}；当前时间：{now.isoformat()}；时区：Asia/Shanghai。\n"
            f"工程根目录：{ROOT}\n\n"
            "本次输出要求（只生成标记为 true 的部分，其余返回 null）：\n"
            + json.dumps({
                "lesson_id": lesson_id, "lesson_title": lesson_title,
                "lesson_path": f"lessons/{lesson_id}.md",
                "generate_lesson": need_lesson, "generate_news": need_news,
            }, ensure_ascii=False) + "\n\n"
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
        bundle = validate_bundle(
            draft.read_text(encoding="utf-8"), lesson_id, day, need_lesson, need_news,
        )
        if datetime.now(TIMEZONE).strftime("%Y-%m-%d") != day:
            raise RuntimeError("Run crossed midnight; draft preserved, rerun for the new day.")
        if need_lesson and progress_file.read_text(encoding="utf-8") != progress:
            raise RuntimeError("Learning progress changed during generation; drafts retained, rerun.")
        if need_lesson:
            publish_document(run_dir / "lesson.md", lesson, bundle["lesson"])
        if need_news:
            title, body = bundle["news"].split("\n", 1)
            content = title + "\n\n" + learning_entry(lesson_id, lesson.exists()) + body.lstrip()
            publish_document(run_dir / "news.md", report, content)
        refresh_lesson_index()
        sync_documents()
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"Daily learning failed: {error}", file=sys.stderr)
        sys.exit(1)
