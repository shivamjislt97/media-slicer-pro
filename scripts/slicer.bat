@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  all-in-one-media-slicer  |  slicer.bat  |  v1.0.1
::  Slices every video in \input into 449-second parts
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."
set "FFMPEG=%ROOT%\tools\ffmpeg.exe"
set "FFPROBE=%ROOT%\tools\ffprobe.exe"
set "INPUT_DIR=%ROOT%\input"
set "OUTPUT_DIR=%ROOT%\output"
set "SLICE_DURATION=449"

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
if not exist "%INPUT_DIR%" (
    echo [ERROR] input\ folder not found.
    pause
    exit /b 1
)

:: ── Create output folder ────────────────────────────────────
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

:: ── Collect video files ─────────────────────────────────────
set "VIDEO_COUNT=0"
for %%F in ("%INPUT_DIR%\*.mp4" "%INPUT_DIR%\*.mkv" "%INPUT_DIR%\*.avi" "%INPUT_DIR%\*.mov" "%INPUT_DIR%\*.wmv" "%INPUT_DIR%\*.flv" "%INPUT_DIR%\*.webm") do (
    if exist "%%F" set /a VIDEO_COUNT+=1
)

if %VIDEO_COUNT%==0 (
    echo [ERROR] No supported video files found in input\ folder.
    echo         Supported formats: mp4, mkv, avi, mov, wmv, flv, webm
    pause
    exit /b 1
)

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║    all-in-one-media-slicer  v1.0.1       ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  [INFO] Found %VIDEO_COUNT% video(s) in input\
echo  [INFO] Slice duration: %SLICE_DURATION% seconds
echo  [INFO] Output folder : %OUTPUT_DIR%
echo.

:: ── Process each video ──────────────────────────────────────
for %%F in ("%INPUT_DIR%\*.mp4" "%INPUT_DIR%\*.mkv" "%INPUT_DIR%\*.avi" "%INPUT_DIR%\*.mov" "%INPUT_DIR%\*.wmv" "%INPUT_DIR%\*.flv" "%INPUT_DIR%\*.webm") do (
    if exist "%%F" call :PROCESS_VIDEO "%%F"
)

echo.
echo  [DONE] All videos processed successfully.
echo.
pause
exit /b 0


:: ════════════════════════════════════════════════════════════
:PROCESS_VIDEO
:: %~1 = full path to video file
:: ════════════════════════════════════════════════════════════
set "VIDEO_PATH=%~1"
set "VIDEO_NAME=%~n1"
set "VIDEO_EXT=%~x1"

echo ──────────────────────────────────────────────────────────
echo  [VIDEO] %VIDEO_NAME%%VIDEO_EXT%
echo ──────────────────────────────────────────────────────────

:: ── Get total duration via ffprobe ──────────────────────────
for /f "delims=" %%D in (
    '"%FFPROBE%" -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%VIDEO_PATH%" 2^>^&1'
) do set "TOTAL_DURATION=%%D"

if not defined TOTAL_DURATION (
    echo  [ERROR] Could not read duration for: %VIDEO_NAME%
    goto :EOF
)

:: Strip decimal for integer math (floor)
for /f "tokens=1 delims=." %%I in ("!TOTAL_DURATION!") do set "TOTAL_INT=%%I"

echo  [INFO] Total duration : !TOTAL_INT! seconds (~!TOTAL_DURATION! s)

:: ── Calculate number of slices ───────────────────────────────
set /a FULL_SLICES=!TOTAL_INT! / %SLICE_DURATION%
set /a REMAINDER=!TOTAL_INT! %% %SLICE_DURATION%

:: If there is a remainder, add one more slice for the tail
set /a TOTAL_SLICES=%FULL_SLICES%
if !REMAINDER! GTR 0 set /a TOTAL_SLICES=%FULL_SLICES% + 1
if !TOTAL_INT! LEQ %SLICE_DURATION% set "TOTAL_SLICES=1"

echo  [INFO] Total slices   : !TOTAL_SLICES!
echo.

:: ── Create per-video output subfolder ───────────────────────
set "VIDEO_OUT=%OUTPUT_DIR%\%VIDEO_NAME%"
if not exist "!VIDEO_OUT!" mkdir "!VIDEO_OUT!"

:: ── Slice loop ───────────────────────────────────────────────
set "PART=1"
set "START=0"

:SLICE_LOOP
if !PART! GTR !TOTAL_SLICES! goto :SLICE_DONE

:: Determine this slice's start and duration
set "SS=!START!"

:: Last slice: let ffmpeg read to EOF (omit -t flag) for clean end
if !PART!==!TOTAL_SLICES! (
    set "DURATION_FLAG="
) else (
    set "DURATION_FLAG=-t %SLICE_DURATION%"
)

set "OUT_FILE=!VIDEO_OUT!\%VIDEO_NAME%_part_!PART!.mp4"

echo  [SLICE !PART!/!TOTAL_SLICES!]  start=!SS!s  ^> !OUT_FILE!

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
    2>> "!VIDEO_OUT!\slicer_log.txt"

if !ERRORLEVEL! NEQ 0 (
    echo  [ERROR] FFmpeg failed on slice !PART!. Check slicer_log.txt
) else (
    echo  [OK]    Slice !PART! complete.
)

:: Advance counters
set /a START=!START! + %SLICE_DURATION%
set /a PART=!PART! + 1
goto :SLICE_LOOP

:SLICE_DONE
echo.
echo  [INFO] Finished: %VIDEO_NAME%  (!TOTAL_SLICES! slices^)
echo.
goto :EOF
