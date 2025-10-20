@echo off
SETLOCAL

REM Ensure the script is running as administrator
:: Check for administrative permissions
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /B
)

REM Change Directory to the Application
cd /d D:\Codes\NetNinja-main

REM Activate the virtual environment
call Scripts\activate

REM Verify activation by checking Python version
python --version

REM Run the Python script and redirect the output to a file
python main.py > output.txt 2>&1

REM Deactivate the virtual environment
deactivate

ENDLOCAL
