@echo off
rem imgops shim: apunta duro al .venv del repo (garantia de interprete, sin MCP).
setlocal
set PYTHONUTF8=1
"%~dp0.venv\Scripts\python.exe" "%~dp0cli.py" %*
