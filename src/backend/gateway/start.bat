@echo off
chcp 65001
echo start API gateway

REM Switch to the current directory.
cd /d %~dp0

echo Activate virtual environment...
call .venv\Scripts\activate

echo Start API gateway...
python "api gateway.py"