@echo off
echo Starting OTA Package Generator...
echo.

REM Get the directory of this batch file
set "SCRIPT_DIR=%~dp0"
cd "%SCRIPT_DIR%"

REM Check if Python is installed and available in PATH
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

REM Run the launcher script
python "%SCRIPT_DIR%launch_gui.py"

REM If we get here, the application has exited
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%
    echo See gui_launcher.log for details
)

pause 