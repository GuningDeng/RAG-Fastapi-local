@echo off
chcp 65001
echo start consulting service

REM Switch to the current directory.
cd /d %~dp0

echo Activate virtual environment...
call .venv\Scripts\activate

echo Start consulting service...
python "main.py"