@echo off
cd /d "%~dp0"
pip install -e ".[dev]" -q
python -m src.main --kr-alpha-weight 31
pause
