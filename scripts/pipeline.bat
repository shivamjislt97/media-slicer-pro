@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  all-in-one-media-slicer  |  pipeline.bat  |  v1.0.1
::
::  Master entry point:
::    1. Slices every video in \input  (449 s per part)
::    2. After EACH video's slices are done, optionally uploads
::       them to MEGA if MEGAcmd is installed
::
::  Double-click this file to run the full pipeline.
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."
set "FFMPEG=%ROOT%\tools\ffmpeg.exe"
set "FFPROBE=%ROOT%\tools\ffprobe.exe"
set "INPUT_DIR=%ROOT%\input"
set "OUTPUT_DIR=%ROOT%\output"
set "SLICE_DURATION=449"

cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║        all-in-one-media-slicer  v1.0.1              ║
echo  ║        Slice + (Optional) MEGA Upload Pipeline      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Root    : %ROOT%
echo  Input   : %INPUT_DIR%
echo  Output  : %OUTPUT_DIR%
echo  Slice   : %SLICE_DURATION% seconds per part
echo.

:: ── Validate tools ──────────────────────────────────────────
if not exist "%FFMPEG%" (
    echo [ERROR] ffmpeg.exe not found at: %FFMPEG%
    echo         Place ffmpeg.exe inside the tools\ folder.
    pause
    exit /b 1
)
if not exist "%FFPROBE%" (
    echo [ERROR] ffprobe.exe not found at: %FFPROBE%
    echo         Place ffprobe.exe inside the tools\ folder.
    pause
    exit /b 1
)

:: ── Validate input folder ───────────────────────────────────
if not exist "%INPUT_DIR%" mkdir "%INPUT_DIR%"

:: ── Create output folder ────────────────────────────────────
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

:: ── Detect MEGAcmd (optional) ───────────────────────────────
set "MEGA_CMD="
set "MEGA_SERVER="
set "MEGA_AVAILABLE=0"

for %%P in (
    "%LOCALAPPDATA%\MEGAcmd\MEGAclient.exe"
    "%ProgramFiles%\MEGAcmd\MEGAclient.exe"
    "%ProgramFiles(x86)%\MEGAcmd\MEGAclient.exe"
) do (
    if exist %%P set "MEGA_CMD=%%~P"
)

for %%P in (
    "%LOCALAPPDATA%\MEGAcmd\MEGAcmdServer.exe"
    "%ProgramFiles%\MEGAcmd\MEGAcmdServer.exe"
    "%ProgramFiles(x86)%\MEGAcmd\MEGAcmdServer.exe"
) do (
    if exist %%P set "MEGA_SERVER=%%~P"
)

if defined MEGA_CMD (
    set "MEGA_AVAILABLE=1"
    echo  [MEGA] MEGAcmd detected — upload enabled.
) else (
    echo  [MEGA] MEGAcmd not found — upload step will be skipped.
)
echo.

:: ── Collect video list ──────────────────────────────────────
set "VIDEO_COUNT=0"
for %%F in ("%INPUT_DIR%\*.mp4" "%INPUT_DIR%\*.mkv" "%INPUT_DIR%\*.avi" "%INPUT_DIR%\*.mov" "%INPUT_DIR%\*.wmv" "%INPUT_DIR%\*.flv" "%INPUT_DIR%\*.webm") do (
    if exist "%%F" set /a VIDEO_COUNT+=1
)

if %VIDEO_COUNT%==0 (
    echo  [ERROR] No supported video files found in input\
    echo          Supported: mp4, mkv, avi, mov, wmv, flv, webm
    pause
    exit /b 1
)

echo  [INFO] %VIDEO_COUNT% video(s) queued for processing.
echo.

:: ── Start MEGA server once (if available) ───────────────────
if !MEGA_AVAILABLE!==1 (
    tasklist /FI "IMAGENAME eq MEGAcmdServer.exe" 2>nul | find /I "MEGAcmdServer.exe" >nul
    if !ERRORLEVEL! NEQ 0 (
        echo  [MEGA] Starting MEGAcmd server...
        start "" "!MEGA_SERVER!"
        timeout /t 5 /nobreak >nul
    )
    :: Verify login
    "!MEGA_CMD!" whoami >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo  [MEGA] WARNING: Not logged in to MEGA.
        echo  [MEGA]          Open MEGAcmd and run: login your@email.com
        echo  [MEGA]          Upload will be skipped this run.
        set "MEGA_AVAILABLE=0"
    ) else (
        for /f "tokens=*" %%U in ('"!MEGA_CMD!" whoami 2^>nul') do set "MEGA_USER=%%U"
        echo  [MEGA] Logged in as: !MEGA_USER!
    )
    echo.
)

:: ── Process each video (slice then upload) ───────────────────
for %%F in ("%INPUT_DIR%\*.mp4" "%INPUT_DIR%\*.mkv" "%INPUT_DIR%\*.avi" "%INPUT_DIR%\*.mov" "%INPUT_DIR%\*.wmv" "%INPUT_DIR%\*.flv" "%INPUT_DIR%\*.webm") do (
    if exist "%%F" (
        call :PIPELINE_VIDEO "%%F"
    )
)

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   Pipeline complete!  Check output\ for your files. ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
pause
exit /b 0


:: ════════════════════════════════════════════════════════════
:PIPELINE_VIDEO
::  Full pipeline for a single video: slice → upload
:: ════════════════════════════════════════════════════════════
set "VIDEO_PATH=%~1"
set "VIDEO_NAME=%~n1"
set "VIDEO_EXT=%~x1"

echo ══════════════════════════════════════════════════════════
echo  PROCESSING: %VIDEO_NAME%%VIDEO_EXT%
echo ══════════════════════════════════════════════════════════

:: ── Get duration ────────────────────────────────────────────
for /f "delims=" %%D in (
    '"%FFPROBE%" -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%VIDEO_PATH%" 2^>^&1'
) do set "TOTAL_DURATION=%%D"

if not defined TOTAL_DURATION (
    echo  [ERROR] Cannot read duration. Skipping %VIDEO_NAME%.
    goto :EOF
)

for /f "tokens=1 delims=." %%I in ("!TOTAL_DURATION!") do set "TOTAL_INT=%%I"

set /a FULL_SLICES=!TOTAL_INT! / %SLICE_DURATION%
set /a REMAINDER=!TOTAL_INT! %% %SLICE_DURATION%
set /a TOTAL_SLICES=!FULL_SLICES!
if !REMAINDER! GTR 0 set /a TOTAL_SLICES=!FULL_SLICES! + 1
if !TOTAL_INT! LEQ %SLICE_DURATION% set "TOTAL_SLICES=1"

echo  Duration : !TOTAL_INT! s   Slices: !TOTAL_SLICES!
echo.

:: ── Create output subfolder ─────────────────────────────────
set "VIDEO_OUT=%OUTPUT_DIR%\%VIDEO_NAME%"
if not exist "!VIDEO_OUT!" mkdir "!VIDEO_OUT!"

:: ── Slice loop with per-slice MEGA upload ───────────────────
set "PART=1"
set "START=0"

:PIPELINE_LOOP
if !PART! GTR !TOTAL_SLICES! goto :PIPELINE_DONE

set "SS=!START!"
if !PART!==!TOTAL_SLICES! (
    set "DURATION_FLAG="
) else (
    set "DURATION_FLAG=-t %SLICE_DURATION%"
)

set "OUT_FILE=!VIDEO_OUT!\%VIDEO_NAME%_part_!PART!.mp4"

echo  [SLICE !PART!/!TOTAL_SLICES!]  Encoding...
echo    Output: !OUT_FILE!

"%FFMPEG%" ^
    -ss !SS! ^
    -i "%VIDEO_PATH%" ^
    !DURATION_FLAG! ^
    -c:v libx264 ^
    -crf 18 ^
    -preset slow ^
    -pix_fmt yuv420p ^
    -c:a aac ^
    -b:a 128k ^
    -avoid_negative_ts make_zero ^
    -reset_timestamps 1 ^
    -movflags +faststart ^
    -y ^
    "!OUT_FILE!" ^
    2>> "!VIDEO_OUT!\pipeline_log.txt"

if !ERRORLEVEL! NEQ 0 (
    echo  [ERROR] Encoding failed for slice !PART!. See pipeline_log.txt
) else (
    echo  [OK]    Slice !PART! encoded.

    :: ── Upload this slice immediately if MEGA is available ──
    if !MEGA_AVAILABLE!==1 (
        set "MEGA_DEST=/all-in-one-media-slicer/%VIDEO_NAME%"
        "!MEGA_CMD!" mkdir -p "!MEGA_DEST!" >nul 2>&1
        echo  [MEGA]  Uploading %VIDEO_NAME%_part_!PART!.mp4 ...
        "!MEGA_CMD!" put "!OUT_FILE!" "!MEGA_DEST!/" >nul 2>&1
        if !ERRORLEVEL!==0 (
            echo  [MEGA]  [OK] Uploaded.
        ) else (
            echo  [MEGA]  [FAIL] Upload failed for part !PART!.
        )
    )
)

set /a START=!START! + %SLICE_DURATION%
set /a PART=!PART! + 1
goto :PIPELINE_LOOP

:PIPELINE_DONE
echo.
echo  [DONE] %VIDEO_NAME% — !TOTAL_SLICES! slice(s) processed.
echo.
goto :EOF
