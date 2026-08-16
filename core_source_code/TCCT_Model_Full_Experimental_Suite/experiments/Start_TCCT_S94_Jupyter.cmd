@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S94_MixedContextRobustnessBlind.ipynb"
set "TCCT_CANDIDATE=E:\engine_wolf\TCCT_S92B_FrozenPairedContrastDecoder.wxf"
set "TCCT_S93=E:\engine_wolf\TCCT_S93_PairedCounterfactualBlindCertificate.json"
set "TCCT_S94_RESULT=E:\engine_wolf\TCCT_S94_MixedContextRobustnessBlindCertificate.json"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s94"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s94"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S94 notebook not found & pause & exit /b 1)
if not exist "%TCCT_CANDIDATE%" (echo Frozen pair candidate not found & pause & exit /b 1)
if not exist "%TCCT_S93%" (echo Locked S93 certificate not found & pause & exit /b 1)
if exist "%TCCT_S94_RESULT%" (echo Prior S94 certificate exists. Preserve it. & pause & exit /b 1)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S94 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8909 --ServerApp.port_retries=5
exit /b 0
