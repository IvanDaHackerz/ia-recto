param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$PythonExe = 'python',
    [string]$NodeExe = 'node',
    [Parameter(Mandatory = $true)][string]$PdfToPpm,
    [Parameter(Mandatory = $true)][string]$NodeModuleRoot,
    [Parameter(Mandatory = $true)][string]$OcrLanguageDirectory,
    [string]$WorkDirectory = (Join-Path $ProjectRoot 'tmp\item7_ocr'),
    [string]$OutputDirectory = (Join-Path $ProjectRoot 'dataset\processed\item7')
)

$ErrorActionPreference = 'Stop'
$model = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'ocr_model.json') -Raw | ConvertFrom-Json
$modelPath = Join-Path $OcrLanguageDirectory $model.file
if (-not (Test-Path -LiteralPath $modelPath)) {
    throw "OCR model not found at $modelPath. Download it from $($model.source)."
}
& $PythonExe (Join-Path $PSScriptRoot 'prepare_ocr.py') --project-root $ProjectRoot --pdftoppm $PdfToPpm --work-dir $WorkDirectory
if ($LASTEXITCODE -ne 0) { throw 'OCR page preparation failed.' }

& $NodeExe (Join-Path $PSScriptRoot 'ocr_images.mjs') --manifest (Join-Path $WorkDirectory 'ocr_manifest.json') --output (Join-Path $WorkDirectory 'ocr_output.jsonl') --lang-path $OcrLanguageDirectory --module-root $NodeModuleRoot
if ($LASTEXITCODE -ne 0) { throw 'OCR failed.' }

& $PythonExe (Join-Path $PSScriptRoot 'extract_canonical.py') --project-root $ProjectRoot --ocr-output (Join-Path $WorkDirectory 'ocr_output.jsonl') --output-dir $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Canonical extraction failed.' }

& $PythonExe (Join-Path $PSScriptRoot 'validate_item7.py') --project-root $ProjectRoot --output-dir $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Item 7 validation failed.' }

& $PythonExe (Join-Path $PSScriptRoot 'jsonl_to_parquet.py') --output-dir $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Parquet conversion failed.' }

Write-Output "Item 7 completed successfully: $OutputDirectory"
