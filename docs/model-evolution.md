# 模型演进与比较方法

最新版本核查日期：2026-10-13。学习范围已确认包括 Qwen、DeepSeek、Kimi、Llama、Mistral/Mixtral、GLM。下表选择从旧到新的代表版本，不宣称穷尽所有检查点；箭头和编号表示学习顺序，不保证直接继承关系。实际学习时重查官方资料，固定模型 ID、权重 revision、代码 commit 和依赖版本后再实验。

## 当前已核实的版本范围

下表以官方模型卡、仓库和发布公告为依据，聚焦语言及视觉语言模型；模型页面的最近更新时间不当作发布日期。开放权重不代表所有系列采用相同许可证，具体使用以选定版本为准。

| 系列 | 本次确认的最新学习范围 | 开放状态与官方依据 |
| --- | --- | --- |
| Qwen（阿里） | Qwen3.8；单列 Qwen3.8-Flash-Next 分支 | [3.8 系列仓库](https://github.com/QwenLM/Qwen3.8)提供 27B、2.4T-A95B 等权重入口；[Flash-Next](https://github.com/QwenLM/Qwen3.8-Flash-Next)也已开放权重，不能据其预览说明将 Qwen4 写成已发布 |
| DeepSeek | DeepSeek-V4.1-Flash | [官方模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)提供权重、报告和最小推理入口 |
| Kimi（月之暗面） | Kimi-K3 | [官方模型卡](https://huggingface.co/moonshotai/Kimi-K3)已开放权重；Kimi Linear 作为独立机制分支保留 |
| Llama（Meta） | Llama 4 Scout / Maverick | [官方版本清单](https://github.com/meta-llama/llama-models)与[模型卡](https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md)列出可获取的两个版本 |
| Mistral/Mixtral（Mistral AI） | 已开放：Large 3 / Ministral 3、Small 4、Medium 3.5；已公布：Large 4 | [官方权重目录](https://huggingface.co/mistralai/models)可查已开放版本；[2026-10-06 Large 4 公告](https://mistral.ai/news/mistral-large-4/)承诺月底发布权重，核查时仍作为待跟进项 |
| GLM（智谱 / Z.ai） | GLM-5.3 与 GLM-5.3-Flash | [GLM-5.3](https://huggingface.co/zai-org/GLM-5.3)、[GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) 官方模型卡均提供权重；两个分支的骨干变化应分别分析 |

更新大纲时重新查看六个系列的官方发布和权重目录，同步本表与[路线](roadmap.md)。仅公布、只有 API 或只有报告的版本可以阅读，不标为已可本地复现；新版本先补齐前置知识，再安排实际课程。

## 千问主线

| 顺序 | 版本/分支 | 学习任务与来源 |
| --- | --- | --- |
| Q01 | Qwen / Qwen1.5 | 从早期 Decoder 建立基线；[Qwen 官方代码](https://github.com/QwenLM/Qwen)。Qwen1.5 检查点开课时选定 |
| Q02 | Qwen2 | 对照 Dense/MoE、注意力和前馈配置；[技术报告](https://arxiv.org/abs/2407.10671) |
| Q03 | Qwen2.5 | 区分结构、训练和上下文能力的变化；[技术报告](https://arxiv.org/abs/2412.15115) |
| Q04 | Qwen3 | 对照 Dense/MoE 实现及路由；[技术报告](https://arxiv.org/abs/2505.09388) |
| Q05 | Qwen3-Next | Gated DeltaNet 与全注意力混合、稀疏专家、MTP；[官方博客](https://qwen.ai/blog?id=qwen3-next) |
| Q06 | Qwen3.5 → Qwen3.6 | 比较混合架构与多模态分支，区分推理相关的实际改变；[官方系列发布记录](https://github.com/QwenLM/Qwen3.8) |
| Q07 | Qwen3.8 | 分别选定 27B 与 2.4T-A95B 的配置，对比规模、专家、状态和部署代价；[官方系列仓库及权重入口](https://github.com/QwenLM/Qwen3.8) |
| Q08 | Qwen3.8-Flash-Next | GDN+QSA、门控残差、N-gram embedding 的算子与状态需求；[官方资料](https://github.com/QwenLM/Qwen3.8-Flash-Next) |

系列版本不是单线继承关系，Qwen3.8 与 Flash-Next 单独比较。仓库重定向不代表旧模型的结构被改写，旧课应保留当时的源码 revision。

## DeepSeek 主线

| 顺序 | 版本/分支 | 学习任务与来源 |
| --- | --- | --- |
| DS01 | DeepSeek LLM | 建立早期 Dense 参照；[官方代码](https://github.com/deepseek-ai/DeepSeek-LLM) |
| DS02 | DeepSeekMoE / V2 | 专家分工、MLA 与缓存/矩阵计算；[V2 官方实现](https://github.com/deepseek-ai/DeepSeek-V2) |
| DS03 | V3 | MoE、MLA、MTP 与推理部署；[技术报告](https://arxiv.org/abs/2412.19437) |
| DS04 | R1 / Distill 分支 | 区分后训练策略和骨干，蒸馏模型按实际 Qwen/Llama 骨干分析；[官方说明](https://github.com/deepseek-ai/DeepSeek-R1) |
| DS05 | V3.2 | 稀疏索引与 Attention 路径，区别实验版与正式版；[正式模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V3.2) |
| DS06 | V4 系列 | CSA、HCA、SWA、mHC、MTP，以及 DSpark 草稿与调度；[V4-Flash 模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash)、[DSpark 官方实现](https://github.com/deepseek-ai/DeepSpec) |
| DS07 | V4.1-Flash | 因果 Encoder–Decoder、CSA2 跨层缓存/索引复用、SWA 状态重建、Engram 与 DSpark 投机解码；[官方模型卡和报告](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)。此处的因果编码器不能直接套用原始 Transformer 的双向编码器解释 |

先读模型报告与最小实现，再研究推理引擎和硬件 kernel。分别记录模型结构、引擎策略和硬件实现，避免混淆。

## Kimi 主线

先认识月之暗面的 Kimi 模型，再用已经学过的 MoE、MLA 等机制拆解具体版本；线性注意力分支单独比较。

| 顺序 | 版本/分支 | 学习任务与来源 |
| --- | --- | --- |
| KI01 | Kimi-K2 Base / Instruct | 从 MoE、MLA、专家路由和缓存建立 Kimi 基线，区分基础模型与后训练版本；[官方仓库](https://github.com/MoonshotAI/Kimi-K2) |
| KI02 | Kimi-K2 Thinking | 对比推理模式、工具调用模板和 INT4 量化；不能把更长的思考输出等同于骨干结构改变；[官方模型卡](https://huggingface.co/moonshotai/Kimi-K2-Thinking) |
| KI03 | Kimi Linear | 学习 KDA（Kimi Delta Attention）、KDA/MLA 混合、递归状态与分块执行；[官方报告与实现入口](https://github.com/MoonshotAI/Kimi-Linear)。对照 Gated DeltaNet，不当作相同算法 |
| KI04 | Kimi-K2.5 → K2.6 / K2.7-Code | 从[K2.5 模型卡](https://huggingface.co/moonshotai/Kimi-K2.5)认识视觉入口，再通过[官方版本目录](https://huggingface.co/moonshotai/models)逐项核对后续分支的配置、模板和推理差异 |
| KI05 | Kimi-K3 | 对比 KDA + Gated MLA、Attention Residuals、LatentMoE 与量化的算子和状态需求；[官方模型卡](https://huggingface.co/moonshotai/Kimi-K3) |

先做小形状的算子/模块参考实现，再按硬件条件选择整模型实践规模。Kimi-VL、Kimi-Audio 等分支留到视觉/音频阶段按差异选学。

## Llama 主线

Meta 的 Llama 用作基础模型参考，优先从较早版本练习完整推理链，再研究新分支。

| 顺序 | 版本/分支 | 学习任务与来源 |
| --- | --- | --- |
| L01 | LLaMA | 对照已学模块拆解 Decoder、位置处理、归一化和前馈层；[原始报告](https://arxiv.org/abs/2302.13971) |
| L02 | Llama 2 | 比较不同规模的头配置、缓存和上下文，区分预训练模型与 Chat 版本；[报告](https://arxiv.org/abs/2307.09288) |
| L03 | Llama 3 / 3.1 / 3.2 / 3.3 | 从[Llama 3 推理实现](https://github.com/meta-llama/llama3)入手，再按[官方版本表](https://github.com/meta-llama/llama-models)核对词表、配置及文本/视觉分支，避免把各后缀当成同一骨干 |
| L04 | Llama 4 Scout / Maverick | 学习 MoE 与视觉早期融合，对照两个版本的专家和状态配置；[官方模型卡](https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md) |

## Mistral/Mixtral 主线

两者均来自 Mistral AI。先借较早模型理解窗口注意力和专家路由，再比较当前不同规模的分支。

| 顺序 | 版本/分支 | 学习任务与来源 |
| --- | --- | --- |
| M01 | Mistral 7B v0.1 | GQA、滑动窗口、掩码和缓存保留；[原始报告](https://arxiv.org/abs/2310.06825)。具体窗口机制以版本配置为准，不推广到所有 Mistral 模型 |
| M02 | Mixtral 8x7B | 每层为每个 token 选择两个专家，追踪路由、分发和结果合并；[原始报告](https://arxiv.org/abs/2401.04088) |
| M03 | Mistral Large 3 / Ministral 3 | 比较大型稀疏模型与小型 Dense 模型的实现、内存和部署代价；[官方发布](https://mistral.ai/news/mistral-3/) |
| M04 | Mistral Small 4 / Medium 3.5 | 分别核对骨干、视觉入口、推理模式和量化部署；[Small 4](https://huggingface.co/mistralai/Mistral-Small-4-119B-2603)、[Medium 3.5](https://huggingface.co/mistralai/Mistral-Medium-3.5-128B) 模型卡 |
| 跟进 | Mistral Large 4 | 2026-10-06 已公布，官方称月底开放权重；先读[公告](https://mistral.ai/news/mistral-large-4/)，待权重及配置发布后确定结构课和复现实验 |

Large、Small、Medium 是不同分支，不能按名称中的数字推断发布时间、参数规模或继承关系。

## GLM 主线

GLM 来自智谱 / Z.ai，先沿 ChatGLM 与 GLM-4 建立版本比较方法，再学习新的稀疏和混合机制。

| 顺序 | 版本/分支 | 学习任务与来源 |
| --- | --- | --- |
| G01 | ChatGLM 系列 → GLM-4 | 比较词表、聊天模板、位置、注意力和缓存；[ChatGLM3](https://github.com/zai-org/ChatGLM3)、[GLM-4](https://github.com/zai-org/GLM-4) 官方实现 |
| G02 | GLM-4.5 / 4.6 / 4.7 | 按实际模型配置比较专家路由、思考模式和运行入口；[官方系列仓库](https://github.com/zai-org/GLM-4.5) |
| G03 | GLM-5 / 5.1 / 5.2 | 学习稀疏注意力索引、IndexShare、MTP 中的 KVShare 与长上下文服务；[5.2 官方说明](https://z.ai/blog/glm-5.2)回溯和比较前代，区分模型机制与引擎优化 |
| G04 | GLM-5.3 | 官方说明与 5.2 共用基础模型，以后训练与推理配置差异为重点，不臆造新骨干；[模型卡](https://huggingface.co/zai-org/GLM-5.3) |
| G05 | GLM-5.3-Flash | 单列新骨干：稀疏/线性混合注意力、mHC 和原生多模态；[模型卡](https://huggingface.co/zai-org/GLM-5.3-Flash)，不当作 5.3 的简单缩小版 |

## 每个模型的比较表

1. **身份**：模型 ID、用途、许可证、权重和代码版本。
2. **结构**：层序、注意力/状态机制、归一化、位置、FFN/MoE、输出头及视觉/音频模块。
3. **形状**：batch、序列长、隐藏维、Q/KV 头数、head dim、专家数，以及 dtype/layout。
4. **状态**：区分权重和 KV/递归/卷积状态，说明追加、复用、回滚与释放。
5. **执行**：分别画 Prefill、Decode、Draft/Verify 路径，列出可复用算子与缺口。
6. **代价与验证**：计算、存储、搬运、通信、精度风险和最小实验。

Gemma 等模型家族暂列补充候选；Mamba/SSM 的机制已纳入[推理技术学习目录](inference-techniques.md)，不要求为每种机制精读一整套模型家族。文本基础完成后扩展视觉和音频的编码器、连接层、预处理与后处理。理解结构后仍需分别完成 CPU 对齐、NPU 算子验证、整模型正确性和性能测量，不能用阅读完某系列代替交付验收。
