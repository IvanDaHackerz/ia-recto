# Repeatable local checks; no provider calls, source approval or training.
[CmdletBinding()]
param([switch]$SkipFrontend)
$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv-item10\Scripts\python.exe'
Push-Location -LiteralPath $PSScriptRoot
try {
    & $pythonPath -m pip check
    if ($LASTEXITCODE) { throw 'Python dependency check failed.' }
    & $pythonPath -m unittest discover -s backend -t . -v
    if ($LASTEXITCODE) { throw 'Backend checks failed.' }
    & $pythonPath -m backend.application.check_metrics
    if ($LASTEXITCODE) { throw 'Metric reconciliation failed.' }
    if (-not $SkipFrontend) {
        Push-Location -LiteralPath (Join-Path $PSScriptRoot 'UI\UX\app')
        try {
            foreach ($task in @('test','lint','build')) {
                & npm.cmd run $task
                if ($LASTEXITCODE) { throw "Frontend $task failed." }
            }
            & node scripts/verify-performance.mjs
            if ($LASTEXITCODE) { throw 'Frontend metric reconciliation failed.' }
            & npm.cmd audit --audit-level=moderate
            if ($LASTEXITCODE) { throw 'Frontend dependency advisory check failed.' }
        } finally { Pop-Location }
    }
} finally { Pop-Location }
