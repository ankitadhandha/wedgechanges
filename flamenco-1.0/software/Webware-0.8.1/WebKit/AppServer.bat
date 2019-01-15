@echo off
:restart
python Launch.py ThreadedAppServer %1 %2 %3 %4 %5
if errorlevel 3 goto restart
