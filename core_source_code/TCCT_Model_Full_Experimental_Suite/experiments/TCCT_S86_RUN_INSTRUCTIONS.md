# TCCT S86 运行说明

## 测试目的

冻结的 S83B `K=19` 候选第一次迁移到独立六分支图语法。S86 不搜索候选、不改 K、不改策略，也不重跑 S83–S85 数据。

- 分支数：6（此前固定为 4）
- 深度：43、71
- 拓扑：DoubleDiamondIn、HierarchicalDiamondIn
- 双分支干预组合：6 组均衡组合
- 每张图检查全部 6 个查询
- 总计：24 个场景、144 个干预前后配对、288 个世界

## 运行方法

1. 双击 `Start_TCCT_S86_Jupyter.cmd`。
2. 打开后确认 notebook 名为 `TCCT_S86_ExternalSixBranchBlind.ipynb`。
3. 选择 `Kernel -> Restart Kernel and Run All Cells`。
4. 等待最后一格出现 `cert86` 数据表。不要单独重复运行中间单元格。

## 首格必须显示

- `CandidateFileLoaded -> True`
- `CandidateK -> 19`
- `CandidatePolicyLength -> 26`
- `PreflightPassed -> True`
- `OriginalFrozenModelChanged -> False`
- `FrozenCandidateChanged -> False`
- `CoreChanged -> False`

若 `PreflightPassed -> False`，立即停止，不要解释后续分数。

## 最终证书判读

有效通过应显示：

- `TestValidityPassed -> True`
- `BlindPerfect -> True`
- `WorldCorrect -> 288`
- `PairCorrect -> 144`
- `ScenarioPerfect -> 24`
- `Outcome -> BLIND_EXTERNAL_SIX_BRANCH_PASS`

如果 `TestValidityPassed -> True` 但 `BlindPerfect -> False`，这是有效盲测失败，应保留结果并进入 S86A 失败审计，不能在同一测试上调参后重新称为盲测。

