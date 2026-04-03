@echo off
chcp 65001
echo start all services...

REM Start the API gateway and srvices

REM Switch to the current directory.
cd /d %~dp0

echo Start conulting service
start "Conulting service" "services\consulting\start.bat"

echo Start API gateway
start "API gateway" "gateway\start.bat"

pause