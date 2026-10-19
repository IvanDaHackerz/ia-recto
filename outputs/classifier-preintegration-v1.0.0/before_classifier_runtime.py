"""Local experimental routing; never generates legal answers or invents referrals."""
from __future__ import annotations
import argparse,json,re,unicodedata
from pathlib import Path
import joblib
import numpy as np

VALID_PAIRS={('labor','fully_supported'),('consumer','fully_supported'),('mixed','fully_supported'),('mixed','partially_supported'),('out_of_scope','unsupported')}
EMPLOYMENT_CONTEXT=re.compile(r'\b(private|pribado|government|govt|municipal|civil.service|kasambahay|household|ofw|overseas|seafarer|seafrer|seaf[a-z]*r|domestic.worker)\b')
PROVIDER_CONTEXT=re.compile(r'\b(store|shop|retail[a-z]*|seller|merchant|online|bank[a-z]*|bnko|insurance|insurer|airline|telecom|telco|mobile|utility|water|electricity|laundry|grocery|groc[a-z]*|appliance|apliance|repair|furniture|blender|fan|kettle|chair|rice.cooker|credit.card)\b')
CONTRACT_CONTEXT=re.compile(r'\b(employ[a-z]*|private|company|job|work|trabaho|government|municipal|seafarer|ofw|overseas|recruit[a-z]*|store|shop|retail[a-z]*|seller|lease|landlord|tenant|condo[a-z]*|developer|insurance|insurer|bank|subscription|phone|internet|service)\b')

def normalize(text:str)->str:
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',text)).strip()

def strip_training_wrappers(text:str)->str:
    """Remove Item 9 generator boilerplate without using label/topic metadata.

    Patterns come from the generator and training rows, not held-out question text.
    Preserve all scenario facts and apply the same transform during inference.
    """
    t=normalize(text).lower()
    t=re.sub(r'^(?:what are my rights if|what should i do if|saan po ako puwedeng lumapit if|saan po ako dapat lumapit if|can this service advise me if)\s+','',t)
    t=re.sub(r'^(?:allowed po ba ito|i have two concerns|my question involves both issues|dalawa po ang concern ko|which parts of this can you answer)\s*:\s*','',t)
    t=re.sub(r'\s*(?:can you help with both|what rules apply|alin dito ang masasagot ninyo)\?\s*$','',t)
    return t

class ComponentSignalClassifier:
    """Experimental compositional heads from three calibrated binary detectors.

    Products use an independence approximation, not a jointly calibrated posterior.
    Empirical calibration metrics must be reported on each evaluation distribution.
    """
    def __init__(self,head,components):
        self.head=head;self.components=components
        self.classes_=np.array(['labor','consumer','mixed','out_of_scope'] if head=='primary' else ['fully_supported','partially_supported','unsupported'])

    def predict_proba(self,texts):
        values={}
        for name,model in self.components.items():values[name]=model.predict_proba(texts)[:,list(model.classes_).index('present')]
        labor=values['supported_labor'];consumer=values['supported_consumer'];excluded=values['excluded']
        neither=(1-labor)*(1-consumer)
        if self.head=='primary':
            only_labor=labor*(1-consumer)*(1-excluded);only_consumer=consumer*(1-labor)*(1-excluded)
            probs=np.column_stack([only_labor,only_consumer,1-neither-only_labor-only_consumer,neither])
        else:probs=np.column_stack([(1-neither)*(1-excluded),(1-neither)*excluded,neither])
        probs=np.clip(probs,0,1);return probs/probs.sum(axis=1,keepdims=True)

def missing_context(text:str):
    t=normalize(text).lower()
    provider_known=PROVIDER_CONTEXT.search(t) or re.search(r'\b(?:transport\s+operator|recruitment\s+agency|cashier)\b',t)
    product_known=re.search(r'\b(?:product|item)\b',t) and re.search(r'\b(?:bought|purchased|binili\w*|nabili\w*|quality|defect\w*)\b',t)
    if not t:return ('empty_input','What labor or consumer concern would you like help with?')
    if len(re.findall(r'\w+',t))<3:return ('too_little_context','What happened, and who was involved in the transaction or employment relationship?')
    if re.search(r'\b(salary|salry|salaries|salries|wages|sahod|sweldo|employer|employr)\b',t) and not EMPLOYMENT_CONTEXT.search(t):
        return ('employment_category_missing','Is this private-sector, government, household, overseas, or seafarer employment?')
    if re.search(r'refund|irefund|money back|payment back|ibalik.{0,30}(bayad|binayad)|(bayad|binayad|binyad).{0,35}(ibalik|ibalk)',t) and not (provider_known or product_known):
        return ('refund_transaction_missing','Who owes the refund, and what purchase or service was it for?')
    if re.search(r'\b(contract|contrct|kontrata)\b',t) and not CONTRACT_CONTEXT.search(t):
        return ('contract_relationship_missing','What kind of contract ended, and who were the parties?')
    if re.search(r'\b(charg[a-z]*|chrge|singil|singgil)\b',t) and not provider_known:
        return ('charge_context_missing','What were you charged for, and who charged you?')
    return None

def route(text,primary,scope,primary_confidence,scope_confidence,thresholds):
    result={'routing_action':'clarify','substantive_answer_admitted':False,'clarification_question':None,'reason':None,'referral_ids':[]}
    missing=missing_context(text)
    if missing:result.update(reason=missing[0],clarification_question=missing[1]);return result
    if (primary,scope) not in VALID_PAIRS:
        result.update(reason='inconsistent_primary_scope',clarification_question='Could you clarify the main concern and whether there is a separate issue?');return result
    if primary_confidence<thresholds['primary'] or scope_confidence<thresholds['scope']:
        result.update(reason='low_confidence',clarification_question='Could you describe what happened and the kind of employer, seller, or service involved?');return result
    if primary=='mixed':
        result.update(reason='mixed_components_not_resolved',clarification_question='Please separate the concerns and identify the employer, seller, or service for each one.');return result
    if primary=='out_of_scope':
        result.update(routing_action='refer_out_of_scope',reason='recognized_excluded_concern');return result
    result.update(routing_action='retrieve_supported_evidence',reason='supported_candidate_requires_evidence',substantive_answer_admitted=True)
    return result

def route_prediction(prediction,thresholds):
    p=prediction
    result=route(p['question_text'],p['predicted_primary'],p['predicted_scope'],p['primary_confidence'],p['scope_confidence'],thresholds)
    if missing_context(p['question_text']):return result
    segmentation=p.get('segmentation_audit')
    if segmentation and (not segmentation['all_fragments_accounted_for'] or segmentation['requires_clarification']):
        result.update(routing_action='clarify',substantive_answer_admitted=False,reason=segmentation['reason'] or 'unaccounted_input_fragment',
            clarification_question='Could you describe each separate concern and identify the employer, seller, or service involved?')
        return result
    if not p.get('has_reliable_component_evidence',True):
        result.update(routing_action='clarify',substantive_answer_admitted=False,reason='no_reliable_component_evidence',clarification_question='Could you describe the specific employment or consumer concern and who is involved?')
        return result
    if result['reason']!='mixed_components_not_resolved' or not p.get('component_routing_enabled',False):return result
    components=p.get('component_evidence',[])
    reliable=[c for c in components if c['atomic_evidence_strength']>=.5]
    if len(reliable)!=len(components):return result
    supported=[c for c in reliable if c['category'] in ('labor','consumer')];excluded=[c for c in reliable if c['category']=='excluded']
    domains={c['category'] for c in supported}
    coherent=bool(supported) and (bool(excluded) if p['predicted_scope']=='partially_supported' else domains=={'labor','consumer'} and not excluded)
    if not coherent or any(missing_context(c['text']) for c in supported):return result
    result.update(routing_action='retrieve_supported_components',reason='separate_supported_components_require_evidence',substantive_answer_admitted=True,clarification_question=None,
        retrieval_requests=[{'query':c['text'],'allowed_domain':c['category'],'requires_answer_eligible_evidence':True} for c in supported],
        excluded_components=[{'text':c['text'],'constraint_topic':c.get('constraint'),'retrieval_allowed':False} for c in excluded])
    return result

def predict_records(bundle,rows):
    texts=[r['question_text'] for r in rows]
    p=bundle['primary_model'].predict_proba(texts);s=bundle['scope_model'].predict_proba(texts)
    pclasses=list(bundle['primary_model'].classes_);sclasses=list(bundle['scope_model'].classes_)
    primary_labels=bundle['primary_model'].predict(texts) if hasattr(bundle['primary_model'],'predict') else np.array(pclasses)[p.argmax(axis=1)]
    scope_labels=bundle['scope_model'].predict(texts) if hasattr(bundle['scope_model'],'predict') else np.array(sclasses)[s.argmax(axis=1)]
    engine=getattr(bundle['primary_model'],'engine',None)
    decisions=engine.decisions(texts) if engine is not None and hasattr(engine,'decisions') else None
    results=[]
    for i,(row,text) in enumerate(zip(rows,texts)):
        primary=primary_labels[i];scope=scope_labels[i];pi=pclasses.index(primary);si=sclasses.index(scope)
        result={'question_id':row.get('question_id'),'question_text':text,'predicted_primary':primary,'predicted_scope':scope,
            'primary_confidence':float(p[i,pi]),'scope_confidence':float(s[i,si]),
            'primary_probabilities':dict(zip(pclasses,map(float,p[i]))),'scope_probabilities':dict(zip(sclasses,map(float,s[i]))),
            'model_version':bundle['model_version'],'deployment_allowed':False,
            'confidence_meaning':'Estimated label probability under the training/calibration distribution; not legal correctness or a real-world guarantee.'}
        result['has_reliable_component_evidence']=decisions[i][2] if decisions is not None else True
        result['component_routing_enabled']=bundle.get('resolve_mixed_components',False)
        if result['component_routing_enabled'] and engine is not None:
            result['component_evidence']=engine.component_evidence(text)
            if hasattr(engine,'segmentation_audit'):result['segmentation_audit']=engine.segmentation_audit(text)
        result.update(route_prediction(result,bundle['thresholds']))
        if bundle.get('referral_routing_enabled',False) and result['routing_action'] in {'refer_out_of_scope','retrieve_supported_components'}:
            from referral_routing import select_referrals
            result['referral_candidates']=select_referrals(result.get('component_evidence',[]))
            result['referral_ids']=[r['referral_id'] for r in result['referral_candidates']]
        results.append(result)
    return results

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--text',required=True);args=p.parse_args()
    # Load only project-created trusted joblib packages, never an untrusted download.
    bundle=joblib.load(args.model)
    print(json.dumps(predict_records(bundle,[{'question_text':args.text}])[0],indent=2,ensure_ascii=False))

if __name__=='__main__':main()
