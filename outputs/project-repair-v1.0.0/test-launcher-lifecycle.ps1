$ErrorActionPreference = 'Stop'
$projectRoot = 'C:\IA'
$parseErrors = $null
$tokens = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $projectRoot 'start-website.ps1'),[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count) { throw 'Launcher syntax errors.' }
$definition = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Stop-OwnedApi' },$true)
if ($null -eq $definition) { throw 'Owned-process shutdown function missing.' }
. ([scriptblock]::Create($definition.Extent.Text))
$probe = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0)
$probe.Start(); $testPort = $probe.LocalEndpoint.Port; $probe.Stop()
$testProcess = $null
try {
    $testProcess = Start-Process -FilePath (Join-Path $projectRoot '.venv-item10\Scripts\python.exe') -ArgumentList '-m','backend.application.server','--port',"$testPort" -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot '.local\website\lifecycle-test.log') -RedirectStandardError (Join-Path $projectRoot '.local\website\lifecycle-test-error.log')
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($testProcess.HasExited) { throw 'Test API exited before readiness.' }
        try { $health = Invoke-RestMethod -Uri "http://127.0.0.1:$testPort/api/health" -TimeoutSec 1; $ready = $health.project_id -eq 'recto-local-ia'; if ($ready) { break } } catch {}
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw 'Test API did not become ready.' }
    $listener = Get-NetTCPConnection -State Listen -LocalPort $testPort
    Stop-OwnedApi $testProcess
    Start-Sleep -Milliseconds 250
    if (Get-NetTCPConnection -State Listen -LocalPort $testPort -ErrorAction SilentlyContinue) { throw 'Owned API listener survived shutdown.' }
    [pscustomobject]@{ passed=$true; port=$testPort; wrapperPid=$testProcess.Id; listenerPid=$listener.OwningProcess; listenerStopped=$true } | ConvertTo-Json
} finally { Stop-OwnedApi $testProcess }
