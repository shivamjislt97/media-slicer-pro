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
    """Convert seconds to HH-MM-SS string for filename"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f'{h:02d}-{m:02d}-{s:02d}'

if len(sys.argv) < 4:
    print('[ERROR] Usage: trimmer.py <filename> <start> <end>')
    input('Press Enter to exit...')
    exit(1)

filename = sys.argv[1]
start_raw = sys.argv[2]
end_raw = sys.argv[3]

video_path = os.path.join(INPUT_DIR, filename)
name = os.path.splitext(filename)[0]

if not os.path.exists(video_path):
    print(f'[ERROR] File not found: {video_path}')
    input('Press Enter to exit...')
    exit(1)

start_sec = parse_time(start_raw)
end_sec = parse_time(end_raw)
duration = end_sec - start_sec

if duration <= 0:
    print('[ERROR] End time must be greater than start time.')
    input('Press Enter to exit...')
    exit(1)

# Filename with timestamp
start_ts = seconds_to_ts(start_sec)
end_ts = seconds_to_ts(end_sec)
out_filename = f'{name}_clip_{start_ts}_to_{end_ts}.mp4'

out_dir = os.path.join(OUTPUT_DIR, name)
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, out_filename)

print(f'[TRIM] {filename}')
print(f'[INFO] Start : {start_raw} ({start_sec}s)')
print(f'[INFO] End   : {end_raw} ({end_sec}s)')
print(f'[INFO] Length: {duration}s')
print(f'[INFO] Output: {out_filename}')
print()

cmd = [
    FFMPEG, '-ss', str(start_sec), '-i', video_path,
    '-t', str(duration),
    '-c:v', 'libx264', '-crf', '18', '-preset', 'slow',
    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
    '-avoid_negative_ts', 'make_zero', '-reset_timestamps', '1',
    '-movflags', '+faststart', '-y', out_file
]

subprocess.run(cmd, stderr=subprocess.DEVNULL)

if os.path.exists(out_file):
    print(f'[OK] Clip saved: {out_file}')
else:
    print('[ERROR] Trim failed. Check your input.')
