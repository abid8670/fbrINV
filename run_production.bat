@echo off
title FBR Digital Invoicing System - Production Server
color 02

echo =========================================================================
echo  FBR DIGITAL INVOICING (DI) SYSTEM - PRODUCTION WSGI SERVER
echo =========================================================================
echo.
echo Starting Multi-Threaded Production Server...
echo.

python server_production.py

pause
