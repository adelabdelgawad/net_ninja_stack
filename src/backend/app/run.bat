@echo off
SETLOCAL

REM Ensure the script is running as administrator
:: Check for administrative permissions
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-ProcessBase '%~f0' -Verb runAs"
    exit /B
)

REM Change Directory to the Application
call cd C:\DailyCheck\NetNinja
call c:

REM Activate the virtual environment
call Scripts\activate

REM Run the Python script
python main.py

ENDLOCAL
