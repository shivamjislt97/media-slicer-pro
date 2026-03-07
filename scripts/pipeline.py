import subprocess, os, math, sys, getpass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
FFMPEG = os.path.join(ROOT, 'tools', 'ffmpeg.exe')
FFPROBE = os.path.join(ROOT, 'tools', 'ffprobe.exe')
INPUT_DIR = os.path.join(ROOT, 'input')
OUTPUT_DIR = os.path.join(ROOT, 'output')

SLICE_DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 449

print(f'[INFO] Slice duration: {SLICE_DURATION} seconds')
print()

MEGA_CMD = None
for path in [
    os.path.expandvars(r'%LOCALAPPDATA%\MEGAcmd\MEGAclient.exe'),
    r'C:\Program Files\MEGAcmd\MEGAclient.exe',
    r'C:\Program Files (x86)\MEGAcmd\MEGAclient.exe',
]:
    if os.path.exists(path):
        MEGA_CMD = path
        break

if not MEGA_CMD:
    print('[MEGA] MEGAcmd not found. Switching to Slice Only mode.')
else:
    print('[MEGA] MEGAcmd detected!')
    result = subprocess.run([MEGA_CMD, 'whoami'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f'[MEGA] Logged in: {result.stdout.strip()}')
    else:
        print('[MEGA] Not logged in.')
        email = input('  Email   : ')
        password = getpass.getpass('  Password: ')
        login = subprocess.run([MEGA_CMD, 'login', email, password], capture_output=True, text=True)
        if login.returncode == 0:
            print('[MEGA] Login successful!')
        else:
            print('[MEGA] Login failed. Switching to Slice Only mode.')
            MEGA_CMD = None

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

    print(f'{"="*54}')
    print(f'[{idx}/{len(videos)}] Processing: {f}')
    print(f'{"="*54}')

    result = subprocess.run(
        [FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    total_slices = math.ceil(duration / SLICE_DURATION)

    print(f'[INFO] Duration: {int(duration)}s | Slices: {total_slices}')
    print(f'[INFO] Mode: Stream Copy (no quality loss, original FPS/resolution)')

    out_dir = os.path.join(OUTPUT_DIR, name)
    os.makedirs(out_dir, exist_ok=True)

    if MEGA_CMD:
        mega_dest = f'/media-slicer-pro/{name}'
        subprocess.run([MEGA_CMD, 'mkdir', '-p', mega_dest], capture_output=True)

    for part in range(1, total_slices + 1):
        start = (part - 1) * SLICE_DURATION
        out_file = os.path.join(out_dir, f'{name}_part_{part}.mp4')

        cmd = [FFMPEG, '-ss', str(start), '-i', video_path]
        if part < total_slices:
            cmd += ['-t', str(SLICE_DURATION)]
        cmd += [
            '-c', 'copy',
            '-avoid_negative_ts', 'make_zero',
            '-reset_timestamps', '1',
            '-movflags', '+faststart',
            '-y', out_file
        ]

        print(f'\n[SLICE {part}/{total_slices}] start={start}s')
        print(f'Output: {os.path.basename(out_file)}')
        print('-' * 54)
        subprocess.run(cmd)
        print(f'[OK] Slice {part}/{total_slices} done!')

        if MEGA_CMD:
            print(f'[MEGA] Uploading part {part}...')
            r = subprocess.run(
                [MEGA_CMD, 'put', out_file, mega_dest + '/'],
                capture_output=True, text=True
            )
            if r.returncode == 0:
                print(f'[MEGA] Part {part} uploaded!')
            else:
                print(f'[MEGA] Upload failed: {r.stderr.strip()}')

    print(f'\n[DONE] {f} -> {total_slices} slices complete!')
    print()

print('[DONE] All videos processed!')
