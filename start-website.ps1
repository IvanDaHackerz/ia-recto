# Local development only. Run from the VS Code terminal: .\start-website.ps1
[CmdletBinding()]
param([ValidateRange(1024,65525)][int]$UiPort = 5173,
      [ValidateRange(1024,65525)][int]$ApiPort = 8766,
      [switch]$PlanOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv-item10\Scripts\python.exe'
$appPath = Join-Path $projectRoot 'UI\UX\app'
$logPath = Join-Path $projectRoot '.local\website'
$runtimeProcess = $null
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'The pinned .venv-item10 Python environment is missing.' }
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'Install Node.js with npm before starting the website.' }
function Read-Health([int]$Port) {
    try { return Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2 } catch { return $null }
}
function Test-FreePort([int]$Port) {
    $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Port)
    try { $listener.Start(); return $true } catch { return $false } finally { $listener.Stop() }
}
function Stop-OwnedApi([Diagnostics.Process]$Process) {
    if ($null -eq $Process -or $Process.HasExited) { return }
    # Windows' venv executable may launch the base Python as a child. Stop that
    # verified module child too; stopping only the wrapper can leave a listener.
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $($Process.Id)" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        if ($child.CommandLine -match '(?:^|\s)-m\s+backend\.application\.server(?:\s|$)') {
            Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
        }
    }
    if (-not $Process.HasExited) { Stop-Process -InputObject $Process }
}
Push-Location -LiteralPath $projectRoot
try { $expected = (& $pythonPath -m backend.application.identity | ConvertFrom-Json) }
finally { Pop-Location }
$reuseApi = $false
foreach ($candidate in $ApiPort..($ApiPort + 10)) {
    $health = Read-Health $candidate
    if ($null -ne $health -and $health.project_id -eq $expected.project_id -and $health.status -eq 'ready' -and $health.runtime_signature -eq $expected.runtime_signature) {
        $ApiPort = $candidate; $reuseApi = $true; break
    }
    if (Test-FreePort $candidate) { $ApiPort = $candidate; break }
    if ($candidate -eq ($ApiPort + 10)) { throw 'No free local API port found. Close an old Recto session or choose -ApiPort.' }
}
$reuseUi = $false
foreach ($candidate in $UiPort..($UiPort + 10)) {
    $health = Read-Health $candidate
    if ($null -ne $health -and $health.project_id -eq $expected.project_id -and $health.status -eq 'ready' -and $health.runtime_signature -eq $expected.runtime_signature) {
        $UiPort = $candidate; $reuseUi = $true; break
    }
    if (Test-FreePort $candidate) { $UiPort = $candidate; break }
    if ($candidate -eq ($UiPort + 10)) { throw 'No free local website port found. Choose -UiPort.' }
}
if ($reuseApi -and $UiPort -notin @(5173,5174) -and -not $reuseUi) {
    $reuseApi = $false
    while (-not (Test-FreePort $ApiPort)) { $ApiPort++; if ($ApiPort -gt 65535) { throw 'No free API port.' } }
}
if ($PlanOnly) {
    [pscustomobject]@{ website="http://127.0.0.1:$UiPort"; api="http://127.0.0.1:$ApiPort"; reuseApi=$reuseApi; reuseUi=$reuseUi; runtimeSignature=$expected.runtime_signature } | ConvertTo-Json
    return
}
if ($reuseUi) { Write-Host "Recto is already running: http://127.0.0.1:$UiPort"; return }
$previousTarget = $env:RECTO_API_TARGET
try {
    if (-not $reuseApi) {
        New-Item -ItemType Directory -Force -Path $logPath | Out-Null
        $runtimeProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m','backend.application.server','--port',"$ApiPort",'--ui-port',"$UiPort" -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logPath "backend-$ApiPort.log") -RedirectStandardError (Join-Path $logPath "backend-$ApiPort-error.log")
        $health = $null
        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            if ($runtimeProcess.HasExited) { throw "Backend startup failed. See $logPath\backend-$ApiPort-error.log" }
            $health = Read-Health $ApiPort
            if ($null -ne $health) { break }
            Start-Sleep -Milliseconds 500
        }
        if ($null -eq $health -or $health.runtime_signature -ne $expected.runtime_signature) { throw 'The expected backend did not become ready. Check .local\website logs.' }
    }
    $env:RECTO_API_TARGET = "http://127.0.0.1:$ApiPort"
    Write-Host "Recto development preview: http://127.0.0.1:$UiPort"
    Write-Host "Local API: $env:RECTO_API_TARGET. Occupied ports are skipped; other processes are left running."
    Write-Host 'AI explanations use recorded sources and automated support checks. Independent legal review is pending. Ctrl+C stops this session.'
    Push-Location -LiteralPath $appPath
    try { & npm.cmd run dev -- --host 127.0.0.1 --port $UiPort --strictPort }
    finally { Pop-Location }
} finally {
    $env:RECTO_API_TARGET = $previousTarget
    Stop-OwnedApi $runtimeProcess
}
