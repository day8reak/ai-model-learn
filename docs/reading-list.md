# 博客、论文与代码阅读清单

筛选日期：2026-10-09。每课推荐 1 篇主阅读、最多 1 篇进阶材料。借鉴作者的图解、实验与解释顺序，用自己的语言讲解并注明来源。

## 核心阅读路径

| 阶段 | 资料 | 用法与边界 |
| --- | --- | --- |
| Transformer 入门 | [Jay Alammar：The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) | 用图理解模块和数据流；先学原始 Encoder–Decoder，再对照 Decoder-only |
| 手写参考实现 | [Sebastian Raschka：LLMs from Scratch](https://sebastianraschka.com/llms-from-scratch/) | 使用作者的代码、分步实现和练习，优先 attention、模型和生成部分 |
| KV Cache | [Hugging Face：How caching works](https://huggingface.co/docs/transformers/main/en/cache_explanation) | 对照缓存与重计算、状态形状；运行时固定库版本 |
| 推理调度 | [Hugging Face：Continuous batching from first principles](https://huggingface.co/blog/continuous_batching) | 从单请求过渡到多请求，分析排队、缓存和吞吐 |
| 最小引擎 | [LMSYS：Mini-SGLang](https://www.lmsys.org/blog/2025-12-17-minisgl/) | 基础建立后追踪引擎调度与内存管理，硬件实现另外适配 |
| 新模型结构 | [千问官方](https://github.com/QwenLM)、[DeepSeek 官方](https://huggingface.co/deepseek-ai) | 通过[版本表](model-evolution.md)选定具体模型，比较配置、forward 和状态 |
| 硬件优化案例 | [昇腾官方：流水优化](https://www.hiascend.com/zh/developer/techArticles/20240819-1) | 借鉴搬运/计算重叠和收益分析，具体 API 留到选定平台后 |

以上核心页面已打开核对。经典资料解释基础，API、支持范围和性能数字按实际版本重新检查。

## 中文推导候选

[苏剑林：Transformer 升级之路·RoPE](https://kexue.fm/archives/8265)可作为位置编码专题的候选。此次找到原站，但正文抓取返回 403，尚未全文复核；可先使用 [RoFormer 原论文](https://arxiv.org/abs/2104.09864)，不根据摘要补造推导。

## 机制核对入口

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)：原始 Transformer。
- [GQA](https://arxiv.org/abs/2305.13245)：Q 头与 KV 头组织。
- [Mistral 7B](https://arxiv.org/abs/2310.06825)：滑动窗口案例。
- [FlashAttention](https://arxiv.org/abs/2205.14135)：注意力计算的分块与数据搬运。
- [PagedAttention](https://arxiv.org/abs/2309.06180)：推理缓存管理。
- [Speculative Decoding](https://arxiv.org/abs/2211.17192)：草稿与验证机制。

## 使用规则

博客帮助理解，公式、模型细节和性能结论回到论文/代码核对。记录对应模型和框架版本，区分旧版解释与当前实现。共享代码前检查许可证和署名要求，不上传整书、整篇转载或付费资源。面经单独整理在[面试练习](interview-practice.md)，只用于发现知识缺口。
