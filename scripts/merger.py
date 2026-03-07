import subprocess, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
FFMPEG = os.path.join(ROOT, 'tools', 'ffmpeg.exe')
MERGER_DIR = os.path.join(ROOT, 'merger')
OUTPUT_DIR = os.path.join(ROOT, 'output')

output_name = sys.argv[1] if len(sys.argv) > 1 else 'merged_output'

clips = sorted([
    f for f in os.listdir(MERGER_DIR)
    if f.endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'))
])

if not clips:
    print('[ERROR] No video files found in merger\\ folder.')
    input('Press Enter to exit...')
    exit(1)

print(f'[MERGER] Found {len(clips)} clip(s) to merge:')
for idx, clip in enumerate(clips, 1):
    print(f'  {idx}. {clip}')
print()

filelist_path = os.path.join(MERGER_DIR, '_filelist.txt')
with open(filelist_path, 'w') as fl:
    for clip in clips:
        clip_path = os.path.join(MERGER_DIR, clip).replace('\\', '/')
        fl.write(f"file '{clip_path}'\n")

merger_out = os.path.join(OUTPUT_DIR, 'merged')
os.makedirs(merger_out, exist_ok=True)
out_file = os.path.join(merger_out, f'{output_name}.mp4')

print(f'[INFO] Output: {out_file}')
print(f'[INFO] Merging {len(clips)} clips...')
print()

cmd = [
    FFMPEG, '-f', 'concat', '-safe', '0',
    '-i', filelist_path,
    '-c', 'copy',
    '-movflags', '+faststart',
    '-y', out_file
]

subprocess.run(cmd)
os.remove(filelist_path)

if os.path.exists(out_file):
    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f'[OK] Merged successfully!')
    print(f'[OK] Output: {out_file}')
    print(f'[OK] Size: {size_mb:.1f} MB')
else:
    print('[ERROR] Merge failed.')
