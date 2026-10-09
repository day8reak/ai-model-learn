param(
    [string]$TaskName = "AI-Model-Learn-Daily",
    [Parameter(Mandatory=$true)][string]$Distro,
    [Parameter(Mandatory=$true)][string]$LinuxUser,
    [Parameter(Mandatory=$true)][string]$ProjectPath
)

$ErrorActionPreference = "Stop"
if ((Get-TimeZone).Id -ne "China Standard Time") {
    throw "Windows must use China Standard Time for this 09:00 local trigger."
}
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    throw "Task already exists. Inspect it before changing its configuration."
}
foreach ($value in @($Distro, $LinuxUser, $ProjectPath)) {
    if ($value -match '["\r\n]') { throw "Unexpected quote or newline in task argument." }
}

# Launch through PowerShell: direct wsl.exe invocation failed in Task Scheduler
# on the initial host. Capture startup errors as well as the Python exit code.
$configJson = @{Distro=$Distro; LinuxUser=$LinuxUser; ProjectPath=$ProjectPath} | ConvertTo-Json -Compress
$configEncoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($configJson))
$launcherTemplate = @'
$ErrorActionPreference = "Continue"
$config = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__CONFIG__')) | ConvertFrom-Json
$logDir = Join-Path $env:LOCALAPPDATA "ai-model-learn"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "launcher.log"
"Started: $(Get-Date -Format o)" | Out-File -FilePath $log -Encoding utf8 -Append
& "$env:SystemRoot\System32\wsl.exe" -d $config.Distro -u $config.LinuxUser --exec /usr/bin/python3 ($config.ProjectPath + "/scripts/daily_learning.py") 2>&1 | Out-File -FilePath $log -Encoding utf8 -Append
$result = $LASTEXITCODE
"Exit: $result" | Out-File -FilePath $log -Encoding utf8 -Append
exit $result
'@
$launcher = $launcherTemplate.Replace('__CONFIG__', $configEncoded)
$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($launcher))
$powershell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$action = New-ScheduledTaskAction -Execute $powershell -Argument "-NoProfile -NonInteractive -EncodedCommand $encodedCommand"
$next = (Get-Date).Date.AddHours(9)
if ($next -le (Get-Date)) { $next = $next.AddDays(1) }
$trigger = New-ScheduledTaskTrigger -Daily -At $next
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Daily LLM inference lesson and verified news, 09:00 Asia/Shanghai; local repository output." | Out-Null
$task = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName
[pscustomobject]@{
    TaskName = $task.TaskName
    State = $task.State.ToString()
    NextRunTime = $info.NextRunTime.ToString("o")
    Launcher = "PowerShell -> WSL -> Python -> Codex"
    Distro = $Distro
    ProjectPath = $ProjectPath
} | ConvertTo-Json
