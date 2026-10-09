# 大模型推理每日学习

从 Transformer、Prefill、Decode、KV Cache 开始，沿千问、DeepSeek 等开源模型从早期到最新公开版本学习结构与优化，建立可复习、检索和实践的中文知识库。

目标是逐步具备独立开发 NPU 算子、打通整模型推理和完成端到端优化的能力。先学通用原理，之后再选平台；通过参考实现、设备验证和性能实验验收能力，不把理解结构等同于已经能够交付所有模型。

## 每日节奏

- **时间**：每天北京时间 09:00（`Asia/Shanghai`）。
- **今日知识**：一个核心问题、直观解释、具体例子、常见误区和 2–3 道自测题；默认约 20–30 分钟，可随时调整深度。
- **最新动态**：每天联网检索，优先阅读官方发布、论文和项目发布说明；每条记录发布日期、来源和对推理的实际影响。
- **学习反馈**：围绕不理解的部分继续讲解；吃透后整理正式笔记并分类保存。
- **快速跳过**：说“太简单”“已了解”或“跳过”，仍归档该知识的简明摘要，标记“已跳过”并记录原因，然后立即进入下一知识点。

每日生成资料不代表已经掌握。无人值守任务依据进度提供新课或巩固练习，不自行把知识标为掌握，也不因跨天跳过未完成内容。

## 学习与归档规则

1. 开始学习前读取[路线](docs/roadmap.md)和[进度](docs/progress.md)，从当前知识点继续。
2. 用户确认吃透后，将定义、原理、例子、理解中的疑问与纠正、适用边界、自测和来源整理成正式笔记，标记“已掌握”。公开笔记只保留技术问题，不包含私人聊天或敏感信息。
3. 用户要求跳过时，直接生成一份简明笔记，保留定义、核心结论、适用场景、来源及跳过原因，标记“已跳过”；不要求再次确认。
4. 归档到 `notes/<分类>/<编号>-<英文短名>.md`，更新[知识索引](notes/README.md)和学习进度，再开始下一个知识点。
5. “已跳过”可以随时重新学习。新技术先进入候选清单，补齐前置知识后再安排，避免打乱基础学习顺序。
6. 理论掌握、CPU 参考实现、NPU 验证和性能优化分别记录；跳过理论不自动视为完成实践。博客辅助理解，面经用于补充自测，技术结论核对原始资料。

## 文件导航

| 路径 | 用途 |
| --- | --- |
| [docs/roadmap.md](docs/roadmap.md) | 从基础到进阶的学习顺序 |
| [docs/progress.md](docs/progress.md) | 当前知识点、掌握与跳过记录 |
| [docs/model-evolution.md](docs/model-evolution.md) | 千问与 DeepSeek 历代结构比较 |
| [docs/practice-milestones.md](docs/practice-milestones.md) | 从参考实现到 NPU 交付的验收标准 |
| [docs/reading-list.md](docs/reading-list.md) | 已筛选的博客、论文和代码 |
| [docs/interview-practice.md](docs/interview-practice.md) | 面经来源与阶段自测 |
| `daily/YYYY/MM/YYYY-MM-DD.md` | 每日知识讲义和最新动态，属于学习材料 |
| [notes/README.md](notes/README.md) | 按主题分类的正式知识索引 |
| [docs/automation.md](docs/automation.md) | 自动运行、查看结果和停用方法 |
| [docs/github-sync.md](docs/github-sync.md) | GitHub 备份、公开范围和故障恢复 |
| [prompts/daily-learning.md](prompts/daily-learning.md) | 每日任务的执行要求 |

## 动态质量要求

默认检索最近 24 小时，必要时扩展至近 7 天并明确标注“近期补充”。没有可核实的新消息时如实说明，不凑数量；搜索失败时标记失败，不声称“今日无新动态”。区分发布日期、事件日期和检索日期；同一事件不重复充当新消息。性能数字必须注明测试条件及信息来源，厂商宣称不视为本工程实测。

## 本地运行

```bash
python3 scripts/daily_learning.py --check  # 检查依赖与登录状态，不生成日报
python3 scripts/daily_learning.py          # 生成今天的日报；已有内容保留；启用后同步 GitHub
python3 scripts/sync_github.py             # 同步公开学习文档；需先完成仓库配置
python3 -m unittest discover -s tests -v    # 离线测试，不调用模型或 GitHub
```

生成日报需要 Python 3.9+、已登录的 Codex CLI 和可用网络，不需要下载模型。任务沿用当前 Codex 默认模型与账户额度。GitHub 同步另需 Git、目标仓库和可用 SSH 认证；凭证始终保留在本机。
