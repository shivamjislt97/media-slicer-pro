@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  all-in-one-media-slicer  |  mega_upload.bat  |  v1.0.1
::  Uploads slices from a given folder to MEGA cloud
::
::  Usage (called from pipeline.bat):
::    mega_upload.bat  "C:\path\to\output\VideoName"  "VideoName"
::
::  Or run standalone — it will scan output\ for subfolders.
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."
set "OUTPUT_DIR=%ROOT%\output"

:: ── Locate MEGAcmd ──────────────────────────────────────────
set "MEGA_CMD="
set "MEGA_SERVER="

:: Common install paths
for %%P in (
    "%LOCALAPPDATA%\MEGAcmd\MEGAclient.exe"
    "%ProgramFiles%\MEGAcmd\MEGAclient.exe"
    "%ProgramFiles(x86)%\MEGAcmd\MEGAclient.exe"
) do (
    if exist %%P (
        set "MEGA_CMD=%%~P"
    )
)

for %%P in (
    "%LOCALAPPDATA%\MEGAcmd\MEGAcmdServer.exe"
    "%ProgramFiles%\MEGAcmd\MEGAcmdServer.exe"
    "%ProgramFiles(x86)%\MEGAcmd\MEGAcmdServer.exe"
) do (
    if exist %%P (
        set "MEGA_SERVER=%%~P"
    )
)

if not defined MEGA_CMD (
    echo  [MEGA] MEGAcmd not found on this system.
    echo  [MEGA] Install MEGAcmd from: https://mega.io/cmd
    echo  [MEGA] Skipping upload step.
    exit /b 0
)

echo  [MEGA] MEGAcmd detected: !MEGA_CMD!

:: ── Start MEGA server if not running ────────────────────────
tasklist /FI "IMAGENAME eq MEGAcmdServer.exe" 2>nul | find /I "MEGAcmdServer.exe" >nul
if !ERRORLEVEL! NEQ 0 (
    echo  [MEGA] Starting MEGAcmd server...
    start "" "!MEGA_SERVER!"
    timeout /t 5 /nobreak >nul
) else (
    echo  [MEGA] MEGAcmd server already running.
)

:: ── Verify login ────────────────────────────────────────────
"!MEGA_CMD!" whoami >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo  [MEGA] Not logged in to MEGA.
    echo  [MEGA] Run MEGAcmd manually and use: login your@email.com
    echo  [MEGA] Then re-run pipeline. Skipping upload.
    exit /b 0
)

for /f "tokens=*" %%U in ('"!MEGA_CMD!" whoami 2^>nul') do set "MEGA_USER=%%U"
echo  [MEGA] Logged in as: !MEGA_USER!

:: ── Determine upload target ─────────────────────────────────
::  If called with arguments: arg1=local folder, arg2=MEGA folder name
if not "%~1"=="" (
    set "LOCAL_FOLDER=%~1"
    set "MEGA_FOLDER_NAME=%~2"
    call :UPLOAD_FOLDER "!LOCAL_FOLDER!" "!MEGA_FOLDER_NAME!"
    exit /b !ERRORLEVEL!
)

:: ── Standalone mode: upload everything in output\ ───────────
echo  [MEGA] Standalone mode — scanning output\ for folders...
echo.
for /d %%D in ("%OUTPUT_DIR%\*") do (
    call :UPLOAD_FOLDER "%%D" "%%~nxD"
)
echo  [MEGA] All uploads complete.
exit /b 0


:: ════════════════════════════════════════════════════════════
:UPLOAD_FOLDER
::  %~1 = local folder path
::  %~2 = MEGA remote folder name
:: ════════════════════════════════════════════════════════════
set "LOCAL=%~1"
set "REMOTE_NAME=%~2"
set "MEGA_DEST=/all-in-one-media-slicer/%REMOTE_NAME%"

echo  [MEGA] Uploading folder : %REMOTE_NAME%
echo  [MEGA] Destination      : %MEGA_DEST%

:: Create remote folder (ignore error if already exists)
"!MEGA_CMD!" mkdir -p "%MEGA_DEST%" >nul 2>&1

:: Upload each .mp4 slice individually so we can report progress
set "UPLOAD_COUNT=0"
set "UPLOAD_FAIL=0"

for %%S in ("%LOCAL%\*.mp4") do (
    echo  [MEGA]   Uploading: %%~nxS ...
    "!MEGA_CMD!" put "%%S" "%MEGA_DEST%/" >nul 2>&1
    if !ERRORLEVEL!==0 (
        echo  [MEGA]   [OK] %%~nxS uploaded.
        set /a UPLOAD_COUNT+=1
    ) else (
        echo  [MEGA]   [FAIL] %%~nxS upload failed.
        set /a UPLOAD_FAIL+=1
    )
)

echo  [MEGA] Folder done — Uploaded: !UPLOAD_COUNT!  Failed: !UPLOAD_FAIL!
echo.
goto :EOF
