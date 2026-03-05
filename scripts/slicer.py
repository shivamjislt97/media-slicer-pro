import subprocess, os, math, sys

FFMPEG = r'C:\Projects\media-slicer-pro\tools\ffmpeg.exe'
FFPROBE = r'C:\Projects\media-slicer-pro\tools\ffprobe.exe'
INPUT_DIR = r'C:\Projects\media-slicer-pro\input'
OUTPUT_DIR = r'C:\Projects\media-slicer-pro\output'

SLICE_DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 449

print(f'[INFO] Slice duration: {SLICE_DURATION} seconds')
print()

videos = sorted([
    f for f in os.listdir(INPUT_DIR)
    if f != '.gitkeep' and f.endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'))
])

if not videos:
    print('[ERROR] No videos found in input\\ folder.')
    input('Press Enter to exit...')
    exit(1)

print(f'[INFO] Found {len(videos)} video(s) - processing sequentially...')
print()

for idx, f in enumerate(videos, 1):
    video_path = os.path.join(INPUT_DIR, f)
    name = os.path.splitext(f)[0]

    print(f'══════════════════════════════════════════════════════')
    print(f'[{idx}/{len(videos)}] Processing: {f}')
    print(f'══════════════════════════════════════════════════════')

    result = subprocess.run(
        [FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    total_slices = math.ceil(duration / SLICE_DURATION)

    print(f'[INFO] Duration: {int(duration)}s | Slices: {total_slices}')

    out_dir = os.path.join(OUTPUT_DIR, name)
    os.makedirs(out_dir, exist_ok=True)

    for part in range(1, total_slices + 1):
        start = (part - 1) * SLICE_DURATION
        out_file = os.path.join(out_dir, f'{name}_part_{part}.mp4')

        cmd = [FFMPEG, '-ss', str(start), '-i', video_path]
        if part < total_slices:
            cmd += ['-t', str(SLICE_DURATION)]
        cmd += [
            '-c:v', 'libx264', '-crf', '18', '-preset', 'slow',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
            '-avoid_negative_ts', 'make_zero', '-reset_timestamps', '1',
            '-movflags', '+faststart', '-y', out_file
        ]

        print(f'[SLICE {part}/{total_slices}] start={start}s encoding...')
        subprocess.run(cmd, stderr=subprocess.DEVNULL)
        print(f'[OK] Slice {part} done -> {os.path.basename(out_file)}')

    print(f'[DONE] {f} -> {total_slices} slices complete')
    print()

print('[DONE] All videos processed!')
