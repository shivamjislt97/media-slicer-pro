$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

Write-Host "[INFO] Repo root: $RepoRoot"

if (-not (Test-Path "bot/.bot.env")) {
    throw "bot/.bot.env missing. Add TELEGRAM_BOT_TOKEN in bot/.bot.env"
}

if (-not (Test-Path ".venv")) {
    Write-Host "[INFO] Creating virtual environment..."
    py -3 -m venv .venv
}

$Python = Join-Path $RepoRoot ".venv/Scripts/python.exe"

Write-Host "[INFO] Installing dependencies..."
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

$TaskName = "MediaSlicerProTelegramBot"
$StartCmd = Join-Path $RepoRoot "scripts/start_bot.cmd"
$CmdArgs = "/c `"$StartCmd`""

Write-Host "[INFO] Registering scheduled task: $TaskName"
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
} catch {
}

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $CmdArgs
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Media Slicer Pro Telegram Bot" -Force | Out-Null

Write-Host "[INFO] Starting scheduled task..."
Start-ScheduledTask -TaskName $TaskName

Write-Host "[DONE] Bot deployment completed."
