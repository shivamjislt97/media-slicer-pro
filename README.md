# media-slicer-pro

**Version:** v1.0.1  
**Platform:** Windows (PC & Server)  
**Purpose:** Automated video slicing pipeline with optional MEGA cloud upload.

---

## Project Structure

```
media-slicer-pro\
├── tools\
│   ├── ffmpeg.exe          ← Place here manually
│   └── ffprobe.exe         ← Place here manually
├── input\                  ← Drop your video files here
├── output\                 ← Sliced parts appear here (auto-created)
├── scripts\
│   ├── slicer.py           ← ★ MAIN SLICER (Python - Recommended)
│   ├── slicer.bat          ← Batch version (Windows)
│   ├── mega_upload.bat     ← Upload only
│   └── pipeline.bat        ← Slice + Upload combined
└── README.md
```

---

## Quick Start (Local PC)

### Step 1 — Add FFmpeg tools

Download FFmpeg Windows build from https://www.gyan.dev/ffmpeg/builds/  
Extract and copy **ffmpeg.exe** and **ffprobe.exe** into the `tools\` folder.

### Step 2 — Install Python

Download Python 3.12 from https://www.python.org/downloads/  
During install: ✅ **Add Python to PATH** tick karo.

### Step 3 — Add your video(s)

Copy any supported video file(s) into the `input\` folder.

**Supported formats:** `.mp4` `.mkv` `.avi` `.mov` `.wmv` `.flv` `.webm`

### Step 4 — Run the slicer

```bash
python scripts\slicer.py
```

---

## Server Deployment (Windows VPS)

### Step 1 — Git install karo

```powershell
winget install Git.Git --source winget
```

### Step 2 — Project clone karo

```powershell
cd C:\
mkdir Projects
cd Projects
git clone https://github.com/shivamjislt97/media-slicer-pro.git
cd media-slicer-pro
```

### Step 3 — Python install karo

```powershell
winget install Python.Python.3.12 --source winget
```

PowerShell band karke dobara kholo taaki PATH load ho.

### Step 4 — FFmpeg download karo

```powershell
Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile "C:\ffmpeg.zip"
Expand-Archive -Path "C:\ffmpeg.zip" -DestinationPath "C:\ffmpeg-temp"
Copy-Item "C:\ffmpeg-temp\ffmpeg-*\bin\ffmpeg.exe" "C:\Projects\media-slicer-pro\tools\"
Copy-Item "C:\ffmpeg-temp\ffmpeg-*\bin\ffprobe.exe" "C:\Projects\media-slicer-pro\tools\"
Remove-Item -Path "C:\ffmpeg-temp" -Recurse -Force
Remove-Item -Path "C:\ffmpeg.zip" -Force
```

### Step 5 — Video input folder mein daalo

RDP se connect ho aur video copy karo:
```
C:\Projects\media-slicer-pro\input\
```

Ya PowerShell se copy karo:
```powershell
$src = "C:\path\to\your\video.mp4"
$dst = "C:\Projects\media-slicer-pro\input\"
Copy-Item -LiteralPath $src -Destination $dst
```

### Step 6 — Slicer chalao

```powershell
python "C:\Projects\media-slicer-pro\scripts\slicer.py"
```

---

## What Happens

1. Pipeline `input\` folder scan karta hai
2. Har video ko **449-second parts** mein slice karta hai
3. Last slice automatically shorter hota hai — no overflow, no padding
4. Output `output\<VideoName>\` mein save hota hai:

```
output\
└── myvideo\
    ├── myvideo_part_1.mp4
    ├── myvideo_part_2.mp4
    ├── myvideo_part_3.mp4
    └── myvideo_part_4.mp4   ← last slice auto-adjusted
```

---

## Encoding Specifications

| Setting | Value |
|---|---|
| Video Codec | libx264 |
| CRF | 18 (near-lossless) |
| Preset | slow |
| Pixel Format | yuv420p |
| Audio Codec | AAC |
| Audio Bitrate | 128k |
| Timestamp Mode | avoid_negative_ts make_zero |
| Timestamp Reset | reset_timestamps 1 |
| Fast Start | movflags +faststart |

- Resolution **unchanged** — output matches source exactly
- No frame drops or quality loss
- No timestamp drift between slices

---

## Optional MEGA Upload

### Requirements

- Install MEGAcmd from: https://mega.io/cmd
- Login once via MEGAcmd shell:

```
mega-login your@email.com yourpassword
```

### Run Pipeline (Slice + Upload)

```powershell
cmd /c "C:\Projects\media-slicer-pro\scripts\pipeline.bat"
```

Each slice uploads to MEGA immediately after encoding:
```
Slice 1 encoded → Upload → Slice 2 encoded → Upload → ...
```

Remote folder created automatically:
```
/media-slicer-pro/<VideoName>/
```

---

## Minimum Server Requirements

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 2 Core | 4 Core |
| RAM | 4 GB | 8 GB |
| Storage | 40 GB | 80 GB+ |
| OS | Windows Server 2019 | Windows Server 2022 |

> Note: No GPU required — libx264 is CPU-only encoder.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ffmpeg.exe not found` | Place ffmpeg.exe in `tools\` folder |
| `Python not found` | Restart terminal after Python install |
| `No videos found` | Make sure video is in `input\` folder |
| MEGA upload skipped | Run `mega-login email password` first |
| Video not copying | Use `Copy-Item -LiteralPath` for special characters in filename |

---

## Version History

### v1.0.1 *(current)*

- **Added:** `slicer.py` — Python-based slicer, reliable on all Windows systems
- **Fixed:** Batch script `for /f` issue with ffprobe output on Windows Server
- **Fixed:** Last slice auto-adjustment for any video duration
- **Fixed:** Special characters in filenames handled via `-LiteralPath`
- **Fixed:** Large file (ffmpeg, videos) excluded from git via `.gitignore`
- **Added:** Full server deployment guide in README
- **Added:** Python install steps for VPS setup
- **Tested:** Successfully tested on Windows Server 2025 VPS
- **Tested:** 1450s video → 4 slices (449s + 449s + 449s + 103s) ✅

### v1.0.0

- Initial release
- Basic FFmpeg slicing via batch scripts
- Manual MEGA upload step
