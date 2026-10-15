# 讲义图示与正确性核查

配图用于解释具体问题。模型结构、数据流、生成循环和张量形状优先使用内嵌 Mermaid 图；图号在每份讲义内编号，不包含个人学习状态。

## 每次新增或修改图时

1. **明确范围**：标出适用模型或教学配置，区分完整实现和简化示意，说明省略的缓存、位置处理等细节。
2. **对照原始资料**：用原论文、官方文档或固定版本源码逐项核对模块顺序、箭头、分支、循环和状态变化。外部图片同样检查内容与版本，不能仅凭画面看起来合理就采用。
3. **验证数据**：涉及形状、索引或数值时手算或执行最小例子；区分位置数、特征数和候选数，确保图、公式、表格和文字一致。
4. **检查显示**：预览 Mermaid 图，检查文字、箭头和标签是否完整、拥挤或歧义。渲染成功不替代技术核对；没有实际执行的检查不写为通过。
5. **保存依据**：图旁给读图说明和来源；存在未核实的关键关系时，先补查，不把它作为确定知识发布。修图时同步检查相关正文和习题。

外部图先核对作者、原始页面及许可，满足公开使用条件后才嵌入并按要求署名。许可不明确时链接原文，另画独立的教学解释。自动任务优先返回内嵌图，不引用不存在的本地资产。

## 2026-10-12 内容核查

| 讲义与图号 | 核查依据与重点 | 简化边界 |
| --- | --- | --- |
| [B001](../lessons/B001.md) 图 1 | [PyTorch 优化教程](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)：计算预测、误差、参数更新；普通推理读取参数 | 带参考目标的训练示意，省略求导和优化器细节 |
| [T001](../lessons/T001.md) 图 1 | [原始 Transformer §3](https://arxiv.org/html/1706.03762v7#S3)及下述 Qwen2 代码：Encoder 输出被 Decoder 交叉注意力读取，Decoder-only 无独立 Encoder | 省略分词、嵌入及归一化 |
| T001 图 2 | [Transformers v4.45.2 Qwen2](https://github.com/huggingface/transformers/blob/v4.45.2/src/transformers/models/qwen2/modeling_qwen2.py)与[生成循环](https://github.com/huggingface/transformers/blob/v4.45.2/src/transformers/generation/utils.py)：Embedding、层堆叠、最终归一化、输出头、取最后位置分数、选 ID、追加、停止判断 | 普通逐 token 生成的逻辑流程；省略缓存、位置处理和流式输出，不能据此推断历史 token 都被重算 |
| T001 图 3 | 同版本 Qwen2 的最终归一化及线性输出头；核对 H→V 的维度变化 | B=1、S=3、H=4、V=6 为教学配置，展示计算所有位置输出头 |
| [T002-1](../lessons/T002-1.md) 图 1 | [Hugging Face Encoding](https://huggingface.co/learn/llm-course/en/chapter2/4#encoding)：先切分，再查 ID；例子按讲义词表核对 | 手工切分，无特殊 token；不冒充真实模型 tokenizer |
| T002-1 图 2 | 讲义原词表与交换后的词表，固定 ID=0 分别查得“我”和“你” | 只比较输出 ID 的文字映射，不假定输入词表变化后模型仍生成相同 ID |

技术来源在本次配图时重新核查。学习者的掌握情况仍以学习日志为准，配图不代表新课程或学习进度变化。

本次验证结果：

- 用独立 Python 小例子复算 token 查表、交换词表后的解释，以及 `[1,3,4] → [1,3,6] → [1,6] → 1 个 ID` 的形状与选择，结果一致；RMSNorm 手算沿用正文明确说明的忽略 ε 的简化。
- 六张图均使用 Mermaid CLI 11.17.0 / Mermaid 11.17.2 在 Chrome 中成功渲染，并逐张检查中文标签、箭头和布局。输出头图显式标明权重转置，生成图显式保留追加与停止判断。
- `git diff --check` 及本地文档链接检查通过。生成预览仅用于本地核查，讲义保留可维护的 Mermaid 源码，不添加阅读依赖。

## 2026-10-13：T002-2 流程与 BPE

| 图号 | 核查依据与重点 | 简化边界 |
| --- | --- | --- |
| [T002-2](../lessons/T002-2.md) 图 1 | [Tokenizers 官方流程](https://huggingface.co/docs/tokenizers/pipeline)：规范化 → 预切分 → 分词模型及 ID 映射 → 后处理；之后才进入神经网络的 Embedding | 配置决定各步骤是否执行；省略其他输出字段、特殊 token 细节，不把文本规范化混同于 RMSNorm |
| T002-2 图 2 | [BPE 官方课程](https://huggingface.co/learn/llm-course/en/chapter6/5)的固定规则应用，加上本课原创词表与计数 | 字符级、单片段、无特殊 token、无随机分词；规则 2 无匹配后应用规则 3，不重新按新输入频次学习 |

已用 Python 复算三轮加权计数，最高频对无并列；新课代码输出 `['ab', 'ac']` 和 `[3, 5]`。另用逐次选择最高优先级相邻对的独立实现核对：在字母表 `{a,b,c}`、长度 1–6 的全部 1092 个非空字符串上，结果与讲义代码一致；也核对了自测例。验证范围只覆盖本课简化规则，不作为真实 tokenizer 的兼容性或性能验证。

两张图均用 Mermaid CLI 11.17.0 / Mermaid 11.17.2 在 Chrome 中渲染，并逐张检查文字、箭头和规则编号。规范化与预切分另对照[官方说明](https://huggingface.co/learn/llm-course/en/chapter6/4)，算法依据复核 [Sennrich 等，2016，§3.2](https://aclanthology.org/P16-1162.pdf)。

## 2026-10-13：T002-3 特殊 token 与文本解码

| 图号 | 核查依据与重点 | 简化边界 |
| --- | --- | --- |
| [T002-3](../lessons/T002-3.md) 图 1 | [Tokenizers 后处理](https://huggingface.co/docs/tokenizers/pipeline#post-processing)与 [Tokenizer API](https://huggingface.co/docs/transformers/main/en/main_classes/tokenizer)：普通片段编码完成后，按预设模板添加边界；ID 数量对应输入张量的位置数 | 原创字符级 BPE、固定 V=9、BOS=6、EOS=7、PAD=8；仅演示完整单片段，不代表实际聊天模板，省略神经网络 |
| T002-3 图 2 | [文本解码流程](https://huggingface.co/docs/tokenizers/pipeline#decoding)与 API 的 `skip_special_tokens`：查回 token、按选项跳过特殊 token、按配套规则重建文字 | 本例用字符片段直接拼接，无字节还原或文本规范化；输入 ID 已存在，不运行 Transformer，不表示生成停止逻辑 |

已执行讲义中的 Python 代码，得到 `<bos>ababac<eos>` 与 `ababac`。独立按合并优先级复算正文及第 1 题的 BPE 编码，核对加入边界后的 ID、S、V，以及填充后的张量位置数和输入掩码；解码跳过 PAD 后文字一致。验证范围为本课教学配置，不作为真实模型运行证据。

两张图均使用 Mermaid CLI 11.17.0 / Mermaid 11.17.2 在 Chrome 中渲染，并逐张查看中文标签、数值、箭头与布局。正文另对照[聊天模板](https://huggingface.co/docs/transformers/main/en/chat_templating)和 [v4.45.2 生成配置](https://huggingface.co/docs/transformers/v4.45.2/en/main_classes/text_generation)，避免把文本解码与模型 Decode、停止判断混为一谈。

## 2026-10-13：T002-4 Embedding 查表与形状

| 图号 | 核查依据与重点 | 简化边界 |
| --- | --- | --- |
| [T002-4](../lessons/T002-4.md) 图 1 | [PyTorch 2.14 Embedding](https://docs.pytorch.org/docs/2.14/generated/torch.nn.Embedding.html) 的索引、权重和输出形状；[v4.45.2 Qwen2 源码](https://github.com/huggingface/transformers/blob/v4.45.2/src/transformers/models/qwen2/modeling_qwen2.py) 的 `embed_tokens` 构造与调用 | 手工 E 为 `[9,3]`，输入 `[1,4]`，输出 `[1,4,3]`；从 0 编号，无额外词表行、位置处理、量化或会改写权重的选项 |

已执行讲义的 Python 列表代码，逐行核对 Markdown 权重表与代码数据，输出与手算一致。另以 one-hot 乘权重表的独立计算核对全部九个 ID、顺序与重复取行；复算正文和自测的输入、权重、输出形状，以及每条序列补一个 PAD 后的变化。只验证本课查表，不验证后续模型层或训练；未安装或运行 PyTorch，也未加载真实模型。

图已用 Mermaid CLI 11.17.0 / Mermaid 11.17.2 在 Chrome 中渲染并查看，ID 与权重两条输入箭头含义清楚，中文标签、行号和输出形状完整。权重来源与表示边界另核对 [PyTorch 官方教程](https://docs.pytorch.org/tutorials/beginner/nlp/word_embeddings_tutorial.html)。

## 2026-10-15：T003 线性投影与偏置广播

| 图号 | 核查依据与重点 | 简化边界 |
| --- | --- | --- |
| [T003](../lessons/T003.md) 图 1 | [PyTorch 2.14 matmul](https://docs.pytorch.org/docs/2.14/generated/torch.matmul.html)、[广播规则](https://docs.pytorch.org/docs/2.14/notes/broadcasting.html)及 [Linear](https://docs.pytorch.org/docs/2.14/generated/torch.nn.Linear.html)：X 与 W 计算 Z，偏置按末轴对齐后加到每个输出位置 | 手工 B=1、S=2、H=3、D=2；W 按 `[H,D]` 展示，省略注意力、激活、位置处理与缓存 |

已执行讲义的 Python 列表代码，输出为 `[[[11,1],[13,0]]]`。另按权重列独立计算点积，复算自测数值及形状，并检查偏置广播的有效/无效情况。范围为本课教学配置；未加载真实模型或执行 NPU 验证。

图已用本地 Mermaid CLI 在 Chrome 中渲染并查看：X/W 两条输入、Z 到加法的连接、偏置广播箭头，以及 `[1,2,3] → [1,2,2]` 的形状均清晰完整。此核查补齐自动准备时未执行的图示预览，不改变正式自测题面。
