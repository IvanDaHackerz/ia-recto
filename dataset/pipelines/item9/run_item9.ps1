param(
    [string]$DatasetRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'
$python = 'C:\Users\gdhsb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$env:PYTHONPATH = Join-Path $DatasetRoot 'pipelines\item7\vendor'

& $python (Join-Path $PSScriptRoot 'build_item9.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python (Join-Path $PSScriptRoot 'validate_item9.py')
exit $LASTEXITCODE
