# 推理技术学习目录

资料核查日期：2026-10-13。下列技术均纳入学习范围，覆盖常用方法及六个模型系列的新机制；随公开资料和实践结果继续补充。这里是专题目录，近期课程仍按[接下来 12 课](../lessons/README.md#近期课程计划)推进。O 编号对应[路线](roadmap.md)中的专题，不表示讲义已生成或已经掌握。

每项按“解决的问题 → 张量与状态 → CPU 参考 → NPU 实现 → 整模型测量”展开；遇到前置知识缺口就拆小课。每个模型版本同时对照[演进表](model-evolution.md)，重复机制做差异比较，新机制单独讲解。

## 注意力、位置与状态：O01–O03

| 技术 | 学习重点与实践目标 | 核对入口 |
| --- | --- | --- |
| MHA / MQA / GQA | 比较 Q/KV 头数、头映射、缓存大小和计算布局；手算并对齐不同头配置 | [GQA 论文](https://arxiv.org/abs/2305.13245) |
| MLA | 拆解低秩投影、缓存压缩、权重吸收与不同执行路径，检查 Prefill/Decode 等价性 | [DeepSeek-V2](https://github.com/deepseek-ai/DeepSeek-V2) |
| SWA（Sliding Window Attention） | 实现滑动窗口掩码、位置处理与环形缓存；区分窗口边界和全局注意力 | [Mistral 7B v0.1](https://arxiv.org/abs/2310.06825) |
| DSA（DeepSeek Sparse Attention） | 索引器、TopK 选择、稀疏 gather 与 Attention；测量选取开销 | [DeepSeek-V3.2](https://huggingface.co/deepseek-ai/DeepSeek-V3.2) |
| CSA（Compressed Sparse Attention） | 先沿序列压缩 KV，再做稀疏选择；检查压缩块边界与状态更新 | [DeepSeek-V4](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash) |
| HCA（Heavily Compressed Attention） | 更高压缩率下对压缩状态做注意力；与 CSA、局部窗口比较信息保留和开销 | [V4 官方技术说明](https://fe-static.deepseek.com/chat/transparency/deepseek-V4-model-card-EN.pdf) |
| CSA2 / Hierarchical Sparse Indexer | Full、Reindex、Reuse 模式，跨层 KV/索引复用与分层候选集；验证共享范围和依赖 | [DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) |
| QSA（Qwen Sparse Attention） | 压缩索引器、微块选择，与 Gated DeltaNet 混合后的状态和算子布局 | [Qwen3.8-Flash-Next](https://github.com/QwenLM/Qwen3.8-Flash-Next) |
| IndexShare / KVShare | 分别解释索引复用与缓存复用；检查 GLM-5.2 骨干及 MTP 路径的共享条件 | [GLM-5.2](https://z.ai/blog/glm-5.2) |
| RoPE / RoPE Scaling / YaRN | 位置旋转、上下文扩展、缓存位置一致性；验证长上下文精度，避免只改配置就认定支持更长输入 | [YaRN](https://arxiv.org/abs/2309.00071) |
| Linear Attention / DeltaNet / Gated DeltaNet | 对照并行分块与递归更新，明确状态形状、衰减、数值稳定和分块边界 | [Qwen3-Next](https://qwen.ai/blog?id=qwen3-next)、[Kimi Linear](https://github.com/MoonshotAI/Kimi-Linear) |
| KDA（Kimi Delta Attention） | 细粒度门控与递归状态，比较 KDA/MLA 混合层；验证分块执行和逐 token 执行 | [Kimi Linear](https://github.com/MoonshotAI/Kimi-Linear) |
| Mamba / Mamba-2 / SSM 混合结构 | 状态空间模型、卷积状态、scan 与递归执行；与线性注意力分别比较 | [Mamba 官方实现](https://github.com/state-spaces/mamba)、[Mamba-2 论文](https://arxiv.org/abs/2405.21060) |

完整注意力、窗口、稀疏、压缩和递归状态分别建参考。FlashAttention 属于执行优化，不能代替上述模型计算语义；压缩/稀疏机制也不能未经验证就加到任意已有权重上。

## 投机解码与多 token 生成：O05

| 技术 | 学习重点与实践目标 | 核对入口 |
| --- | --- | --- |
| Speculative Decoding / Rejection Sampling | 草稿、验证、接受、拒绝修正和额外 token；分别证明贪心一致性与采样分布正确性 | [原始论文](https://arxiv.org/abs/2211.17192) |
| MTP（Multi-Token Prediction） | 区分训练目标与推理时的草稿模块，检查参数/缓存共享和递归调用 | [DeepSeek-V3](https://arxiv.org/abs/2412.19437) |
| EAGLE / EAGLE-2 / EAGLE-3 | 特征条件、草稿树、动态候选和目标验证；比较草稿质量与额外开销 | [官方代码与论文入口](https://github.com/SafeAILab/EAGLE) |
| Medusa / Self-Speculative Decoding / LayerSkip | 多解码头、模型自身作为草稿与提前退出；核对训练条件、验证规则及输出保证的区别 | [Medusa](https://arxiv.org/abs/2401.10774)、[LayerSkip](https://arxiv.org/abs/2404.16710) |
| DFlash | 轻量块扩散草稿的并行预测、目标隐藏特征注入、块长与验证路径 | [原始论文](https://arxiv.org/abs/2602.06036)、[官方代码](https://github.com/z-lab/dflash) |
| DFlash 2 | 对比 DFlash：相邻候选的轻量路径选择、块内局部动态卷积；区分并行打分和后续路径选择 | [作者发布与模型入口](https://inco.ai/blog/dflash2/) |
| DSpark | 并行骨干与轻量顺序模块组合；根据置信度和负载调整验证长度，统计浪费的验证工作 | [原始论文](https://arxiv.org/abs/2607.05147)、[DeepSpec](https://github.com/deepseek-ai/DeepSpec) |
| 动态草稿长度 / 树验证 / 状态回滚 | 比较固定与自适应长度；拒绝后恢复 KV、压缩块、递归状态及位置，覆盖 EOS、变长、多请求 | [DeepSpec](https://github.com/deepseek-ai/DeepSpec)、[EAGLE](https://github.com/SafeAILab/EAGLE) |

DFlash 2 的块内卷积不应被当作跨生成轮次保存的 SSM 状态。实现投机时不能只检查接受率：还需计算草稿、验证、修正、状态处理和调度的总耗时。原论文的输出保证依赖具体接受/修正规则，不能用普通 TopK 截断冒充精确采样。

## MoE 与专家执行：O04

| 技术 | 学习重点与实践目标 | 核对入口 |
| --- | --- | --- |
| Sparse MoE / TopK Routing / Shared Experts | 路由权重、共享与路由专家、归一化、token 分发和输出合并；区分总参数与每 token 激活参数 | [Mixtral](https://arxiv.org/abs/2401.04088)、[DeepSeek-V3](https://arxiv.org/abs/2412.19437) |
| Grouped GEMM / 融合 MoE | 按专家组织变长 token 批次，融合排列、量化和矩阵计算，测量负载不均与尾块 | [DeepGEMM](https://github.com/deepseek-ai/DeepGEMM) |
| 专家负载均衡 / 冗余专家 / EP | 区分训练的路由均衡与推理调度；检查热点、分发/合并通信和内存代价 | [DeepSeek-V3](https://arxiv.org/abs/2412.19437)、[DeepEP](https://github.com/deepseek-ai/DeepEP) |
| LatentMoE | 拆解潜空间专家输入输出，与传统专家维度和投影成本比较 | [Kimi-K3](https://huggingface.co/moonshotai/Kimi-K3) |

## 量化、低精度与压缩：O07

| 技术 | 学习重点与实践目标 | 核对入口 |
| --- | --- | --- |
| PTQ / QAT；W8A8 / W4A16 | 训练后量化与量化感知训练；权重/激活量化、尺度、零点、分组粒度及校准 | [SmoothQuant](https://arxiv.org/abs/2211.10438)、[Kimi-K2 Thinking](https://huggingface.co/moonshotai/Kimi-K2-Thinking) |
| GPTQ | 低比特权重量化与重建误差，比较不同分组和校准输入 | [论文](https://arxiv.org/abs/2210.17323) |
| AWQ | 激活统计辅助的权重量化；检查通道缩放、权重布局和反量化融合 | [论文](https://arxiv.org/abs/2306.00978) |
| SmoothQuant | 激活异常值与等价缩放，比较 W8A8 的精度和算子代价 | [论文](https://arxiv.org/abs/2211.10438) |
| FP8 / FP4 / MXFP4 / NVFP4 | 格式、分块缩放、累加精度、打包和转换；核对硬件原生支持，不把相同位宽视为相同格式 | [Kimi-K3](https://huggingface.co/moonshotai/Kimi-K3)、[Mistral 官方量化检查点](https://huggingface.co/mistralai/models) |
| KV Cache 量化 / KIVI | 分别分析 K/V 分布、量化粒度与反量化路径，检查长序列误差积累 | [KIVI](https://arxiv.org/abs/2402.02750)、[V4.1 FP4 缓存](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) |
| TurboQuant / PolarQuant / QJL | 向量量化、旋转/变换和注意力分数估计；区分公开基准结果、数值近似和端到端质量 | [Google Research](https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/) |
| 结构化/非结构化剪枝 / SparseGPT | 稀疏模式、精度恢复和稀疏算子；检验减少参数能否转化为硬件加速 | [SparseGPT](https://arxiv.org/abs/2301.00774) |
| 知识蒸馏 / MiniLLM | 教师与学生、训练目标和实际骨干；对学生重新验收质量和推理代价 | [MiniLLM](https://arxiv.org/abs/2306.08543) |

## 缓存、调度与服务：O06、O08、O09

| 技术 | 学习重点与实践目标 | 核对入口 |
| --- | --- | --- |
| FlashAttention 1 / 2 / 3 / 4 | 在线 softmax、分块与计算/搬运调度的演进；从数学等价参考推导目标 NPU 实现 | [官方代码与各代论文入口](https://github.com/Dao-AILab/flash-attention) |
| PagedAttention / Paged KV Cache | 页表、块分配、非连续访问与碎片；区分内存管理与注意力计算公式 | [论文](https://arxiv.org/abs/2309.06180) |
| Prefix Caching / Radix Cache | 前缀匹配、缓存键、共享和引用管理；验证命中条件及不同请求的状态隔离 | [vLLM](https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/)、[SGLang](https://github.com/sgl-project/sglang) |
| Continuous Batching / In-flight Batching | token 级请求加入/退出、batch 重组、吞吐与尾延迟的取舍 | [vLLM 调优](https://docs.vllm.ai/en/latest/configuration/optimization/) |
| Chunked Prefill / Prefill–Decode 混合调度 | 提示词分块、预算分配、首次输出延迟与生成间隔，覆盖块边界位置 | [vLLM 调优](https://docs.vllm.ai/en/latest/configuration/optimization/) |
| PD Disaggregation | 分离 Prefill/Decode、转移缓存与元数据；评估网络、队列和部署规模带来的代价 | [SGLang 官方文档](https://docs.sglang.io/docs/advanced_features/pd_disaggregation) |
| 分层缓存 / Offload / 重计算 / Eviction | 设备、主存和磁盘之间搬运、预取和回收；区分完整重算与会改变结果的近似淘汰 | [SGLang](https://github.com/sgl-project/sglang)、[vLLM 调优](https://docs.vllm.ai/en/latest/configuration/optimization/) |
| H2O / SnapKV | 重要 token 选择与 KV 保留/压缩；比较内存节省、选择开销和长上下文质量 | [H2O](https://arxiv.org/abs/2306.14048)、[SnapKV](https://arxiv.org/abs/2404.14469) |
| SWA Bounded Replay | 只重放必要窗口以恢复局部状态，检查依赖和重建成本 | [DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) |
| LoRA 合并 / Multi-LoRA Serving | 低秩分支合并与动态适配器、批处理和分页内存；核对每个请求使用的权重 | [S-LoRA](https://arxiv.org/abs/2311.03285) |

## 并行与通信：O10

| 技术 | 学习重点与实践目标 | 核对入口 |
| --- | --- | --- |
| TP（Tensor Parallelism） | 行/列切分、AllReduce、AllGather、ReduceScatter；核对分片权重与输出 | [Megatron-LM](https://github.com/NVIDIA/Megatron-LM) |
| PP（Pipeline Parallelism） | 按层切分、流水气泡与跨设备状态传递，比较低并发延迟和高并发吞吐 | [Megatron-LM](https://github.com/NVIDIA/Megatron-LM) |
| DP（Data Parallelism） | 请求副本、负载均衡与缓存局部性；区分推理副本和训练梯度同步 | [vLLM](https://github.com/vllm-project/vllm) |
| SP / CP（Sequence / Context Parallelism） | 沿序列或上下文切分，跟踪注意力依赖和数据交换；具体含义以框架为准 | [Megatron-LM](https://github.com/NVIDIA/Megatron-LM) |
| EP / All-to-All / 通信计算重叠 | 专家分片、分发与合并、流水/异步通信；根据消息大小和设备拓扑测量 | [DeepEP](https://github.com/deepseek-ai/DeepEP) |

Megatron 的训练实现用于理解分片与通信原理，实际推理还需验证请求调度和缓存生命周期。GPU 库作为参考，通信接口与 kernel 在选定 NPU 上重新适配。

## 算子、编译器与运行时：O11

| 技术 | 学习重点与实践目标 |
| --- | --- |
| GEMM / GEMV / Batch GEMM / Split-K | 对照长序列与单 token 形状，分析矩阵单元利用率、尾块和归约代价 |
| Kernel Fusion | QKV 投影、残差+归一化、门控 FFN、RoPE+缓存写入及采样融合；检查访存节省、寄存器和片上内存压力 |
| Tiling / Layout / Packing | 分块、对齐、转置、权重预打包和布局传播；减少重复转换并覆盖非整齐形状 |
| Double Buffer / Pipeline / 异步执行 | 双缓冲、搬运计算重叠、多核分工和同步；检查越界、竞争及重复运行稳定性 |
| 静态图 / 动态形状 / Shape Bucketing / 图重放 | 识别编译、调度和 kernel 启动成本；比较预编译、形状分桶和运行时重放 |
| 内存池 / Buffer 复用 / 零拷贝条件 | 根据生命周期复用内存，核对别名和状态所有权，测量峰值内存与复制成本 |
| TopK / TopP / Softmax / LM Head 优化 | 分数计算、归约和 token 选择；核对完整词表与候选词表映射、随机采样及精度 |

以[DeepGEMM](https://github.com/deepseek-ai/DeepGEMM)、[FlashAttention](https://github.com/Dao-AILab/flash-attention)作为实现案例，结合[硬件阶段与实践里程碑](practice-milestones.md)学习。CUDA Graph、CUDA/Triton 等具体实现只作参考；NPU 对应接口与支持情况在平台确定后核查。

## 新结构与多模态推理：O12、O13

| 技术 | 学习重点与实践目标 | 核对入口 |
| --- | --- | --- |
| mHC / Single-Pass mHC / Gated Residual / Attention Residuals | 对照多路残差、门控和跨层聚合；分别实现，不将名称相近的机制混为同一算法 | [V4](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash)、[V4.1](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)、[Qwen Flash-Next](https://github.com/QwenLM/Qwen3.8-Flash-Next)、[Kimi-K3](https://huggingface.co/moonshotai/Kimi-K3) |
| Engram / N-gram Embedding | 条件查表、稀疏访问、权重与运行时状态、设备外存储及搬运；与普通 Embedding 区分 | [V4.1](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)、[Qwen Flash-Next](https://github.com/QwenLM/Qwen3.8-Flash-Next) |
| Causal Encoder–Decoder（CED） | 因果编码器、解码器与跨层缓存生成；分别追踪 Prefill/Decode 的实际路径 | [DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) |
| 视觉/音频编码器、连接层与多模态 token | 图像 patch、分辨率/帧数、音频分块、投影与位置；核对预处理、计算图和状态，优化复用与流式执行 | [Kimi 官方模型目录](https://huggingface.co/moonshotai/models)、[Llama 4](https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md) |

## 精度与性能验收：O14

- **逐算子、逐层与 logits 对齐**：独立参考、误差指标、异常输入、多请求、变长与状态恢复；采样比较分布或使用适用的确定性设置。
- **Profiler / Roofline / 带宽与计算瓶颈**：记录实际搬运量、计算量、通信和主机开销，定位瓶颈后选择优化。
- **TTFT / TPOT / ITL / 吞吐 / P50、P95、P99 / 峰值内存**：明确端到端计时边界；固定模型、精度、输入输出长度、并发、采样、预热和同步。
- **A/B、消融与回归**：优化分别开关，测量组合效果；量化/近似方法同时报告质量，投机方法同时记录接受长度、草稿/验证时间和回滚成本。

完成标准见[实践里程碑](practice-milestones.md)。官方实验、公开实现、本人 CPU 复现、目标 NPU 正确性与 NPU 端到端收益分别记录。目前本工程尚未完成这些专题的设备验证；公开实现和“最新”均不保证特定平台、形状或并发下更快。
