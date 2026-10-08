@echo off
title Build Standalone Windows EXE - FBR Digital Invoicing
color 0B
echo =================================================================
echo  Compiling Standalone Windows .EXE (with Embedded Database)
echo =================================================================
echo.
python build_exe.py
echo.
echo Process complete. Check dist\FBR_Digital_Invoicing folder.
pause
