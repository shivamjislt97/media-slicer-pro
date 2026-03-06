@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  media-slicer-pro  |  setup.bat  |  v2.0.1
::  One-click setup - Run Once Only
:: ============================================================

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "TOOLS=%ROOT%\tools"
set "SCRIPTS=%ROOT%\scripts"

cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║       media-slicer-pro  -  Setup v2.0.1            ║
echo  ║       One-Click Automatic Setup                     ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Installing:
echo    [1] Python 3.12
echo    [2] FFmpeg + FFprobe
echo    [3] MEGAcmd
echo    [4] MEGA Login
echo    [5] Create run.bat
echo.
echo  Please wait...
echo.

:: ════════════════════════════════════════════════════════════
echo [STEP 1/5] Python...
:: ════════════════════════════════════════════════════════════

set "PYTHON="
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
    echo  [INFO] Installing Python...
    winget install Python.Python.3.12 --source winget --silent --accept-package-agreements --accept-source-agreements
    timeout /t 8 /nobreak >nul

    :: Refresh PATH
    for /f "tokens=*" %%P in ('where python 2^>nul') do set "PYTHON=%%P"

    :: Check common paths again
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "C:\Python312\python.exe"
    ) do (
        if exist %%P set "PYTHON=%%~P"
    )
)

if defined PYTHON (
    echo  [OK] Python: !PYTHON!
) else (
    echo  [WARN] Python path not detected yet - will retry later
)

:: ════════════════════════════════════════════════════════════
echo.
echo [STEP 2/5] FFmpeg...
:: ════════════════════════════════════════════════════════════

if exist "%TOOLS%\ffmpeg.exe" (
    echo  [OK] FFmpeg already exists.
) else (
    if not exist "%TOOLS%" mkdir "%TOOLS%"
    echo  [INFO] Downloading FFmpeg ~110MB...

    powershell -Command "try { Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'C:\ffmpeg_setup.zip' -UseBasicParsing } catch { exit 1 }"

    if exist "C:\ffmpeg_setup.zip" (
        echo  [INFO] Extracting FFmpeg...
        powershell -Command "Expand-Archive -Path 'C:\ffmpeg_setup.zip' -DestinationPath 'C:\ffmpeg_temp' -Force"
        for /d %%D in ("C:\ffmpeg_temp\ffmpeg-*") do (
            copy "%%D\bin\ffmpeg.exe" "%TOOLS%\" >nul 2>&1
            copy "%%D\bin\ffprobe.exe" "%TOOLS%\" >nul 2>&1
        )
        powershell -Command "Remove-Item -Path 'C:\ffmpeg_temp' -Recurse -Force" >nul 2>&1
        del "C:\ffmpeg_setup.zip" >nul 2>&1

        if exist "%TOOLS%\ffmpeg.exe" (
            echo  [OK] FFmpeg installed!
        ) else (
            echo  [ERROR] FFmpeg install failed. Check internet connection.
        )
    ) else (
        echo  [ERROR] FFmpeg download failed. Check internet connection.
    )
)

:: ════════════════════════════════════════════════════════════
echo.
echo [STEP 3/5] MEGAcmd...
:: ════════════════════════════════════════════════════════════

set "MEGA_CMD="
for %%P in (
    "%LOCALAPPDATA%\MEGAcmd\MEGAclient.exe"
    "%ProgramFiles%\MEGAcmd\MEGAclient.exe"
    "%ProgramFiles(x86)%\MEGAcmd\MEGAclient.exe"
) do (
    if exist %%P set "MEGA_CMD=%%~P"
)

if defined MEGA_CMD (
    echo  [OK] MEGAcmd already installed: !MEGA_CMD!
) else (
    echo  [INFO] Installing MEGAcmd...
    powershell -Command "try { Invoke-WebRequest -Uri 'https://mega.nz/MEGAcmdSetup64.exe' -OutFile 'C:\MEGAcmdSetup64.exe' -UseBasicParsing } catch { exit 1 }"

    if exist "C:\MEGAcmdSetup64.exe" (
        start /wait "" "C:\MEGAcmdSetup64.exe" /S
        timeout /t 8 /nobreak >nul
        del "C:\MEGAcmdSetup64.exe" >nul 2>&1

        for %%P in (
            "%LOCALAPPDATA%\MEGAcmd\MEGAclient.exe"
            "%ProgramFiles%\MEGAcmd\MEGAclient.exe"
        ) do (
            if exist %%P set "MEGA_CMD=%%~P"
        )

        if defined MEGA_CMD (
            echo  [OK] MEGAcmd installed!
        ) else (
            echo  [WARN] MEGAcmd install failed. Upload will be skipped.
        )
    ) else (
        echo  [WARN] MEGAcmd download failed. Upload will be skipped.
    )
)

:: ════════════════════════════════════════════════════════════
echo.
echo [STEP 4/5] MEGA Login...
:: ════════════════════════════════════════════════════════════

if not defined MEGA_CMD (
    echo  [SKIP] MEGAcmd not available. Skipping login.
) else (
    "!MEGA_CMD!" whoami >nul 2>&1
    if !ERRORLEVEL!==0 (
        for /f "tokens=*" %%U in ('"!MEGA_CMD!" whoami 2^>nul') do set "MEGA_USER=%%U"
        echo  [OK] Already logged in: !MEGA_USER!
    ) else (
        echo.
        echo  Enter your MEGA credentials:
        echo.
        set /p "MEGA_EMAIL=  Email   : "
        set /p "MEGA_PASS=  Password: "
        echo.
        echo  [INFO] Logging in...
        "!MEGA_CMD!" login "!MEGA_EMAIL!" "!MEGA_PASS!"
        if !ERRORLEVEL!==0 (
            echo  [OK] MEGA login successful!
        ) else (
            echo  [WARN] Login failed. You can login later manually.
        )
    )
)

:: ════════════════════════════════════════════════════════════
echo.
echo [STEP 5/5] Creating run.bat...
:: ════════════════════════════════════════════════════════════

:: Re-detect Python one more time
if not defined PYTHON (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "C:\Python312\python.exe"
    ) do (
        if exist %%P set "PYTHON=%%~P"
    )
)

if not defined PYTHON (
    echo  [ERROR] Python not found. Please restart terminal and run setup.bat again.
    pause
    exit /b 1
)

(
    echo @echo off
    echo setlocal EnableDelayedExpansion
    echo set "ROOT=%ROOT%"
    echo set "PYTHON=!PYTHON!"
    echo set "SLICE_DURATION=449"
    echo :MAIN_MENU
    echo cls
    echo echo.
    echo echo  ╔══════════════════════════════════════════════════════╗
    echo echo  ║           media-slicer-pro  v2.0.1                  ║
    echo echo  ╚══════════════════════════════════════════════════════╝
    echo echo.
    echo echo  Input   : %ROOT%\input\
    echo echo  Output  : %ROOT%\output\
    echo echo  Slice   : %%SLICE_DURATION%% seconds per part
    echo echo.
    echo echo  ════════════════════════════════════════════════════════
    echo echo   SELECT AN OPTION:
    echo echo  ════════════════════════════════════════════════════════
    echo echo.
    echo echo    [1]  Slicing Only
    echo echo    [2]  Slicing + MEGA Auto Upload
    echo echo    [3]  Change Slice Duration     ^(Current: %%SLICE_DURATION%%s^)
    echo echo    [4]  Specific Duration Trimmer
    echo echo    [5]  Custom Multiple Slices
    echo echo    [6]  Clip Merger
    echo echo    [7]  Audio Extractor
    echo echo    [8]  Exit
    echo echo.
    echo echo  ════════════════════════════════════════════════════════
    echo echo.
    echo set /p "CHOICE=  Enter your choice ^(1-8^): "
    echo if "%%CHOICE%%"=="1" "!PYTHON!" "%SCRIPTS%\slicer.py" %%SLICE_DURATION%%
    echo if "%%CHOICE%%"=="2" "!PYTHON!" "%SCRIPTS%\pipeline.py" %%SLICE_DURATION%%
    echo if "%%CHOICE%%"=="3" goto :CHANGE_DUR
    echo if "%%CHOICE%%"=="4" goto :TRIMMER
    echo if "%%CHOICE%%"=="5" goto :CUSTOM
    echo if "%%CHOICE%%"=="6" "!PYTHON!" "%SCRIPTS%\merger.py"
    echo if "%%CHOICE%%"=="7" goto :AUDIO
    echo if "%%CHOICE%%"=="8" exit /b 0
    echo goto :MAIN_MENU
    echo :CHANGE_DUR
    echo set /p "SLICE_DURATION=  Enter seconds: "
    echo goto :MAIN_MENU
    echo :TRIMMER
    echo set /p "TF=  Video filename: "
    echo set /p "TS=  Start time: "
    echo set /p "TE=  End time: "
    echo "!PYTHON!" "%SCRIPTS%\trimmer.py" "%%TF%%" "%%TS%%" "%%TE%%"
    echo goto :MAIN_MENU
    echo :CUSTOM
    echo set /p "CF=  Video filename: "
    echo set "CTS="
    echo set "N=0"
    echo :CL
    echo set /a N+=1
    echo set /p "CT=  Slice %%N%% ^(START,END or DONE^): "
    echo if /i "%%CT%%"=="DONE" goto :CD
    echo set "CTS=%%CTS%% %%CT%%"
    echo goto :CL
    echo :CD
    echo "!PYTHON!" "%SCRIPTS%\custom_slicer.py" "%%CF%%" %%CTS%%
    echo goto :MAIN_MENU
    echo :AUDIO
    echo set /p "AF=  Video filename: "
    echo set /p "AFMT=  Format ^(mp3/aac^): "
    echo set /p "AS=  Start ^(blank=full^): "
    echo set /p "AE=  End ^(blank=full^): "
    echo "!PYTHON!" "%SCRIPTS%\audio_extractor.py" "%%AF%%" "%%AFMT%%" "%%AS%%" "%%AE%%"
    echo goto :MAIN_MENU
) > "%ROOT%\run.bat"

echo  [OK] run.bat created!

:: ════════════════════════════════════════════════════════════
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║              Setup Complete!  ✓                     ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  HOW TO USE:
echo  ─────────────────────────────────────────────────────
echo  1. Put video(s) in : %ROOT%\input\
echo  2. Double-click    : %ROOT%\run.bat
echo  ─────────────────────────────────────────────────────
echo.
pause
exit /b 0
