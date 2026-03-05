import subprocess, os, math, getpass

FFMPEG = r'C:\Projects\media-slicer-pro\tools\ffmpeg.exe'
FFPROBE = r'C:\Projects\media-slicer-pro\tools\ffprobe.exe'
INPUT_DIR = r'C:\Projects\media-slicer-pro\input'
OUTPUT_DIR = r'C:\Projects\media-slicer-pro\output'
SLICE_DURATION = 449

# ── Detect MEGAcmd ──────────────────────────────────────────
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
    print('[MEGA] MEGAcmd not found.')
    print('[MEGA] Install from: https://mega.io/cmd')
    print('[MEGA] Switching to Slice Only mode.')
    MEGA_CMD = None
else:
    print('[MEGA] MEGAcmd detected!')

    # ── Check login status ──────────────────────────────────
    result = subprocess.run([MEGA_CMD, 'whoami'], capture_output=True, text=True)

    if result.returncode == 0:
        print(f'[MEGA] Already logged in: {result.stdout.strip()}')
    else:
        print('[MEGA] Not logged in.')
        print()
        print('  Enter your MEGA credentials:')
        email = input('  Email   : ')
        password = getpass.getpass('  Password: ')
        print()
        print('[MEGA] Logging in...')

        login = subprocess.run([MEGA_CMD, 'login', email, password], capture_output=True, text=True)

        if login.returncode == 0:
            print('[MEGA] Login successful! ✅')
        else:
            print('[MEGA] Login failed. Switching to Slice Only mode.')
            print(f'       Reason: {login.stderr.strip()}')
            MEGA_CMD = None

print()

# ── Process videos ──────────────────────────────────────────
for f in os.listdir(INPUT_DIR):
    if f == '.gitkeep':
        continue
    if not f.endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm')):
        continue

    video_path = os.path.join(INPUT_DIR, f)
    name = os.path.splitext(f)[0]

    result = subprocess.run(
        [FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    total_slices = math.ceil(duration / SLICE_DURATION)

    print(f'[VIDEO] {name} | Duration: {int(duration)}s | Slices: {total_slices}')

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
            '-c:v', 'libx264', '-crf', '18', '-preset', 'slow',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
            '-avoid_negative_ts', 'make_zero', '-reset_timestamps', '1',
            '-movflags', '+faststart', '-y', out_file
        ]

        print(f'[SLICE {part}/{total_slices}] start={start}s encoding...')
        subprocess.run(cmd)
        print(f'[OK] Slice {part} encoded')

        if MEGA_CMD:
            print(f'[MEGA] Uploading part {part}...')
            r = subprocess.run(
                [MEGA_CMD, 'put', out_file, mega_dest + '/'],
                capture_output=True, text=True
            )
            if r.returncode == 0:
                print(f'[MEGA] Part {part} uploaded! ✅')
            else:
                print(f'[MEGA] Upload failed: {r.stderr.strip()}')

print()
print('[DONE] All videos processed!')
