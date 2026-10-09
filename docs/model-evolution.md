# 模型演进与比较方法

资料核对日期：2026-10-09。下表是学习选型快照，不宣称穷尽所有分支。实际学习时重查官方资料，固定模型 ID、权重 revision、代码 commit 和依赖版本后再实验。

## 千问主线

| 顺序 | 版本/分支 | 学习任务与来源 |
| --- | --- | --- |
| Q01 | Qwen / Qwen1.5 | 从早期 Decoder 建立基线；[Qwen 官方代码](https://github.com/QwenLM/Qwen)。Qwen1.5 检查点开课时选定 |
| Q02 | Qwen2 | 对照 Dense/MoE、注意力和前馈配置；[技术报告](https://arxiv.org/abs/2407.10671) |
| Q03 | Qwen2.5 | 区分结构、训练和上下文能力的变化；[技术报告](https://arxiv.org/abs/2412.15115) |
| Q04 | Qwen3 | 对照 Dense/MoE 实现及路由；[技术报告](https://arxiv.org/abs/2505.09388) |
| Q05 | Qwen3-Next | Gated DeltaNet 与全注意力混合、稀疏专家、MTP；[官方博客](https://qwen.ai/blog?id=qwen3-next) |
| Q06 | Qwen3.5 → Qwen3.6 → Qwen3.8 | 比较混合架构与多模态分支，区分推理相关的实际改变；[官方系列仓库](https://github.com/QwenLM/Qwen3.8) |
| Q07 | Qwen3.8-Flash-Next | GDN+QSA、门控残差、N-gram embedding 的算子与状态需求；[官方资料](https://github.com/QwenLM/Qwen3.8-Flash-Next) |

系列版本不是单线继承关系，Qwen3.8 与 Flash-Next 单独比较。仓库重定向不代表旧模型的结构被改写，旧课应保留当时的源码 revision。

## DeepSeek 主线

| 顺序 | 版本/分支 | 学习任务与来源 |
| --- | --- | --- |
| DS01 | DeepSeek LLM | 建立早期 Dense 参照；[官方代码](https://github.com/deepseek-ai/DeepSeek-LLM) |
| DS02 | DeepSeekMoE / V2 | 专家分工、MLA 与缓存/矩阵计算；[V2 官方实现](https://github.com/deepseek-ai/DeepSeek-V2) |
| DS03 | V3 | MoE、MLA、MTP 与推理部署；[技术报告](https://arxiv.org/abs/2412.19437) |
| DS04 | R1 / Distill 分支 | 区分后训练策略和骨干，蒸馏模型按实际 Qwen/Llama 骨干分析；[官方说明](https://github.com/deepseek-ai/DeepSeek-R1) |
| DS05 | V3.2 | 稀疏索引与 Attention 路径，区别实验版与正式版；[正式模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V3.2) |
| DS06 | V4 系列 | 压缩/稀疏注意力、残差与服务实现；[V4-Flash 模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash) |
| DS07 | V4.1-Flash | 因果 Encoder–Decoder、跨层缓存复用与状态压缩；[官方模型卡和报告](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) |

先读模型报告与最小实现，再研究推理引擎和硬件 kernel。分别记录模型结构、引擎策略和硬件实现，避免混淆。

## 每个模型的比较表

1. **身份**：模型 ID、用途、许可证、权重和代码版本。
2. **结构**：层序、注意力/状态机制、归一化、位置、FFN/MoE、输出头及视觉/音频模块。
3. **形状**：batch、序列长、隐藏维、Q/KV 头数、head dim、专家数，以及 dtype/layout。
4. **状态**：区分权重和 KV/递归/卷积状态，说明追加、复用、回滚与释放。
5. **执行**：分别画 Prefill、Decode、Draft/Verify 路径，列出可复用算子与缺口。
6. **代价与验证**：计算、存储、搬运、通信、精度风险和最小实验。

用 [Mistral 7B](https://arxiv.org/abs/2310.06825)补充滑动窗口；再按差异选择 Llama、Gemma、GLM、Kimi、SSM/混合模型。文本主线完成后扩展视觉和音频的编码器、连接层、预处理与后处理。
