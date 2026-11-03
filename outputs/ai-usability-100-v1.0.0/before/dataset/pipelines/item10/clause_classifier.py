"""Training-only atomic cases and multilingual clause classification."""
from __future__ import annotations
import re,collections
import numpy as np
from scipy.special import softmax
from sklearn.pipeline import FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from scipy import sparse
from classifier_runtime import normalize,missing_context,route
from semantic_encoder import encode

ATOMIC=['labor','consumer','excluded']
STATES=['100','010','110','101','011','001']
PREFIX=r'^(?:allowed po ba ito|i have two concerns|my question involves both issues|dalawa po ang concern ko|which parts of this can you answer)\s*[:?.]?\s*'
FRONT=r'^(?:what are my rights if|what should i do if|saan po ako puwedeng lumapit if|saan po ako dapat lumapit if|can this service advise me if)\s+'
SUFFIX=r'\s*(?:can you help with both|what rules apply|alin dito ang masasagot ninyo)\?\s*$'
LEGAL_CUES=re.compile(r'\b(pay\w*|paid|deduct\w*|wage\w*|salar\w*|sahod|sweldo|employ\w*|trabaho|work\w*|private|government|municipal|holiday|rest|overtime|ot|13th|thirteenth|probation\w*|contract|kontrata|dismiss\w*|fir\w*|coe|seafar\w*|ofw|kasambahay|union|pension|retire\w*|osha?|safety|consumer|shop|store|retail\w*|seller|appliance|product|item|fan|kettle|blender|rice|vacuum|keyboard|chair|repair|refund|warr?ant\w*|warant\w*|defect\w*|gumagana|sira|binili|bili|order|deliver\w*|bill\w*|return\w*|price|singil|sukli|change|charge\w*|chrge|cashier|grocer\w*|online|laundry|bank\w*|credit|interest|insur\w*|claim|investment|fund|privacy|data|id|doctor|surgeon|medical|patient|treatment|hospital|condo\w*|developer|airline|flight|water|electric\w*|mobile|phone|internet|telecom|scam|fraud|criminal|police|case|tribunal|nlrc|sena|dole|dti|minimum|standards|ventilation|chemical)\b')
SEGMENT=re.compile(r';\s*(?:and\s+)?|[\n]+|[.!?]+\s*|\s*\+\s*|\band\s+also\s+|\b(?:separately|tapos|kasabay nito|tsaka|saka)\b\s*[,.:]?\s*|\s+also\s+(?=(?:i|my|a|an|the|may|yung)\b)|,?\s+\b(?:and|while)\s+(?=(?:i|my|a|an|the|we|our|what\w*|help\s+with|advice\s+about)\b)|\bat\s+(?=(?:gusto|may|sa|yung|ang|kailangan)\b)',re.I)
EMPLOYMENT_CUES=re.compile(r'\b(pay|wage\w*|salary|salaries|sahod|sweldo|employ\w*|job|overtime|rest.day|thirteenth|13th|probation\w*|dismiss\w*|fired|coe|appeal\w*|administrative)\b')
CONTEXT=re.compile(r'\b(private|pribado|government|govt|municipal|kasambahay|household|overseas|ofw|seaf[a-z]*r)\b')
NON_EMPLOYMENT=re.compile(r'\b(bank|credit|insur\w*|store|shop|retail\w*|seller|online|appliance|product|refund|grocery|laundry|payment|repair|service|cashier|item|consumer)\b')

def clean(text):
    from typing_repair import matching_text
    t=matching_text(normalize(text)).lower();t=re.sub(FRONT,'',t);t=re.sub(PREFIX,'',t);return re.sub(SUFFIX,'',t).strip(' .?;')

ISSUE_INTENT=re.compile(r'\b(?:complaint|reklamo|problema|dispute)\b|\b(?:my|another|separate|second|a|have|may)\s+(?:concern|problem|issue)\b',re.I)
BACKGROUND_INTRO=re.compile(r"^(?:i\s+(?:am|work|am employed)\b|i'm\b|(?:seaf[a-z]*r|ofw|kasambahay)\s+ako\b|(?:private|government|municipal)\b.*\b(?:employee|employe|worker)\b)",re.I)
FOLLOW_UP_REFERENCE=re.compile(r'^(?:how\s+(?:do|can|should)\s+(?:i|we)\s+(?:raise|dispute|challenge|resolve|handle|report)\s+(?:(?:each|both|these|those)\s+(?:disputes?|issues?|concerns?)|it|this|that|(?:this|that|the)\s+(?:dispute|issue|denial|decision))|can\s+you\s+explain\s+(?:the\s+)?(?:exclusion|denial|decision)(?:\s+and\s+how\s+to\s+(?:dispute|challenge|appeal)\s+it)?)(?:\s+please)?$',re.I)
JOINED_COMPLAINT=re.compile(r"\s+(?:at|and|pero|but)\s+(?:(?:then|later|subsequently)\s+)?(?=(?:ayaw|hindi|di|wala(?:ng)?|refuse\w*|posted|published|leaked|exposed|pinost|inilabas|won't|will\s+not|doesn't|does\s+not|didn't|did\s+not|cannot|can't)\b)",re.I)
PAY_BACKGROUND=re.compile(r'^(?:i|we)\s+(?:(?:was|were|am|are)\s+)?(?:about\s+to|going\s+to|heading\s+to|on\s+(?:my|our)\s+way\s+to)\s+(?:get|collect|receive)\s+(?:my|our)\s+(?:pay|salary|wages)\s*$',re.I)
TRAVEL_BACKGROUND=re.compile(r'^(?:i|we)\s+(?:(?:was|were|am|are)\s+)?(?:walking\s+to|on\s+(?:my|our)\s+way\s+to)\s+(?:work|the\s+(?:office|store|shop))$',re.I)


def same_topic_rule_follow_up(previous, fragment):
    """Attach a rule question only when its topic is already in the scenario.

    Preserve both sentences verbatim. A new topic, actor, employment category,
    or asserted fact cannot be absorbed by this question-only template.
    """
    from scope_constraints import constraint
    previous_scope,follow_scope=constraint(previous),constraint(fragment)
    if follow_scope and follow_scope[0]=='excluded' and (not previous_scope or previous_scope[1]!=follow_scope[1]):return False
    # These requests point back to a described concern. A generic word such as
    # 'complaint' must not manufacture a new Consumer concern on its own.
    if re.fullmatch(r'(?:where\s+(?:does|would)\s+(?:this|that|the)\s+(?:dispute|complaint|concern|issue)\s+fit|can\s+you\s+(?:handle|help\s+with|explain|assess)\s+(?:this|that|the)\s+(?:dispute|complaint|concern|issue))',fragment):
        return True
    if re.fullmatch(r'(?:what|which)\s+(?:(?:general|basic|consumer|service|pay)\s+){0,3}(?:rules|rights|protections|options)\s+(?:apply(?:\s+(?:here|to\s+(?:this|that)))?|cover\s+(?:it|this|that|the\s+staff\s+who\s+worked))|what\s+(?:kind|type)\s+of\s+(?:sales\s+)?practice\s+is\s+this|which\s+scope\s+does\s+that\s+fall\s+under',fragment):
        return True
    from scope_constraints import employment_issue
    if employment_issue(previous) and re.fullmatch(r'is\s+(?:the|that|this)\s+extra\s+(?:time|work)\s+paid\s+(?:differently|extra)',fragment):return True
    if employment_issue(previous) and re.fullmatch(r'(?:do|does|should|would)\s+(?:those|these|that|this|the)\s+(?:minutes|hours|time|briefing|waiting\s+time)\s+(?:count|qualify)(?:\s+as)?\s+(?:paid\s+)?(?:working\s+time|work|hours\s+worked)',fragment):return True
    if employment_issue(previous) and re.fullmatch(r'(?:should|would|could|can)\s+(?:i|we)\s+(?:still\s+)?(?:have\s+been\s+|be\s+)?(?:paid|compensated)\s+for\s+(?:that|this|the.same)\s+(?:day|time|work|shift|hours)',fragment):
        return True
    if employment_issue(previous) and re.fullmatch(r'where\s+can\s+(?:workers|employees|i|we)\s+(?:begin|start|ask\s+for\s+help)',fragment):return True
    # Topic-bearing questions inherit only a topic already asserted in the
    # scenario. New actors, categories, or separate concerns remain separate.
    themes=[r'\b(?:employment.status|project.contracts?|project.based|regulari[sz]\w*|regular.employ\w*)\b',
            r'\b(?:working.time|hours?.of.work|clock\s+in|clock-in|required.waiting|equipment.check)\b',
            r'\b(?:warrant\w*|guarant\w*)\b',r'\b(?:refund|replac\w*|repair)\b',
            r'\b(?:dismiss\w*|termination|removed.{0,40}roster|fired)\b',
            r'\b(?:product.safety|unsafe|exposed.(?:live.)?(?:wir(?:es?|ing)|metal)|extension.cord)\b',
            r'\b(?:wages?|salary|salaries|payday|sahod|sweldo)\b',
            r'\b(?:overtime|ot)\b',r'\b(?:holiday|christmas|pasko)\b',
            r'\b(?:rest.day|weekly.rest|day.off)\b',r'\b(?:13th|thirteenth)\b',
            r'\b(?:price.tag|price-tag|sukli|shortchang\w*)\b',
            r'\b(?:service.quality|repair.service|laundry)\b',
            r'\b(?:advert\w*|misleading)\b',r'\b(?:online|internet.transaction|marketplace)\b']
    question=re.match(r'^(?:what|which|how|is|are|can\s+you)\b',fragment)
    specific_actor=re.search(r'\b(?:government|household|overseas|ofw|seafar\w*|another|separate|my\s+(?:employer|seller|landlord)|i\s+(?:bought|work|paid))\b',fragment)
    if question and not specific_actor and any(re.search(p,previous) and re.search(p,fragment) for p in themes):return True
    match=re.fullmatch(r'(?:what|which)\s+([\w -]+?)\s+(?:rules?(?:\s+and\s+exceptions?)?|exceptions?)\s+apply(?:\s+(?:here|to\s+(?:this|that)))?',fragment)
    if not match:return False
    def concepts(text):
        words=set(re.findall(r'\w+',text))
        aliases={'christmas':'holiday','pasko':'holiday','holidays':'holiday','paid':'pay','payment':'pay',
                 'wages':'wage','salaries':'salary','rules':'rule','refunds':'refund'}
        return {aliases.get(w,w) for w in words}
    topic=concepts(match.group(1))-{'the','applicable'}
    return bool(topic) and topic<=concepts(previous)


def split_joined_complaints(text):
    """Split predicate-led complaints only when each side has its own issue.

    A conjunction alone is insufficient: noun lists (wages and overtime),
    negated employment categories and unanchored follow-ups stay together.
    Apply this after the existing explicit sentence/subject boundaries, before
    exclusion rules can let one concern override the other.
    """
    from scope_constraints import RETAIL,CONSUMER_ISSUE,LABOR,constraint,scope_text
    def issue(part):
        return bool(constraint(part) or LABOR.search(scope_text(part)) or ISSUE_INTENT.search(part)
                    or RETAIL.search(part) and CONSUMER_ISSUE.search(part))
    for match in JOINED_COMPLAINT.finditer(text):
        # Do not introduce a new boundary inside an explicitly quoted passage.
        if any(a.start() <= match.start() < a.end() for a in re.finditer(r'"[^"\n]*"|“[^”\n]*”',text)):
            continue
        left,right=text[:match.start()].strip(),text[match.end():].strip()
        if issue(left) and issue(right):
            return [left,*split_joined_complaints(right)]
    return [text]

def segment_question(text,propagate_context=True):
    """Retain an account of every fragment, including background and unresolved issues.

    Background must be an explicit self-introduction, not merely a clause lacking
    a wage/product keyword. An excluded-topic complaint is a concern in its own
    right. Background never becomes a second concern by itself.
    """
    from scope_constraints import RETAIL,CONSUMER_ISSUE,LABOR,constraint,scope_text,literal_concern_text,negated_scope_statement,historical_background,employment_background,FOREIGN_WORKPLACE
    t=clean(literal_concern_text(text));parts=[re.sub(r'^also\s*,?\s*','',p.strip(' ,.:;?!'))
        for explicit in SEGMENT.split(t) for p in split_joined_complaints(explicit)]
    parts=[piece for p in parts if p for piece in re.split(r',?\s+(?:but|pero)\s+(?=(?:i|my|we|our|ako)\b)',p,flags=re.I)]
    anchored=re.compile(r'\b(?:company|redundan\w*|bus|passenger|cord|table|unsafe|faulty|overseas|retailer|sukli|pinost|posted|public|exact|minimun|minimum)\b')
    kept=[];fragments=[];pending=[];unresolved=[]
    for p in parts:
        if not p:continue
        fragment={'fragment_id':len(fragments),'text':p,'role':None,'component_index':None}
        fragments.append(fragment)
        from scope_constraints import employment_issue
        if (kept and employment_issue(kept[-1])
                and re.match(r'^(?:my|our|the)\s+(?:payslip|payroll|pay.stub|timesheet)\b',p)
                and not (constraint(p) and constraint(p)[0]=='excluded')):
            fragment.update(role='follow_up',component_index=len(kept)-1);kept[-1]+='. '+p;continue
        # A description of the item just bought retains the purchase relation.
        # New actors/transactions and explicit exclusions remain separate.
        if kept and re.search(r'\b(?:bought|purchased|bumili|binili|nabili|kakabili)\b',kept[-1]) and RETAIL.search(kept[-1]):
            defect=re.search(r'\b(?:broken|cracked|faulty|defect\w*|sira|basag|not\s+working|hindi\s+gumagana|di\s+gumagana)\b',p)
            reference=re.search(r'\b(?:it|its|the|yung|ang|unit|switch|screen|casing|item|product)\b',p)
            new_actor=re.search(r'\b(?:another|separate|also|separately|my\s+(?:employer|bank|insurer)|bought|purchased|bumili|binili)\b',p)
            rule=constraint(p)
            if defect and reference and not new_actor and (not rule or rule[0]=='consumer'):
                fragment.update(role='follow_up',component_index=len(kept)-1);kept[-1]+='. '+p;continue
        # A payment detail using only "it/this/that" belongs to its existing
        # transaction; it does not assert a second employment concern.
        if kept and re.fullmatch(r'(?:i|we)\s+(?:already\s+)?(?:paid|have\s+paid|made\s+(?:a|the)\s+payment)\s+(?:for\s+)?(?:it|this|that)',p):
            fragment.update(role='follow_up',component_index=len(kept)-1);kept[-1]+='. '+p;continue
        # Purchase anaphora describe the transaction just introduced, not a
        # new transaction with a second scope. Preserve the asserted claim.
        if kept and re.fullmatch(r'(?:i|we)\s+(?:bought|purchased|ordered)\s+(?:it|this|that)\s+(?:based\s+on|because\s+of)\s+(?:that|the|this)\s+(?:claim|promise|advertisement)',p):
            fragment.update(role='follow_up',component_index=len(kept)-1);kept[-1]+='. '+p;continue
        if PAY_BACKGROUND.fullmatch(p) or TRAVEL_BACKGROUND.fullmatch(p) or negated_scope_statement(p) or (len(parts)>1 and (historical_background(p) or employment_background(p))):
            fragment['role']='background';continue
        if re.fullmatch(r'(?:\w+\s+){0,3}(?:paydays?|days?|weeks?|months?)\s+have\s+(?:passed|elapsed)',p):
            fragment['role']='preface';pending.append(fragment);continue
        if len(parts)>1 and re.fullmatch(r'(?:i|we)\s+used\s+(?:it|this|that)\s+at\s+(?:a|the)\s+(?:store|shop|retailer)',p):
            fragment['role']='preface';pending.append(fragment);continue
        # Work history without a disputed act is context for the later request,
        # not an independent termination complaint merely because it says resign.
        if re.search(r'\b(?:resigned|worked|nagtrabaho|nagresign)\b',p) and not re.match(r'^(?:what|which|how|why|when|where|is|are|can|could|may|ano|paano)\b',p) and not ISSUE_INTENT.search(p) and not re.search(r'\b(?:refus\w*|denied|withheld|unpaid|not.paid|without|fired|dismiss\w*|owe\w*|holiday|overtime|13th|thirteenth|final.pay|coe|warrant\w*)\b',p) and len(parts)>1:
            fragment['role']='preface';pending.append(fragment);continue
        cues=[m.group(0) for m in LEGAL_CUES.finditer(p) if m.group(0) not in {'claim','case'}]
        rule=constraint(p)
        anchored_fact=bool(cues or anchored.search(p) or rule or LABOR.search(p) or CONSUMER_ISSUE.search(p)
                           or CONTEXT.search(t) and re.search(r'\b(?:appeal\w*|administrative)\b',p))
        context_only=(BACKGROUND_INTRO.search(p) and CONTEXT.search(p) and not ISSUE_INTENT.search(p)
            and not LABOR.search(scope_text(p)) and not CONSUMER_ISSUE.search(p)
            and not re.search(r'\b(?:question|promotion|required|changed|denied|refuse\w*|gusto|want|need|malaman|appeal|correct|dispute|help)\b',p)
            and (rule is None or rule[1] in {'labor.ofw','labor.seafarers','labor.government_employment','labor.kasambahay'}))
        if context_only:
            fragment['role']='background';continue
        # A standalone question still reaches the learned classifier even if
        # the structural cue vocabulary does not contain its wording. These
        # cues distinguish fragments; they are not a whitelist of legal topics.
        generic_only=re.fullmatch(r'(?:hello(?: there)?|hi|hey|thanks|thank you|(?:can|could) you help(?: me| us)?(?: please)?|what (?:can|should) i do(?: next| now)?|what happens next)',p)
        if len(parts)==1 and len(p.split())>=3 and not ISSUE_INTENT.search(p) and not generic_only:anchored_fact=True
        # An anaphoric request about existing concerns is a follow-up. New
        # explicit topics still have cues/rules and remain independent concerns.
        if kept and (not anchored_fact and FOLLOW_UP_REFERENCE.search(p) or same_topic_rule_follow_up(kept[-1],p)):
            fragment['role']='follow_up';fragment['component_index']=len(kept)-1
            kept[-1]+='. '+p;continue
        if not anchored_fact and ISSUE_INTENT.search(p):
            fragment['role']='unresolved_concern';unresolved.append(fragment['fragment_id'])
        elif not anchored_fact:
            fragment['role']='follow_up' if kept else 'preface'
            if kept:
                kept[-1]+='. '+p;fragment['component_index']=len(kept)-1
            else:pending.append(fragment)
            continue
        else:fragment['role']='concern'
        fragment['component_index']=len(kept)
        prefix='. '.join(f['text'] for f in pending)
        kept.append((prefix+'. ' if prefix else '')+p)
        for f in pending:f['component_index']=fragment['component_index']
        pending=[]
    # A pending preface is retained even when no recognizable concern follows it.
    if pending:
        kept.append('. '.join(f['text'] for f in pending))
        for f in pending:f['component_index']=len(kept)-1
    parts=kept
    if propagate_context:
        contexts={m.group() for m in CONTEXT.finditer(t)
            if not re.search(r'\b(?:not|hindi|never)\s+(?:(?:a|an|the|ako|sa)\s+){0,2}$',t[max(0,m.start()-24):m.start()])}
        # Actor introductions can name a public employer without the literal
        # word "government". Carry that category only to employment concerns.
        if re.search(r'\b(?:employ\w*|work\w*)\b.{0,35}\bcity\s+hall\b',t):contexts.add('government')
        if re.search(r'\bpublic\s+(?:school\s+teacher|hospital\s+(?:nurse|employee|worker))\b',t):contexts.add('government')
        if FOREIGN_WORKPLACE.search(t):contexts.add('ofw')
        job_context=constraint(t)
        if job_context and job_context[0]=='excluded':
            if job_context[1]=='labor.government_employment':contexts.add('government')
            if job_context[1]=='labor.kasambahay':contexts.add('kasambahay')
            if job_context[1]=='labor.ofw':contexts.add('ofw')
        if re.search(r'\blive[- ]in\s+(?:helper|maid|nanny|housekeeper)\b',t):contexts.add('kasambahay')
        context_alias={'pribado':'private','govt':'government','municipal':'government','household':'kasambahay','overseas':'ofw'}
        contexts={('seafarer' if c.startswith('seaf') else context_alias.get(c,c)) for c in contexts}
        if 'seafarer' in contexts:contexts.discard('ofw')
        # Private ownership does not cancel an explicitly specialized job.
        if contexts & {'ofw','seafarer','government','kasambahay'}:contexts.discard('private')
        # Propagate only one unambiguous employment category, and only into employment clauses.
        if len(contexts)==1:
            context=next(iter(contexts));parts=[context+' employment: '+p if (EMPLOYMENT_CUES.search(p) or LABOR.search(p)) and not CONTEXT.search(p) and not NON_EMPLOYMENT.search(p) else p for p in parts]
        if any(RETAIL.search(p) for p in parts):
            parts=['retail transaction: '+p if CONSUMER_ISSUE.search(p) and not LABOR.search(p) and not RETAIL.search(p) and constraint(p) is None else p for p in parts]
        regulated={'consumer.telecommunications':'telecom service','consumer.banking_credit':'bank account','consumer.insurance':'insurance service','consumer.utility_billing':'utility billing'}
        contexts={rule[1] for p in parts if (rule:=constraint(p)) and rule[1] in regulated}
        if len(contexts)==1:
            context=regulated[next(iter(contexts))]
            parts=[context+': '+p if re.search(r'\b(?:charge\w*|chrge|refund|bill\w*|service)\b',p) and not RETAIL.search(p) and not LABOR.search(p) and constraint(p) is None else p for p in parts]
    # Keep source-fragment accounting through deduplication; never truncate away
    # a thirteenth concern. Excess complexity is instead blocked by the router.
    unique=list(dict.fromkeys(parts));remap={i:unique.index(p) for i,p in enumerate(parts)}
    for f in fragments:
        if f['component_index'] is not None:f['component_index']=remap[f['component_index']]
    has_concern=any(f['role'] in {'concern','unresolved_concern'} for f in fragments)
    return {'components':unique,'fragments':fragments,'unresolved_fragment_ids':unresolved,
        'all_fragments_accounted_for':all(f['role'] is not None and (f['component_index'] is not None or f['role']=='background') for f in fragments),
        'requires_clarification':bool(unresolved) or not has_concern or len(unique)>12,
        'reason':'unresolved_concern' if unresolved else 'no_identified_concern' if not has_concern else 'too_many_concerns' if len(unique)>12 else None}

def split_clauses(text,propagate_context=True):
    return segment_question(text,propagate_context)['components']

def state_of(row):return ''.join(str(int(v)) for v in (any(t.startswith('labor.') for t in row['supported_topic_ids']),any(t.startswith('consumer.') for t in row['supported_topic_ids']),bool(row['excluded_topic_ids'])))

def training_atoms(row):
    t=clean(row['question_text']);state=state_of(row)
    if row['primary_label']!='mixed':
        category='excluded' if state=='001' else 'labor' if state=='100' else 'consumer'
        topics=row['excluded_topic_ids'] if category=='excluded' else row['supported_topic_ids']
        return [{'text':t,'category':category,'topic_ids':topics,'source_question_id':row['question_id'],'source_group':row['leakage_group_id'],'origin':'training_parent_atomic_derivation'}]
    # Item 9 orders a supported issue first, then consumer (full mixed) or an excluded issue (partial).
    # Use explicit generator separators; never infer atom labels from evaluation questions.
    patterns=[r';\s*(?:and\s+)?',r'\.\s*(?:also|tapos)\s*,?\s*',r',\s*and\s+(?=(?:i|my|a|an|the)\b)']
    parts=None
    for pattern in patterns:
        candidate=re.split(pattern,t,maxsplit=1,flags=re.I)
        if len(candidate)==2:parts=candidate;break
    if parts is None:raise ValueError('Unparsed mixed training row: '+row['question_id']+' '+t)
    first_category='labor' if state[0]=='1' else 'consumer'
    second_category='consumer' if state=='110' else 'excluded'
    cats=[first_category,second_category]
    result=[]
    for text,category in zip(parts,cats):
        topics=[x for x in (row['excluded_topic_ids'] if category=='excluded' else row['supported_topic_ids']) if category=='excluded' or x.startswith(category+'.')]
        result.append({'text':text.strip(' .?;'),'category':category,'topic_ids':topics,'source_question_id':row['question_id'],'source_group':row['leakage_group_id'],'origin':'training_parent_atomic_derivation'})
    return result

def glossary_atoms(taxonomy):
    result=[]
    for row in taxonomy:
        category='excluded' if row['scope_status']=='excluded' else row['domain']
        description=re.sub(r'\b(?:are|is) outside (?:the )?(?:initial |consumer )?mvp\.?','',row['description'],flags=re.I)
        description=re.sub(r'\b(?:are|is) excluded\.?','',description,flags=re.I)
        text=row['label']+'. '+description
        result.append({'text':text,'category':category,'topic_ids':[row['topic_id']],'source_question_id':None,'source_group':'taxonomy:'+row['topic_id'],'origin':'project_scope_taxonomy_definition'})
    return result

def deduplicate(atoms):
    unique={}
    for atom in atoms:
        key=' '.join(re.findall(r'\w+',atom['text'].lower()))
        if key in unique:
            if unique[key]['category']!=atom['category']:raise ValueError('Conflicting atom labels '+key)
            unique[key]['parent_ids']+=([atom['source_question_id']] if atom['source_question_id'] else [])
            unique[key]['topic_ids']=sorted(set(unique[key]['topic_ids'])|set(atom['topic_ids']))
        else:unique[key]={**atom,'normalized_fact':key,'parent_ids':[atom['source_question_id']] if atom['source_question_id'] else []}
    return list(unique.values())

class AtomicClassifier:
    def __init__(self,feature_kind='semantic',C=10.,semantic_weight=1.,use_scope_constraints=False):self.feature_kind=feature_kind;self.C=C;self.semantic_weight=semantic_weight;self.use_scope_constraints=use_scope_constraints
    def fit(self,atoms):
        self.atoms=deduplicate(atoms);texts=[a['text'] for a in self.atoms];y=[a['category'] for a in self.atoms]
        self.lexical=None
        if self.feature_kind in ('lexical','hybrid'):
            self.lexical=FeatureUnion([('words',TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,min_df=1,max_features=15000)),('characters',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True,min_df=1,max_features=30000))]);lex=self.lexical.fit_transform(texts)
        if self.feature_kind=='semantic':features=encode(texts)*self.semantic_weight
        elif self.feature_kind=='lexical':features=lex
        else:features=sparse.hstack([lex,sparse.csr_matrix(encode(texts)*self.semantic_weight)],format='csr')
        self.model=LogisticRegression(C=self.C,class_weight='balanced',max_iter=2500,random_state=20261017).fit(features,y)
        return self
    def probabilities(self,texts):
        if self.feature_kind=='semantic':features=encode(texts)*self.semantic_weight
        elif self.feature_kind=='lexical':features=self.lexical.transform(texts)
        else:features=sparse.hstack([self.lexical.transform(texts),sparse.csr_matrix(encode(texts)*self.semantic_weight)],format='csr')
        p=self.model.predict_proba(features);return p[:,[list(self.model.classes_).index(c) for c in ATOMIC]]
    def question_features(self,texts):
        audits=[segment_question(t) for t in texts]
        # Prefaces/background alone supply no domain evidence. Retain them in
        # the audit without letting an arbitrary classifier guess drive labels.
        groups=[a['components'] if a['reason']!='no_identified_concern' else [] for a in audits]
        allparts=list(dict.fromkeys(p for group in groups for p in group))
        lookup=dict(zip(allparts,self.probabilities(allparts))) if allparts else {};features=[]
        for parts in groups:
            if not parts:features.append([0.]*6);continue
            p=np.array([lookup[t] for t in parts]);dominant=np.zeros_like(p)
            winners=p.argmax(axis=1)
            for i,winner in enumerate(winners):
                rule=None
                if getattr(self,'use_scope_constraints',False):
                    from scope_constraints import constraint
                    rule=constraint(parts[i])
                if rule:dominant[i,ATOMIC.index(rule[0])]=1.
                elif p[i,winner]>=.5:dominant[i,winner]=p[i,winner]
            mx=dominant.max(axis=0)
            # No sentence count or secondary-class noise: repeated same-domain details cannot create a second issue.
            features.append([*mx,mx[0]*mx[1],mx[0]*mx[2],mx[1]*mx[2]])
        return np.array(features,dtype=float)

class ClauseEngine:
    def __init__(self,atomic,joint_model):self.atomic=atomic;self.joint_model=joint_model
    def state_probabilities(self,texts):return self.joint_model.predict_proba(self.atomic.question_features(texts))
    def component_evidence(self,text):
        parts=split_clauses(text);p=self.atomic.probabilities(parts)
        return [{'text':t,'category':ATOMIC[int(np.argmax(v))],'probabilities':dict(zip(ATOMIC,map(float,v)))} for t,v in zip(parts,p)]

class ClauseHead:
    def __init__(self,head,engine):
        self.head=head;self.engine=engine;self.classes_=np.array(['labor','consumer','mixed','out_of_scope'] if head=='primary' else ['fully_supported','partially_supported','unsupported'])
    def predict_proba(self,texts):
        p=self.engine.state_probabilities(texts);out=np.zeros((len(texts),len(self.classes_)))
        for i,state in enumerate(self.engine.joint_model.classes_):
            l,c,e=map(int,state)
            target='out_of_scope' if not(l or c) else 'mixed' if e or(l and c) else 'labor' if l else 'consumer'
            scope='unsupported' if not(l or c) else 'partially_supported' if e else 'fully_supported'
            out[:,list(self.classes_).index(target if self.head=='primary' else scope)]+=p[:,i]
        return out
