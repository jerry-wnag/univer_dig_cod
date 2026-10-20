# Validation and Limitations
# 验证范围与限制

**Reference package / 参考包：** [TCCT_NonARC_ScopedRepair_ReadSafety_20261020_R1_NOT_STABLE](https://drive.google.com/drive/folders/14yHozPvgvO3hZO-x6-VarZ8xcSD2q8Th)  
**Date / 日期：** 2026-10-20  
**Status / 状态：** fixed-Windows scoped repair delivery; not stable, not portable, not a general installer / 固定 Windows 环境下的有限范围修复交付，非稳定版、非可移植版、非通用安装包。

This page summarizes the evidence recorded in that package. It does not report a new Windows native rerun. The original R518 diagram is a historical architecture guide, not proof that every depicted path has been revalidated in R1.

本页汇总该包所记录的证据，不代表一次新的 Windows 原生复跑。原始 R518 架构图用于历史架构导览，不证明图中每条路径均已在 R1 中重新验证。

## 1. What changed / 修改内容

The underlying constructor repair is limited to **three list-level `Lookup` projections changed to per-row `Map` projections**: two in S160 and one in S161. R1 retains that repair and adds read-supervision and failure-handling checks. It introduces no new planner or semantic rules and does not replace the original rewriting, deduplication, or freezing mechanism.

底层构造器修复限于**三处由列表级 `Lookup` 投影改为逐行 `Map` 投影**：S160 两处，S161 一处。R1 保留该修复，并增加读取监管与失败处理检查；没有引入新的规划器或语义规则，也没有替换原始重写、去重或冻结机制。

## 2. Evidence layers / 证据层次

### Core regression and historical compatibility / 核心回归与历史兼容

The retained evidence records an old/new D01 contrast, **42 frozen test applications = 21 distinct inputs × 2 byte-identical source variants**, plus **four full historical-result comparisons**. The 42 applications check selected frozen contract fields and list lengths, not complete-output equality. They are not 42 distinct inputs, and the two variants are not independent algorithms.

保留证据记录了 D01 的修复前后对照、**42 次冻结测试应用 = 21 个不同输入 × 2 份字节一致的源码变体**，以及**4 个完整历史结果对照**。42 次应用检查选定的冻结契约字段与列表长度，并非完整输出相等性比较；它们不是 42 个不同输入，两份变体也不是独立算法。

The four historical comparisons cover `S160A_D2`, `JOINT_ACTIVE`, `CAUSAL_FULL`, and `CAUSAL_REDUCED`. They preserve complete recorded results rather than reducing compatibility to a single success flag. `CAUSAL_REDUCED` retains its original `RESIDUAL_NOT_ESTABLISHED_NO_PROPOSAL` outcome.

4 个历史对照覆盖 `S160A_D2`、`JOINT_ACTIVE`、`CAUSAL_FULL` 和 `CAUSAL_REDUCED`，保留完整记录结果，而非只比较一个成功标志。`CAUSAL_REDUCED` 原有的 `RESIDUAL_NOT_ESTABLISHED_NO_PROPOSAL` 结果保持不变。

### Windows native execution / Windows 原生执行

The package retains earlier fixed-host public-entry native evidence for S160 `HISTORICAL_S160A_D2_CAP3_COST2` and S161 `HISTORICAL_C01_ACTIVE_AND_CAUSAL_GATE`, including its original three cases. These are retained R0 records. R1 performs **no new owner, learner, query, source-algorithm, or Wolfram model computation**.

包内保留了此前固定主机上的公开入口原生执行证据：S160 的 `HISTORICAL_S160A_D2_CAP3_COST2`，以及 S161 的 `HISTORICAL_C01_ACTIVE_AND_CAUSAL_GATE`（包含原有三个案例）。这些是保留的 R0 记录。R1 **未新增 owner、learner、query、源码算法或 Wolfram 模型计算**。

### R1 read and failure checks / R1 读取与失败检查

R1 checks saved authentic results through the revised public read entry and preserves their state, results, counters, and reasons. It adds S161 failure controls and read-supervision evidence. Synthetic invalid-state and I/O fixtures are labeled synthetic; they are not fresh native model failures or new reasoning successes.

R1 经修订后的公开读取入口检查已保存的真实结果，保留其状态、结果、计数器和原因，并补充 S161 失败控制与读取监管证据。无效状态和 I/O 合成测试会标明其合成性质，不应视为新的原生模型失败或新的推理成功。

## 3. Read timeout and result meaning / 读取超时与结果含义

- The release specifies a **90-second supervised read-worker budget plus up to 5 seconds for cleanup** for the fenced read path associated with the current raw task. This is not a whole-CLI deadline, a bound on model reasoning, or proof that every path is time-bounded.
- A separate synthetic hanging-I/O fixture, including a child process, uses a **1-second test deadline** to check process-tree cleanup. This tests the supervision mechanism, not arbitrary production inputs.
- A timeout reports `READ_FAILED` / `READ_TIMEOUT`, with CLI exit code `124` and no automatic retry. It does not mean that the reasoning model proved there is no solution.
- Complete authenticated results may contain an authentic semantic refusal or no-proposal outcome. Source timeouts, missing or partial outputs, wrong-task receipts, and tampering are not promoted to successful complete results.
- The parent writes audit receipts outside kernel state. “Read-only” here does not mean that no file is written anywhere; it means that the protected read worker does not change kernel task/source/claim/semantic state, write files, or start children.

- 发布配置为当前原始任务所对应的受保护读取路径设定了 **90 秒读取工作进程预算，外加最多 5 秒清理时间**。这不是整个 CLI 的总时限，不限制模型推理时间，也不证明每条路径都有时限。
- 独立的挂起 I/O 合成测试包含一个子进程，以 **1 秒测试时限**检查进程树清理。它验证监管机制，而非任意实际输入。
- 超时返回 `READ_FAILED` / `READ_TIMEOUT`，CLI 退出码为 `124`，不自动重试。这不表示推理模型已证明问题无解。
- 完整认证结果可以包含真实的语义拒绝或无提案结论。源码执行超时、缺失或部分输出、错误任务回执及篡改记录，不会被提升为成功的完整结果。
- 父进程在内核状态之外写入审计回执。这里的“只读”不表示任何位置都不写文件，而是受保护的读取工作进程不改变内核任务／源码／授权声明／语义状态，不写文件，也不启动子进程。

## 4. Reproduction requirements and remaining limits / 复现要求与尚存限制

The recorded native environment is Windows 11, Python 3.13.5 with the existing Anaconda/PyWin32 environment, and a licensed Wolfram 15.0.0 installation. R1 depends on exact external project files and original fixed paths. Python, Wolfram, their dependencies, and the Wolfram license are not supplied by the ZIP. Downloading or extracting it does not establish a working installation on another machine.

记录中的原生环境为 Windows 11、既有 Anaconda/PyWin32 环境中的 Python 3.13.5，以及已获许可的 Wolfram 15.0.0。R1 依赖特定外部项目文件和原固定路径。ZIP 不提供 Python、Wolfram、其依赖或 Wolfram 许可，下载或解压并不等于可以在另一台电脑上直接运行。

The package does not establish arbitrary S161-input service, a fresh public D01 profile, an all-history rerun, cross-machine portability, blind generalization, unrestricted recursion, arbitrary providers, or ARC support. It is not a performance, stability, security, or concurrency certification. The delivery does not replace the default installed entry.

该包未确立任意 S161 输入服务、新的公开 D01 配置、全历史复跑、跨机器可移植性、盲测泛化、无限递归、任意提供方或 ARC 支持，也不是性能、稳定性、安全或并发认证。该交付未替换默认已安装入口。

Historical reasoning results retain their original experimental scope. Neither the unified-entry architecture nor this scoped repair establishes AGI, demonstrated Turing completeness, 25 independent reasoning kernels, or correctness for all inputs.

历史推理结果保留各自原有的实验范围。统一入口架构及本次有限修复均不确立 AGI、已证明的图灵完备性、25 个独立推理内核或所有输入上的正确性。

## 5. Package identity and source records / 包标识与证据记录

**R1 ZIP / R1 压缩包：** `TCCT_NonARC_FixedWindows_ScopedRepair_ReadSafety_20261020_R1.zip`  
**SHA-256：** `6415893faad33ae6280a44ccdc4cb7abca018dc1eea627ca946e8305209f2143`

**Repaired core SHA-256 / 修复后核心 SHA-256：**  
`ac569f8a4e45016d451550ef70e9ce16c8f94443bbc2acd343ae54292cce3c1c`

For the underlying records, consult the following files inside the linked R1 package and its evidence tree:

核对底层记录时，请查看所链接 R1 包及其证据目录中的以下文件：

- `README_FIRST_EN.txt` / `README_FIRST_ZH.txt`
- `RELEASE_SCOPE_R1_EN.json`
- `R1_DEPENDENCIES_EN.json`
- `FINAL_FIXED_HOST_PINS_EN.json` (retained earlier environment pins / 保留的此前环境绑定)
- `TEST_ACCEPTANCE_EN.json`
- `FINAL_READ_ACCEPTANCE_EN.json`
- `S161_FAILURE_SCOPE_TESTS_EN.json`
- `TIMEOUT_PROCESS_TREE_EN.json`

Hash verification establishes file identity, not scientific validity or successful execution. Follow the package's own first-read instructions before attempting verification or recovery; this documentation folder contains no installer or runtime.

哈希校验确立文件身份，不等于科学结论有效或执行成功。尝试校验或恢复前应先阅读包内首读说明；本说明文件夹不包含安装器或运行时。
