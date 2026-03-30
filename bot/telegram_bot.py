import asyncio
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = Path(os.getenv("BOT_DATA_DIR", str(ROOT)))
INPUT_ROOT = DATA_ROOT / "input" / "telegram"
OUTPUT_ROOT = DATA_ROOT / "output" / "telegram"
MERGER_DIR = DATA_ROOT / "merger"
TRANSFER_ROOT = OUTPUT_ROOT / "transfers"

ALLOWED_USERS_RAW = os.getenv("BOT_ALLOWED_USERS", "").strip()
ALLOWED_USERS = {
    int(x.strip())
    for x in ALLOWED_USERS_RAW.split(",")
    if x.strip().isdigit()
}


def _resolve_binary(binary_name: str) -> str:
    local = ROOT / "tools" / f"{binary_name}.exe"
    if local.exists():
        return str(local)

    on_path = shutil.which(binary_name)
    if on_path:
        return on_path

    raise RuntimeError(f"{binary_name} not found. Put it in tools/ or install in PATH.")


try:
    FFMPEG = _resolve_binary("ffmpeg")
    FFPROBE = _resolve_binary("ffprobe")
except RuntimeError:
    FFMPEG = ""
    FFPROBE = ""


def _resolve_mega_client() -> str:
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\MEGAcmd\MEGAclient.exe"),
        r"C:\Program Files\MEGAcmd\MEGAclient.exe",
        r"C:\Program Files (x86)\MEGAcmd\MEGAclient.exe",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    on_path = shutil.which("MEGAclient")
    if on_path:
        return on_path

    return ""


MEGA_CMD = _resolve_mega_client()
RCLONE_CMD = shutil.which("rclone") or ""


SUPPORTED_VIDEO_EXT = (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm")
MAX_TELEGRAM_FILE_BYTES = 49 * 1024 * 1024


def parse_time(value: str) -> float:
    value = value.strip()
    if not value:
        raise ValueError("time value is empty")

    if ":" in value:
        parts = value.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])

    return float(value)


def seconds_to_label(total_seconds: float) -> str:
    total_seconds = int(total_seconds)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}-{m:02d}-{s:02d}"


def is_allowed_user(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS


def user_input_dir(user_id: int) -> Path:
    path = INPUT_ROOT / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_output_dir(user_id: int) -> Path:
    path = OUTPUT_ROOT / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return await asyncio.to_thread(
        subprocess.run,
        command,
        capture_output=True,
        text=True,
    )


async def probe_duration(video_path: Path) -> float:
    command = [
        FFPROBE,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = await run_command(command)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")

    raw = result.stdout.strip()
    if not raw:
        raise RuntimeError("Empty duration from ffprobe")

    return float(raw)


async def send_files_if_small(update: Update, files: Iterable[Path]) -> None:
    for file_path in files:
        if not file_path.exists():
            continue

        size = file_path.stat().st_size
        if size > MAX_TELEGRAM_FILE_BYTES:
            await update.effective_message.reply_text(
                f"File {file_path.name} bahut bada hai ({size / 1024 / 1024:.1f} MB), Telegram limit cross ho gayi."
            )
            continue

        with file_path.open("rb") as f:
            await update.effective_message.reply_document(document=f, filename=file_path.name)


async def mega_login(email: str, password: str) -> tuple[bool, str]:
    if not MEGA_CMD:
        return False, "MEGAcmd install nahi mila. https://mega.io/cmd install karo."

    login_result = await run_command([MEGA_CMD, "login", email, password])
    if login_result.returncode != 0:
        error = login_result.stderr.strip() or login_result.stdout.strip() or "Unknown login error"
        return False, f"MEGA login failed: {error[:250]}"

    whoami_result = await run_command([MEGA_CMD, "whoami"])
    if whoami_result.returncode != 0:
        return False, "MEGA login verify nahi ho paya."

    return True, whoami_result.stdout.strip() or "Logged in"


def _parse_drive_folder_id(value: str) -> str:
    value = value.strip()
    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", value)
    if match:
        return match.group(1)

    match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", value)
    if match:
        return match.group(1)

    return value


async def download_mega_link(dest_dir: Path, mega_link: str) -> tuple[bool, str, Path | None]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    before = {p.resolve() for p in dest_dir.glob("*") if p.is_file()}

    result = await run_command([MEGA_CMD, "get", mega_link, str(dest_dir)])
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "MEGA get failed"
        return False, err[:350], None

    after_files = [p.resolve() for p in dest_dir.glob("*") if p.is_file() and p.resolve() not in before]
    if after_files:
        latest = max(after_files, key=lambda p: p.stat().st_mtime)
        return True, "Downloaded", latest

    all_files = [p.resolve() for p in dest_dir.glob("*") if p.is_file()]
    if not all_files:
        return False, "Download complete but file locate nahi hui.", None

    latest = max(all_files, key=lambda p: p.stat().st_mtime)
    return True, "Downloaded", latest


async def download_google_drive_link(dest_dir: Path, drive_link: str) -> tuple[bool, str, Path | None]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_file = dest_dir / "gdrive_input.bin"

    cmd = [
        sys.executable,
        "-m",
        "gdown",
        "--fuzzy",
        drive_link,
        "-O",
        str(out_file),
    ]
    result = await run_command(cmd)
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "gdown failed"
        return False, err[:350], None

    if not out_file.exists() or out_file.stat().st_size == 0:
        return False, "Google Drive file download nahi hui.", None

    return True, "Downloaded", out_file


async def upload_file_to_mega(local_file: Path, remote_folder: str) -> tuple[bool, str]:
    mkdir_result = await run_command([MEGA_CMD, "mkdir", "-p", remote_folder])
    if mkdir_result.returncode != 0:
        return False, "MEGA remote folder create nahi hua."

    put_result = await run_command([MEGA_CMD, "put", str(local_file), f"{remote_folder}/"])
    if put_result.returncode != 0:
        err = put_result.stderr.strip() or put_result.stdout.strip() or "MEGA put failed"
        return False, err[:350]

    return True, "Uploaded"


async def upload_file_to_google_drive(local_file: Path, folder_ref: str) -> tuple[bool, str]:
    if not RCLONE_CMD:
        return False, "rclone install nahi mila. MEGA -> Google Drive ke liye rclone required hai."

    remotes = await run_command([RCLONE_CMD, "listremotes"])
    if remotes.returncode != 0 or "gdrive:" not in remotes.stdout:
        return False, "rclone remote 'gdrive:' configured nahi hai."

    folder_id = _parse_drive_folder_id(folder_ref)
    copy_cmd = [
        RCLONE_CMD,
        "copyto",
        str(local_file),
        f"gdrive:{local_file.name}",
        "--drive-root-folder-id",
        folder_id,
    ]
    result = await run_command(copy_cmd)
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "Google Drive upload failed"
        return False, err[:350]

    return True, "Uploaded"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✂️ Slice Video", callback_data="menu_slice")],
            [InlineKeyboardButton("🎬 Trim Clip", callback_data="menu_trim")],
            [InlineKeyboardButton("🧩 Custom Multi Slices", callback_data="menu_custom")],
            [InlineKeyboardButton("🎵 Extract Audio", callback_data="menu_audio")],
            [InlineKeyboardButton("🧱 Merge (merger folder)", callback_data="menu_merge")],
            [InlineKeyboardButton("☁️ Google Drive -> MEGA", callback_data="menu_gdrive_to_mega")],
            [InlineKeyboardButton("🔄 MEGA -> Google Drive", callback_data="menu_mega_to_gdrive")],
            [
                InlineKeyboardButton("📊 Status", callback_data="menu_status"),
                InlineKeyboardButton("❓ Help", callback_data="menu_help"),
            ],
        ]
    )


def duration_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏱️ 5 min (300s)", callback_data="dur_300"),
                InlineKeyboardButton("⏱️ 7m29s (449s)", callback_data="dur_449"),
            ],
            [
                InlineKeyboardButton("⏱️ 10 min (600s)", callback_data="dur_600"),
                InlineKeyboardButton("🛠️ Custom", callback_data="dur_custom"),
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="menu_back")],
        ]
    )


def audio_format_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎧 MP3", callback_data="audio_fmt_mp3"),
                InlineKeyboardButton("🔊 AAC", callback_data="audio_fmt_aac"),
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="menu_back")],
        ]
    )


def audio_scope_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎼 Full Audio", callback_data="audio_scope_full")],
            [InlineKeyboardButton("🕒 Specific Range", callback_data="audio_scope_range")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None or not is_allowed_user(user.id):
        await update.effective_message.reply_text("Aapko is bot ka access nahi diya gaya hai.")
        return

    context.user_data.clear()
    await update.effective_message.reply_text(
        "Media Slicer Pro Bot ready. Neeche buttons se feature choose karo.",
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Step-by-step guide:\n"
        "1) Button se feature select karo\n"
        "2) Bot pehle MEGA credentials maangega: email,password\n"
        "3) Video processing modes me input sirf MEGA file link do\n"
        "4) Transfer modes:\n"
        "   - Google Drive -> MEGA: Drive link do\n"
        "   - MEGA -> Google Drive: MEGA link + Google Drive folder link/ID do\n"
        "5) Bot har step pe next prompt dega\n\n"
        "Time format: HH:MM:SS ya seconds\n"
        "Custom slices format: start,end;start,end"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ffmpeg_ok = bool(FFMPEG)
    ffprobe_ok = bool(FFPROBE)
    mega_ok = bool(MEGA_CMD)
    rclone_ok = bool(RCLONE_CMD)
    state = context.user_data.get("state", "idle")
    await update.effective_message.reply_text(
        f"Status:\n"
        f"- ffmpeg: {'OK' if ffmpeg_ok else 'MISSING'}\n"
        f"- ffprobe: {'OK' if ffprobe_ok else 'MISSING'}\n"
        f"- megacmd: {'OK' if mega_ok else 'MISSING'}\n"
        f"- rclone: {'OK' if rclone_ok else 'MISSING'}\n"
        f"- state: {state}\n"
        f"- data root: {DATA_ROOT}"
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.effective_message.reply_text(
        "Current operation cancel ho gaya.",
        reply_markup=main_menu_keyboard(),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.from_user is None or not is_allowed_user(query.from_user.id):
        await query.edit_message_text("Aapko access nahi diya gaya hai.")
        return

    data = query.data or ""

    if data in {"menu_back", "cancel"}:
        context.user_data.clear()
        await query.edit_message_text(
            "Main menu", reply_markup=main_menu_keyboard()
        )
        return

    if data == "menu_help":
        await query.edit_message_text(
            "Help: mode choose karo -> MEGA credentials do -> MEGA/GDrive link do -> bot guide follow karo.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu_status":
        ffmpeg_ok = bool(FFMPEG)
        ffprobe_ok = bool(FFPROBE)
        mega_ok = bool(MEGA_CMD)
        rclone_ok = bool(RCLONE_CMD)
        state = context.user_data.get("state", "idle")
        await query.edit_message_text(
            f"ffmpeg: {'OK' if ffmpeg_ok else 'MISSING'}\n"
            f"ffprobe: {'OK' if ffprobe_ok else 'MISSING'}\n"
            f"megacmd: {'OK' if mega_ok else 'MISSING'}\n"
            f"rclone: {'OK' if rclone_ok else 'MISSING'}\n"
            f"state: {state}",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu_slice":
        context.user_data.clear()
        context.user_data["state"] = "slice_pick_duration"
        await query.edit_message_text(
            "Slice duration choose karo:",
            reply_markup=duration_keyboard(),
        )
        return

    if data.startswith("dur_"):
        if data == "dur_custom":
            context.user_data["state"] = "slice_custom_duration"
            await query.edit_message_text(
                "Custom duration seconds me bhejo. Example: 420"
            )
            return

        duration = int(data.split("_")[1])
        context.user_data["mode"] = "slice"
        context.user_data["slice_duration"] = duration
        context.user_data["state"] = "await_mega_credentials"
        await query.edit_message_text(
            f"Duration set: {duration}s\nAb MEGA credentials bhejo: email,password"
        )
        return

    if data == "menu_trim":
        context.user_data.clear()
        context.user_data["mode"] = "trim"
        context.user_data["state"] = "await_mega_credentials"
        await query.edit_message_text("Trim mode on. MEGA credentials bhejo: email,password")
        return

    if data == "menu_custom":
        context.user_data.clear()
        context.user_data["mode"] = "custom"
        context.user_data["state"] = "await_mega_credentials"
        await query.edit_message_text(
            "Custom slices mode on. MEGA credentials bhejo: email,password"
        )
        return

    if data == "menu_audio":
        context.user_data.clear()
        context.user_data["mode"] = "audio"
        context.user_data["state"] = "audio_pick_format"
        await query.edit_message_text(
            "Audio format choose karo:",
            reply_markup=audio_format_keyboard(),
        )
        return

    if data.startswith("audio_fmt_"):
        fmt = data.replace("audio_fmt_", "")
        context.user_data["audio_format"] = fmt
        context.user_data["state"] = "await_mega_credentials"
        await query.edit_message_text(
            f"Format set: {fmt.upper()}\nAb MEGA credentials bhejo: email,password"
        )
        return

    if data == "audio_scope_full":
        context.user_data["audio_scope"] = "full"
        await process_audio(update, context)
        return

    if data == "audio_scope_range":
        context.user_data["state"] = "await_audio_range"
        await query.edit_message_text(
            "Range bhejo: start,end\nExample: 00:01:00,00:03:30"
        )
        return

    if data == "menu_merge":
        await query.edit_message_text("Merge process start ho raha hai...")
        await process_merge(update, context)
        return

    if data == "menu_gdrive_to_mega":
        context.user_data.clear()
        context.user_data["mode"] = "gdrive_to_mega"
        context.user_data["state"] = "await_mega_credentials"
        await query.edit_message_text(
            "Google Drive -> MEGA transfer mode.\nMEGA credentials bhejo: email,password"
        )
        return

    if data == "menu_mega_to_gdrive":
        context.user_data.clear()
        context.user_data["mode"] = "mega_to_gdrive"
        context.user_data["state"] = "await_mega_credentials"
        await query.edit_message_text(
            "MEGA -> Google Drive transfer mode.\nMEGA credentials bhejo: email,password"
        )
        return


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or not is_allowed_user(update.effective_user.id):
        await update.effective_message.reply_text("Aapko access nahi diya gaya hai.")
        return

    state = context.user_data.get("state", "")
    text = (update.effective_message.text or "").strip()

    if state == "await_mega_credentials":
        try:
            email, password = [x.strip() for x in text.split(",", 1)]
            if not email or not password:
                raise ValueError("missing")
        except Exception:
            await update.effective_message.reply_text(
                "Invalid format. MEGA credentials aise bhejo: email,password"
            )
            return

        await update.effective_message.reply_text("MEGA login verify ho raha hai...")
        ok, login_msg = await mega_login(email, password)
        if not ok:
            await update.effective_message.reply_text(login_msg)
            return

        context.user_data["mega_email"] = email
        mode = context.user_data.get("mode")

        if mode in {"slice", "trim", "custom", "audio"}:
            context.user_data["state"] = "await_mega_video_link"
            await update.effective_message.reply_text(
                "Login successful. Ab MEGA video link bhejo (video input ke liye MEGA link required hai)."
            )
            return

        if mode == "gdrive_to_mega":
            context.user_data["state"] = "await_gdrive_link"
            await update.effective_message.reply_text(
                "Login successful. Ab Google Drive file link bhejo."
            )
            return

        if mode == "mega_to_gdrive":
            context.user_data["state"] = "await_mega_source_link"
            await update.effective_message.reply_text(
                "Login successful. Ab MEGA file link bhejo jo Google Drive me upload karna hai."
            )
            return

        await update.effective_message.reply_text("Mode missing. /start bhejo.")
        return

    if state == "await_mega_video_link":
        mode = context.user_data.get("mode")
        if mode not in {"slice", "trim", "custom", "audio"}:
            await update.effective_message.reply_text("Mode invalid. /start bhejo.")
            return

        if not FFMPEG or not FFPROBE:
            await update.effective_message.reply_text(
                "ffmpeg/ffprobe missing hai. tools folder check karo."
            )
            return

        user_id = update.effective_user.id
        in_dir = user_input_dir(user_id)
        out_dir = user_output_dir(user_id)

        await update.effective_message.reply_text("MEGA link se video download ho raha hai...")
        ok, msg, file_path = await download_mega_link(in_dir, text)
        if not ok or file_path is None:
            await update.effective_message.reply_text(f"Download failed: {msg}")
            return

        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_VIDEO_EXT:
            await update.effective_message.reply_text(
                "Downloaded file supported video format me nahi hai."
            )
            return

        context.user_data["source_path"] = str(file_path)
        context.user_data["result_dir"] = str(out_dir)

        if mode == "slice":
            await update.effective_message.reply_text("Processing slice...")
            await process_slice(update, context)
            return

        if mode == "trim":
            context.user_data["state"] = "await_trim_range"
            await update.effective_message.reply_text(
                "Range bhejo: start,end\nExample: 00:02:00,00:05:00"
            )
            return

        if mode == "custom":
            context.user_data["state"] = "await_custom_ranges"
            await update.effective_message.reply_text(
                "Custom ranges bhejo: start,end;start,end\nExample: 00:01:00,00:02:00;120,180"
            )
            return

        if mode == "audio":
            context.user_data["state"] = "await_audio_scope"
            await update.effective_message.reply_text(
                "Full audio ya specific range?",
                reply_markup=audio_scope_keyboard(),
            )
            return

    if state == "await_gdrive_link":
        user_id = update.effective_user.id
        transfer_dir = TRANSFER_ROOT / str(user_id) / "gdrive_to_mega"
        await update.effective_message.reply_text("Google Drive file download ho rahi hai...")
        ok, msg, local_file = await download_google_drive_link(transfer_dir, text)
        if not ok or local_file is None:
            await update.effective_message.reply_text(f"Google Drive download failed: {msg}")
            return

        await update.effective_message.reply_text("MEGA par upload ho raha hai...")
        ok, upload_msg = await upload_file_to_mega(local_file, "/media-slicer-pro/telegram-transfers")
        if not ok:
            await update.effective_message.reply_text(f"MEGA upload failed: {upload_msg}")
            return

        context.user_data.clear()
        await update.effective_message.reply_text(
            "Transfer complete: Google Drive -> MEGA done.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if state == "await_mega_source_link":
        user_id = update.effective_user.id
        transfer_dir = TRANSFER_ROOT / str(user_id) / "mega_to_gdrive"
        await update.effective_message.reply_text("MEGA file download ho rahi hai...")
        ok, msg, local_file = await download_mega_link(transfer_dir, text)
        if not ok or local_file is None:
            await update.effective_message.reply_text(f"MEGA download failed: {msg}")
            return

        context.user_data["transfer_local_file"] = str(local_file)
        context.user_data["state"] = "await_gdrive_folder_link"
        await update.effective_message.reply_text(
            "Ab Google Drive folder link ya folder ID bhejo jahan upload karna hai."
        )
        return

    if state == "await_gdrive_folder_link":
        local_file_raw = context.user_data.get("transfer_local_file")
        if not local_file_raw:
            await update.effective_message.reply_text("Local transfer file missing. /start bhejo.")
            return

        local_file = Path(local_file_raw)
        if not local_file.exists():
            await update.effective_message.reply_text("Transfer file missing ho gayi. Dobara try karo.")
            return

        await update.effective_message.reply_text("Google Drive upload ho raha hai...")
        ok, upload_msg = await upload_file_to_google_drive(local_file, text)
        if not ok:
            await update.effective_message.reply_text(f"Google Drive upload failed: {upload_msg}")
            return

        context.user_data.clear()
        await update.effective_message.reply_text(
            "Transfer complete: MEGA -> Google Drive done.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if state == "slice_custom_duration":
        if not text.isdigit() or int(text) <= 0:
            await update.effective_message.reply_text("Valid positive seconds bhejo.")
            return

        context.user_data["mode"] = "slice"
        context.user_data["slice_duration"] = int(text)
        context.user_data["state"] = "await_mega_credentials"
        await update.effective_message.reply_text("Duration set. Ab MEGA credentials bhejo: email,password")
        return

    if state == "await_trim_range":
        try:
            start_raw, end_raw = [x.strip() for x in text.split(",", 1)]
            start_sec = parse_time(start_raw)
            end_sec = parse_time(end_raw)
            if end_sec <= start_sec:
                raise ValueError("end must be greater")
            context.user_data["trim_start"] = start_sec
            context.user_data["trim_end"] = end_sec
        except Exception:
            await update.effective_message.reply_text(
                "Invalid format. Example: 00:02:00,00:05:00"
            )
            return

        await process_trim(update, context)
        return

    if state == "await_custom_ranges":
        try:
            ranges = []
            for chunk in text.split(";"):
                if not chunk.strip():
                    continue
                a, b = [x.strip() for x in chunk.split(",", 1)]
                start = parse_time(a)
                end = parse_time(b)
                if end <= start:
                    raise ValueError("bad range")
                ranges.append((start, end))
            if not ranges:
                raise ValueError("empty")
            context.user_data["custom_ranges"] = ranges
        except Exception:
            await update.effective_message.reply_text(
                "Invalid format. Example: 00:01:00,00:02:00;120,180"
            )
            return

        await process_custom(update, context)
        return

    if state == "await_audio_range":
        try:
            start_raw, end_raw = [x.strip() for x in text.split(",", 1)]
            start_sec = parse_time(start_raw)
            end_sec = parse_time(end_raw)
            if end_sec <= start_sec:
                raise ValueError("end must be greater")
            context.user_data["audio_scope"] = "range"
            context.user_data["audio_start"] = start_sec
            context.user_data["audio_end"] = end_sec
        except Exception:
            await update.effective_message.reply_text(
                "Invalid format. Example: 00:01:00,00:03:30"
            )
            return

        await process_audio(update, context)
        return

    await update.effective_message.reply_text(
        "Please menu se mode choose karo ya /start bhejo.",
        reply_markup=main_menu_keyboard(),
    )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or not is_allowed_user(update.effective_user.id):
        await update.effective_message.reply_text("Aapko access nahi diya gaya hai.")
        return

    await update.effective_message.reply_text(
        "Video input ke liye direct upload allowed nahi hai.\n"
        "Please mode select karo, phir MEGA credentials do, phir MEGA video link bhejo."
    )


async def process_slice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    source_path = Path(context.user_data["source_path"])
    duration_each = int(context.user_data.get("slice_duration", 449))

    base_name = source_path.stem
    out_dir = Path(context.user_data["result_dir"]) / base_name
    out_dir.mkdir(parents=True, exist_ok=True)

    total_duration = await probe_duration(source_path)
    total_slices = max(1, math.ceil(total_duration / duration_each))

    produced = []
    for part in range(1, total_slices + 1):
        start = (part - 1) * duration_each
        out_file = out_dir / f"{base_name}_part_{part}.mp4"

        command = [FFMPEG, "-ss", str(start), "-i", str(source_path)]
        if part < total_slices:
            command += ["-t", str(duration_each)]
        command += [
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            "-reset_timestamps",
            "1",
            "-movflags",
            "+faststart",
            "-y",
            str(out_file),
        ]

        result = await run_command(command)
        if result.returncode != 0:
            await update.effective_message.reply_text(
                f"Slice failed at part {part}: {result.stderr[:700]}"
            )
            return
        produced.append(out_file)

    await update.effective_message.reply_text(
        f"Slicing complete: {len(produced)} file(s). Sending files..."
    )
    await send_files_if_small(update, produced[:10])

    context.user_data.clear()
    await update.effective_message.reply_text("Done.", reply_markup=main_menu_keyboard())


async def process_trim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    source_path = Path(context.user_data["source_path"])
    start = float(context.user_data["trim_start"])
    end = float(context.user_data["trim_end"])

    base_name = source_path.stem
    out_dir = Path(context.user_data["result_dir"]) / base_name
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"{base_name}_clip_{seconds_to_label(start)}_to_{seconds_to_label(end)}.mp4"

    command = [
        FFMPEG,
        "-ss",
        str(start),
        "-i",
        str(source_path),
        "-t",
        str(end - start),
        "-c",
        "copy",
        "-avoid_negative_ts",
        "make_zero",
        "-reset_timestamps",
        "1",
        "-movflags",
        "+faststart",
        "-y",
        str(out_file),
    ]

    result = await run_command(command)
    if result.returncode != 0:
        await update.effective_message.reply_text(f"Trim failed: {result.stderr[:700]}")
        return

    await update.effective_message.reply_text("Trim complete. Sending file...")
    await send_files_if_small(update, [out_file])

    context.user_data.clear()
    await update.effective_message.reply_text("Done.", reply_markup=main_menu_keyboard())


async def process_custom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    source_path = Path(context.user_data["source_path"])
    ranges = context.user_data["custom_ranges"]

    base_name = source_path.stem
    out_dir = Path(context.user_data["result_dir"]) / base_name
    out_dir.mkdir(parents=True, exist_ok=True)

    produced = []
    for start, end in ranges:
        out_file = out_dir / f"{base_name}_clip_{seconds_to_label(start)}_to_{seconds_to_label(end)}.mp4"
        command = [
            FFMPEG,
            "-ss",
            str(start),
            "-i",
            str(source_path),
            "-t",
            str(end - start),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            "-reset_timestamps",
            "1",
            "-movflags",
            "+faststart",
            "-y",
            str(out_file),
        ]

        result = await run_command(command)
        if result.returncode != 0:
            await update.effective_message.reply_text(
                f"Custom slice failed: {result.stderr[:700]}"
            )
            return
        produced.append(out_file)

    await update.effective_message.reply_text(
        f"Custom slicing complete: {len(produced)} file(s). Sending files..."
    )
    await send_files_if_small(update, produced[:10])

    context.user_data.clear()
    await update.effective_message.reply_text("Done.", reply_markup=main_menu_keyboard())


async def process_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    source_path = Path(context.user_data["source_path"])
    audio_format = context.user_data.get("audio_format", "mp3")
    scope = context.user_data.get("audio_scope", "full")

    base_name = source_path.stem
    out_dir = Path(context.user_data["result_dir"]) / base_name
    out_dir.mkdir(parents=True, exist_ok=True)

    if scope == "range":
        start = float(context.user_data["audio_start"])
        end = float(context.user_data["audio_end"])
        out_file = out_dir / (
            f"{base_name}_audio_{seconds_to_label(start)}_to_{seconds_to_label(end)}.{audio_format}"
        )
    else:
        start = None
        end = None
        out_file = out_dir / f"{base_name}_audio_full.{audio_format}"

    command = [FFMPEG]
    if start is not None:
        command += ["-ss", str(start)]
    command += ["-i", str(source_path)]
    if start is not None and end is not None:
        command += ["-t", str(end - start)]

    if audio_format == "mp3":
        command += ["-vn", "-c:a", "libmp3lame", "-b:a", "192k"]
    else:
        command += ["-vn", "-c:a", "aac", "-b:a", "192k"]

    command += ["-y", str(out_file)]

    result = await run_command(command)
    if result.returncode != 0:
        await update.effective_message.reply_text(
            f"Audio extraction failed: {result.stderr[:700]}"
        )
        return

    await update.effective_message.reply_text("Audio extraction complete. Sending file...")
    await send_files_if_small(update, [out_file])

    context.user_data.clear()
    await update.effective_message.reply_text("Done.", reply_markup=main_menu_keyboard())


async def process_merge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not MERGER_DIR.exists():
        await update.effective_message.reply_text("merger folder missing hai.")
        return

    clips = sorted([p for p in MERGER_DIR.iterdir() if p.suffix.lower() in SUPPORTED_VIDEO_EXT])
    if not clips:
        await update.effective_message.reply_text("merger folder me clips nahi mile.")
        return

    filelist = MERGER_DIR / "_filelist.txt"
    with filelist.open("w", encoding="utf-8") as f:
        for clip in clips:
            f.write(f"file '{clip.as_posix()}'\n")

    out_dir = OUTPUT_ROOT / "merged"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "merged_output.mp4"

    command = [
        FFMPEG,
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(filelist),
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        "-y",
        str(out_file),
    ]

    result = await run_command(command)
    try:
        filelist.unlink(missing_ok=True)
    except Exception:
        pass

    if result.returncode != 0:
        await update.effective_message.reply_text(f"Merge failed: {result.stderr[:700]}")
        return

    await update.effective_message.reply_text("Merge complete. Sending output...")
    await send_files_if_small(update, [out_file])
    await update.effective_message.reply_text("Done.", reply_markup=main_menu_keyboard())


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    app = build_application(token)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
