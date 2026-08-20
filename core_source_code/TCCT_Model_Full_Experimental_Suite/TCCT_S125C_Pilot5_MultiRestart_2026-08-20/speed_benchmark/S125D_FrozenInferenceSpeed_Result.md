# TCCT S125-D 冻结推理速度基准

## 结论

在本机 CPU、同一 NumPy 进程、共享输入编码口径下，TCCT 推理核心明显快于两个冻结 Transformer reasoner。五世界所有完整性审计均通过。

| 推理器 | 单个 14-probe 签名中位延迟 | 五世界中位 P95 | 完整 666 签名吞吐 |
|---|---:|---:|---:|
| TCCT 原 S125-C 路径 | 0.107777 ms | 0.124327 ms | 14,469.9 signatures/s |
| TCCT 状态缓存路径 | 0.009982 ms | 0.011205 ms | 134,553.6 signatures/s |
| Matched Transformer | 4.507300 ms | 5.250240 ms | 216.3 signatures/s |
| Strong Transformer | 13.581500 ms | 14.243100 ms | 73.0 signatures/s |

相对单签名延迟：

- 原 S125-C TCCT 比 Matched 快约 41.82×，比 Strong 快约 126.01×。
- 状态缓存 TCCT 比 Matched 快约 451.55×，比 Strong 快约 1360.63×。

相对完整工作负载吞吐：

- 原 S125-C TCCT 是 Matched 的约 66.88×、Strong 的约 198.15×。
- 状态缓存 TCCT 是 Matched 的约 621.94×、Strong 的约 1842.55×。

状态缓存没有改变 TCCT 模型、重写、去重、冻结或转移规则。它只避免原 S125-C 在生成一个 14-bit 签名时为每个 probe 重复计算整段 factorized state；五个世界中，缓存路径与原路径在全部 666 个签名上逐项完全一致。

## 测试口径

- 五个 S125-C 世界，冻结模型直接加载，不重新训练、不调参、不改变权重。
- 每世界 74 个状态签名和 592 个转移签名，共 666 个签名、9,324 个 probe 预测。
- 冻结最大序列长度为 16；实测最长序列长度为 11。
- Transformer 覆盖 sequence batch 1、32、256；本机 CPU 上两种网络均以 batch 1 吞吐最高。
- TCCT 使用真实冻结规则文件；Transformer 直接读取真实 `.wlnet` HDF5 权重，并在 NumPy 中重放相同的线性层、因果多头注意力、残差 MLP 和 last-token readout。
- 运行环境：Windows 11，Intel64 Family 6 Model 154，16 logical processors，NumPy 2.1.3，MKL 10 threads。

## 规模与存储

- TCCT：41–42 个 conditional cells；冻结文件中位数约 3.30 KiB。
- Matched Transformer：85,890 参数；343,560 参数字节；冻结文件 364,096 bytes。
- Strong Transformer：339,170 参数；1,356,680 参数字节；冻结文件 1,383,112 bytes。

## 解释边界

这是 reasoner-only、CPU、同运行环境的架构级速度基准。当前 Wolfram 命令行许可证返回 `No valid password found`，因此这些数字不是 Wolfram kernel 的墙钟时间。NumPy Transformer 使用了优化 BLAS，而 TCCT 仍是普通 Python 字典和循环实现。

整体混合模型仍包含共享的外层 Transformer 感知器，因此端到端系统延迟等于“共享感知延迟 + 推理核心延迟”。如果感知器占据主要耗时，整机端到端倍数会小于这里的 reasoner-only 倍数；GPU、大批量和更长序列也需要另行测试。

## 当前判断

在当前 17-token、14-probe、单样本/小批量受控任务上，TCCT 不仅结构规模更小、高阶 exact 泛化更强，推理核心也显著更快。下一步若要形成最终工程结论，应修复 Wolfram 许可证后复测原生 Wolfram 墙钟时间，并单独测量共享感知器，使端到端延迟能够完整分解。
