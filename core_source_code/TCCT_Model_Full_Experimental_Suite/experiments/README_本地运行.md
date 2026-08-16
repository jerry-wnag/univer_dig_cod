# TCCT S71 本地运行

当前环境已经固定使用：

- Wolfram 14.3：`E:\Wolfram_engine`
- Notebook 前端：`E:\Wolfram_engine\WolframNB.exe`
- 内核：`E:\Wolfram_engine\WolframKernel.exe`
- 源代码：`TCCT_S71_recovered_full.wl`

## 第一次使用

1. 在 Wolfram 官方页面重置密码：<https://account.wolfram.com/auth/forgot-password>
2. 运行 `E:\Wolfram_engine\wolfram.exe`，输入 Wolfram ID 与新密码完成一次性激活。
3. 双击 `Start_TCCT_Notebook.cmd`。
4. Notebook 打开后，从上到下逐格按 `Shift+Enter`；也可以使用 **Evaluation > Evaluate Notebook**。

完整代码包含 142 个输入单元，第一次执行搜索阶段可能需要一些时间。

## 两种运行方式

- `Start_TCCT_Notebook.cmd`：推荐。打开带图形、表格和结果图的可视化 Notebook。
- `Run_TCCT_Headless.cmd`：不打开界面，批量执行后把摘要保存到 `results\TCCT_S71_result.json`。

若修改了 Notebook 构建脚本，可以运行 `Rebuild_TCCT_Notebook.cmd` 重新生成可视化 Notebook。

## 科研边界

`TCCT_S71_recovered_full.wl` 是从 PDF 恢复出的 S71 封存代码。不要在其中调整冻结模型：

```text
K = 5
Params = {0,-1,1,-1,-1,0}
Policy = {1,4}
```

S72 应另建文件，避免污染 S71 检查点。
