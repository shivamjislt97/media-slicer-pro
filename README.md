# media-slicer-pro

**Version:** v2.0.1  
**Platform:** Windows (PC & Server)  
**Purpose:** All-in-one automated video processing pipeline.

---

## Quick Start (New User)

```bash
# Step 1 - Clone
git clone https://github.com/shivamjislt97/media-slicer-pro.git
cd media-slicer-pro

# Step 2 - Setup (sirf ek baar)
setup.bat

# Step 3 - Run karo
run.bat
```

---

## run.bat Menu

```
╔══════════════════════════════════════════════════════╗
║           media-slicer-pro  v2.0.1                  ║
╚══════════════════════════════════════════════════════╝

  [1]  Slicing Only
  [2]  Slicing + MEGA Auto Upload
  [3]  Change Slice Duration        (Current: 449s)
  [4]  Specific Duration Trimmer
  [5]  Custom Multiple Slices
  [6]  Clip Merger
  [7]  Audio Extractor
  [8]  Exit
```

---

## Features

### [1] Slicing Only
- Input folder ke saare videos sequentially slice hote hain
- Equal parts mein cut hota hai (default 449s)
- Last slice auto-adjust hoti hai
- Output: `output\<VideoName>\<VideoName>_part_1.mp4`

### [2] Slicing + MEGA Auto Upload
- Same as Option 1 + har slice MEGA pe upload hoti hai
- Agar logged in nahi → email + password ek baar maangta hai
- Har slice encode hone ke baad turant upload

### [3] Change Slice Duration
- Default: 449 seconds
- User apni marzi se seconds enter kar sakta hai
- Examples: 300 (5 min), 600 (10 min), 3600 (1 hour)

### [4] Specific Duration Trimmer
- Ek video se ek specific clip nikalo
- Format: `HH:MM:SS` ya seconds dono accept karta hai
- Output filename mein timestamp automatically add hota hai
- Example output: `myvideo_clip_00-05-30_to_00-12-45.mp4`

### [5] Custom Multiple Slices
- Ek video se multiple custom clips nikalo
- Har slice ke liye apna start aur end time daalo
- Format: `00:05:00,00:10:00` ya `300,600`
- Example output: `myvideo_clip_00-05-00_to_00-10-00.mp4`

### [6] Clip Merger
- `merger\` folder ke saare clips ek video mein merge
- Ascending order mein merge hote hain (alphabetical/numerical)
- Output: `output\merged\<name>.mp4`
- Merger folder structure:
```
merger\
  01_intro.mp4
  02_middle.mp4
  03_end.mp4
  ↓
output\merged\final.mp4
```

### [7] Audio Extractor
- Video se sirf audio nikalo
- Format choose karo: MP3 ya AAC
- Optional: specific duration only extract karo
- Example output: `myvideo_audio_00-02-00_to_00-05-00.mp3`

---

## Project Structure

```
media-slicer-pro\
├── tools\
│   ├── ffmpeg.exe          ← Auto download via setup.bat
│   └── ffprobe.exe         ← Auto download via setup.bat
├── input\                  ← Videos yahan daalo
├── output\                 ← Processed files yahan aate hain
├── merger\                 ← Merge karne wale clips yahan
├── scripts\
│   ├── slicer.py           ← Option 1: Slice only
│   ├── pipeline.py         ← Option 2: Slice + MEGA
│   ├── trimmer.py          ← Option 4: Duration trimmer
│   ├── custom_slicer.py    ← Option 5: Custom slices
│   ├── merger.py           ← Option 6: Clip merger
│   ├── audio_extractor.py  ← Option 7: Audio extractor
│   ├── slicer.bat          ← Legacy batch
│   ├── mega_upload.bat     ← Legacy MEGA upload
│   └── pipeline.bat        ← Legacy batch pipeline
├── setup.bat               ← First time setup
├── run.bat                 ← Main entry point
└── README.md
```

---

## Output Naming Convention

| Feature | Output Filename |
|---|---|
| Slicing | `video_part_1.mp4` |
| Trimmer | `video_clip_00-05-30_to_00-12-45.mp4` |
| Custom Slices | `video_clip_00-05-00_to_00-10-00.mp4` |
| Merger | `merged_output.mp4` |
| Audio (full) | `video_audio_full.mp3` |
| Audio (partial) | `video_audio_00-02-00_to_00-05-00.mp3` |

---

## Encoding Specifications

| Setting | Value |
|---|---|
| Video Codec | libx264 |
| CRF | 18 (near-lossless) |
| Preset | slow |
| Pixel Format | yuv420p |
| Audio Codec | AAC / MP3 |
| Audio Bitrate | 128k (video) / 192k (audio extract) |
| Timestamp Mode | avoid_negative_ts make_zero |
| Timestamp Reset | reset_timestamps 1 |
| Fast Start | movflags +faststart |

---

## Auto Downloaded Dependencies (via setup.bat)

| Dependency | Size |
|---|---|
| Python 3.12 | ~25 MB |
| FFmpeg + FFprobe | ~110 MB |
| MEGAcmd | ~50 MB |

---

## Supported Formats

Input: `.mp4` `.mkv` `.avi` `.mov` `.wmv` `.flv` `.webm`  
Audio output: `.mp3` `.aac`

---

## Server Deployment

```powershell
winget install Git.Git --source winget
cd C:\Projects
git clone https://github.com/shivamjislt97/media-slicer-pro.git
cd media-slicer-pro
cmd /c setup.bat
```

---

## Version History

### v2.0.1 (current)

- **Added:** Option 4 — Specific Duration Trimmer
- **Added:** Option 5 — Custom Multiple Slices with timestamps
- **Added:** Option 6 — Clip Merger (ascending order)
- **Added:** Option 7 — Audio Extractor (MP3/AAC, optional duration)
- **Added:** Option 3 — Custom slice duration in menu
- **Added:** `merger\` folder for clip merging
- **Improved:** Output filenames include timestamps for trimmer/custom slices
- **Improved:** Multiple videos processed sequentially (Option 1 & 2)
- **Improved:** run.bat loops back to menu after each operation
- **Fixed:** All previous v1.0.1 fixes retained

### v1.0.1

- Added: setup.bat one-click setup
- Added: run.bat menu (Slice Only / Slice + Upload)
- Added: slicer.py Python-based slicer
- Added: pipeline.py auto MEGA login
- Fixed: ffprobe batch script issue on Windows Server
- Tested: Windows Server 2025 VPS

### v1.0.0

- Initial release
- Basic FFmpeg slicing
- Manual MEGA upload
