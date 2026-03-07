import subprocess, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
FFMPEG = os.path.join(ROOT, 'tools', 'ffmpeg.exe')
INPUT_DIR = os.path.join(ROOT, 'input')
OUTPUT_DIR = os.path.join(ROOT, 'output')

def parse_time(t):
    t = t.strip()
    if not t:
        return None
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
    print('[ERROR] Usage: audio_extractor.py <filename> <mp3|aac> [start] [end]')
    input('Press Enter to exit...')
    exit(1)

filename = sys.argv[1]
fmt = sys.argv[2].lower()
start_raw = sys.argv[3] if len(sys.argv) > 3 else ''
end_raw = sys.argv[4] if len(sys.argv) > 4 else ''

video_path = os.path.join(INPUT_DIR, filename)
name = os.path.splitext(filename)[0]

if not os.path.exists(video_path):
    print(f'[ERROR] File not found: {video_path}')
    input('Press Enter to exit...')
    exit(1)

start_sec = parse_time(start_raw)
end_sec = parse_time(end_raw)

if start_sec is not None and end_sec is not None:
    out_filename = f'{name}_audio_{seconds_to_ts(start_sec)}_to_{seconds_to_ts(end_sec)}.{fmt}'
else:
    out_filename = f'{name}_audio_full.{fmt}'

out_dir = os.path.join(OUTPUT_DIR, name)
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, out_filename)

print(f'[AUDIO] {filename}')
print(f'[INFO] Format : {fmt.upper()}')
if start_sec is not None:
    print(f'[INFO] Start  : {start_raw}')
if end_sec is not None:
    print(f'[INFO] End    : {end_raw}')
print(f'[INFO] Output : {out_filename}')
print()

cmd = [FFMPEG]
if start_sec is not None:
    cmd += ['-ss', str(start_sec)]
cmd += ['-i', video_path]
if start_sec is not None and end_sec is not None:
    cmd += ['-t', str(end_sec - start_sec)]
if fmt == 'mp3':
    cmd += ['-vn', '-c:a', 'libmp3lame', '-b:a', '192k']
else:
    cmd += ['-vn', '-c:a', 'aac', '-b:a', '192k']
cmd += ['-y', out_file]

subprocess.run(cmd)

if os.path.exists(out_file):
    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f'[OK] Audio extracted!')
    print(f'[OK] Size: {size_mb:.1f} MB')
else:
    print('[ERROR] Audio extraction failed.')
