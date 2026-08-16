@echo off
chcp 65001 >nul
setlocal

set "TCCT_DIR=%~dp0"
set "WOLFRAM_HOME=E:\Wolfram_engine"
set "WOLFRAMSCRIPT=%ProgramFiles%\Wolfram Research\WolframScript\wolframscript.exe"
set "WOLFRAMSCRIPT_CONFIGURATIONPATH=%TCCT_DIR%WolframScript_TCCT.conf"
set "WOLFRAMSCRIPT_KERNELPATH=%WOLFRAM_HOME%\WolframKernel.exe"

if not exist "%WOLFRAM_HOME%\WolframNB.exe" (
  echo 找不到 Wolfram Notebook 前端：%WOLFRAM_HOME%\WolframNB.exe
  pause
  exit /b 1
)

if not exist "%TCCT_DIR%TCCT_S71_Local.nb" (
  echo 首次运行，正在创建可视化 Notebook...
  "%WOLFRAMSCRIPT%" -file "%TCCT_DIR%build_visual_notebook.wls"
  if errorlevel 1 (
    echo Notebook 创建失败。请先完成 Wolfram Engine 激活。
    pause
    exit /b 1
  )
)

start "" "%WOLFRAM_HOME%\WolframNB.exe" "%TCCT_DIR%TCCT_S71_Local.nb"
