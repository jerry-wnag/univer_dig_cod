@echo off
chcp 65001 >nul
setlocal

set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S88_EightBranchFrozenDecoderBlind.ipynb"
set "TCCT_K33=E:\engine_wolf\TCCT_S86E_K33FrozenCandidate.wl"
set "TCCT_DECODER_RUNTIME=E:\engine_wolf\TCCT_S87D_FrozenDecoderRuntime.wl"
set "TCCT_DECODER=E:\engine_wolf\TCCT_S87D_FrozenWorldMultisetDecoder.wxf"
set "TCCT_FREEZE_CERT=E:\engine_wolf\TCCT_S87D_FreezeCertificate.json"
set "TCCT_S88_RESULT=E:\engine_wolf\TCCT_S88_BlindResultCertificate.json"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s88"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s88"
set "PYTHONUTF8=1"

if not exist "%JUPYTER_LAB%" (
  echo JupyterLab not found: %JUPYTER_LAB%
  pause
  exit /b 1
)
if not exist "%TCCT_NOTEBOOK%" (
  echo S88 notebook not found: %TCCT_NOTEBOOK%
  pause
  exit /b 1
)
if not exist "%TCCT_K33%" (
  echo Frozen K33 candidate not found: %TCCT_K33%
  pause
  exit /b 1
)
if not exist "%TCCT_DECODER_RUNTIME%" (
  echo Frozen decoder runtime not found: %TCCT_DECODER_RUNTIME%
  pause
  exit /b 1
)
if not exist "%TCCT_DECODER%" (
  echo Frozen S87D decoder not found: %TCCT_DECODER%
  pause
  exit /b 1
)
if not exist "%TCCT_FREEZE_CERT%" (
  echo S87D freeze certificate not found: %TCCT_FREEZE_CERT%
  pause
  exit /b 1
)
if exist "%TCCT_S88_RESULT%" (
  echo A prior S88 result certificate already exists.
  echo Preserve it and do not rerun or overwrite the blind test.
  echo %TCCT_S88_RESULT%
  pause
  exit /b 1
)

if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"

start "TCCT S88 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8901 --ServerApp.port_retries=5
exit /b 0

