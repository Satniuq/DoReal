@echo off
setlocal
cd /d %~dp0
python 08_scripts\cli.py --project-root C:\Users\JoseVitorinoQuintas\DoReal run-all --steps 20
endlocal
