@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S95_StrictBlind.ipynb"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s95"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s95"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S95 notebook not found & pause & exit /b 1)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S95 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8896 --ServerApp.port_retries=5
exit /b 0
