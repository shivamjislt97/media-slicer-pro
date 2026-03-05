@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  media-slicer-pro  |  setup.bat  |  v1.0.1
::  Run this ONCE to set up everything automatically
:: ============================================================

set "ROOT=C:\Projects\media-slicer-pro"
set "TOOLS=%ROOT%\tools"
set "SCRIPTS=%ROOT%\scripts"
set "PYTHON="
set "MEGA_CMD="

cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║          media-slicer-pro  -  Setup v1.0.1          ║
echo  ║          First Time Setup - Run Once Only           ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  This will:
echo    [1] Check / Install Python
echo    [2] Download FFmpeg automatically
echo    [3] Check / Install MEGAcmd
echo    [4] Login to MEGA
echo    [5] Create run.bat for daily use
echo.
pause

:: ════════════════════════════════════════════════════════════
echo.
echo  [STEP 1/5] Checking Python...
echo  ════════════════════════════════════════════════════════
:: ════════════════════════════════════════════════════════════

for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
) do (
    if exist %%P set "PYTHON=%%~P"
)

if not defined PYTHON (
    echo  [INFO] Python not found. Installing...
    winget install Python.Python.3.12 --source winget
    timeout /t 5 /nobreak >nul
    set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    echo  [INFO] Please close and reopen this window after install.
    echo  [INFO] Then run setup.bat again.
    pause
    exit /b 0
) else (
    echo  [OK] Python found: !PYTHON!
)

:: ════════════════════════════════════════════════════════════
echo.
echo  [STEP 2/5] Setting up FFmpeg...
echo  ════════════════════════════════════════════════════════
:: ════════════════════════════════════════════════════════════

if exist "%TOOLS%\ffmpeg.exe" (
    echo  [OK] FFmpeg already exists. Skipping download.
) else (
    echo  [INFO] Downloading FFmpeg ~110MB, please wait...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'C:\ffmpeg_setup.zip'"
    
    if not exist "C:\ffmpeg_setup.zip" (
        echo  [ERROR] FFmpeg download failed. Check internet connection.
        pause
        exit /b 1
    )
    
    echo  [INFO] Extracting FFmpeg...
    powershell -Command "Expand-Archive -Path 'C:\ffmpeg_setup.zip' -DestinationPath 'C:\ffmpeg_temp' -Force"
    
    if not exist "%TOOLS%" mkdir "%TOOLS%"
    
    for /d %%D in ("C:\ffmpeg_temp\ffmpeg-*") do (
        copy "%%D\bin\ffmpeg.exe" "%TOOLS%\" >nul
        copy "%%D\bin\ffprobe.exe" "%TOOLS%\" >nul
    )
    
    powershell -Command "Remove-Item -Path 'C:\ffmpeg_temp' -Recurse -Force"
    del "C:\ffmpeg_setup.zip" >nul 2>&1
    
    if exist "%TOOLS%\ffmpeg.exe" (
        echo  [OK] FFmpeg installed successfully!
    ) else (
        echo  [ERROR] FFmpeg installation failed.
        pause
        exit /b 1
    )
)

:: ════════════════════════════════════════════════════════════
echo.
echo  [STEP 3/5] Checking MEGAcmd...
echo  ════════════════════════════════════════════════════════
:: ════════════════════════════════════════════════════════════

for %%P in (
    "%LOCALAPPDATA%\MEGAcmd\MEGAclient.exe"
    "%ProgramFiles%\MEGAcmd\MEGAclient.exe"
    "%ProgramFiles(x86)%\MEGAcmd\MEGAclient.exe"
) do (
    if exist %%P set "MEGA_CMD=%%~P"
)

if not defined MEGA_CMD (
    echo  [INFO] MEGAcmd not found. Installing...
    powershell -Command "Invoke-WebRequest -Uri 'https://mega.nz/MEGAcmdSetup64.exe' -OutFile 'C:\MEGAcmdSetup64.exe'"
    start /wait "C:\MEGAcmdSetup64.exe" /S
    del "C:\MEGAcmdSetup64.exe" >nul 2>&1
    timeout /t 5 /nobreak >nul
    set "MEGA_CMD=%LOCALAPPDATA%\MEGAcmd\MEGAclient.exe"
    echo  [OK] MEGAcmd installed!
) else (
    echo  [OK] MEGAcmd found: !MEGA_CMD!
)

:: ════════════════════════════════════════════════════════════
echo.
echo  [STEP 4/5] MEGA Login...
echo  ════════════════════════════════════════════════════════
:: ════════════════════════════════════════════════════════════

:: Check if already logged in
"!MEGA_CMD!" whoami >nul 2>&1
if !ERRORLEVEL!==0 (
    for /f "tokens=*" %%U in ('"!MEGA_CMD!" whoami 2^>nul') do set "MEGA_USER=%%U"
    echo  [OK] Already logged in as: !MEGA_USER!
) else (
    echo.
    echo  Enter your MEGA credentials:
    echo.
    set /p "MEGA_EMAIL=  Email: "
    set /p "MEGA_PASS=  Password: "
    echo.
    echo  [INFO] Logging in to MEGA...
    "!MEGA_CMD!" login "!MEGA_EMAIL!" "!MEGA_PASS!"
    
    if !ERRORLEVEL!==0 (
        echo  [OK] MEGA login successful!
    ) else (
        echo  [WARN] MEGA login failed. Upload will be skipped.
        echo  [WARN] You can login later manually and re-run setup.
    )
)

:: ════════════════════════════════════════════════════════════
echo.
echo  [STEP 5/5] Creating run.bat...
echo  ════════════════════════════════════════════════════════
:: ════════════════════════════════════════════════════════════

(
    echo @echo off
    echo echo  Starting media-slicer-pro...
    echo echo  Input folder: %ROOT%\input
    echo echo  Output folder: %ROOT%\output
    echo echo.
    echo "!PYTHON!" "%SCRIPTS%\pipeline.py"
    echo pause
) > "%ROOT%\run.bat"

echo  [OK] run.bat created at: %ROOT%\run.bat

:: ════════════════════════════════════════════════════════════
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║              Setup Complete!                        ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  HOW TO USE:
echo  ───────────────────────────────────────────────────────
echo  1. Put your video(s) in:
echo     %ROOT%\input\
echo.
echo  2. Double-click:
echo     %ROOT%\run.bat
echo.
echo  3. Done! Slices will appear in:
echo     %ROOT%\output\
echo.
echo  MEGA Upload: Automatic after each slice
echo  ───────────────────────────────────────────────────────
echo.
pause
exit /b 0
