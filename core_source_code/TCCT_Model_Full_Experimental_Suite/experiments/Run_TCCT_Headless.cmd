@echo off
chcp 65001 >nul
setlocal

set "TCCT_DIR=%~dp0"
set "WOLFRAMSCRIPT=%ProgramFiles%\Wolfram Research\WolframScript\wolframscript.exe"
set "WOLFRAMSCRIPT_CONFIGURATIONPATH=%TCCT_DIR%WolframScript_TCCT.conf"
set "WOLFRAMSCRIPT_KERNELPATH=E:\Wolfram_engine\WolframKernel.exe"

"%WOLFRAMSCRIPT%" -file "%TCCT_DIR%TCCT_S71_headless.wls"
echo.
if errorlevel 1 (
  echo 运行失败。请检查激活状态或上方错误信息。
) else (
  echo 运行完成，结果位于 wolfram\results。
)
pause
