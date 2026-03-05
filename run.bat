@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  media-slicer-pro  |  run.bat  |  v1.0.1
::  Main entry point - double click to run
:: ============================================================

set "ROOT=C:\Projects\media-slicer-pro"
set "PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"

:: Auto detect Python if not found
if not exist "!PYTHON!" (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "C:\Python312\python.exe"
    ) do (
        if exist %%P set "PYTHON=%%~P"
    )
)

cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           media-slicer-pro  v1.0.1                  ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Input  : %ROOT%\input\
echo  Output : %ROOT%\output\
echo.
echo  ════════════════════════════════════════════════════════
echo  Select an option:
echo  ════════════════════════════════════════════════════════
echo.
echo    [1]  Slicing Only
echo         (No upload - just cut video into parts)
echo.
echo    [2]  Slicing + MEGA Auto Upload
echo         (Cut video into parts AND upload to MEGA)
echo.
echo    [3]  Exit
echo.
echo  ════════════════════════════════════════════════════════
echo.
set /p "CHOICE=  Enter your choice (1/2/3): "

if "!CHOICE!"=="1" goto :SLICE_ONLY
if "!CHOICE!"=="2" goto :SLICE_UPLOAD
if "!CHOICE!"=="3" goto :EXIT

echo.
echo  [ERROR] Invalid choice. Please enter 1, 2 or 3.
echo.
pause
goto :EOF

:: ════════════════════════════════════════════════════════════
:SLICE_ONLY
:: ════════════════════════════════════════════════════════════
cls
echo.
echo  [MODE] Slicing Only - No Upload
echo  ════════════════════════════════════════════════════════
echo.
"!PYTHON!" "%ROOT%\scripts\slicer.py"
goto :DONE

:: ════════════════════════════════════════════════════════════
:SLICE_UPLOAD
:: ════════════════════════════════════════════════════════════
cls
echo.
echo  [MODE] Slicing + MEGA Auto Upload
echo  ════════════════════════════════════════════════════════
echo.
"!PYTHON!" "%ROOT%\scripts\pipeline.py"
goto :DONE

:: ════════════════════════════════════════════════════════════
:DONE
:: ════════════════════════════════════════════════════════════
echo.
echo  ════════════════════════════════════════════════════════
echo  [DONE] Check output folder:
echo  %ROOT%\output\
echo  ════════════════════════════════════════════════════════
echo.
pause
goto :EOF

:: ════════════════════════════════════════════════════════════
:EXIT
:: ════════════════════════════════════════════════════════════
echo.
echo  Goodbye!
echo.
exit /b 0
