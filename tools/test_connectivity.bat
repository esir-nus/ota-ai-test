@echo off
REM Test OTA connectivity with the mock server

python %~dp0\test_connectivity.py --simulation --config=%~dp0\..\daemon\config\test_config.json %*

if %ERRORLEVEL% NEQ 0 (
  echo Test failed with error code %ERRORLEVEL%
  exit /b %ERRORLEVEL%
)

echo Test completed successfully 