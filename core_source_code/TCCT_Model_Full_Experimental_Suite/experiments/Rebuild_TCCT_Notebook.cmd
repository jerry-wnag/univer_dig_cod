@echo off
chcp 65001 >nul
setlocal

set "TCCT_DIR=%~dp0"
set "WOLFRAMSCRIPT=%ProgramFiles%\Wolfram Research\WolframScript\wolframscript.exe"
set "WOLFRAMSCRIPT_CONFIGURATIONPATH=%TCCT_DIR%WolframScript_TCCT.conf"
set "WOLFRAMSCRIPT_KERNELPATH=E:\Wolfram_engine\WolframKernel.exe"

"%WOLFRAMSCRIPT%" -file "%TCCT_DIR%build_visual_notebook.wls"
if errorlevel 1 (
  echo 重建失败。请确认 Wolfram Engine 已激活。
) else (
  echo TCCT_S71_Local.nb 已重建。
)
pause
