"""Read-only source contracts and conservative Item 11 retrieval eligibility."""
from __future__ import annotations
import csv,hashlib,json,re
from pathlib import Path
from supplemental_sources import MANIFEST as SUPPLEMENT_MANIFEST, apply_supplements

ROOT=Path(__file__).resolve().parents[3]
PIPELINE=Path(__file__).parent
SOURCE_FILES=[
 'dataset/processed/item7/documents.jsonl','dataset/processed/item7/provisions.jsonl',
 'dataset/processed/item7/retrieval_chunks.jsonl','dataset/processed/item7/validation_report.json',
 'dataset/data_contract/controlled_vocabularies.json','dataset/data_contract/topic_taxonomy.csv',
 'dataset/canonical_sources/manifests/canonical_documents.csv',
 'dataset/canonical_sources/manifests/legal_status_review.csv',
 'dataset/canonical_sources/manifests/legal_status_relationships.csv','dataset/authoritative_source_registry.csv',
 'project_legal_scope.md','dataset/pipelines/item10/scope_constraints.py',
 'dataset/pipelines/item10/typing_repair.py','dataset/pipelines/item10/typing_vocabulary.py',
 SUPPLEMENT_MANIFEST,'dataset/pipelines/item11/supplemental_sources.py']

def readrows(path):return [json.loads(l) for l in Path(path).read_text(encoding='utf-8').splitlines() if l.strip()]
def csvrows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def jsonl(path,rows):Path(path).write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows),encoding='utf-8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def sources():
    documents=readrows(ROOT/SOURCE_FILES[0]);provisions=readrows(ROOT/SOURCE_FILES[1]);chunks=readrows(ROOT/SOURCE_FILES[2])
    vocab=json.loads((ROOT/SOURCE_FILES[4]).read_text());taxonomy=csvrows(ROOT/SOURCE_FILES[5])
    canonical={r['document_id']:r for r in csvrows(ROOT/SOURCE_FILES[6])}
    legal={r['document_id']:r for r in csvrows(ROOT/SOURCE_FILES[7])}
    registry={r['source_id']:r for r in csvrows(ROOT/SOURCE_FILES[9])}
    apply_supplements(ROOT,documents,provisions,chunks,canonical,legal,registry)
    for rows,key in [(documents,'document_id'),(provisions,'provision_id'),(chunks,'chunk_id')]:
        if len({r[key] for r in rows})!=len(rows):raise ValueError('Duplicate '+key)
    if json.loads((ROOT/SOURCE_FILES[3]).read_text())['status']!='passed':raise ValueError('Item 7 validation is not passed')
    docs={r['document_id']:r for r in documents};provs={r['provision_id']:r for r in provisions}
    raw_hashes={}
    for d in documents:
        c=canonical[d['document_id']];l=legal[d['document_id']];s=registry[d['source_id']]
        expected='dataset/canonical_sources/'+c['local_path'].replace('\\','/')
        if d['raw_local_path']!=expected or not (ROOT/expected).is_file():raise ValueError('Canonical source missing or mismatched: '+d['document_id'])
        for key in ['official_source_url','retrieval_url','verification_status']:
            if d[key]!=c[key]:raise ValueError('Canonical metadata mismatch: '+key)
        for key in ['legal_status','status_as_of','retrieval_use_policy','freshness_rule']:
            if d[key]!=l[key]:raise ValueError('Legal status mismatch: '+d['document_id']+' '+key)
        if d['authority_level']!=s['authority_level'] or d['permitted_use']!=s['permitted_use']:raise ValueError('Registry mismatch')
        raw_hashes[expected]=sha(ROOT/expected)
    for c in chunks:
        p=provs.get(c['provision_id'])
        if p is None or p['document_id']!=c['document_id']:raise ValueError('Orphan/mismatched chunk')
        a,b=c['normalized_char_start'],c['normalized_char_end']
        if not(0<=a<b<=len(p['normalized_text'])) or p['normalized_text'][a:b]!=c['display_text']:raise ValueError('Chunk text/offset mismatch: '+c['chunk_id'])
        for field in ['domains','scope_status','supported_topics','excluded_topics','legal_status','status_family','status_as_of','answer_use_mode','citation_display']:
            if c[field]!=p[field]:raise ValueError('Chunk/provision metadata mismatch: '+c['chunk_id']+' '+field)
    return {'documents':docs,'provisions':provs,'chunks':chunks,'vocab':vocab,'taxonomy':taxonomy,'canonical':canonical,'legal':legal,'registry':registry,
        'relationships':csvrows(ROOT/SOURCE_FILES[8]),'source_sha256':{name:sha(ROOT/name) for name in SOURCE_FILES},'raw_source_sha256':raw_hashes}

# These screens quarantine whole provisions for narrower MVP review. They do
# not edit Item 7 labels or claim that a new legal-professional review occurred.
SPECIALIZED_HEADERS=[
 ('specialized_employment',r'\b(?:overseas|seafar\w*|kasambahay|househelpers?|domestic.worker|government.employ\w*|civil.service)\b'),
 ('collective_bargaining',r'\b(?:collective.bargain\w*|bargain.collectively|labor.organizations?|union\w*|unfair.labor.practice)\b'),
 ('compensation_safety',r'\b(?:occupational|workers?.compensation|disability|medical.and.dental|pension|retirement)\b'),
 ('specialized_consumer_products',r'\b(?:food|drugs?|cosmetics?|cigarettes?|hazardous.substances?|mislabeled.drugs)\b'),
 ('specialized_financial_services',r'\b(?:credit.plan|banking|insurance|investments?|securities)\b'),
 ('overseas_remittance',r'\bforeign.exchange.remittance\b'),
]

def eligibility(c,p,d,source):
    reasons=[];v=source['vocab'];topicmap={r['topic_id']:r for r in source['taxonomy']}
    if c.get('answer_eligible') is not True:reasons.append('chunk_not_eligible')
    if p.get('provision_answer_eligible') is not True:reasons.append('provision_not_eligible')
    if d.get('document_answer_eligible_candidate') is not True:reasons.append('document_not_candidate')
    if source['canonical'][d['document_id']]['answer_eligible_candidate'].lower()!='true':reasons.append('canonical_not_candidate')
    if d['authority_level']!='primary_official' or d['permitted_use']!='answer_and_citation':reasons.append('source_not_answer_authority')
    registry=source['registry'][d['source_id']]
    if registry['answer_eligible'].lower()!='true':reasons.append('registry_not_eligible')
    if d['processing_state']!='validated':reasons.append('document_not_validated')
    if any(r.get('scope_status')!='supported' for r in [c,p]):reasons.append('scope_not_supported')
    if any(r.get('answer_use_mode')!='default_answer' for r in [c,p]):reasons.append('restricted_answer_mode')
    if any(r.get('status_family') not in {'current','current_with_conditions'} for r in [c,p,d]):reasons.append('restricted_legal_status')
    active_policies={'active_with_freshness_check','active_with_related_authorities','framework_only','active_with_current_rule','active_provision_level',
        'active_with_implementing_rule','active_provision_level_only','active_current_procedure','active_with_parent_statute'}
    if d['retrieval_use_policy'] not in active_policies:reasons.append('unknown_or_restricted_retrieval_policy')
    if p.get('review_status') not in {'machine_validated','sample_verified','verified'}:reasons.append('human_review_pending')
    if p.get('ocr_used') and p.get('review_status')!='verified':reasons.append('unverified_ocr')
    flags=set(c.get('quality_flags',[]))|set(p.get('quality_flags',[]))
    if flags&set(v['blocking_quality_flags']):reasons.append('blocking_quality_flag')
    if flags-set(v['blocking_quality_flags'])-set(v['nonblocking_quality_flags']):reasons.append('unknown_quality_flag')
    if c['excluded_topics'] or p['excluded_topics']:reasons.append('excluded_topic_present')
    if not c['supported_topics'] or any(t not in topicmap or topicmap[t]['scope_status']!='supported' for t in c['supported_topics']):reasons.append('invalid_supported_topics')
    if any(t in topicmap and topicmap[t]['domain'] not in c['domains'] for t in c['supported_topics']):reasons.append('topic_domain_mismatch')
    if set(c['domains'])-{'labor','consumer'}:reasons.append('invalid_domain')
    if not d['verification_status'].startswith('verified'):reasons.append('source_verification_pending')
    text=p['normalized_text']
    if '\ufffd' in text or text.count('^')>=3 or re.search(r'(?:\b[A-Za-z]\s+){8,}',text):reasons.append('extraction_anomaly_requires_review')
    locator=p['source_locator']
    if locator.get('pdf_page_start') is None and locator.get('source_char_start') is None and not locator.get('html_anchor'):reasons.append('missing_source_locator')
    if not reasons:
        header=' '.join([p.get('heading') or '']+[x or '' for x in p['hierarchy'].values()])
        # PDF footnote markers can attach to a word (e.g. HOUSEHELPERS112).
        # Normalize them only for screening; preserve the source/display text.
        header=re.sub(r'(?<=[A-Za-z])\d+\b','',header)
        for label,pattern in SPECIALIZED_HEADERS:
            if re.search(pattern,header,re.I):reasons.append('scope_quarantine:'+label)
    return reasons

def curate(source):
    included=[];excluded=[]
    # Section headings such as "Regular working hours" can omit the worker
    # category specified by their enclosing Rule. Carry that Rule's exact
    # coverage text as a restriction, never as newly approved answer evidence.
    def rule_key(p):
        h=p['hierarchy']
        return (p['document_id'],tuple(h.get(k) for k in ['book','title','chapter','part','rule']))
    coverage={}
    for p in source['provisions'].values():
        if p['hierarchy'].get('rule') and re.search(r'\bcoverage\b',p.get('heading') or '',re.I):
            coverage.setdefault(rule_key(p),[]).append(p['normalized_text'])
    for c in source['chunks']:
        p=source['provisions'][c['provision_id']];d=source['documents'][c['document_id']];reasons=eligibility(c,p,d,source)
        if reasons:
            excluded.append({'chunk_id':c['chunk_id'],'provision_id':p['provision_id'],'document_id':d['document_id'],'item7_answer_eligible':c['answer_eligible'],'reasons':reasons});continue
        conditions=[d['freshness_rule'],*coverage.get(rule_key(p),[])]
        relationships=[r for r in source['relationships'] if r['source_document_id']==d['document_id'] or r['target_document_id']==d['document_id']]
        included.append({**c,'heading':p['heading'],'source_locator':p['source_locator'],'former_locator_labels':p['former_locator_labels'],
            'parent_provision_id':p['parent_provision_id'],'parent_text':p['normalized_text'],'parent_heading':p['heading'],
            'document_title':d['title'],'official_source_url':d['official_source_url'],'retrieval_url':d['retrieval_url'],
            'raw_local_path':d['raw_local_path'],'source_id':d['source_id'],'authority_level':d['authority_level'],
            'source_verification_status':d['verification_status'],'retrieval_use_policy':d['retrieval_use_policy'],'freshness_rule':d['freshness_rule'],
            'conditions':conditions,'legal_relationships':relationships,'extraction_method':p['extraction_method'],'ocr_used':p['ocr_used'],
            'review_status':p['review_status'],'source_hierarchy':p['hierarchy'],
            'index_text':(p['citation_display']+'\n'+(p['heading'] or '')+'\n'+(p['heading'] or '')+'\n'+d['title']+'\n'+c['display_text']),
            'answer_generation_allowed':False,'retrieval_candidate_only':True})
    return included,excluded
