"""Coherent multi-label clause decisions with training-only grouped probability calibration."""
from __future__ import annotations
import hashlib,re
import numpy as np
from sklearn.base import BaseEstimator,ClassifierMixin
from scipy.special import softmax
from clause_classifier import AtomicClassifier,training_atoms,clean,ATOMIC,STATES

def decoded_state(value):
    # cross_val_predict encodes class strings to integer indices inside calibration.
    return sorted(STATES)[int(value)] if isinstance(value,(int,np.integer)) else value

def fact_texts(text):
    t=clean(text)
    for pattern in [r';\s*(?:and\s+)?',r'\.\s*(?:also|tapos)\s*,?\s*',r',\s*and\s+(?=(?:i|my|a|an|the)\b)']:
        parts=re.split(pattern,t,maxsplit=1,flags=re.I)
        if len(parts)==2:return parts
    return [t]

def normalized_fact(t):return ' '.join(re.findall(r'\w+',t.lower()))

def row_from_state(text,state):
    state=decoded_state(state)
    l,c,e=map(int,state)
    return {'question_text':text,'question_id':'TRAIN_'+hashlib.sha256(text.encode()).hexdigest()[:16],'leakage_group_id':'derived_parent',
        'primary_label':'out_of_scope' if not(l or c) else 'mixed' if e or(l and c) else 'labor' if l else 'consumer',
        'supported_topic_ids':(['labor.derived_signal'] if l else [])+(['consumer.derived_signal'] if c else []),'excluded_topic_ids':['excluded.derived_signal'] if e else []}

class LogicalClauseEstimator(ClassifierMixin,BaseEstimator):
    def __init__(self,feature_kind='semantic',C=10.,semantic_weight=1.,training_texts=None,glossary=None,minimum_atomic_confidence=.5,use_scope_constraints=False):
        self.feature_kind=feature_kind;self.C=C;self.semantic_weight=semantic_weight;self.training_texts=training_texts;self.glossary=glossary;self.minimum_atomic_confidence=minimum_atomic_confidence;self.use_scope_constraints=use_scope_constraints
    def fit(self,X,y):
        self.classes_=np.array(sorted(set(y)));current=set(X)
        forbidden={normalized_fact(t) for p in self.training_texts if p not in current for t in fact_texts(p)}
        atoms=[a for text,state in zip(X,y) for a in training_atoms(row_from_state(text,state))]
        kept=[a for a in atoms if normalized_fact(a['text']) not in forbidden]
        self.atomic=AtomicClassifier(self.feature_kind,self.C,self.semantic_weight,self.use_scope_constraints).fit(kept+self.glossary)
        self.fit_parent_texts_=list(X);self.purged_facts_=len(atoms)-len(kept)
        self.fit_atom_facts_=[normalized_fact(a['text']) for a in self.atomic.atoms]
        if set(self.fit_atom_facts_)&forbidden:raise ValueError('Atomic fact leaked into calibration fold')
        return self
    def signals(self,X):
        features=self.atomic.question_features(X);return features[:,:3]
    def decision_function(self,X):
        signals=self.signals(X);p=np.clip(signals,.03,.97);scores=[]
        for state in self.classes_:
            state=decoded_state(state)
            bits=np.array(list(map(int,state)));scores.append((np.log(p)*bits+np.log1p(-p)*(1-bits)).sum(axis=1))
        return np.column_stack(scores)
    def predict_proba(self,X):return softmax(self.decision_function(X),axis=1)
    def predict(self,X):return self.classes_[self.predict_proba(X).argmax(axis=1)]

class LogicalClauseEngine:
    def __init__(self,joint_model,atomic_model,minimum_atomic_confidence=.5):
        self.joint_model=joint_model;self.atomic=atomic_model;self.minimum_atomic_confidence=minimum_atomic_confidence
    def state_probabilities(self,texts):return self.joint_model.predict_proba(texts)
    def decisions(self,texts):
        evidence=self.atomic.question_features(texts)[:,:3]
        result=[]
        for v in evidence:
            present=v>=self.minimum_atomic_confidence
            if not present.any():
                # The routing layer treats this as insufficient evidence regardless of posterior confidence.
                result.append(('out_of_scope','unsupported',False));continue
            l,c,e=present
            primary='out_of_scope' if not(l or c) else 'mixed' if e or(l and c) else 'labor' if l else 'consumer'
            scope='unsupported' if not(l or c) else 'partially_supported' if e else 'fully_supported'
            result.append((primary,scope,True))
        return result
    def component_evidence(self,text):
        from clause_classifier import segment_question
        audit=segment_question(text);parts=audit['components'] if audit['reason']!='no_identified_concern' else []
        if not parts:return []
        p=self.atomic.probabilities(parts)
        from scope_constraints import constraint
        result=[]
        for t,v in zip(parts,p):
            rule=constraint(t) if getattr(self.atomic,'use_scope_constraints',False) else None
            result.append({'text':t,'category':rule[0] if rule else ATOMIC[int(v.argmax())],
                'decision_source':'scope_constraint' if rule else 'learned_atomic_classifier','constraint':rule[1] if rule else None,
                'uncalibrated_atomic_probabilities':dict(zip(ATOMIC,map(float,v))),'atomic_evidence_strength':1. if rule else float(v.max())})
        return result
    def segmentation_audit(self,text):
        from clause_classifier import segment_question
        return segment_question(text)

class LogicalClauseHead:
    def __init__(self,head,engine):
        self.head=head;self.engine=engine;self.classes_=np.array(['labor','consumer','mixed','out_of_scope'] if head=='primary' else ['fully_supported','partially_supported','unsupported'])
    def predict(self,texts):return np.array([d[0 if self.head=='primary' else 1] for d in self.engine.decisions(texts)])
    def predict_proba(self,texts):
        return self.probabilities_from_states(self.engine.state_probabilities(texts))
    def probabilities_from_states(self,p):
        """Project both heads from one joint inference, without changing values."""
        out=np.zeros((len(p),len(self.classes_)))
        for i,state in enumerate(self.engine.joint_model.classes_):
            l,c,e=map(int,state);primary='out_of_scope' if not(l or c) else 'mixed' if e or(l and c) else 'labor' if l else 'consumer';scope='unsupported' if not(l or c) else 'partially_supported' if e else 'fully_supported'
            out[:,list(self.classes_).index(primary if self.head=='primary' else scope)]+=p[:,i]
        return out
