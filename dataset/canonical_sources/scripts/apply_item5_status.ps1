param(
    [string]$CanonicalManifest = (Join-Path $PSScriptRoot '..\manifests\canonical_documents.csv'),
    [string]$StatusReview = (Join-Path $PSScriptRoot '..\manifests\legal_status_review.csv')
)

$ErrorActionPreference = 'Stop'

$documents = @(Import-Csv -LiteralPath $CanonicalManifest)
$reviews = @(Import-Csv -LiteralPath $StatusReview)

$reviewById = @{}
foreach ($review in $reviews) {
    if ($reviewById.ContainsKey($review.document_id)) {
        throw "Duplicate legal-status review for $($review.document_id)."
    }
    $reviewById[$review.document_id] = $review
}

foreach ($document in $documents) {
    if (-not $reviewById.ContainsKey($document.document_id)) {
        throw "No legal-status review exists for $($document.document_id)."
    }

    $review = $reviewById[$document.document_id]
    $document.legal_status_review = "reviewed_$($review.legal_status)"

    # Annual guidance from a past year must not enter the default current-law answer set.
    if ($review.retrieval_use_policy -eq 'historical_or_2025_only') {
        $document.answer_eligible_candidate = 'false'
    }
}

$unknownReviews = @($reviews | Where-Object { $_.document_id -notin $documents.document_id })
if ($unknownReviews.Count -gt 0) {
    throw "Legal-status review contains unknown document IDs: $($unknownReviews.document_id -join ', ')"
}

$tempPath = "$CanonicalManifest.item5.tmp"
$documents | Export-Csv -LiteralPath $tempPath -NoTypeInformation -Encoding utf8
Move-Item -LiteralPath $tempPath -Destination $CanonicalManifest -Force

Write-Output "Updated $($documents.Count) canonical records from $($reviews.Count) legal-status reviews."
