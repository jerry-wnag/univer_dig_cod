# TCCT S71：免费 Wolfram Engine 15 + JupyterLab

## 当前状态

- 免费 Wolfram Engine 15.0 已安装并激活：`E:\engine_wolf`
- JupyterLab 已安装：`E:\anaconda\Scripts\jupyter-lab.exe`
- Jupyter 内核名称：`Wolfram Language 15`
- TCCT 笔记本：`TCCT_S71_Jupyter.ipynb`
- 一键启动：`Start_TCCT_Jupyter.cmd`
- 计算与图形测试：已通过

## 怎么打开

双击 `Start_TCCT_Jupyter.cmd`。浏览器打开 JupyterLab 后，等待右上角显示
`Wolfram Language 15`。

先运行最上面的 Environment check 单元格。看到 Wolfram 15.0 后，再用菜单：

`Kernel` → `Restart Kernel and Run All Cells`

完整 S59–S71 会按原顺序运行。第一次生成图形时可能下载 Wolfram 图形组件，
因此会慢一到两分钟；之后通常更快。

## 路径说明

由于 Windows 中文用户名会导致旧版 WolframScript/Jupyter 接口乱码，启动器已经把
Jupyter 的配置、内核和临时目录固定到：

`E:\engine_wolf\jupyter`

请不要删除该目录，也不要直接用旧的 `E:\Wolfram_engine` 14.3 安装启动本项目。

## 安全提醒

激活密钥和机器密码不要再截图发送或公开保存。它们不是运行代码时需要输入的内容。
