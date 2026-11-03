"""Versioned, provenance-bound source additions and narrow scope-map repairs."""
import copy
import hashlib
import json
from pathlib import Path

MANIFEST='dataset/canonical_sources/supplements/labor_basics_v1.0.1.json'


def apply_supplements(root,documents,provisions,chunks,canonical,legal,registry):
    root=Path(root);data=json.loads((root/MANIFEST).read_text(encoding='utf-8'))
    if data['schema_version']!='1.0' or data['independent_human_or_legal_approval'] is not False:
        raise ValueError('Unknown supplemental source policy')
    for name,expected in data['raw_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Supplemental raw source changed: '+name)
    # Scope mapping may recover clean machine-extracted provisions. It cannot
    # approve held OCR, remove quality flags, replace text or grant legal review.
    for change in data['scope_mapping_repairs']:
        p=next(p for p in provisions if p['provision_id']==change['provision_id'])
        if (p['ocr_used'] or p['review_status']!='machine_validated'
                or set(p['quality_flags'])-{'footnotes_present','table_structure_present'}
                or hashlib.sha256(p['normalized_text'].encode()).hexdigest()!=change['parent_text_sha256']):
            raise ValueError('Scope-map repair cannot release a held or changed source')
        p.update(scope_status='supported',supported_topics=change['supported_topics'],
                 answer_use_mode='default_answer',provision_answer_eligible=True)
        for c in chunks:
            if c['provision_id']==p['provision_id']:
                c.update(scope_status=p['scope_status'],supported_topics=p['supported_topics'],
                         answer_use_mode=p['answer_use_mode'],answer_eligible=True)
    for collection,key,new_rows in [(documents,'document_id',data['documents']),
                                    (provisions,'provision_id',data['provisions']),
                                    (chunks,'chunk_id',data['chunks'])]:
        existing={r[key] for r in collection}
        if existing & {r[key] for r in new_rows}:raise ValueError('Supplement may not replace an existing source')
        collection.extend(copy.deepcopy(new_rows))
    for target,key,new_rows in [(canonical,'document_id',data['canonical']),
                                (legal,'document_id',data['legal_status']),
                                (registry,'source_id',data['registry'])]:
        for row in new_rows:
            if row[key] in target:raise ValueError('Supplement may not replace authority metadata')
            target[row[key]]=copy.deepcopy(row)
    return data
