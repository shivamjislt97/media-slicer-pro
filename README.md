# all-in-one-media-slicer

**Version:** v1.0.1  
**Platform:** Windows (Personal PC)  
**Purpose:** Automated video slicing pipeline with optional MEGA cloud upload.

---

## Project Structure

```
all-in-one-media-slicer\
├── tools\
│   ├── ffmpeg.exe          ← Place here manually
│   └── ffprobe.exe         ← Place here manually
├── input\                  ← Drop your video files here
├── output\                 ← Sliced parts appear here (auto-created)
├── scripts\
│   ├── slicer.bat          ← Slice only
│   ├── mega_upload.bat     ← Upload only (standalone or called internally)
│   └── pipeline.bat        ← ★ MAIN ENTRY POINT — Slice + Upload
└── README.md
```

---

## Quick Start

### Step 1 — Add FFmpeg tools

Download the FFmpeg Windows build from https://www.gyan.dev/ffmpeg/builds/  
Extract and copy **ffmpeg.exe** and **ffprobe.exe** into the `tools\` folder.

### Step 2 — Add your video(s)

Copy any supported video file(s) into the `input\` folder.

**Supported formats:** `.mp4` `.mkv` `.avi` `.mov` `.wmv` `.flv` `.webm`

### Step 3 — Run the pipeline

Double-click **`scripts\pipeline.bat`**

That's it. No command-line knowledge required.

---

## What Happens

1. The pipeline scans `input\` for all video files.
2. Each video is sliced into **449-second parts**.
3. The last slice is automatically shorter to match the remaining duration — no padding, no overflow.
4. Output is saved to `output\<VideoName>\` with clean naming:

```
output\
└── MyVideo\
    ├── MyVideo_part_1.mp4
    ├── MyVideo_part_2.mp4
    ├── MyVideo_part_3.mp4
    └── pipeline_log.txt
```

5. **If MEGAcmd is installed and you are logged in:** each slice is uploaded to MEGA immediately after encoding — no waiting for all slices to finish first.

---

## Encoding Specifications

| Setting          | Value         |
|------------------|---------------|
| Video Codec      | libx264       |
| CRF              | 18 (near-lossless) |
| Preset           | slow          |
| Pixel Format     | yuv420p       |
| Audio Codec      | AAC           |
| Audio Bitrate    | 128k          |
| Timestamp Mode   | avoid_negative_ts make_zero |
| Timestamp Reset  | reset_timestamps 1 |
| Fast Start       | movflags +faststart |

- Resolution is **never changed** — output matches source exactly.
- No frame drops or quality degradation.
- No timestamp drift between slices.

---

## Optional MEGA Upload

### Requirements

- Install **MEGAcmd** from: https://mega.io/cmd
- Log in once via the MEGAcmd shell:

```
mega-login your@email.com yourpassword
```

### Behavior

- The pipeline **auto-detects** MEGAcmd on your system (no config needed).
- Starts the MEGAcmd server automatically if it is not running.
- Creates a remote folder: `/all-in-one-media-slicer/<VideoName>/`
- Uploads each slice right after it is encoded.
- If MEGAcmd is not installed or you are not logged in, the upload step is **silently skipped** — slicing continues normally.

### Standalone Upload

To upload an already-sliced output folder without re-slicing:

```
Double-click: scripts\mega_upload.bat
```

It will scan `output\` and upload all subfolders.

---

## Individual Scripts

| Script             | Purpose                                                  |
|--------------------|----------------------------------------------------------|
| `pipeline.bat`     | **Recommended.** Full slice + upload in one run.         |
| `slicer.bat`       | Slice only. No MEGA interaction.                        |
| `mega_upload.bat`  | Upload only. Scans `output\` and uploads everything.    |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ffmpeg.exe not found` | Place ffmpeg.exe and ffprobe.exe in the `tools\` folder |
| `No video files found` | Make sure your video is in `input\` with a supported extension |
| Slices have wrong duration | Check `pipeline_log.txt` inside the output subfolder |
| MEGA upload skipped | Open MEGAcmd and run `mega-login email password` first |
| Script closes instantly | Right-click → "Run as administrator" or check error message before it closes |

---

## Version History

### v1.0.1 *(current)*

- **Rebuilt from scratch** for stability and reliability
- Fixed: batch script crashing on double-click due to uninitialized variables
- Fixed: last slice could overflow video duration — now auto-adjusts cleanly
- Fixed: negative timestamp artifacts eliminated with `avoid_negative_ts make_zero`
- Fixed: timestamp drift between slices fixed with `reset_timestamps 1`
- Added: per-video output subfolders (prevents file collisions on multi-video runs)
- Added: `pipeline_log.txt` written per video for debugging
- Added: real-time slice-by-slice MEGA upload (no waiting for all slices)
- Added: MEGAcmd auto-detection across all common install paths
- Added: MEGAcmd server auto-start if not running
- Added: login check before attempting any upload
- Improved: clear progress output showing `[SLICE X/Y]` per video
- Improved: `movflags +faststart` for better MP4 streaming compatibility
- Code: all scripts use `setlocal EnableDelayedExpansion` correctly

### v1.0.0

- Initial release
- Basic FFmpeg slicing
- Manual MEGA upload step

---

## Notes

- All tools are self-contained. No installers run from this project.
- MEGAcmd must be installed system-wide by the user once.
- FFmpeg must be placed in `tools\` by the user once.
- After that, everything is fully automated by double-clicking `pipeline.bat`.
