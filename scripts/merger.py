import subprocess, os, sys

FFMPEG = r'C:\Projects\media-slicer-pro\tools\ffmpeg.exe'
MERGER_DIR = r'C:\Projects\media-slicer-pro\merger'
OUTPUT_DIR = r'C:\Projects\media-slicer-pro\output'

output_name = sys.argv[1] if len(sys.argv) > 1 else 'merged_output'

# ── Collect clips in ascending order ────────────────────────
clips = sorted([
    f for f in os.listdir(MERGER_DIR)
    if f.endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'))
])

if not clips:
    print('[ERROR] No video files found in merger\\ folder.')
    print('        Add clips to: C:\\Projects\\media-slicer-pro\\merger\\')
    input('Press Enter to exit...')
    exit(1)

print(f'[MERGER] Found {len(clips)} clip(s) to merge:')
for idx, clip in enumerate(clips, 1):
    print(f'  {idx}. {clip}')
print()

# ── Create filelist.txt for FFmpeg concat ───────────────────
filelist_path = os.path.join(MERGER_DIR, '_filelist.txt')
with open(filelist_path, 'w') as fl:
    for clip in clips:
        clip_path = os.path.join(MERGER_DIR, clip).replace('\\', '/')
        fl.write(f"file '{clip_path}'\n")

# ── Output path ──────────────────────────────────────────────
merger_out = os.path.join(OUTPUT_DIR, 'merged')
os.makedirs(merger_out, exist_ok=True)
out_file = os.path.join(merger_out, f'{output_name}.mp4')

print(f'[INFO] Output: {out_file}')
print(f'[INFO] Merging {len(clips)} clips...')
print()

cmd = [
    FFMPEG,
    '-f', 'concat',
    '-safe', '0',
    '-i', filelist_path,
    '-c:v', 'libx264', '-crf', '18', '-preset', 'slow',
    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
    '-movflags', '+faststart',
    '-y', out_file
]

subprocess.run(cmd, stderr=subprocess.DEVNULL)

# Cleanup filelist
os.remove(filelist_path)

if os.path.exists(out_file):
    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f'[OK] Merged successfully!')
    print(f'[OK] Output: {out_file}')
    print(f'[OK] Size: {size_mb:.1f} MB')
else:
    print('[ERROR] Merge failed. Check clips in merger\\ folder.')
