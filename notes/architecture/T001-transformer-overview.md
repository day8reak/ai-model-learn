# T001 — Transformer 全局结构

- 分类：模型结构
- 状态：已掌握（理论：整体流程与输出端基础）
- 首次学习：2026-10-10；巩固材料：2026-10-11；确认与归档：2026-10-12
- 前置知识：[B001 — 什么是大模型推理](../foundations/B001-what-is-inference.md)
- 确认依据：首次自测经补讲后三题通过，输出端巩固三题通过，学习者明确确认吃透。
- 实践状态：尚未完成 Decoder Block 的 CPU 参考实现、NPU 验证或性能优化。

## 核心流程与结构

Transformer 通过注意力和前馈计算逐层更新数字表示。在本课的 Decoder-only 文本生成基线中，一步生成经过：

```text
输入文字 → Tokenizer → token ID → Embedding → 多层 Decoder Block
         → 最终归一化 → LM Head → 候选分数 → 选择下一个 token
```

选出的 token 追加到序列，后续继续生成。一次普通生成步骤中，多层共同计算下一个 token，层数不等于生成数量。

| 结构 | 数据流 |
| --- | --- |
| Encoder–Decoder | Encoder 处理原文；Decoder 结合编码后的原文表示和已有译文，通过交叉注意力读取 Encoder 输出 |
| Decoder-only | 提示词与已生成内容通过同一组 Decoder 层；因果注意力只允许当前位置访问自身及之前的位置 |

是否存在独立 Encoder 由模型架构确定，不能在同一模型的一次普通推理中随意省略。[原始 Transformer §3](https://arxiv.org/html/1706.03762v7#S3)、[Qwen2 技术报告](https://arxiv.org/html/2407.10671v4#S2.SS2)

## 模块分工

| 模块 | 本课需要理解的作用 |
| --- | --- |
| Tokenizer | 将文本处理为 token ID 序列；token 不固定等于一个汉字 |
| Embedding | 根据 ID 取得对应的特征向量 |
| Self-Attention | 汇集允许访问的位置的信息 |
| FFN | 分别变换各位置的特征 |
| 残差连接 | 将原输入与变换结果相加 |
| 归一化 | 调整特征尺度，具体位置与类型由模型决定 |
| LM Head | 将隐藏特征映射为词表候选分数 |
| 选择策略 | 根据分数或概率确定下一个 token ID |

位置的信息也参与计算，具体机制留给位置编码专题。Decoder Block 是神经网络中的计算模块；Decode 是逐步生成阶段；Tokenizer 的 decode 是把 ID 转回文本，三者需区分。

## 张量形状与数据变化

记 B 为批大小、S 为已有 token 位置数、H 为隐藏维度、V 为词表候选数。以 B=1、S=3、H=4、V=6 为教学配置：

| 数据 | 一般形状 | 教学形状 |
| --- | --- | --- |
| token ID | `[B,S]` | `[1,3]` |
| Embedding、各 Block 边界及最终归一化的输出 | `[B,S,H]` | `[1,3,4]` |
| 计算所有位置的 LM Head 输出 | `[B,S,V]` | `[1,3,6]` |
| 最后位置的候选分数 | `[B,V]` | `[1,6]` |

Block 的输入、输出维度由结构设计为一致；其中的数值随计算更新，内部维度可以暂时变化。普通推理更新的是中间结果，通常不更新模型权重。

最后一维从 H 变为 V，表示特征被转换成词表分数，不能解释成生成了 V 个 token。普通逐步生成取最后一个位置的分数选择一个新 token；实现也可以只计算所需位置的输出头。

## 输出归一化、LM Head 与选择

本课以 Transformers v4.45.2 的 Qwen2 实现为例：所有 Decoder 层之后执行 RMSNorm，再调用无偏置的线性输出头。[固定版本源码](https://github.com/huggingface/transformers/blob/v4.45.2/src/transformers/models/qwen2/modeling_qwen2.py)

### RMSNorm：调整每个位置的特征尺度

对 H 维向量 x，计算：

$$
r=\sqrt{\frac{1}{H}\sum_{i=1}^{H}x_i^2+\epsilon},\qquad y_i=\gamma_i\frac{x_i}{r}
$$

沿每个位置的 H 维计算均方根；形状不变。`ε` 是数值稳定项，`γ` 是训练得到、普通推理时固定的缩放参数。统计量随输入变化不等于参数更新。[RMSNorm 定义](https://docs.pytorch.org/docs/stable/generated/torch.nn.RMSNorm.html)

手算示例：设 `x=[3,4,0,0]`、`γ=[1,1,1,1]`，仅为手算忽略 ε。均方根为 `sqrt((9+16)/4)=2.5`，输出为 `[1.2,1.6,0,0]`。可见归一化后的特征不一定在 0 到 1 之间，也不是概率。实际实现需保留 ε。

LayerNorm 会减去均值，再按含稳定项的标准差缩放；RMSNorm 使用均方根、不减均值。完整推导与实现留给 T009。[LayerNorm 论文](https://arxiv.org/abs/1607.06450)、[RMSNorm 论文](https://arxiv.org/abs/1910.07467)

### LM Head：为词表候选打分

采用 PyTorch 的权重排列，W 的形状为 `[V,H]`，每行对应一个候选。线性层执行 `z=yWᵀ+b`；b 为可选偏置。每个分数是输入向量与对应权重行的点积，再加偏置（若有）。[Linear 定义](https://docs.pytorch.org/docs/main/generated/torch.nn.functional.linear.html)

独立的巩固例子：输出头输入 `y=[2,-1]`，无偏置。

| 候选 ID | 权重行 | 计算 | 分数 |
| --- | --- | --- | --- |
| 0 | `[1,0]` | `2×1+(-1)×0` | 2 |
| 1 | `[0,1]` | `2×0+(-1)×1` | -1 |
| 2 | `[1,1]` | `2×1+(-1)×1` | 1 |

得到 logits `[2,-1,1]`。权重与输入均为教学构造，不代表真实模型参数。LM Head 自身不汇集其他位置的信息；它读取的向量已经由前面的 Block 融合上下文。

### 从分数到 token

logits 是原始分数，不是概率。需要概率时，可沿词表维度计算 `p_j=exp(z_j)/sum_k(exp(z_k))`。softmax 处理候选分数，最终归一化处理隐藏特征，两者不同。[Softmax 定义](https://docs.pytorch.org/docs/main/generated/torch.nn.functional.softmax.html)

贪心选择直接取最高分对应的 ID；上例选择 ID `0`。softmax 不改变排序，所以只求最高分时无须显式计算概率。按概率采样时，最高分候选不保证每次被选中。

## 自测与理解记录

| 材料与题目 | 回答要点及结果 |
| --- | --- |
| 10 月 10 日第 1 题：翻译 Decoder 使用哪两类信息？ | 原文表示与已经生成的译文前缀；正确 |
| 10 月 10 日第 2 题：Block 与输出头形状为何不同？ | 经补讲理解 B/S/H/V；迁移例 H=8、V=10 时正确回答 `[1,3,8]` 与 `[1,3,10]` |
| 10 月 10 日第 3 题：文字到下一 token 的流程？ | 经补讲完整复述 Tokenizer、Embedding、Decoder Blocks、最终归一化、LM Head、选择；正确说明 Self-Attention 的信息汇集作用 |
| 10 月 11 日第 1 题，10 月 12 日作答：三个输出环节产生什么？ | 归一化后的特征、词表分数、下一个 token；正确 |
| 10 月 11 日第 2 题，10 月 12 日作答：点积与贪心选择？ | 分数 `[2,-1,1]`，选择 ID `0`；正确 |
| 10 月 11 日第 3 题，10 月 12 日作答：`[1,2,3]` 含义？ | 2 为已有位置数、3 为候选数，仍需选择 token；正确 |

学习中重点纠正了“多个 Block 共同计算即可解释形状不变”“独立 Encoder 可以随意省略”以及把 Decoder Block 与 Decode 混用的问题。补讲还区分了隐藏特征、logits、概率和最终 ID。

## 适用边界与后续学习

本笔记确认整体流程和输出端基础的理论掌握；Tokenizer、注意力、归一化、输出头仍会按路线分别深入。模型结构不同，模块位置、缓存和生成方式需要重新核对。本课没有完成 CPU 模型复现或 NPU 设备验证。

RMSNorm 对应逐元素运算和归约，LM Head 对应矩阵乘法，这是后续算子实践的入口。数据布局、精度误差及性能需通过独立实验验证。

下一主题为 T002 — Token、Tokenizer、词表与 Embedding。按学习者明确要求，于 2026-10-12 开始第一节“Token、token ID 与词表”；后续各子课仍按一天一课推进，除非另有明确安排。

## 讲义与来源记录

- [10 月 10 日完整讲义与补讲](../../daily/2026/10/2026-10-10.md)。
- [10 月 11 日输出端巩固与自测反馈](../../daily/2026/10/2026-10-11.md)。
- 技术来源沿用上述讲义在 2026-10-10 至 2026-10-11 核对的论文、官方文档与固定版本代码；本次归档整理既有学习内容。
- [学习路线](../../docs/roadmap.md)、[学习进度](../../docs/progress.md)、[实践里程碑](../../docs/practice-milestones.md)。
