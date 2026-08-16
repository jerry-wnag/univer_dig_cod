@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S91_BaselineAblationBenchmark.ipynb"
set "TCCT_ARCHIVE=%TCCT_DIR%artifacts\TCCT_S90_BenchmarkWorlds.json"
set "TCCT_DECODER=E:\engine_wolf\TCCT_S87D_FrozenWorldMultisetDecoder.wxf"
set "TCCT_S90_RESULT=E:\engine_wolf\TCCT_S90_BlindResultCertificate.json"
set "TCCT_S91_RESULT=E:\engine_wolf\TCCT_S91_BenchmarkCertificate.json"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s91"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s91"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S91 notebook not found & pause & exit /b 1)
if not exist "%TCCT_ARCHIVE%" (echo Locked S90 benchmark archive not found & pause & exit /b 1)
if not exist "%TCCT_DECODER%" (echo Frozen S87D decoder not found & pause & exit /b 1)
if not exist "%TCCT_S90_RESULT%" (echo Locked S90 certificate not found & pause & exit /b 1)
if exist "%TCCT_S91_RESULT%" (
  echo A prior S91 benchmark certificate already exists.
  echo Preserve it and do not overwrite it.
  pause & exit /b 1
)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S91 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8904 --ServerApp.port_retries=5
exit /b 0
