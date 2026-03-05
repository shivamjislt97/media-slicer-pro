@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  media-slicer-pro  |  run.bat  |  v2.0.1
::  Main entry point - double click to run
:: ============================================================

set "ROOT=C:\Projects\media-slicer-pro"
set "SLICE_DURATION=449"

:: Auto detect Python
set "PYTHON="
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python312\python.exe"
) do (
    if exist %%P set "PYTHON=%%~P"
)

if not defined PYTHON (
    echo [ERROR] Python not found. Please run setup.bat first.
    pause & exit /b 1
)

:MAIN_MENU
cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           media-slicer-pro  v2.0.1                  ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Input   : %ROOT%\input\
echo  Output  : %ROOT%\output\
echo  Merger  : %ROOT%\merger\
echo  Slice   : %SLICE_DURATION% seconds per part
echo.
echo  ════════════════════════════════════════════════════════
echo   SELECT AN OPTION:
echo  ════════════════════════════════════════════════════════
echo.
echo    [1]  Slicing Only
echo         Cut video into equal parts - no upload
echo.
echo    [2]  Slicing + MEGA Auto Upload
echo         Cut video into parts + upload to MEGA
echo.
echo    [3]  Change Slice Duration
echo         Current: %SLICE_DURATION% seconds per part
echo.
echo    [4]  Specific Duration Trimmer
echo         Extract one clip from a video (start to end^)
echo.
echo    [5]  Custom Multiple Slices
echo         Extract multiple clips with custom timestamps
echo.
echo    [6]  Clip Merger
echo         Merge all clips in merger\ folder into one
echo.
echo    [7]  Audio Extractor
echo         Extract audio from video (MP3 or AAC^)
echo.
echo    [8]  Exit
echo.
echo  ════════════════════════════════════════════════════════
echo.
set /p "CHOICE=  Enter your choice (1-8): "

if "!CHOICE!"=="1" goto :SLICE_ONLY
if "!CHOICE!"=="2" goto :SLICE_UPLOAD
if "!CHOICE!"=="3" goto :CHANGE_DURATION
if "!CHOICE!"=="4" goto :TRIMMER
if "!CHOICE!"=="5" goto :CUSTOM_SLICES
if "!CHOICE!"=="6" goto :MERGER
if "!CHOICE!"=="7" goto :AUDIO
if "!CHOICE!"=="8" goto :EXIT

echo.
echo  [ERROR] Invalid choice. Enter 1-8.
timeout /t 2 /nobreak >nul
goto :MAIN_MENU


:: ════════════════════════════════════════════════════════════
:CHANGE_DURATION
:: ════════════════════════════════════════════════════════════
cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           Change Slice Duration                     ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Current : %SLICE_DURATION% seconds
echo.
echo  Examples:
echo    449  = 7 min 29 sec  (default^)
echo    300  = 5 minutes
echo    600  = 10 minutes
echo    900  = 15 minutes
echo    1800 = 30 minutes
echo    3600 = 1 hour
echo.
set /p "NEW_DURATION=  Enter new duration in seconds: "
if "!NEW_DURATION!"=="" goto :MAIN_MENU
set /a "TEST=!NEW_DURATION!" 2>nul
if !TEST! LEQ 0 (
    echo  [ERROR] Invalid. Must be greater than 0.
    timeout /t 2 /nobreak >nul
    goto :CHANGE_DURATION
)
set "SLICE_DURATION=!NEW_DURATION!"
echo  [OK] Duration set to !SLICE_DURATION! seconds
timeout /t 2 /nobreak >nul
goto :MAIN_MENU


:: ════════════════════════════════════════════════════════════
:SLICE_ONLY
:: ════════════════════════════════════════════════════════════
cls
echo.
echo  [MODE] Slicing Only
echo  [INFO] Duration: %SLICE_DURATION% seconds per part
echo  ════════════════════════════════════════════════════════
echo.
"!PYTHON!" "%ROOT%\scripts\slicer.py" %SLICE_DURATION%
goto :DONE


:: ════════════════════════════════════════════════════════════
:SLICE_UPLOAD
:: ════════════════════════════════════════════════════════════
cls
echo.
echo  [MODE] Slicing + MEGA Auto Upload
echo  [INFO] Duration: %SLICE_DURATION% seconds per part
echo  ════════════════════════════════════════════════════════
echo.
"!PYTHON!" "%ROOT%\scripts\pipeline.py" %SLICE_DURATION%
goto :DONE


:: ════════════════════════════════════════════════════════════
:TRIMMER
:: ════════════════════════════════════════════════════════════
cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           Specific Duration Trimmer                 ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Format: HH:MM:SS  or  seconds
echo  Example: 00:05:30  or  330
echo.
echo  Videos in input\:
dir /b "%ROOT%\input\*.mp4" "%ROOT%\input\*.mkv" "%ROOT%\input\*.avi" "%ROOT%\input\*.mov" 2>nul
echo.
set /p "TRIM_FILE=  Enter video filename (e.g. myvideo.mp4^): "
set /p "TRIM_START=  Start time (e.g. 00:05:30 or 330^): "
set /p "TRIM_END=    End time   (e.g. 00:12:45 or 750^): "
echo.
"!PYTHON!" "%ROOT%\scripts\trimmer.py" "!TRIM_FILE!" "!TRIM_START!" "!TRIM_END!"
goto :DONE


:: ════════════════════════════════════════════════════════════
:CUSTOM_SLICES
:: ════════════════════════════════════════════════════════════
cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           Custom Multiple Slices                    ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Videos in input\:
dir /b "%ROOT%\input\*.mp4" "%ROOT%\input\*.mkv" "%ROOT%\input\*.avi" "%ROOT%\input\*.mov" 2>nul
echo.
set /p "CS_FILE=  Enter video filename (e.g. myvideo.mp4^): "
echo.
echo  Enter timestamps one by one.
echo  Format: START,END  (e.g. 00:00:00,00:07:29 or 0,449^)
echo  Type DONE when finished.
echo.
set "TIMESTAMPS="
set "TS_COUNT=0"
:TS_LOOP
set /a TS_COUNT+=1
set /p "TS=  Slice !TS_COUNT! (START,END or DONE^): "
if /i "!TS!"=="DONE" goto :TS_DONE
if "!TS!"=="" goto :TS_DONE
set "TIMESTAMPS=!TIMESTAMPS! !TS!"
goto :TS_LOOP
:TS_DONE
if "!TIMESTAMPS!"=="" (
    echo  [ERROR] No timestamps entered.
    timeout /t 2 /nobreak >nul
    goto :MAIN_MENU
)
echo.
"!PYTHON!" "%ROOT%\scripts\custom_slicer.py" "!CS_FILE!" !TIMESTAMPS!
goto :DONE


:: ════════════════════════════════════════════════════════════
:MERGER
:: ════════════════════════════════════════════════════════════
cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           Clip Merger                               ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Files in merger\ folder:
dir /b "%ROOT%\merger\*.mp4" "%ROOT%\merger\*.mkv" "%ROOT%\merger\*.avi" 2>nul
echo.
echo  These will be merged in ascending order (alphabetical/numerical^)
echo.
set /p "MERGE_NAME=  Output filename (without .mp4^): "
if "!MERGE_NAME!"=="" set "MERGE_NAME=merged_output"
echo.
"!PYTHON!" "%ROOT%\scripts\merger.py" "!MERGE_NAME!"
goto :DONE


:: ════════════════════════════════════════════════════════════
:AUDIO
:: ════════════════════════════════════════════════════════════
cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║           Audio Extractor                           ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  Videos in input\:
dir /b "%ROOT%\input\*.mp4" "%ROOT%\input\*.mkv" "%ROOT%\input\*.avi" "%ROOT%\input\*.mov" 2>nul
echo.
set /p "AUDIO_FILE=  Enter video filename (e.g. myvideo.mp4^): "
echo.
echo  Format: [1] MP3   [2] AAC
set /p "AUDIO_FORMAT=  Choose format (1 or 2^): "
if "!AUDIO_FORMAT!"=="1" (set "AFMT=mp3") else (set "AFMT=aac")
echo.
echo  Optional: Extract specific duration only
echo  Leave blank to extract full audio
echo.
set /p "AUDIO_START=  Start time (e.g. 00:02:00 or blank^): "
set /p "AUDIO_END=    End time   (e.g. 00:05:00 or blank^): "
echo.
"!PYTHON!" "%ROOT%\scripts\audio_extractor.py" "!AUDIO_FILE!" "!AFMT!" "!AUDIO_START!" "!AUDIO_END!"
goto :DONE


:: ════════════════════════════════════════════════════════════
:DONE
:: ════════════════════════════════════════════════════════════
echo.
echo  ════════════════════════════════════════════════════════
echo  [DONE] Check output folder: %ROOT%\output\
echo  ════════════════════════════════════════════════════════
echo.
pause
goto :MAIN_MENU


:: ════════════════════════════════════════════════════════════
:EXIT
:: ════════════════════════════════════════════════════════════
echo.
echo  Goodbye!
echo.
exit /b 0
