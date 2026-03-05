@echo off
setlocal EnableDelayedExpansion
set "FFMPEG=C:\Projects\media-slicer-pro\tools\ffmpeg.exe"
set "FFPROBE=C:\Projects\media-slicer-pro\tools\ffprobe.exe"
set "INPUT_DIR=C:\Projects\media-slicer-pro\input"
set "OUTPUT_DIR=C:\Projects\media-slicer-pro\output"
set "SLICE_DURATION=449"
if not exist "%FFMPEG%" (echo [ERROR] ffmpeg not found & pause & exit /b 1)
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
set "VIDEO_COUNT=0"
for %%F in ("%INPUT_DIR%\*.mp4" "%INPUT_DIR%\*.mkv" "%INPUT_DIR%\*.avi" "%INPUT_DIR%\*.mov") do (if exist "%%F" if not "%%~nxF"==".gitkeep" set /a VIDEO_COUNT+=1)
if %VIDEO_COUNT%==0 (echo [ERROR] No videos found & pause & exit /b 1)
echo [INFO] Found %VIDEO_COUNT% video(s)
for %%F in ("%INPUT_DIR%\*.mp4" "%INPUT_DIR%\*.mkv" "%INPUT_DIR%\*.avi" "%INPUT_DIR%\*.mov") do (if exist "%%F" if not "%%~nxF"==".gitkeep" call :PROCESS_VIDEO "%%F")
echo [DONE] All videos processed!
pause & exit /b 0
:PROCESS_VIDEO
set "VIDEO_PATH=%~1"
set "VIDEO_NAME=%~n1"
echo [VIDEO] %VIDEO_NAME%
for /f "delims=" %%D in ('"%FFPROBE%" -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%VIDEO_PATH%" 2^>^&1') do set "TOTAL_DURATION=%%D"
if not defined TOTAL_DURATION (echo [ERROR] Cannot read duration & goto :EOF)
for /f "tokens=1 delims=." %%I in ("!TOTAL_DURATION!") do set "TOTAL_INT=%%I"
set /a FULL_SLICES=!TOTAL_INT! / %SLICE_DURATION%
set /a REMAINDER=!TOTAL_INT! %% %SLICE_DURATION%
set /a TOTAL_SLICES=!FULL_SLICES!
if !REMAINDER! GTR 0 set /a TOTAL_SLICES=!FULL_SLICES! + 1
if !TOTAL_INT! LEQ %SLICE_DURATION% set "TOTAL_SLICES=1"
echo [INFO] Duration: !TOTAL_INT!s - Slices: !TOTAL_SLICES!
set "VIDEO_OUT=%OUTPUT_DIR%\%VIDEO_NAME%"
if not exist "!VIDEO_OUT!" mkdir "!VIDEO_OUT!"
set "PART=1"
set "START=0"
:SLICE_LOOP
if !PART! GTR !TOTAL_SLICES! goto :SLICE_DONE
set "SS=!START!"
if !PART!==!TOTAL_SLICES! (set "DURATION_FLAG=") else (set "DURATION_FLAG=-t %SLICE_DURATION%")
set "OUT_FILE=!VIDEO_OUT!\%VIDEO_NAME%_part_!PART!.mp4"
echo [SLICE !PART!/!TOTAL_SLICES!] start=!SS!s
"%FFMPEG%" -ss !SS! -i "%VIDEO_PATH%" !DURATION_FLAG! -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac -b:a 128k -avoid_negative_ts make_zero -reset_timestamps 1 -movflags +faststart -y "!OUT_FILE!" 2>> "!VIDEO_OUT!\slicer_log.txt"
if !ERRORLEVEL! NEQ 0 (echo [ERROR] Slice !PART! failed) else (echo [OK] Slice !PART! done)
set /a START=!START! + %SLICE_DURATION%
set /a PART=!PART! + 1
goto :SLICE_LOOP
:SLICE_DONE
echo [DONE] %VIDEO_NAME% - !TOTAL_SLICES! slices complete!
echo.
goto :EOF
