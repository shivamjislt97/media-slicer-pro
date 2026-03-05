# media-slicer-pro

**Version:** v1.0.1  
**Platform:** Windows (PC & Server)  
**Purpose:** Automated video slicing pipeline with optional MEGA cloud upload.

---

## Quick Start (New User)

### Step 1 — Repo Clone Karo

```bash
git clone https://github.com/shivamjislt97/media-slicer-pro.git
cd media-slicer-pro
```

### Step 2 — Setup Karo (Sirf Ek Baar)

```
setup.bat double-click karo
```

Yeh automatically install karega:
- ✅ Python 3.12
- ✅ FFmpeg + FFprobe
- ✅ MEGAcmd
- ✅ MEGA Login (email + password sirf ek baar)
- ✅ run.bat create karega

### Step 3 — Video Daalo

```
input\ folder mein apni video copy karo
```

### Step 4 — Run Karo

```
run.bat double-click karo
```

---

## run.bat Menu

Jab run.bat chaloge yeh menu dikhega:

```
╔══════════════════════════════════════════════════════╗
║           media-slicer-pro  v1.0.1                  ║
╚══════════════════════════════════════════════════════╝

  [1]  Slicing Only
       (No upload - just cut video into parts)

  [2]  Slicing + MEGA Auto Upload
       (Cut video into parts AND upload to MEGA)

  [3]  Exit

  Enter your choice (1/2/3):
```

### Option 1 — Slicing Only
- Video ko 449 second parts mein cut karta hai
- MEGA login nahi maangta
- Output output\ folder mein save hota hai

### Option 2 — Slicing + MEGA Auto Upload
- Pehle MEGA login check karta hai
- Agar logged in hai → seedha upload
- Agar logged in nahi → email + password maangta hai
- Har slice encode hone ke baad turant MEGA pe upload
- Output output\ folder mein bhi save rehta hai

---

## Project Structure

```
media-slicer-pro\
├── tools\
│   ├── ffmpeg.exe          ← Auto download via setup.bat
│   └── ffprobe.exe         ← Auto download via setup.bat
├── input\                  ← Apni videos yahan daalo
├── output\                 ← Sliced parts yahan aate hain
├── scripts\
│   ├── slicer.py           ← Slicing only (Python)
│   ├── pipeline.py         ← Slicing + MEGA upload (Python)
│   ├── slicer.bat          ← Batch version
│   ├── mega_upload.bat     ← MEGA upload only
│   └── pipeline.bat        ← Batch pipeline
├── setup.bat               ← First time setup (run once)
├── run.bat                 ← Daily use entry point
└── README.md
```

---

## What Happens During Slicing

1. input\ folder scan hota hai
2. Har video 449 second parts mein cut hoti hai
3. Last slice automatically adjust hoti hai — no overflow
4. Output output\<VideoName>\ mein save hota hai:

```
output\
└── myvideo\
    ├── myvideo_part_1.mp4   (0s - 449s)
    ├── myvideo_part_2.mp4   (449s - 898s)
    ├── myvideo_part_3.mp4   (898s - 1347s)
    └── myvideo_part_4.mp4   (1347s - end) ← auto adjusted
```

---

## MEGA Upload Flow

```
Option 2 select karo
    ↓
Already logged in?
    ↓ Haan → Seedha upload start
    ↓ Nahi → Email + Password maango → Login → Upload start

Har slice ke baad:
Slice encode → MEGA upload → Next slice → ...

MEGA pe folder:
/media-slicer-pro/<VideoName>/
    ├── myvideo_part_1.mp4
    ├── myvideo_part_2.mp4
    └── ...
```

---

## Auto Downloaded Dependencies

| Dependency | Size | Source |
|---|---|---|
| Python 3.12 | ~25 MB | python.org via winget |
| FFmpeg | ~110 MB | gyan.dev |
| FFprobe | ~110 MB | gyan.dev (FFmpeg ke saath) |
| MEGAcmd | ~50 MB | mega.nz |

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

- Resolution unchanged — output matches source exactly
- No frame drops or quality loss
- No GPU required — CPU only

---

## Server Deployment (Windows VPS)

### Recommended Specs

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 2 Core | 4 Core |
| RAM | 4 GB | 8 GB |
| Storage | 40 GB | 80 GB+ |
| OS | Windows Server 2019 | Windows Server 2022 |

### Deploy Steps

```powershell
winget install Git.Git --source winget
cd C:\
mkdir Projects && cd Projects
git clone https://github.com/shivamjislt97/media-slicer-pro.git
cd media-slicer-pro
cmd /c setup.bat
```

---

## Supported Video Formats

.mp4  .mkv  .avi  .mov  .wmv  .flv  .webm

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Python not found | PowerShell band karke dobara kholo |
| FFmpeg not found | setup.bat dobara chalao |
| MEGA login failed | Email/password check karo |
| Video not found | input\ folder mein video daalo |
| Special characters in filename | File rename karo simple naam se |
| Git not recognized | Terminal restart karo after install |

---

## Version History

### v1.0.1 (current)

- Added: setup.bat — one-click first time setup
- Added: run.bat — menu with 2 options (Slice Only / Slice + Upload)
- Added: slicer.py — reliable Python-based slicer
- Added: pipeline.py — Python pipeline with auto MEGA login
- Fixed: Option 2 pe hi MEGA login maangta hai — Option 1 pe nahi
- Fixed: Already logged in hai toh dobara login nahi maangta
- Fixed: Last slice auto-adjustment for any video duration
- Fixed: Special characters in filenames
- Fixed: Large files excluded from git
- Tested: Windows Server 2025 VPS pe successfully
- Tested: 1450s video — 4 slices (449+449+449+103)
- Tested: MEGA auto upload after each slice

### v1.0.0

- Initial release
- Basic FFmpeg slicing via batch scripts
- Manual MEGA upload
