@echo off
echo Starting HandGesture Studio...
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
start http://localhost:8000
pause
