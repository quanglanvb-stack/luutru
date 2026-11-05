@echo off
setlocal
cd /d "%~dp0"
title QUANGLAN - BUILD Bieu Cat_Tao Marker Opitex V3

call "%~dp0BUILD_EXE_CORE.bat"
if errorlevel 1 goto :FAIL

echo.
echo BUILD THANH CONG:
echo %CD%\dist\Bieu_Cat_Tao_Marker_Opitex.exe
explorer "%CD%\dist"
pause
exit /b 0

:FAIL
echo.
echo BUILD THAT BAI. Ma loi: %errorlevel%
pause
exit /b 1
