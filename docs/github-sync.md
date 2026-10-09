# GitHub 公开备份

目标仓库：[day8reak/ai-model-learn](https://github.com/day8reak/ai-model-learn)，公开。2026-10-09 已通过本地 SSH 完成首次上传，发布分支为 `main`，当前主机已启用同步。后续是否启用，以本机 `git config --local --get learning.syncGitHub` 和实际推送结果为准。

## 公开范围

初次提交包含经过检查的文档、日报、提示词、脚本和测试。后续自动提交只包含 `README.md` 及 `docs/`、`daily/`、`notes/` 下的 Markdown 文件。学习总结和跳过记录仍由用户反馈触发，归档后运行同步脚本。

自动推送会包含 `main` 上尚未上传的本地提交，手动提交前也需检查内容。日志、任务配置、登录凭证、SSH 私钥、模型权重和数据集不上传。公开文档只保留可分享的技术问题与原创总结，引用外部资料附链接和署名，不整篇转载。

## 首次配置

在 GitHub 创建空公开仓库，先检查 SSH 账号，再配置地址。其他使用者应替换为自己的仓库。

```bash
ssh -T git@github.com
git remote add origin git@github.com:day8reak/ai-model-learn.git
git push -u origin main
git config --local learning.syncGitHub true
```

SSH 成功时会显示账号且通常返回退出码 1；这不表示认证失败。创建仓库需要 GitHub 网页或 API 授权，SSH 只负责访问已有仓库。

## 日常同步

```bash
python3 scripts/sync_github.py
git status --short
git log -3 --oneline
```

每天的生成脚本在保存日报后同步；当天日报已经存在时也重试同步，不重新生成或覆盖正文。只有本机明确设置 `learning.syncGitHub=true` 才启用，克隆本仓库不会自动启用推送。

网络失败时，文件和本地提交仍保留，脚本返回失败以便调度器重试。出现已有暂存内容、正在合并、非 `main` 分支或远端历史分叉时停止同步，不自动合并或强制推送；检查错误并处理后重新运行。同步前后编辑文件时应避免同时手动操作 Git 索引。

```bash
git config --local learning.syncGitHub false  # 只停用上传，保留本地每日生成
```

当前方案依赖本机开机、用户登录、网络和 SSH 可用，不是在 GitHub 云端定时生成。
