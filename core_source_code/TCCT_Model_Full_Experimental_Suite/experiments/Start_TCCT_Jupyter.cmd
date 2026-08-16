@echo off
chcp 65001 >nul
setlocal

set "TCCT_NOTEBOOK=%~dp0TCCT_S71_Jupyter.ipynb"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=E:\engine_wolf\jupyter\config"
set "JUPYTER_RUNTIME_DIR=E:\engine_wolf\jupyter\runtime"
set "PYTHONUTF8=1"

if not exist "%JUPYTER_LAB%" (
  echo JupyterLab not found: %JUPYTER_LAB%
  pause
  exit /b 1
)

if not exist "%TCCT_NOTEBOOK%" (
  echo TCCT notebook not found: %TCCT_NOTEBOOK%
  pause
  exit /b 1
)

start "TCCT JupyterLab" "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%"
exit /b 0
