# TCCT S125-E Saturated Neural Baseline

本目录保存“低阶接近饱和后再打开高阶”的五世界确认测试。

## 最重要结果

- 五个世界全部通过低阶饱和门槛。
- 神经低阶验证 balanced accuracy：`99.489%` 至 `99.696%`。
- 神经低阶验证完整 14-bit 签名 exact：`94.905%` 至 `96.739%`。
- 高阶状态：TCCT `370/370`，神经基线 `194/370`。
- 高阶转移：TCCT `2960/2960`，神经基线 `954/2960`。
- 神经基线 176,270 个可训练参数；TCCT 为 41 或 42 个 conditional transition cells。

详细解释见 `S125E_SaturatedNeural_Result.md`，机器可读结果见 `confirmatory_results/S125E_aggregate.json` 和 `confirmatory_results/S125E_per_world.csv`。

## 目录

- `source/`：原样锁定的测试源码和依赖说明
- `protocol/`：高阶打开之前生成的预注册清单
- `development_low_order_only/`：只做低阶训练、没有打开高阶的五世界开发审计
- `confirmatory_results/`：随机抽取五个冻结严格世界后的完整结果、冻结模型和逐世界记录
- `frozen_world_inputs/`：本次读取的五份 TCCT freeze 文件和原严格 summary
- `SHA256SUMS.txt`：本目录全部归档文件的 SHA-256 校验值

## 证据边界

这是从既有 20 个严格 fresh-world 冻结池中，按预声明随机种子抽取 5 个世界进行的离线确认性压力测试，不是重新生成的 5 个 fresh worlds。训练和模型选择没有使用高阶标签；模型保存并重新加载后才打开高阶测试。

本轮没有修改 TCCT 核心机制、重写、冻结、去重或原迭代规则。

