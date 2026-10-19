$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python=Join-Path $root '.venv-item10\Scripts\python.exe'
$known=Get-Content (Join-Path $root '.local\website\repair-processes.json') -Raw | ConvertFrom-Json
$listeners=@(Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue)
foreach ($listener in $listeners) {
    $process=Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)"
    $parent=Get-CimInstance Win32_Process -Filter "ProcessId = $($process.ParentProcessId)"
    if ($process.CommandLine -notmatch '-m\s+backend\.application\.server\s+--port\s+8766' -or
        $parent.ProcessId -ne $known.apiPid -or $parent.ExecutablePath -ne $python) {
        throw 'The port is not owned by the recorded Recto API. No process was stopped.'
    }
    Stop-Process -Id $process.ProcessId
    if (Get-Process -Id $parent.ProcessId -ErrorAction SilentlyContinue) {Stop-Process -Id $parent.ProcessId}
}
$api=Start-Process -FilePath $python -ArgumentList @('-m','backend.application.server','--port','8766') -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $root '.local\website\holiday-api.log') -RedirectStandardError (Join-Path $root '.local\website\holiday-api-error.log')
$known.apiPid=$api.Id
$known | ConvertTo-Json | Set-Content (Join-Path $root '.local\website\repair-processes.json')
for ($attempt=0;$attempt -lt 40;$attempt++) {
    try {$health=Invoke-RestMethod 'http://127.0.0.1:8766/api/health' -TimeoutSec 1;break} catch {Start-Sleep -Milliseconds 500}
}
if (-not $health) {throw 'API startup did not complete. Inspect the holiday API log.'}
$health | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $PSScriptRoot 'live-health.json')
$expected=(& $python -m backend.application.identity | ConvertFrom-Json)
if ($health.runtime_signature -ne $expected.runtime_signature) {throw 'The API did not load the current application.'}
Write-Output "Current Recto API ready on 8766; existing Vite processes preserved."
