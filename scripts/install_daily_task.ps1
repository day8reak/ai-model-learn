param(
    [string]$TaskName = "AI-Model-Learn-Daily",
    [Parameter(Mandatory=$true)][string]$Distro,
    [Parameter(Mandatory=$true)][string]$LinuxUser,
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [string]$GitHubRepository = "",
    [switch]$UpdateExisting
)

$ErrorActionPreference = "Stop"
if ((Get-TimeZone).Id -ne "China Standard Time") {
    throw "Windows must use China Standard Time for this 09:00 local trigger."
}
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask -and -not $UpdateExisting) {
    throw "Task already exists. Use -UpdateExisting to replace its action while preserving its schedule."
}
if ($GitHubRepository -and $GitHubRepository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') {
    throw "GitHubRepository must have the form owner/repository."
}
foreach ($value in @($Distro, $LinuxUser, $ProjectPath)) {
    if ($value -match '["\r\n]') { throw "Unexpected quote or newline in task argument." }
}

# Launch through PowerShell: direct wsl.exe invocation failed in Task Scheduler
# on the initial host. Capture startup errors as well as the Python exit code.
$configJson = @{Distro=$Distro; LinuxUser=$LinuxUser; ProjectPath=$ProjectPath; GitHubRepository=$GitHubRepository} | ConvertTo-Json -Compress
$configEncoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($configJson))
$launcherTemplate = @'
$ErrorActionPreference = "Continue"
$config = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__CONFIG__')) | ConvertFrom-Json
$logDir = Join-Path $env:LOCALAPPDATA "ai-model-learn"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "launcher.log"
"Started: $(Get-Date -Format o)" | Out-File -FilePath $log -Encoding utf8 -Append
$reportDay = Get-Date -Format 'yyyy-MM-dd'
$output = & "$env:SystemRoot\System32\wsl.exe" -d $config.Distro -u $config.LinuxUser --exec /usr/bin/python3 ($config.ProjectPath + "/scripts/daily_learning.py") 2>&1
$result = $LASTEXITCODE
$output | Out-File -FilePath $log -Encoding utf8 -Append
"Exit: $result" | Out-File -FilePath $log -Encoding utf8 -Append
if ($result -eq 0 -and $config.GitHubRepository) {
    $syncMessage = "Synced learning documents: git@github.com:$($config.GitHubRepository).git"
    $published = ($output | Out-String).Contains($syncMessage)
    $marker = Join-Path $logDir "last-opened-report.txt"
    $monthPath = $reportDay.Substring(0, 7).Replace('-', '/')
    $url = "https://github.com/$($config.GitHubRepository)/blob/main/daily/$monthPath/$reportDay.md"
    $alreadyOpened = (Test-Path -LiteralPath $marker) -and ((Get-Content -LiteralPath $marker -Raw).Trim() -eq $url)
    if ($published -and -not $alreadyOpened) {
        try {
            Start-Process -FilePath $url -ErrorAction Stop
            $url | Set-Content -LiteralPath $marker -Encoding utf8 -ErrorAction Stop
            "Opened report: $url" | Out-File -FilePath $log -Encoding utf8 -Append
        } catch {
            "Could not open report: $($_.Exception.Message)" | Out-File -FilePath $log -Encoding utf8 -Append
            exit 1
        }
    } elseif (-not $published) {
        "Report not opened: GitHub publication was not confirmed." | Out-File -FilePath $log -Encoding utf8 -Append
    } else {
        "Report already opened today; browser launch skipped." | Out-File -FilePath $log -Encoding utf8 -Append
    }
}
exit $result
'@
$launcher = $launcherTemplate.Replace('__CONFIG__', $configEncoded)
$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($launcher))
$powershell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$action = New-ScheduledTaskAction -Execute $powershell -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand $encodedCommand"
if ($existingTask) {
    $backupDir = Join-Path $env:LOCALAPPDATA "ai-model-learn\task-backups"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    $backupName = ($TaskName -replace '[^A-Za-z0-9_.-]', '_') + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.xml'
    Export-ScheduledTask -TaskName $TaskName -TaskPath $existingTask.TaskPath | Set-Content -LiteralPath (Join-Path $backupDir $backupName) -Encoding utf8
    Set-ScheduledTask -TaskName $TaskName -TaskPath $existingTask.TaskPath -Action $action | Out-Null
} else {
    $next = (Get-Date).Date.AddHours(9)
    if ($next -le (Get-Date)) { $next = $next.AddDays(1) }
    $trigger = New-ScheduledTaskTrigger -Daily -At $next
    $principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 15)
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Daily LLM inference lesson and verified news, 09:00 Asia/Shanghai; local repository output." | Out-Null
}
$task = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName
[pscustomobject]@{
    TaskName = $task.TaskName
    State = $task.State.ToString()
    NextRunTime = $info.NextRunTime.ToString("o")
    Launcher = "PowerShell -> WSL -> Python -> Codex"
    Distro = $Distro
    ProjectPath = $ProjectPath
    HiddenWindow = $true
    GitHubRepository = $GitHubRepository
} | ConvertTo-Json
