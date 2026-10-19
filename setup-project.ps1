# Recreate dependencies in a NEW Python environment; never retrain/rebind sources.
[CmdletBinding()]
param([string]$EnvironmentPath = '.venv-item10', [switch]$DownloadEmbeddingModel)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $targetPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $EnvironmentPath))
    $rootPrefix = [IO.Path]::GetFullPath($PSScriptRoot) + [IO.Path]::DirectorySeparatorChar
    if (-not $targetPath.StartsWith($rootPrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Environment must be inside this project.' }
    if (Test-Path -LiteralPath $targetPath) { throw 'Environment already exists. Choose a new -EnvironmentPath; this script never overwrites one.' }
    & py -3.12 -m venv $targetPath
    if ($LASTEXITCODE) { throw 'Python 3.12 is required.' }
    $pythonPath = Join-Path $targetPath 'Scripts\python.exe'
    & $pythonPath -m pip install 'pip==26.2.1'
    if ($LASTEXITCODE) { throw 'Installer setup failed.' }
    $artifacts = Get-Content -LiteralPath CURRENT_ARTIFACTS.json -Raw | ConvertFrom-Json
    & $pythonPath -m pip install --only-binary=:all: -r (Join-Path $PSScriptRoot "$($artifacts.classifier)/requirements.lock.txt")
    if ($LASTEXITCODE) { throw 'Pinned dependency installation failed.' }
    Push-Location -LiteralPath UI\UX\app
    try { & npm.cmd ci; if ($LASTEXITCODE) { throw 'Node dependency installation failed.' } }
    finally { Pop-Location }
    if ($DownloadEmbeddingModel) {
        & $pythonPath -c 'from dataset.pipelines.item10.semantic_encoder import encoder; encoder(allow_download=True)'
        if ($LASTEXITCODE) { throw 'Embedding download failed.' }
    }
    & $pythonPath -c 'from backend.terminal_test import load_runtime; v=load_runtime(); print("Runtime and pinned source/model integrity checked")'
    if ($LASTEXITCODE) { throw 'Runtime integrity failed. Restore the exact model/cache/source hashes from the release manifest; do not silently rebind them.' }
    Write-Host 'Dependencies and pinned runtime checked. Configure a new server-side key separately if AI is needed.'
} finally { Pop-Location }
