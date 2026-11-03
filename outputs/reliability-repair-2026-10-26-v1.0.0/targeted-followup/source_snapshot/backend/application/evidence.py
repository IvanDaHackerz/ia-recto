"""Presentation metadata and field-verified referral lookups, never legal approval."""
from collections import Counter
import json
from pathlib import Path
import re
from .source_issues import issue_for

ROOT=Path(__file__).resolve().parents[2]

def citation_labels(verifier):
    counts=Counter(r['citation_display'] for r in verifier.records.values());labels={}
    for r in verifier.records.values():
        label=r['citation_display']
        if counts[label]>1:
            context=[]
            for value in r.get('source_hierarchy',{}).values():
                if value:
                    m=re.match(r'((?:BOOK|RULE|TITLE|CHAPTER|PART)\s+[\w.-]+)',value,re.I)
                    context.append(m.group(1) if m else value)
            page=r.get('source_locator',{}).get('pdf_page_start')
            if page is not None:context.append('PDF page '+str(page))
            if r.get('heading') and not context:context.append(r['heading'])
            label+=' — '+', '.join(dict.fromkeys(context)) if context else ''
        labels[r['chunk_id']]=label
    groups={}
    for r in verifier.records.values():groups.setdefault(labels[r['chunk_id']],set()).add(r['provision_id'])
    collisions={label for label,ids in groups.items() if len(ids)>1}
    for r in verifier.records.values():
        if labels[r['chunk_id']] in collisions:labels[r['chunk_id']]+=' · stored locator '+r['provision_id'].split('__',1)[-1].replace('_',' ')
    return labels

def decorate(packet,verifier,labels):
    result=packet.get('result');packet['referrals']=[];packet['source_review_notices']=[]
    if result:
        for c in result['components']:
            for hit in c['candidates']:
                hit['citation_label']=labels.get(hit['chunk_id'],hit['citation_display'])
                if issue_for(hit):hit['explanation_restriction']=issue_for(hit)['message']
        for claim in packet['explanation'].get('claims',[]):
            for cite in claim['citations']:cite['citation_label']=labels.get(cite['chunk_id'],cite['citation_display'])
        ids=set(result.get('referral_ids',[]))
        if any(c['allowed_domain']=='labor' for c in result['components']):ids.add('REF_DOLE_ARMS')
        if any(c['allowed_domain']=='consumer' for c in result['components']):ids.add('REF_DTI_CARE')
        if any(str(c.get('constraint_topic',c.get('scope_constraint',''))).startswith('outside.family') for c in result['excluded_components']):ids.add('REF_PAO')
        directory={r['referral_id']:r for r in json.loads((ROOT/'dataset/processed/item10/referral_refresh_v1.0.0/directory.json').read_text(encoding='utf-8'))}
        for rid in sorted(ids):
            row=directory.get(rid)
            if not row:continue
            fields={k:v for k,v in row['confirmed_fields'].items() if k in row['field_verification']}
            packet['referrals'].append({'id':rid,'agency':row['agency'],'service':row['service'],'contact':fields,
                'checked_on':row['checked_on'],'information_url':row['verification_source_url'],'note':row['note'],
                'complete':row['complete_contact_verification'],'jurisdiction_certified':False})
        missing={r.split(':',1)[1] for c in result['components'] for g in c['evidence_gates'] for r in g['reasons'] if r.startswith('related_authority_unavailable:')}
        if any(not c['candidates'] and re.search(r'\bfinal\s*pay\b|\bcoe\b|certificate\s+of\s+employment',c['query'],re.I) for c in result['components']):missing.add('DOLE_LA_06_20')
        for doc_id in sorted(missing):
            doc=verifier.source['documents'].get(doc_id)
            if doc:packet['source_review_notices'].append({'document_id':doc_id,'title':doc['title'],
                'official_url':doc['official_source_url'],'reason':'Required source text or review is missing. This record is not being used to generate an answer.'})
    return packet
