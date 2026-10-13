# 从 Transformer 到 NPU 端到端推理

更新时间：2026-10-13。先学通用原理，之后再选 NPU 平台。默认一天一课，吃透并归档后下一课留到次日；仅用户主动要求继续或跳过换课时提前推进。编号表示学习顺序，不对应固定日期。跳过的知识仍归档。

## 主线与学习方法

**模型结构与数据流 → Prefill/Decode 与状态 → 历代模型差异 → 优化机制 → NPU 算子 → 整模型运行 → 端到端优化。**

每个主题回答五个问题：解决什么问题？公式与张量形状是什么？读写哪些数据？如何实现并验证？性能受什么限制？

T001 先建立完整流程，后续逐模块深入。每个模块按“直观作用 → 小例子与手算 → 公式和形状 → 最小参考代码 → 自测”展开，进入 NPU 阶段后再做对应的设备实现与优化。较大主题可拆成连续多天的小课，每天仍只学习一个核心问题；当天追问属于当前课的补讲，不代表已经完成后面的专题。

讲义配合结构图、流程图和数据示意图：结构课看模块连接，推理课看 token 与缓存随步骤变化，算子课看形状、内存和计算流向。每图回答一个具体问题，附读图说明与简化范围；采用自绘图或来源、使用条件明确的外部图，不只堆放文字和公式。

讲义统一按课号保存到 `lessons/<课号>.md`；学习日期、实际回答、状态变化与暂停位置写入 `study-log/YYYY/MM/YYYY-MM-DD.md`。同一课可以跨天，同一天也可以按明确要求学多课；日期不会自动推进课号。

模型演进与专题交叉学习：遇到新机制先补专题，再返回模型。例如学习 Qwen3-Next 前补线性注意力，学习 DeepSeek-V2 前补 MoE 与 MLA，学习 Kimi Linear 前补门控递归状态。训练知识围绕结构、权重和推理行为按需补充。

[近期课程计划](../lessons/README.md#近期课程计划)先列接下来 12 个主题，并滚动保留至少 10 个待学主题。复杂内容可拆分为子课，按反馈更新目录，不将长远路线固定为日历。首次介绍模型时先解释开发团队、用途与选择理由，再讲结构差异。

## 第一阶段：Transformer 与推理基础

| 编号 | 主题 | 学习产出 |
| --- | --- | --- |
| T001 | Transformer 全局结构：原始 Encoder–Decoder 与现代 Decoder-only | 画出输入到输出的计算流程 |
| T002 | Token、Tokenizer、词表与 Embedding | 分步学习文本切分、BPE 等分词方法、特殊 token、ID 与文本转换，以及 Embedding 查表、权重和输出形状 |
| T003 | 张量形状、矩阵乘法与广播 | 写出模型中主要张量的维度 |
| T004 | Self-Attention 与 Q/K/V | 从输入投影到 Q/K/V，手算注意力分数、缩放和对 V 的加权汇集，追踪各步形状 |
| T005 | 因果掩码与 softmax | 说明为什么不能看到未来位置 |
| T006 | 多头注意力与输出投影 | 区分切分头与复制数据 |
| T007 | 位置编码与 RoPE | 解释位置如何影响注意力 |
| T008 | FFN、激活与门控 | 拆解前馈计算 |
| T009 | 残差、LayerNorm 与 RMSNorm | 手算均值、方差、均方根和仿射变换，解释稳定项、归约维度、Block 内与最终归一化的位置 |
| T010 | LM Head 与下一个 token 的选择 | 实现隐藏向量到词表的投影，理解权重共享，区分 logits、softmax、温度、贪心与 Top-k/Top-p 采样 |
| I001 | Prefill | 画出输入长度为 S 时的计算 |
| I002 | Decode | 逐步追踪新 token 的输入、各层计算、缓存更新、输出选择与停止条件，并与 Prefill 对照 |
| I003 | KV Cache：缓存什么，为什么能复用 | 对照有缓存与无缓存的结果 |
| I004 | KV Cache 容量、位置与生命周期 | 估算内存，验证追加和清空 |
| I005 | TTFT、逐 token 延迟与吞吐 | 明确测量口径 |
| I006 | 计算量、访存量与瓶颈 | 解释形状和并发为何影响性能 |

术语分别安排：Decoder Block 是模型中的计算模块，在 T004–T009 拆解后通过阶段实践组装；Decode 是逐步生成阶段，在 I002 专讲；Tokenizer 的 decode 是把 token ID 转回文本，在 T002 讲解。

T002 分课顺序：T002-1 Token、token ID 与词表 → T002-2 Tokenizer 的处理流程与 BPE 入门 → T002-3 特殊 token、模型配套与文本解码 → T002-4 Embedding 查表、权重与形状。每节独立反馈和归档，T002 的整体状态在各子课完成后汇总；内容较多时继续拆分，不为赶进度压缩成一天。

阶段实践：用小张量实现 Decoder Block 和生成循环，逐层对齐参考结果，验证 KV Cache。见[实践里程碑](practice-milestones.md)。原 B001“什么是推理”等内容保留为按需补课，不要求先完成独立的泛基础阶段。

## 第二阶段：开源模型从旧到新

| 主线 | 顺序 | 比较重点 |
| --- | --- | --- |
| 千问 | Qwen / Qwen1.5 → Qwen2 → Qwen2.5 → Qwen3 → Qwen3-Next → Qwen3.5 / 3.6 → Qwen3.8；另学 3.8-Flash-Next | Dense/MoE、混合注意力、稀疏索引、门控残差与 N-gram embedding |
| DeepSeek | DeepSeek LLM → DeepSeekMoE / V2 → V3 → R1 分支辨析 → V3.2 → V4 → V4.1-Flash | MLA、MTP、压缩/稀疏注意力、因果 Encoder–Decoder、跨层缓存与投机解码 |
| Kimi | K2 → K2 Thinking → K2.5 / K2.6 / K2.7-Code → K3；穿插 Kimi Linear 分支 | MoE、MLA、量化、KDA 递归状态、多模态与残差结构 |
| Llama | LLaMA → Llama 2 → Llama 3 / 3.1 / 3.2 / 3.3 → Llama 4 Scout / Maverick | 从基础 Decoder 到不同头配置、MoE 和视觉融合 |
| Mistral/Mixtral | Mistral 7B → Mixtral 8x7B → Large 3 / Ministral 3 → Small 4 / Medium 3.5；Large 4 待开放权重 | 滑动窗口、专家选择、不同规模与部署路径；各分支分别比较 |
| GLM | ChatGLM 系列 → GLM-4 → GLM-4.5 / 4.6 / 4.7 → GLM-5 / 5.1 / 5.2 → GLM-5.3 与 5.3-Flash | 模型配套、稀疏索引复用、缓存、MTP 与混合注意力 |
| 模型家族补充候选 | Gemma 等其他模型家族 | 整个家族是否精读按差异选择；Mamba/SSM 机制与多模态推理已纳入后续专题 |

以上最新范围已于 2026-10-13 核对，官方来源与开放状态见[模型演进表](model-evolution.md)。Mistral Large 4 的官方公告承诺本月底发布权重，当前仅作跟进项。箭头表示学习顺序，不表示所有分支直接继承；系列先后可按前置知识调整，建议用较早的 Llama 建立完整推理基线，再穿插其他系列。

每个代表版本产出“相对前代的差异表”和最小实验；同构更新侧重差异，避免重复精读。新发布进入大纲前检查官方公告、模型卡及权重，记录核查日期，不能只填“后续版本”。模型名称、规模与后缀不能替代配置和代码检查。

## 第三阶段：随模型穿插的优化专题

| 编号 | 专题 | 实现关注点 |
| --- | --- | --- |
| O01 | MHA → MQA → GQA → MLA | 头映射、投影方式与实际缓存布局 |
| O02 | SWA、DSA、CSA、HCA、CSA2、QSA、IndexShare；RoPE Scaling / YaRN | 窗口、稀疏索引、压缩、跨层复用和位置 |
| O03 | Linear Attention、DeltaNet、Gated DeltaNet、KDA、Mamba / Mamba-2 | 递归/卷积状态、分块并行、数值稳定与恢复 |
| O04 | Sparse MoE、Shared Experts、Grouped GEMM、LatentMoE | 路由、TopK、分发/合并、负载与融合 |
| O05 | Speculative Decoding、MTP、EAGLE 1/2/3、Medusa、LayerSkip、DFlash、DFlash 2、DSpark | Draft/Verify、拒绝采样、动态长度、树验证和状态回滚 |
| O06 | FlashAttention 1/2/3/4、PagedAttention | 在线 softmax、分块、计算搬运调度与分页管理 |
| O07 | PTQ/QAT、GPTQ、AWQ、SmoothQuant、FP8/FP4/MXFP4/NVFP4、KIVI、TurboQuant/PolarQuant/QJL、SparseGPT、蒸馏 | 量化、剪枝、校准、格式、反量化融合与质量 |
| O08 | Continuous Batching、Prefix/Radix Cache、Chunked Prefill、PD Disaggregation、Multi-LoRA | 请求调度、缓存/适配器匹配、状态隔离和尾延迟 |
| O09 | 分层缓存、Offload、预取、重计算、H2O、SnapKV、SWA Bounded Replay | 设备/主存/磁盘搬运、恢复条件与近似边界 |
| O10 | TP、PP、DP、SP/CP、EP、All-to-All、通信计算重叠 | 分片、集合通信、设备拓扑和推理状态 |
| O11 | GEMM/GEMV、Split-K、Kernel Fusion、Tiling、Layout、双缓冲、图重放、内存池 | 从热点算子到编译与运行时开销，覆盖动态形状 |
| O12 | mHC、Single-Pass mHC、Gated Residual、Attention Residuals、Engram、N-gram Embedding、CED | 残差流、条件查表、跨层缓存和新的执行路径 |
| O13 | 视觉/音频编码器、连接层、多模态 token 与流式处理 | 预处理、动态输入、位置、复用和状态 |
| O14 | 精度对齐、Profiler/Roofline、TTFT/TPOT/ITL、尾延迟、消融与回归 | 固定负载后衡量质量、内存、延迟与吞吐 |

区分改变模型计算语义、改变计算实现、改变缓存组织的技术；例如 FlashAttention 不等于线性注意力。核对入口：[FlashAttention](https://arxiv.org/abs/2205.14135)、[GQA](https://arxiv.org/abs/2305.13245)、[PagedAttention](https://arxiv.org/abs/2309.06180)。

以上均纳入学习范围，不仅学习列出的几个新名词。各项解释、前置关系、实践目标与官方来源集中维护在[推理技术目录](inference-techniques.md)。专题随模型穿插，可拆成多节小课；公开实验收益与本工程 NPU 实测分开记录。

## 第四阶段：NPU 编程的通用底座

顺序：H01 C++ 与张量内存 → H02 向量/矩阵单元和片上存储 → H03 布局、对齐、搬运 → H04 Tiling、尾块、多核分工 → H05 流水、双缓冲、同步 → H06 数值精度与归约 → H07 Profiling 与 Roofline → H08 图编译、动态形状与运行时。

先分析通用数据依赖和资源约束，再绑定芯片、SDK、指令和调优工具。GPU 实现和性能不能直接视为 NPU 结论。

## 第五阶段：从算子到整模型

顺序：K01 elementwise/归约 → K02 softmax/归一化/RoPE → K03 GEMM/FFN → K04 Prefill/Decode Attention → K05 缓存管理 → K06 MoE/递归状态/投机验证 → E01 算子注册与图集成 → E02 权重转换 → E03 自回归循环 → E04 服务与并行。

先做参考实现与正确基线，再优化。交付物包含输入约束、构建运行入口、测试、误差报告和性能证据。

## 第六阶段：端到端优化与陌生模型适配

按测量结果逐项验证：融合、布局、访存、权重预处理、缓存、调度、量化、投机解码、张量/流水线/专家并行、通信与计算重叠。确认收益体现在整模型，并解释质量、内存、吞吐与延迟的取舍。

最终选择一个此前未精读的公开模型，独立完成结构拆解、算子缺口分析、NPU 基线和优化报告。以可复现结果验收，不用阅读数量替代工程能力。
