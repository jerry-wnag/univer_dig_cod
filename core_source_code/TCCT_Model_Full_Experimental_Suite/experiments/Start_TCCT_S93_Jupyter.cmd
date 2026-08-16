@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S93_PairedCounterfactualBlind.ipynb"
set "TCCT_CANDIDATE=E:\engine_wolf\TCCT_S92B_FrozenPairedContrastDecoder.wxf"
set "TCCT_S92B=E:\engine_wolf\TCCT_S92B_PairedContrastDecoderCertificate.json"
set "TCCT_S93_RESULT=E:\engine_wolf\TCCT_S93_PairedCounterfactualBlindCertificate.json"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s93"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s93"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S93 notebook not found & pause & exit /b 1)
if not exist "%TCCT_CANDIDATE%" (echo Frozen S92B candidate not found & pause & exit /b 1)
if not exist "%TCCT_S92B%" (echo Locked S92B certificate not found & pause & exit /b 1)
if exist "%TCCT_S93_RESULT%" (
  echo A prior S93 blind certificate already exists.
  echo Preserve it. Do not rerun or overwrite S93.
  pause & exit /b 1
)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S93 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8908 --ServerApp.port_retries=5
exit /b 0
