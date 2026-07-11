@echo off
cd /d "%~dp0"
pip install -e ".[data,dev]" -q
python -m src.collect_main --scope holdings
python -m src.main --kr-alpha-weight 31
pause
