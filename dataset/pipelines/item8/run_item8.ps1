param(
    [string]$DatasetRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'
$python = 'C:\Users\gdhsb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$env:PYTHONPATH = Join-Path $DatasetRoot 'pipelines\item7\vendor'

& $python (Join-Path $PSScriptRoot 'filter_bettergov.py') --dataset-root $DatasetRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python (Join-Path $PSScriptRoot 'validate_item8.py') --dataset-root $DatasetRoot
exit $LASTEXITCODE
