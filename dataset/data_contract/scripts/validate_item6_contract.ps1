param(
    [string]$DataContractRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
)

$ErrorActionPreference = 'Stop'
$errors = [System.Collections.Generic.List[string]]::new()

function Add-ValidationError {
    param([string]$Message)
    $script:errors.Add($Message)
}

function Read-JsonLines {
    param([string]$Path)
    $records = [System.Collections.Generic.List[object]]::new()
    $lineNumber = 0
    foreach ($line in Get-Content -LiteralPath $Path -Encoding utf8) {
        $lineNumber++
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $records.Add(($line | ConvertFrom-Json))
        }
        catch {
            Add-ValidationError "$Path line $lineNumber is not valid JSON: $($_.Exception.Message)"
        }
    }
    return @($records)
}

function Test-RequiredAndKnownFields {
    param(
        [object[]]$Records,
        [object]$Schema,
        [string]$RecordLabel
    )
    $required = @($Schema.required)
    $known = @($Schema.properties.PSObject.Properties.Name)
    foreach ($record in $Records) {
        $identifier = @($record.document_id, $record.provision_id, $record.chunk_id) |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Select-Object -First 1
        foreach ($field in $required) {
            if ($field -notin $record.PSObject.Properties.Name) {
                Add-ValidationError "$RecordLabel $identifier is missing required field $field."
            }
        }
        foreach ($field in $record.PSObject.Properties.Name) {
            if ($field -notin $known) {
                Add-ValidationError "$RecordLabel $identifier contains unknown field $field."
            }
        }
    }
}

$schemaPaths = @(
    (Join-Path $DataContractRoot 'schemas\legal_document.schema.json'),
    (Join-Path $DataContractRoot 'schemas\legal_provision.schema.json'),
    (Join-Path $DataContractRoot 'schemas\retrieval_chunk.schema.json')
)
$schemas = @{}
foreach ($schemaPath in $schemaPaths) {
    try {
        $schemas[[IO.Path]::GetFileName($schemaPath)] = Get-Content -LiteralPath $schemaPath -Raw -Encoding utf8 | ConvertFrom-Json
    }
    catch {
        Add-ValidationError "Schema $schemaPath is not valid JSON: $($_.Exception.Message)"
    }
}

$vocabPath = Join-Path $DataContractRoot 'controlled_vocabularies.json'
try {
    $vocab = Get-Content -LiteralPath $vocabPath -Raw -Encoding utf8 | ConvertFrom-Json
}
catch {
    Add-ValidationError "Controlled vocabulary is not valid JSON: $($_.Exception.Message)"
    $vocab = [pscustomobject]@{}
}

$taxonomyPath = Join-Path $DataContractRoot 'topic_taxonomy.csv'
$taxonomy = @(Import-Csv -LiteralPath $taxonomyPath)
$topicIds = @($taxonomy.topic_id)
if ($topicIds.Count -ne (@($topicIds | Sort-Object -Unique)).Count) {
    Add-ValidationError 'The topic taxonomy contains duplicate topic IDs.'
}
foreach ($topic in $taxonomy) {
    if ($topic.domain -notin @($vocab.domains)) {
        Add-ValidationError "Topic $($topic.topic_id) has unknown domain $($topic.domain)."
    }
    if ($topic.scope_status -notin @($vocab.scope_statuses)) {
        Add-ValidationError "Topic $($topic.topic_id) has unknown scope status $($topic.scope_status)."
    }
    if ($topic.topic_id -notmatch '^(labor|consumer)\.[a-z0-9_]+$') {
        Add-ValidationError "Topic ID $($topic.topic_id) does not follow the stable naming rule."
    }
}
$onlineTopic = @($taxonomy | Where-Object topic_id -eq 'consumer.online_transactions')
if ($onlineTopic.Count -ne 1 -or $onlineTopic[0].scope_status -ne 'supported') {
    Add-ValidationError 'consumer.online_transactions must exist exactly once and be marked supported.'
}
$fraudTopic = @($taxonomy | Where-Object topic_id -eq 'consumer.criminal_online_fraud')
if ($fraudTopic.Count -ne 1 -or $fraudTopic[0].scope_status -ne 'excluded') {
    Add-ValidationError 'consumer.criminal_online_fraud must exist exactly once and be marked excluded.'
}

$documents = @(Read-JsonLines (Join-Path $DataContractRoot 'samples\sample_documents.jsonl'))
$provisions = @(Read-JsonLines (Join-Path $DataContractRoot 'samples\sample_provisions.jsonl'))
$chunks = @(Read-JsonLines (Join-Path $DataContractRoot 'samples\sample_retrieval_chunks.jsonl'))

if ($schemas.ContainsKey('legal_document.schema.json')) {
    Test-RequiredAndKnownFields $documents $schemas['legal_document.schema.json'] 'Document'
}
if ($schemas.ContainsKey('legal_provision.schema.json')) {
    Test-RequiredAndKnownFields $provisions $schemas['legal_provision.schema.json'] 'Provision'
}
if ($schemas.ContainsKey('retrieval_chunk.schema.json')) {
    Test-RequiredAndKnownFields $chunks $schemas['retrieval_chunk.schema.json'] 'Chunk'
}

foreach ($group in @(
    @{ Label = 'document'; Values = @($documents.document_id) },
    @{ Label = 'provision'; Values = @($provisions.provision_id) },
    @{ Label = 'chunk'; Values = @($chunks.chunk_id) }
)) {
    if ($group.Values.Count -ne (@($group.Values | Sort-Object -Unique)).Count) {
        Add-ValidationError "Sample $($group.Label) IDs are not unique."
    }
}

$canonicalManifestPath = Join-Path $ProjectRoot 'dataset\canonical_sources\manifests\canonical_documents.csv'
$canonicalDocuments = @(Import-Csv -LiteralPath $canonicalManifestPath)
$canonicalById = @{}
foreach ($canonical in $canonicalDocuments) { $canonicalById[$canonical.document_id] = $canonical }

$sourceRegistryPath = Join-Path $ProjectRoot 'dataset\authoritative_source_registry.csv'
$sourceRegistry = @(Import-Csv -LiteralPath $sourceRegistryPath)
$sourceIds = @($sourceRegistry.source_id)

$relationshipPath = Join-Path $ProjectRoot 'dataset\canonical_sources\manifests\legal_status_relationships.csv'
$relationshipIds = @((Import-Csv -LiteralPath $relationshipPath).relationship_id)

$documentById = @{}
foreach ($document in $documents) {
    $documentById[$document.document_id] = $document
    if ($document.contract_version -ne $vocab.contract_version) {
        Add-ValidationError "Document $($document.document_id) uses contract version $($document.contract_version)."
    }
    if ($document.document_id -notmatch '^[A-Z0-9_]+$') {
        Add-ValidationError "Document ID $($document.document_id) is invalid."
    }
    if ($document.source_id -notin $sourceIds) {
        Add-ValidationError "Document $($document.document_id) references unknown source $($document.source_id)."
    }
    if ($document.authority_level -notin @($vocab.authority_levels)) {
        Add-ValidationError "Document $($document.document_id) has unknown authority level $($document.authority_level)."
    }
    if ($document.permitted_use -notin @($vocab.permitted_uses)) {
        Add-ValidationError "Document $($document.document_id) has unknown permitted use $($document.permitted_use)."
    }
    foreach ($domain in @($document.domains)) {
        if ($domain -notin @($vocab.domains)) {
            Add-ValidationError "Document $($document.document_id) has unknown domain $domain."
        }
    }
    if (-not $canonicalById.ContainsKey($document.document_id)) {
        Add-ValidationError "Sample document $($document.document_id) is absent from the canonical manifest."
        continue
    }
    $canonical = $canonicalById[$document.document_id]
    $expectedRelativePath = 'dataset/canonical_sources/' + ($canonical.local_path -replace '\\', '/')
    if ($document.raw_local_path -ne $expectedRelativePath) {
        Add-ValidationError "Sample document $($document.document_id) local path differs from the canonical manifest."
    }
    if ($document.official_source_url -ne $canonical.official_source_url) {
        Add-ValidationError "Sample document $($document.document_id) official source URL differs from the canonical manifest."
    }
    if ($document.retrieval_url -ne $canonical.retrieval_url) {
        Add-ValidationError "Sample document $($document.document_id) retrieval URL differs from the canonical manifest."
    }
    $rawPath = Join-Path $ProjectRoot $document.raw_local_path
    if (-not (Test-Path -LiteralPath $rawPath)) {
        Add-ValidationError "Sample document $($document.document_id) raw file does not exist at $rawPath."
    }
}

$allQualityFlags = @($vocab.blocking_quality_flags) + @($vocab.nonblocking_quality_flags)
$provisionById = @{}
foreach ($provision in $provisions) {
    $provisionById[$provision.provision_id] = $provision
    if ($provision.provision_id -notmatch '^[A-Z0-9_]+__[a-z0-9_]+(?:__[a-z0-9_]+)*$') {
        Add-ValidationError "Provision ID $($provision.provision_id) is invalid."
    }
    if (-not $documentById.ContainsKey($provision.document_id)) {
        Add-ValidationError "Provision $($provision.provision_id) references missing document $($provision.document_id)."
        continue
    }
    $document = $documentById[$provision.document_id]
    if ($null -ne $provision.parent_provision_id -and $provision.parent_provision_id -notin @($provisions.provision_id)) {
        Add-ValidationError "Provision $($provision.provision_id) references missing parent $($provision.parent_provision_id)."
    }
    foreach ($topic in @($provision.supported_topics) + @($provision.excluded_topics)) {
        if ($topic -notin $topicIds) {
            Add-ValidationError "Provision $($provision.provision_id) references unknown topic $topic."
        }
    }
    foreach ($relationship in @($provision.relationship_ids)) {
        if ($relationship -notin $relationshipIds) {
            Add-ValidationError "Provision $($provision.provision_id) references unknown relationship $relationship."
        }
    }
    foreach ($flag in @($provision.quality_flags)) {
        if ($flag -notin $allQualityFlags) {
            Add-ValidationError "Provision $($provision.provision_id) has unknown quality flag $flag."
        }
    }
    foreach ($textField in @('verbatim_text', 'normalized_text', 'search_text')) {
        if ([string]::IsNullOrWhiteSpace($provision.$textField)) {
            Add-ValidationError "Provision $($provision.provision_id) has empty $textField."
        }
        elseif ($provision.$textField.Contains([char]0xFFFD)) {
            Add-ValidationError "Provision $($provision.provision_id) contains unresolved U+FFFD in $textField."
        }
    }
    $locator = $provision.source_locator
    $hasLocator = ($null -ne $locator.pdf_page_start) -or
        (-not [string]::IsNullOrWhiteSpace($locator.html_anchor)) -or
        ($null -ne $locator.source_char_start) -or
        (-not [string]::IsNullOrWhiteSpace($locator.source_region))
    if (-not $hasLocator) {
        Add-ValidationError "Provision $($provision.provision_id) has no usable source locator."
    }
    if ($null -ne $locator.pdf_page_start -and $null -ne $locator.pdf_page_end -and $locator.pdf_page_start -gt $locator.pdf_page_end) {
        Add-ValidationError "Provision $($provision.provision_id) has a reversed PDF page range."
    }
    if ($provision.provision_answer_eligible) {
        if (-not $document.document_answer_eligible_candidate) {
            Add-ValidationError "Provision $($provision.provision_id) is more permissive than its document."
        }
        if ($provision.scope_status -ne 'supported' -or $provision.answer_use_mode -ne 'default_answer') {
            Add-ValidationError "Provision $($provision.provision_id) is answer eligible without supported/default-answer status."
        }
        if ($provision.status_family -in @('historical', 'time_bound', 'explanatory', 'verification_pending')) {
            Add-ValidationError "Provision $($provision.provision_id) is answer eligible with blocking status family $($provision.status_family)."
        }
        $blocking = @($provision.quality_flags | Where-Object { $_ -in @($vocab.blocking_quality_flags) })
        if ($blocking.Count -gt 0) {
            Add-ValidationError "Provision $($provision.provision_id) is answer eligible with blocking flags: $($blocking -join ', ')."
        }
    }
}

foreach ($chunk in $chunks) {
    if ($chunk.chunk_id -notmatch '^[A-Z0-9_]+__[a-z0-9_]+(?:__[a-z0-9_]+)*__chunk_[0-9]{4}$') {
        Add-ValidationError "Chunk ID $($chunk.chunk_id) is invalid."
    }
    if (-not $provisionById.ContainsKey($chunk.provision_id)) {
        Add-ValidationError "Chunk $($chunk.chunk_id) references missing provision $($chunk.provision_id)."
        continue
    }
    $provision = $provisionById[$chunk.provision_id]
    if ($chunk.document_id -ne $provision.document_id) {
        Add-ValidationError "Chunk $($chunk.chunk_id) document does not match its provision."
    }
    if ($chunk.normalized_char_start -gt $chunk.normalized_char_end -or $chunk.normalized_char_end -gt $provision.normalized_text.Length) {
        Add-ValidationError "Chunk $($chunk.chunk_id) has invalid normalized-text offsets."
    }
    else {
        $expectedText = $provision.normalized_text.Substring(
            $chunk.normalized_char_start,
            $chunk.normalized_char_end - $chunk.normalized_char_start
        )
        if ($chunk.display_text -ne $expectedText) {
            Add-ValidationError "Chunk $($chunk.chunk_id) display text does not match its parent offsets."
        }
    }
    if ($chunk.character_count -ne $chunk.display_text.Length) {
        Add-ValidationError "Chunk $($chunk.chunk_id) character count is incorrect."
    }
    foreach ($topic in @($chunk.supported_topics) + @($chunk.excluded_topics)) {
        if ($topic -notin $topicIds) {
            Add-ValidationError "Chunk $($chunk.chunk_id) references unknown topic $topic."
        }
    }
    foreach ($flag in @($chunk.quality_flags)) {
        if ($flag -notin $allQualityFlags) {
            Add-ValidationError "Chunk $($chunk.chunk_id) has unknown quality flag $flag."
        }
    }
    if ($chunk.answer_eligible -and -not $provision.provision_answer_eligible) {
        Add-ValidationError "Chunk $($chunk.chunk_id) is more permissive than its parent provision."
    }
    if ($chunk.answer_eligible -and ($chunk.scope_status -ne 'supported' -or $chunk.answer_use_mode -ne 'default_answer')) {
        Add-ValidationError "Chunk $($chunk.chunk_id) is answer eligible without supported/default-answer status."
    }
    if ($chunk.answer_eligible -and @($chunk.quality_flags | Where-Object { $_ -in @($vocab.blocking_quality_flags) }).Count -gt 0) {
        Add-ValidationError "Chunk $($chunk.chunk_id) is answer eligible with a blocking quality flag."
    }
}

if ($errors.Count -gt 0) {
    foreach ($validationError in $errors) { Write-Error $validationError }
    exit 1
}

Write-Output "Item 6 validation passed: $($documents.Count) sample documents, $($provisions.Count) sample provisions, $($chunks.Count) sample chunks, and $($taxonomy.Count) taxonomy topics checked."
