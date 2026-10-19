param(
    [string]$CanonicalManifest = (Join-Path $PSScriptRoot '..\manifests\canonical_documents.csv'),
    [string]$StatusReview = (Join-Path $PSScriptRoot '..\manifests\legal_status_review.csv'),
    [string]$RelationshipManifest = (Join-Path $PSScriptRoot '..\manifests\legal_status_relationships.csv')
)

$ErrorActionPreference = 'Stop'

$documents = @(Import-Csv -LiteralPath $CanonicalManifest)
$reviews = @(Import-Csv -LiteralPath $StatusReview)
$relationships = @(Import-Csv -LiteralPath $RelationshipManifest)
$documentIds = @($documents.document_id)

$errors = [System.Collections.Generic.List[string]]::new()

if ($documentIds.Count -ne (@($documentIds | Sort-Object -Unique)).Count) {
    $errors.Add('The canonical manifest contains duplicate document IDs.')
}

if ($reviews.document_id.Count -ne (@($reviews.document_id | Sort-Object -Unique)).Count) {
    $errors.Add('The status review contains duplicate document IDs.')
}

foreach ($document in $documents) {
    $matchingReview = @($reviews | Where-Object document_id -eq $document.document_id)
    if ($matchingReview.Count -ne 1) {
        $errors.Add("$($document.document_id) has $($matchingReview.Count) status reviews; expected one.")
    }
    if ($document.legal_status_review -notlike 'reviewed_*') {
        $errors.Add("$($document.document_id) is not marked reviewed in the canonical manifest.")
    }
}

foreach ($review in $reviews) {
    if ($review.document_id -notin $documentIds) {
        $errors.Add("Status review references unknown document $($review.document_id).")
    }
    foreach ($requiredField in @('status_as_of', 'legal_status', 'retrieval_use_policy', 'freshness_rule', 'evidence_url', 'confidence')) {
        if ([string]::IsNullOrWhiteSpace($review.$requiredField)) {
            $errors.Add("Status review $($review.document_id) is missing $requiredField.")
        }
    }
}

foreach ($relationship in $relationships) {
    if ($relationship.source_document_id -notin $documentIds) {
        $errors.Add("Relationship $($relationship.relationship_id) has unknown source $($relationship.source_document_id).")
    }
    if (-not [string]::IsNullOrWhiteSpace($relationship.target_document_id) -and $relationship.target_document_id -notin $documentIds) {
        $errors.Add("Relationship $($relationship.relationship_id) has unknown internal target $($relationship.target_document_id).")
    }
    if ([string]::IsNullOrWhiteSpace($relationship.target_document_id) -and [string]::IsNullOrWhiteSpace($relationship.target_citation_if_external)) {
        $errors.Add("Relationship $($relationship.relationship_id) has no target.")
    }
}

$timeBoundCurrentCandidates = @(
    $reviews |
        Where-Object retrieval_use_policy -eq 'historical_or_2025_only' |
        ForEach-Object document_id |
        Where-Object { $_ -in @($documents | Where-Object answer_eligible_candidate -eq 'true' | ForEach-Object document_id) }
)
if ($timeBoundCurrentCandidates.Count -gt 0) {
    $errors.Add("Time-bound documents remain default answer candidates: $($timeBoundCurrentCandidates -join ', ').")
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Output "Item 5 validation passed: $($documents.Count) documents reviewed and $($relationships.Count) relationships checked."
