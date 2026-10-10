# 每日自动学习

## 约定

每天北京时间 09:00 生成一份中文知识讲义和联网动态，保存到 `daily/YYYY/MM/YYYY-MM-DD.md`。Windows 任务计划程序经 PowerShell 启动 WSL 中的 Python 脚本，脚本调用已登录的 Codex CLI；无需一直打开聊天窗口。

默认一天一课：当天掌握归档后结束，下一课按进度中的计划日期开始。提前准备的草稿不算已上课，也不因用户答对自测自动追加课程。

任务名：`AI-Model-Learn-Daily`。2026-10-09 已注册并确认启用，首次定时触发为 **2026-10-10 09:00 +08:00**，之后每天运行。现场状态记录在 `.automation/schedule.json`；后续是否仍启用以及运行结果，以 Windows 任务状态为准。

## 运行条件

- Windows 已开机、用户已登录（锁屏可以），WSL 发行版与工程路径仍可用。
- Codex 保持登录，账户有可用额度，网络能够访问模型服务和检索服务。
- Windows 时区为 `China Standard Time`，内容日期固定使用 `Asia/Shanghai`。
- 关机或睡眠期间不能保证准点执行；已启用错过后补运行。只补当前日期的一份内容，不补造过去几天的新闻。

任务在隐藏窗口中运行，确认 GitHub 上传成功后，通过 Windows 默认浏览器打开当天的日报。同一天成功打开过的页面不重复弹出；停用上传时不会打开尚未发布的 GitHub 页面。浏览器启动记录保存在 `%LOCALAPPDATA%\ai-model-learn\last-opened-report.txt`。

未配置在此聊天、邮件或手机中推送通知。Codex 在只读沙箱中研究和生成正文，由 Python 脚本检查标题、日期、章节和来源链接后保存。自动任务不修改学习进度，不归档为已掌握，也不修改 `AGENTS.md`。

## 手动运行与查看

在工程根目录执行：

```bash
python3 scripts/daily_learning.py --check
python3 scripts/daily_learning.py
```

同日文件已存在时保留人工修订；若已[启用 GitHub 同步](github-sync.md)，仍重试上传。新生成的日报也先落盘，再上传；上传失败不会删除本地文件。运行记录在 `.automation/runs/`，失败返回非零退出码；调度器最多间隔 15 分钟重试两次。检查报告格式不能代替事实核查，应阅读来源与首批输出。

Windows 启动日志位于 `%LOCALAPPDATA%\ai-model-learn\launcher.log`，用于排查 WSL 启动失败或确认已有日报被保留。

在 Windows PowerShell 中查看：

```powershell
Get-ScheduledTask -TaskName AI-Model-Learn-Daily
Get-ScheduledTaskInfo -TaskName AI-Model-Learn-Daily
```

## 停用与恢复

```powershell
Disable-ScheduledTask -TaskName AI-Model-Learn-Daily
Enable-ScheduledTask -TaskName AI-Model-Learn-Daily
```

停用只阻止后续触发。如需同时停止正在运行的任务，再执行 `Stop-ScheduledTask -TaskName AI-Model-Learn-Daily`。

安装使用 `scripts/install_daily_task.ps1`；遇到同名任务默认停止。传入 `-UpdateExisting` 可更新启动动作，保留已有触发时间、运行身份和重试设置，并将原任务 XML 备份到 `%LOCALAPPDATA%\ai-model-learn\task-backups\`。更换时区、发行版或工程路径后需要同步检查任务。

安装时显式传入自己的 WSL 发行版、Linux 用户和工程绝对路径，例如：

```powershell
.\scripts\install_daily_task.ps1 -Distro "Ubuntu" -LinuxUser "your-user" -ProjectPath "/home/your-user/ai-model-learn" -GitHubRepository "your-name/ai-model-learn"
```

`-GitHubRepository` 指定成功后要打开的仓库，必须与 SSH 上传目标一致；省略此项只生成与同步，不打开浏览器。更新已有任务时在命令末尾加上 `-UpdateExisting`。

## 初次验证（2026-10-09）

- 通过 Windows → WSL 路径实际调用 Codex，完成联网检索并生成首份日报。
- 4 项自动测试通过，覆盖成功保存、保留已有日报、模型调用失败和错误日期。
- Windows 任务实际触发成功，返回码为 `0`；此次检查命中同日报告保护，没有重复调用模型。
- 首份日报的新闻原文和日期已复核；`AGENTS.md` 内容未修改。

同日加入 GitHub 同步后，离线测试扩展为 12 项并全部通过，另覆盖上传失败后保留与重试、公开文件范围、重复执行、已有暂存内容保护、符号链接拒绝和远端分叉保护。测试使用临时本地 Git 仓库。

2026-10-09 17:17 +08:00 再次实际触发 Windows 任务：保留当日日报，通过 SSH 提交并上传文档到公开仓库 `day8reak/ai-model-learn`，任务返回码为 `0`。此轮验证没有重复调用模型；下次定时运行仍为 2026-10-10 09:00 +08:00。

## 2026-10-10 阅读入口验证

09:00 的首次定时运行成功，日报于 09:01:57 保存并上传。原启动动作没有隐藏窗口，也没有打开日报，因此用户只能看到终端。

随后将启动动作设置为隐藏窗口，在确认目标仓库上传成功后打开当天的 GitHub 日报。实际触发验证返回 `0`，启动日志记录了正确的日报 URL；当日文件保持不变，没有重新调用模型。再次触发时正常同步并跳过重复打开。更新保留了原触发时间、运行身份和重试设置；下次运行是 2026-10-11 09:00 +08:00。

## 参考

- [OpenAI：Scheduled tasks](https://learn.chatgpt.com/docs/automations)：也可使用产品内的定时任务；本工程采用 Windows 本地调度。
- [OpenAI：Codex 非交互执行](https://developers.openai.com/blog/eval-skills)：`codex exec` 的进度和结果可以重定向到日志与文件；阅读入口由本工程的启动脚本提供。
- [Microsoft：任务运行身份](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskprincipal?view=windowsserver2025-ps)。
- [Microsoft：任务设置](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset?view=windowsserver2025-ps)。
