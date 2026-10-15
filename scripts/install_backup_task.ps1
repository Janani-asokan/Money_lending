param(
    [string]$TaskName = "MoneyLendingEncryptedBackup",
    [string]$At = "02:00"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = (Get-Command python -ErrorAction Stop).Source
$script = Join-Path $projectRoot "scripts\run_backup.py"
$server = Join-Path $projectRoot "server"
$log = Join-Path $projectRoot "backups\scheduled-backup.log"
$command = "Set-Location -LiteralPath '$server'; & '$python' '$script' *>> '$log'; exit `$LASTEXITCODE"
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -NonInteractive -EncodedCommand $encoded"
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Daily encrypted MongoDB application backup" -Force
Write-Host "Installed $TaskName. Backups run daily at $At and log to $log"
