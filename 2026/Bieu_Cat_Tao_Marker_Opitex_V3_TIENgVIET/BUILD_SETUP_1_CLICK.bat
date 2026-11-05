@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title QUANGLAN - BUILD SETUP V3

call "%~dp0BUILD_EXE_CORE.bat"
if errorlevel 1 goto :FAIL

set "ISCC="
for %%P in (
  "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
  "%ProgramFiles%\Inno Setup 6\ISCC.exe"
  "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) do (
  if exist %%P set "ISCC=%%~P"
)

if not defined ISCC (
  where ISCC.exe >nul 2>nul
  if not errorlevel 1 set "ISCC=ISCC.exe"
)

if not defined ISCC (
  echo Khong tim thay Inno Setup 6.
  pause
  exit /b 1
)

"%ISCC%" "%~dp0BIEU_CAT_TAO_MARKER_OPITEX_SETUP.iss"
if errorlevel 1 goto :FAIL

echo.
echo SETUP DA TAO:
echo %CD%\dist_setup\SETUP_Bieu_Cat_Tao_Marker_Opitex.exe
explorer "%CD%\dist_setup"
pause
exit /b 0

:FAIL
echo.
echo BUILD SETUP THAT BAI.
pause
exit /b 1
