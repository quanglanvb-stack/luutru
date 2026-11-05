@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PY=py -3.15"

echo ============================================================
echo  QUANGLAN - BUILD Bieu Cat_Tao Marker Opitex V3
echo  Python 3.15
echo ============================================================
echo.

echo [0/7] Kiem tra source...
%PY% -c "from pathlib import Path; t=Path(r'Bieu_Cat_Tao_Marker_Opitex.py').read_text(encoding='utf-8-sig'); assert 'APP_VERSION = \"3.0.0\"' in t or 'APP_VERSION = \"3.' in t; print('SOURCE OK')"
if errorlevel 1 exit /b 40

echo [1/7] Kiem tra Python 3.15...
%PY% --version
if errorlevel 1 exit /b 11

echo [2/7] Kiem tra thu vien build...
%PY% -c "import PyInstaller, openpyxl, PIL" >nul 2>nul
if errorlevel 1 (
  echo Thieu thu vien. Dang cai PyInstaller, openpyxl, Pillow cho Python 3.15...
  %PY% -m pip install --upgrade pyinstaller openpyxl pillow
  if errorlevel 1 exit /b 12
)
%PY% -c "import PyInstaller, openpyxl, PIL; print('DEPENDENCIES OK')"
if errorlevel 1 exit /b 13

echo [3/7] Kiem tra cu phap...
%PY% -m py_compile "Bieu_Cat_Tao_Marker_Opitex.py"
if errorlevel 1 exit /b 21
%PY% -m py_compile "module_cut.py"
if errorlevel 1 exit /b 22
%PY% -m py_compile "module_marker.py"
if errorlevel 1 exit /b 23
%PY% -m py_compile "module_tem.py"
if errorlevel 1 exit /b 24

echo [4/7] Xoa build cu...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "Bieu_Cat_Tao_Marker_Opitex.spec" del /f /q "Bieu_Cat_Tao_Marker_Opitex.spec"

set "RUNTIME_TMP=."

echo [5/7] Build EXE...
%PY% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --noupx ^
  --runtime-tmpdir "%RUNTIME_TMP%" ^
  --name "Bieu_Cat_Tao_Marker_Opitex" ^
  --icon "QUANGLAN.ico" ^
  --collect-all openpyxl ^
  --collect-all PIL ^
  --collect-submodules tkinter ^
  --hidden-import tkinter ^
  --hidden-import tkinter.ttk ^
  --hidden-import tkinter.filedialog ^
  --hidden-import tkinter.messagebox ^
  --hidden-import tkinter.simpledialog ^
  --hidden-import module_cut ^
  --hidden-import module_marker ^
  --hidden-import module_tem ^
  "Bieu_Cat_Tao_Marker_Opitex.py"

if errorlevel 1 exit /b 31
if not exist "dist\Bieu_Cat_Tao_Marker_Opitex.exe" exit /b 32

echo [6/7] Tao SHA256...
for /f "tokens=*" %%H in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 '.\dist\Bieu_Cat_Tao_Marker_Opitex.exe').Hash.ToLower()"') do set "HASH=%%H"
echo %HASH%>"dist\Bieu_Cat_Tao_Marker_Opitex.sha256.txt"

echo [7/7] Hoan tat.
exit /b 0
