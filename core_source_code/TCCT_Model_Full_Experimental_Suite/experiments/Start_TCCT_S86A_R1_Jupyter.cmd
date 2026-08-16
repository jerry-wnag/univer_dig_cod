@echo off
chcp 65001 >nul
setlocal

set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S86A_R1_SixBranchFailureAudit.ipynb"
set "TCCT_CANDIDATE=E:\engine_wolf\TCCT_S83B_FrozenCandidate.wl"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s86a_r1"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s86a_r1"
set "PYTHONUTF8=1"

if not exist "%JUPYTER_LAB%" (
  echo JupyterLab not found: %JUPYTER_LAB%
  pause
  exit /b 1
)

if not exist "%TCCT_NOTEBOOK%" (
  echo S86A-R1 notebook not found: %TCCT_NOTEBOOK%
  pause
  exit /b 1
)

if not exist "%TCCT_CANDIDATE%" (
  echo Frozen K19 candidate not found: %TCCT_CANDIDATE%
  pause
  exit /b 1
)

if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"

start "TCCT S86A-R1 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8891 --ServerApp.port_retries=5
exit /b 0
