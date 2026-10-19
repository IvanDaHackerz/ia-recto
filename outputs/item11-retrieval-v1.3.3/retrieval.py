"""Filtered offline BM25, local semantic search and reciprocal-rank fusion."""
from __future__ import annotations
import argparse,collections,json,re,sys,unicodedata
from pathlib import Path
import numpy as np
from common import ROOT,PIPELINE,readrows,csvrows,sha
from encoder import encode,windows

STOP=set('a an the of to and or in on at for from with by is are was be been this that it my i me we our you your ang ng sa mga ako ko po ba yung at na ay may'.split())
CONCEPTS=[
 (r'\b(?:sukli|shortchang\w*)\b','change'),
 (r'\b(?:labels?|labeling|labelling)\b','label'),
 (r'\b(?:short\s+(?:hours|workday)|kulang\s+(?:ang\s+)?oras|undertime)\b','undertime'),
 (r'\b(?:gaano\s+kadalas|how\s+often|frequency|frequently|regularity)\b','frequency'),
 (r'\b(?:sahod|sweldo|suweldo|salary|salaries|wages?)\b','wage'),
 (r'\b(?:ibigay|bigay|bayad|pagbabayad|paid|pay|payments?|paying)\b','payment'),
 (r'\b(?:lawyers?|attorneys?)\b','lawyer'),
 (r'\b(?:agents?)\b','agent'),
 (r'\b(?:representatives?|representing|represent)\b','representative'),
 (r'\b(?:pagharap|appearance|appearing)\b','appearance'),
 (r'\b(?:sena|conciliation.mediation)\b','conciliation'),
 (r'\b(?:palpak|flawed|faulty|defective|imperfections?)\b','defect'),
 (r'\b(?:redo|reperformance|reexecution)\b','reperformance'),
 (r'\b(?:refunds?|reimbursements?)\b','refund'),
 (r'\b(?:bawas|reductions?)\b','reduction'),
 (r'\b(?:presyo|prices?)\b','price'),
 (r'\b(?:services?)\b','service'),
 (r'\b(?:employers?)\b','employer'),
 (r'\b(?:employees?)\b','employee'),
 (r'\b(?:working|worked|works|work)\b','work'),
 (r'\b(?:rules?)\b','rule'),
]

def tokens(text):
    # Symmetric source/query glossary. Disclosed development preprocessing.
    text=unicodedata.normalize('NFKC',text).casefold()
    for pattern,replacement in CONCEPTS:text=re.sub(pattern,replacement,text)
    return [w for w in re.findall(r'[^\W_]+',text) if w not in STOP]

def ranking_expansion(query,allowed_domain):
    """Bounded labor concepts for lexical ranking, never user facts or citations.

    Preserve every original word, especially negations and qualifications. No
    expected question/provision IDs, learned query statistics or answer claims
    enter these transparent development rules.
    """
    if allowed_domain!='labor':return []
    words=set(tokens(query));extra=[]
    if 'wage' in words and ('frequency' in words or re.search(r'\b(?:delay\w*|late|overdue|unpaid|unpayed)\b|\b(?:not|never)\s+(?:been\s+)?paid\b',query,re.I)):
        extra+=['time','payment','frequency']
    if 'overtime' in words and words&{'payment','unpaid','unpayed','compensation'}:
        extra+=['work','additional','compensation']
        if not words&{'holiday','holidays','rest','undertime','offset','emergency','compulsory','health','hospital','clinic'}:
            extra.append('ordinary')
    return list(dict.fromkeys(extra))

class LegalRetriever:
    def __init__(self,index_dir,verify_sources=True):
        self.path=Path(index_dir);self.manifest=json.loads((self.path/'index_manifest.json').read_text());self.config=json.loads((self.path/'retrieval_config.json').read_text())
        for name,h in json.loads((self.path/'index_checksums.json').read_text()).items():
            if sha(self.path/name)!=h:raise ValueError('Index checksum mismatch: '+name)
        for name,h in self.manifest['runtime_source_sha256'].items():
            if sha(PIPELINE/name)!=h:raise ValueError('Retrieval runtime changed; rebuild the index: '+name)
        if verify_sources:
            for name,h in self.manifest['source_sha256'].items():
                if sha(ROOT/name)!=h:raise ValueError('Source changed; rebuild the index: '+name)
            for name,h in json.loads((self.path/'source_audit.json').read_text())['raw_source_sha256'].items():
                if sha(ROOT/name)!=h:raise ValueError('Canonical file changed; rebuild the index: '+name)
        if sha(ROOT/'models/embedding_backbone_manifest.json')!=self.manifest['semantic_model_manifest_sha256']:raise ValueError('Encoder changed; rebuild the index')
        self.records=readrows(self.path/'records.jsonl');self.taxonomy={r['topic_id']:r for r in csvrows(ROOT/'dataset/data_contract/topic_taxonomy.csv')}
        data=np.load(self.path/'semantic_vectors.npz',allow_pickle=False);self.vectors=data['vectors'];self.window_records=data['record_indices']
        self.counts=[collections.Counter(tokens(r['index_text'])) for r in self.records];self.length=np.array([sum(c.values()) for c in self.counts]);self.average_length=float(self.length.mean())
        self.df=collections.Counter(t for c in self.counts for t in c)

    def lexical_scores(self,query):
        result=np.zeros(len(self.records));n=len(result);k=self.config['bm25_k1'];b=self.config['bm25_b']
        for term in set(tokens(query)):
            df=self.df[term]
            if not df:continue
            tf=np.array([c[term] for c in self.counts]);idf=np.log(1+(n-df+.5)/(df+.5))
            result+=idf*(tf*(k+1))/(tf+k*(1-b+b*self.length/self.average_length))
        return result

    def semantic_scores(self,query):
        pieces=windows(query)
        if not pieces:return np.zeros(len(self.records))
        similarities=(encode([w['text'] for w in pieces])@self.vectors.T).max(axis=0)
        result=np.full(len(self.records),-1.,dtype=float);np.maximum.at(result,self.window_records,similarities)
        return result

    def search(self,query,allowed_domain,method=None,top_k=5,topic_ids=None):
        if allowed_domain not in {'labor','consumer'}:raise ValueError('Explicit labor/consumer domain required')
        if isinstance(top_k,bool) or not isinstance(top_k,int) or not 1<=top_k<=20:raise ValueError('top_k must be an integer from 1 to 20')
        method=method or self.config['default_method']
        if method not in self.config['methods']:raise ValueError('Unknown retrieval method')
        if topic_ids is not None:
            if not topic_ids:raise ValueError('Empty topic filter is not a domain-wide search')
            for t in topic_ids:
                if t not in self.taxonomy or self.taxonomy[t]['scope_status']!='supported' or self.taxonomy[t]['domain']!=allowed_domain:raise ValueError('Invalid/excluded topic filter: '+t)
        base={'query':query,'allowed_domain':allowed_domain,'method':method,'index_version':self.manifest['index_version'],'answer_generation_allowed':False,'deployment_allowed':False,
            'score_meaning':'Retrieval ranking score only; not confidence, legal correctness, currentness, or sufficient evidence','hits':[]}
        if not isinstance(query,str) or not query.strip():base.update(status='clarify',reason='empty_query');return base
        sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
        from scope_constraints import constraint
        rule=constraint(query)
        if rule and (rule[0]=='excluded' or rule[0]!=allowed_domain):base.update(status='blocked_scope',reason=rule[1]);return base
        if topic_ids is None and allowed_domain=='labor' and re.search(r'\b(?:final\s*pay|coe|certificate\s+of\s+employment)\b',query,re.I):
            topic_ids=['labor.final_pay_coe'];base['explicit_query_topic_filter']=topic_ids
        if (topic_ids is None and allowed_domain=='labor'
            and re.search(r'\b(?:holidays?|christmas|pasko)\b',query,re.I)
            and not re.search(r'\b(?:overtime|rest\s*days?|weekly\s+rest|night\s+shift|13th|thirteenth|dismiss\w*|terminat\w*|resign\w*|frequency|minimum\s+wage|salary|salaries|wages?|sahod|sweldo|deduct\w*)\b',query,re.I)):
            # A named holiday supplies a search topic, never an entitlement or
            # employment fact. Keep multi-topic requests domain-wide.
            topic_ids=['labor.holiday_premium_pay'];base['explicit_query_topic_filter']=topic_ids
        allowed=[i for i,r in enumerate(self.records) if allowed_domain in r['domains'] and (topic_ids is None or set(topic_ids)&set(r['supported_topics']))]
        unworked_holiday=(allowed_domain=='labor' and bool(re.search(r'\b(?:holidays?|christmas|pasko)\b',query,re.I))
            and bool(re.search(r'\b(?:no\s+work\s+(?:was\s+)?performed|did\s+not\s+work|didn\x27t\s+work|unworked|hindi\s+nagtrabaho)\b',query,re.I))
            and not re.search(r'\b(?:overtime|premium|rest\s*days?)\b|\b(?:worked|working)\s+on\b|\b(?:if|when)\s+(?:i|we|they)\s+work\b',query,re.I))
        if unworked_holiday:
            # Rules exclusively headed as compensation for work performed do
            # not supply the basic rule for an explicitly unworked holiday.
            allowed=[i for i in allowed if not re.search(r'\b(?:overtime|premium)\b',self.records[i]['heading'] or '',re.I)]
            base['query_relevance_filter']='exclude_worked_holiday_premium_for_explicit_unworked_holiday'
        # Actor direction matters: employee resignation is not employer dismissal.
        # These exclusions affect candidate relevance, never source eligibility,
        # user facts, legal support or the value of a BM25 score.
        employer_dismissal=allowed_domain=='labor' and bool(re.search(
            r'\b(?:employer|boss|company)\b.{0,70}\b(?:fired|dismiss\w*|terminat\w*|sinibak|tinanggal)\b|\b(?:fired|dismissed|terminated)\s+(?:me|us|by)\b',query,re.I))
        if employer_dismissal and not re.search(r'\b(?:resign\w*|quit|employee.initiated)\b',query,re.I):
            allowed=[i for i in allowed if not re.search(r'\btermination\s+by\s+employee\b|\b(?:resignation|voluntary\s+resignation)\b',self.records[i]['heading'] or '',re.I)]
            base['query_relevance_filter']='exclude_employee_initiated_termination_for_explicit_employer_dismissal'
        if not allowed:base.update(status='no_eligible_evidence',reason='no_indexed_chunks_for_requested_scope');return base
        expansion=ranking_expansion(query,allowed_domain)
        lexical_query=query+(' '+' '.join(expansion) if expansion else '')
        base['ranking_expansion']={'terms':expansion,'meaning':'Lexical ranking only; not supplied facts, confidence or legal support'}
        lex=self.lexical_scores(lexical_query) if method in {'bm25','hybrid'} else None
        sem=self.semantic_scores(query) if method in {'semantic','hybrid'} else None
        def ranking(scores,positive=False):return sorted([i for i in allowed if not positive or scores[i]>0],key=lambda i:(-float(scores[i]),self.records[i]['chunk_id']))
        if method=='bm25':score=lex;order=ranking(lex,True)
        elif method=='semantic':score=sem;order=ranking(sem)
        else:
            score=np.zeros(len(self.records));depth=self.config['rrf_candidate_depth'];constant=self.config['rrf_k']
            # Fuse at provision level so long/multi-chunk provisions cannot occupy
            # multiple ranks in either stream. Return the best matching chunk.
            for values,positive in [(lex,True),(sem,False)]:
                seen=set();rank=0
                for i in ranking(values,positive):
                    pid=self.records[i]['provision_id']
                    if pid in seen:continue
                    seen.add(pid);rank+=1
                    if rank>depth:break
                    siblings=[j for j in allowed if self.records[j]['provision_id']==pid]
                    for j in siblings:score[j]+=1/(constant+rank)
            order=ranking(score,True)
            order.sort(key=lambda i:(-score[i],-(float(sem[i])+float(lex[i])/(1+float(lex[i]))),self.records[i]['chunk_id']))
        seen=set()
        for i in order:
            r=self.records[i]
            if r['provision_id'] in seen:continue
            seen.add(r['provision_id']);hit={k:r[k] for k in ['chunk_id','provision_id','document_id','citation_display','heading','display_text','normalized_char_start','normalized_char_end','source_locator','former_locator_labels',
                'parent_provision_id','parent_text','document_title','official_source_url','retrieval_url','raw_local_path','domains','supported_topics','legal_status','status_family','status_as_of','freshness_rule','conditions','legal_relationships','quality_flags','review_status','extraction_method']}
            hit.update(score=float(score[i]),bm25_score=None if lex is None else float(lex[i]),semantic_similarity=None if sem is None else float(sem[i]),retrieval_candidate_only=True,answer_generation_allowed=False)
            base['hits'].append(hit)
            if len(base['hits'])==top_k:break
        base.update(status='candidates_found' if base['hits'] else 'no_lexical_match',reason='requires_freshness_evidence_and_citation_verification' if base['hits'] else 'no_matching_terms')
        return base

    def retrieve_question(self,text,classifier_bundle,method=None,top_k=5):
        sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
        from classifier_runtime import predict_records
        p=predict_records(classifier_bundle,[{'question_text':text}])[0]
        result={'classification':p,'components':[],'answer_generation_allowed':False,'deployment_allowed':False}
        if p['routing_action'] not in {'retrieve_supported_evidence','retrieve_supported_components'}:return result
        requests=p.get('retrieval_requests')
        if requests is None:
            requests=[{'query':c['text'],'allowed_domain':c['category']} for c in p.get('component_evidence',[]) if c['category']==p['predicted_primary'] and c['atomic_evidence_strength']>=.5]
        for request in requests or []:result['components'].append(self.search(request['query'],request['allowed_domain'],method,top_k))
        return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True);p.add_argument('--query',required=True);p.add_argument('--domain',choices=['labor','consumer']);p.add_argument('--method',choices=['bm25','semantic','hybrid']);p.add_argument('--top-k',type=int,default=5);p.add_argument('--topic',action='append');p.add_argument('--classifier',type=Path);a=p.parse_args()
    retriever=LegalRetriever(a.index)
    if a.classifier:
        if a.domain or a.topic:p.error('--domain and --topic are manual-search filters; omit them with --classifier')
        sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
        import joblib
        result=retriever.retrieve_question(a.query,joblib.load(a.classifier),a.method,a.top_k)
    else:
        if not a.domain:p.error('--domain is required unless using --classifier')
        result=retriever.search(a.query,a.domain,a.method,a.top_k,a.topic)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
