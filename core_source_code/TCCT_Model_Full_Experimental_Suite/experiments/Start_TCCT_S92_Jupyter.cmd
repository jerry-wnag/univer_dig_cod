@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S92_CardinalityMatchedUniformActionBlind.ipynb"
set "TCCT_S91_RESULT=E:\engine_wolf\TCCT_S91_BenchmarkCertificate.json"
set "TCCT_S92_RESULT=E:\engine_wolf\TCCT_S92_BlindResultCertificate.json"
set "TCCT_DECODER=E:\engine_wolf\TCCT_S87D_FrozenWorldMultisetDecoder.wxf"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s92"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s92"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S92 notebook not found & pause & exit /b 1)
if not exist "%TCCT_S91_RESULT%" (echo Locked S91 certificate not found & pause & exit /b 1)
if not exist "%TCCT_DECODER%" (echo Frozen decoder not found & pause & exit /b 1)
if exist "%TCCT_S92_RESULT%" (
  echo A prior S92 result certificate already exists.
  echo Preserve it and do not rerun or overwrite the blind test.
  pause & exit /b 1
)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S92 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8905 --ServerApp.port_retries=5
exit /b 0
