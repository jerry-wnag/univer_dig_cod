# TCCT S125-C Pilot-5 Multi-Restart Matched Comparison

本目录保存 S125-C 五世界严格 fresh-world 对比测试的源代码、冻结模型、逐世界原始结果、汇总表与 PDF 报告。

## 结论

- 严格协议：5/5 世界通过，`S125COverallPass = True`。
- TCCT：370/370 个未见高阶状态 exact，2960/2960 个未见高阶转移 exact。
- matched Transformer（85,890 参数）：状态与转移 exact 均为 0。
- 4× strong Transformer（339,170 参数）：状态与转移 exact 均为 0。
- TCCT 的结构表示为每世界 41–42 个 sparse conditional cells。它们与神经网络权重不是同一种参数，不能声称严格的 1:1 压缩倍数；但在共享并冻结感知器的 reasoner-only 对比下，TCCT 用很小的离散规则表获得了 100% exact，而两种 Transformer 都未恢复完整高阶结构。

## S125-C 改动边界

S125-C 只修复 S125-B 中 matched Transformer 单次初始化偶发不能通过低阶能力门控的问题：

1. 预先登记 3 个 selection seeds，只依据低阶 validation balanced accuracy 选择初始化。
2. 预先登记 3 个 final seeds，只依据低阶 training balanced accuracy 选择并冻结最终模型。
3. 高阶 holdout 在所有模型冻结后才首次打开，`HighOrderUsedForSelection = False`。

TCCT 的重写、冻结、去重、原迭代规则以及 matched/strong Transformer 的网络架构均未修改。

## 目录说明

- `source/`：S125-C runner、S124 T5R1 canonical notebook，以及每个世界实际执行的 Wolfram source。
- `aggregate/`：预注册 manifest、五世界汇总 WL/CSV。
- `worlds/`：五个世界的完整原始目录，包含冻结感知器、冻结 TCCT、冻结 matched/strong reasoner、日志和结果。
- `report/`：三页中文结果报告。
- `tools/`：本轮用于提交、预检和选择逻辑检查的辅助脚本；不属于 TCCT 核心机制。
- `speed_benchmark/`：S125-D 冻结 reasoner-only CPU 速度基准的代码、原始 JSON、汇总 CSV 与结论。
- `SHA256SUMS.csv`：交付目录内文件的 SHA-256 与大小，用于完整性复核。

## S125-D 速度补充

五世界同机 NumPy CPU 基准中，原 S125-C TCCT 路径的单个 14-probe 签名中位延迟为 `0.107777 ms`，状态只计算一次的等价缓存路径为 `0.009982 ms`；Matched 与 Strong Transformer 分别为 `4.507300 ms` 和 `13.581500 ms`。缓存路径与原路径在每世界全部 666 个签名上完全一致。该结果是共享感知器之后的 reasoner-only 架构级比较，不是 Wolfram kernel 或完整感知到推理端到端时间。

## 关键协议标识

- Canonical base source SHA-256: `9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b`
- S125-C manifest SHA-256: `c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540`
- Pre-world protocol SHA-256: `617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9`

## 解释边界

该结果支持的是：在共享冻结感知、低阶训练、密封高阶 holdout 和预注册门控条件下，TCCT 相对合格 matched Transformer 与约 4 倍参数 strong Transformer 的高阶 exact 组合泛化优势。它不等于已经证明 TCCT 在自然语言、现实视觉或所有大规模开放任务上全面优于 Transformer。
