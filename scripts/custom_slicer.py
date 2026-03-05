import subprocess, os, sys

FFMPEG = r'C:\Projects\media-slicer-pro\tools\ffmpeg.exe'
INPUT_DIR = r'C:\Projects\media-slicer-pro\input'
OUTPUT_DIR = r'C:\Projects\media-slicer-pro\output'

def parse_time(t):
    """Accept HH:MM:SS or seconds, return seconds as float"""
    t = t.strip()
    if ':' in t:
        parts = t.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
    return float(t)

def seconds_to_ts(seconds):
    """Convert seconds to HH-MM-SS for filename"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f'{h:02d}-{m:02d}-{s:02d}'

if len(sys.argv) < 3:
    print('[ERROR] No timestamps provided.')
    input('Press Enter to exit...')
    exit(1)

filename = sys.argv[1]
timestamp_args = sys.argv[2:]

video_path = os.path.join(INPUT_DIR, filename)
name = os.path.splitext(filename)[0]

if not os.path.exists(video_path):
    print(f'[ERROR] File not found: {video_path}')
    input('Press Enter to exit...')
    exit(1)

# Parse timestamps - format: "start,end"
slices = []
for ts in timestamp_args:
    ts = ts.strip()
    if ',' not in ts:
        print(f'[WARN] Skipping invalid timestamp: {ts}')
        continue
    parts = ts.split(',')
    if len(parts) != 2:
        print(f'[WARN] Skipping invalid timestamp: {ts}')
        continue
    start = parse_time(parts[0])
    end = parse_time(parts[1])
    if end <= start:
        print(f'[WARN] End must be greater than start: {ts}')
        continue
    slices.append((start, end))

if not slices:
    print('[ERROR] No valid timestamps found.')
    input('Press Enter to exit...')
    exit(1)

out_dir = os.path.join(OUTPUT_DIR, name)
os.makedirs(out_dir, exist_ok=True)

print(f'[VIDEO] {filename}')
print(f'[INFO] {len(slices)} custom slice(s) to extract')
print()

for idx, (start, end) in enumerate(slices, 1):
    duration = end - start
    start_ts = seconds_to_ts(start)
    end_ts = seconds_to_ts(end)
    out_filename = f'{name}_clip_{start_ts}_to_{end_ts}.mp4'
    out_file = os.path.join(out_dir, out_filename)

    print(f'[SLICE {idx}/{len(slices)}] {start_ts} → {end_ts} ({duration:.0f}s)')

    cmd = [
        FFMPEG, '-ss', str(start), '-i', video_path,
        '-t', str(duration),
        '-c:v', 'libx264', '-crf', '18', '-preset', 'slow',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
        '-avoid_negative_ts', 'make_zero', '-reset_timestamps', '1',
        '-movflags', '+faststart', '-y', out_file
    ]

    subprocess.run(cmd, stderr=subprocess.DEVNULL)

    if os.path.exists(out_file):
        print(f'[OK] Saved: {out_filename}')
    else:
        print(f'[ERROR] Failed: {out_filename}')

print()
print(f'[DONE] {len(slices)} custom slices complete!')
