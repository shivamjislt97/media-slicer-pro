import subprocess, os, sys

SCRIPT_DIR = __import__('os').path.dirname(__import__('os').path.abspath(__file__))
ROOT = __import__('os').path.dirname(SCRIPT_DIR)
FFMPEG = __import__('os').path.join(ROOT, 'tools', 'ffmpeg.exe')
INPUT_DIR = __import__('os').path.join(ROOT, 'input')
OUTPUT_DIR = __import__('os').path.join(ROOT, 'output')

def parse_time(t):
    t = t.strip()
    if ':' in t:
        parts = t.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
    return float(t)

def seconds_to_ts(seconds):
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

probe = subprocess.run(
    [
        os.path.join(ROOT, 'tools', 'ffprobe.exe'),
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path,
    ],
    capture_output=True,
    text=True,
)

if probe.returncode != 0 or not probe.stdout.strip():
    print('[ERROR] Unable to read video duration via ffprobe.')
    input('Press Enter to exit...')
    exit(1)

video_duration = float(probe.stdout.strip())

slices = []
for ts in timestamp_args:
    ts = ts.strip()
    if ',' not in ts:
        continue
    parts = ts.split(',')
    if len(parts) != 2:
        continue
    start = parse_time(parts[0])
    end = parse_time(parts[1])
    if end <= start:
        continue
    if start < 0 or end > video_duration:
        continue
    slices.append((start, end))

if not slices:
    print(f'[ERROR] No valid timestamps found. Ensure ranges are within video duration ({video_duration:.2f}s).')
    input('Press Enter to exit...')
    exit(1)

out_dir = os.path.join(OUTPUT_DIR, name)
os.makedirs(out_dir, exist_ok=True)

print(f'[VIDEO] {filename}')
print(f'[INFO] {len(slices)} custom slice(s) to extract')
print(f'[INFO] Mode: Stream Copy (no quality loss)')
print()

for idx, (start, end) in enumerate(slices, 1):
    duration = end - start
    start_ts = seconds_to_ts(start)
    end_ts = seconds_to_ts(end)
    out_filename = f'{name}_clip_{start_ts}_to_{end_ts}.mp4'
    out_file = os.path.join(out_dir, out_filename)

    print(f'[SLICE {idx}/{len(slices)}] {start_ts} -> {end_ts} ({duration:.0f}s)')

    cmd = [
        FFMPEG,
        '-ss', str(start),
        '-i', video_path,
        '-t', str(duration),
        '-c', 'copy',
        '-avoid_negative_ts', 'make_zero',
        '-reset_timestamps', '1',
        '-movflags', '+faststart',
        '-y', out_file
    ]

    result = subprocess.run(cmd)

    if result.returncode == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 0:
        print(f'[OK] Saved: {out_filename}')
    else:
        print(f'[ERROR] Failed: {out_filename}')

print()
print(f'[DONE] {len(slices)} custom slices complete!')

