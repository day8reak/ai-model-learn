# T002-3 — 特殊 token、模型配套与文本解码

- 分类：基础
- 状态：已掌握（理论：特殊 token、模型配套与 ID 解码）
- 首次学习、确认与归档：2026-10-13
- 前置知识：[T002-2 — Tokenizer 与 BPE](T002-2-tokenizer-bpe.md)
- 确认依据：三题已作答，第 2、3 题通过，第 1 题的 PAD 计数经补讲；学习者随后明确确认吃透。
- 实践状态：尚未完成真实 tokenizer、CPU 模型或 NPU 实现验证。

## 特殊 token 与位置计数

BOS 标记序列开始，EOS 标记结束，PAD 用于填充。它们有自己的 ID，加入输入后也占序列位置；实际 ID、添加方式及是否复用编号取决于具体模型。生成是否停止由生成配置和运行逻辑决定，文本解码的显示选项不能替代停止判断。[Tokenizer API](https://huggingface.co/docs/transformers/main/en/main_classes/tokenizer) · [生成配置](https://huggingface.co/docs/transformers/v4.45.2/en/main_classes/text_generation)

教学词表预先固定为九项：`a:0,b:1,c:2,ab:3,abab:4,ac:5,<bos>:6,<eos>:7,<pad>:8`。沿用上一课三条 BPE 规则，并约定句首加 BOS、句尾加 EOS：

```text
abac → ab / ac → [3,5] → [6,3,5,7]
S=4，V=9
再补一个 PAD：[6,3,5,7,8]，S=5，V=9
```

填充增加的是输入位置数，不是词表项数。补一个与补两个 PAD 必须分别计数。PAD 需要配套掩码处理，不能仅插入编号就视为自动忽略；例中右填充不代表所有推理引擎的推荐配置。

## 配套要求不限于 V 一样

至少核对 token 内容、ID 对应关系、切分与规范化规则、特殊 token 配置；聊天模型还需使用对应模板。模型权重按训练时的编号约定解释输入，不能随意更换 tokenizer。[官方编码说明](https://huggingface.co/learn/llm-course/en/chapter2/4#encoding)

聊天模板组织角色和内容，通常已添加必要边界。若先生成模板文本、再单独分词，要避免重复添加特殊 token；按官方说明设置后续分词的 `add_special_tokens=False`。[聊天模板说明](https://huggingface.co/docs/transformers/main/en/chat_templating)

## 文本解码与还原边界

`tokenizer.decode` 将已有 ID 查回 token，再依照规则重建文字。ID 可以来自原文编码，也可以来自模型生成；此过程不要求运行 Transformer。它与模型逐步生成 token 的 Decode 阶段、模型内部的 Decoder Block 是三个不同概念。[解码流程](https://huggingface.co/docs/tokenizers/pipeline#decoding)

`skip_special_tokens=True` 跳过已配置的特殊 token，例如本例的 BOS、EOS、PAD；不是自动删除所有符号或标点。教学序列 `[6,3,5,7]` 跳过特殊 token 后得到 `abac`。

编码、解码不保证无损往返：若编码前将 `Hello` 规范化成 `hello`，大小写信息已丢失；未知 token 替代与空白处理也可能改变原文。具体以 tokenizer 配置为准。[规范化说明](https://huggingface.co/docs/tokenizers/pipeline#normalization)

## 复习与下一课

- 区分词表大小 V、含填充的张量位置数 S、非 PAD 的有效位置数。
- 能说明仅 V 相同为什么不足以更换 tokenizer。
- 能区分 ID 解码、模型生成和停止判断，并说明无法逐字还原的例子。

自测与图示见[完整讲义](../../lessons/T002-3.md)，原答、补讲与确认见[2026-10-13 学习日志](../../study-log/2026/10/2026-10-13.md)。以上资料于 2026-10-13 核对；本笔记不作为工程实践验收。

下一课：[T002-4 — Embedding 查表、权重与形状](../../lessons/T002-4.md)。
