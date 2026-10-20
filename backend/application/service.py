"""Local application: short inference locks, opt-in storage and controlled providers."""
from __future__ import annotations
import copy
import os
import re
import threading
import uuid
import time
from backend.classifier.contracts import validate_request,RequestError
from backend.clarification import payment_follow_up,unresolved_payment_follow_up
from backend.normalization import from_environment,ConditionalNormalizer
from backend.normalization_provider import TogetherProvider
from backend.terminal_test import inspect_question,load_runtime
from .explanation import explain,TogetherExplanation,from_environment as explanation_from_environment
from .performance import performance_report
from .development_explanation import TogetherDevelopmentExplanation,explain_recorded_sources
from .safety import safety_notice
from .privacy import redact
from .identity import identity
from .controls import RequestRegistry,RequestContext,UsageLedger,CancellableTransport
from .history import HistoryStore,session_key
from .evidence import citation_labels,decorate
from .conversation import prepare_general_information,response_for

class ApplicationService:
    def __init__(self,verifier=None,normalizer=None,explanation_provider=None,development_provider=None,*,history_store=None,ledger=None,use_controls=False):
        self.verifier=verifier if verifier is not None else load_runtime()
        self.normalizer=normalizer if normalizer is not None else from_environment()
        self.explanation_provider=explanation_provider;self.development_provider=development_provider
        self.history_store=history_store;self.ledger=ledger;self.use_controls=use_controls
        self.registry=RequestRegistry();self._lock=threading.Lock();self._slots=threading.BoundedSemaphore(4)
        self._identity=identity();self._labels=citation_labels(self.verifier)
        self._last_integrity=time.time()

    @classmethod
    def configured(cls):
        provider=explanation_from_environment();enabled=os.environ.get('RECTO_ENABLE_EXPLANATIONS','1')=='1'
        normalizer=from_environment() if os.environ.get('RECTO_ENABLE_NORMALIZATION','1')=='1' else ConditionalNormalizer()
        ledger=UsageLedger(maximum_calls=int(os.environ.get('RECTO_MAX_DAILY_CALLS','100')),maximum_usd=float(os.environ.get('RECTO_MAX_DAILY_USD','.50')))
        service=cls(normalizer=normalizer,explanation_provider=provider,
            development_provider=TogetherDevelopmentExplanation(provider.model,provider._key) if provider and enabled else None,
            history_store=HistoryStore(),ledger=ledger,use_controls=True)
        service.session_key=session_key()
        return service

    def health(self):
        # Cheap liveness never queues behind a provider call. Inference checks integrity.
        return {'schema_version':'1.0','status':'ready','development_only':True,**self._identity,
            'classifier':self.verifier.policy['classifier'],'retrieval':self.verifier.policy['retrieval'],
            'verifier':self.verifier.policy['version'],'normalizer_configured':self.normalizer.provider is not None,
            'explanation_adapter_configured':self.explanation_provider is not None,
            'development_explanations_enabled':self.development_provider is not None,
            'history_available':bool(self.history_store and self.history_store.available),
            'history_retention_days':self.history_store.retention_days if self.history_store else None,
            'last_integrity_check_unix':self._last_integrity,'maximum_active_questions':4,
            'answer_generation_allowed':False,'display_allowed':False,'deployment_allowed':False}

    @staticmethod
    def _request(payload):
        if type(payload) is not dict or set(payload)-{'question_text','request_id','use_ai','save_history','conversation_id'}:
            raise RequestError('invalid_request','Use question_text, request_id and the documented privacy/history options.')
        question,rid=validate_request({k:v for k,v in payload.items() if k in {'question_text','request_id'}})
        for k in ['use_ai','save_history']:
            if k in payload and type(payload[k]) is not bool:raise RequestError('invalid_request',k+' must be true or false.')
        cid=payload.get('conversation_id')
        if cid is not None and (type(cid) is not str or not re.fullmatch(r'[a-f0-9]{32}',cid)):raise RequestError('invalid_request','Invalid saved conversation ID.')
        return question,rid or uuid.uuid4().hex

    def _inspect(self,question):
        if not self._lock.acquire(timeout=2):raise RequestError('server_busy','The local model is checking another question. Please retry shortly.',503)
        try:
            packet=inspect_question(self.verifier,question,None);self._last_integrity=time.time();return packet
        finally:self._lock.release()

    def _normalizer_for(self,ctx):
        source=self.normalizer.provider
        if self.use_controls and isinstance(source,TogetherProvider):
            return ConditionalNormalizer(TogetherProvider(model=source.model,api_key=source._api_key,timeout=source.timeout,transport=CancellableTransport(ctx,self.ledger,'normalization')))
        if self.use_controls and source is not None:return ConditionalNormalizer()
        return self.normalizer

    def chat(self,payload,*,session='local'):
        question,rid=self._request(payload)
        if not question.strip():raise RequestError('empty_question','Type a question before asking.')
        ctx,cached=self.registry.begin(session,rid,payload) if self.use_controls else (RequestContext(session,rid),None)
        if cached is not None:return copy.deepcopy(cached)
        if not self._slots.acquire(blocking=False):
            if self.use_controls:self.registry.abandon(ctx)
            raise RequestError('server_busy','All local question slots are busy. Please retry shortly.',503)
        try:
            start=time.perf_counter();ctx.check()
            privacy=redact(question);notice=safety_notice(question)
            effective=privacy['text'] if privacy['redacted'] else question
            packet=self._inspect(effective);ctx.check();use_ai=payload.get('use_ai',True)
            if use_ai and not notice:
                normalization=self._normalizer_for(ctx).prepare(effective,routing=packet['result']['routing'])
                if normalization['gate']['needed']:normalization['baseline_routing']=dict(packet['result']['routing'])
                packet['normalization']=normalization;ctx.check()
                interpreted=normalization['effective_question_text']
                if interpreted is None:
                    packet['result']=None;follow=unresolved_payment_follow_up(effective)
                    packet['clarification_follow_up']=follow
                    if follow:normalization['clarification_question']=follow['question']
                elif interpreted!=effective:
                    packet['result']=self._inspect(interpreted)['result']
                    packet['clarification_follow_up']=payment_follow_up(interpreted,packet['result']['routing'])
            packet['original_question_text']=effective if 'credential' in privacy['categories'] else question
            packet['privacy']={k:v for k,v in privacy.items() if k!='text'}|{'external_ai_enabled':use_ai}
            packet['safety_notice']=notice
            if not notice and packet.get('result'):
                prepare_general_information(packet,packet['result']['question_text'],self._inspect)
            packet['explanation']={'status':'withheld','reason':'local_only','llm_calls':0,'claims':[]}
            if notice:packet['explanation']['reason']='safety_assistance_first'
            elif use_ai:
                approved_provider=self.explanation_provider
                if self.use_controls and isinstance(approved_provider,TogetherExplanation):
                    approved_provider=TogetherExplanation(approved_provider.model,approved_provider._key)
                    approved_provider.transport=CancellableTransport(ctx,self.ledger,'reviewed_explanation')
                packet['explanation']=explain(self.verifier,packet['result'],approved_provider)
                if self.development_provider is not None and packet['explanation']['llm_calls']==0 and packet['explanation']['status']!='verified':
                    provider=self.development_provider.fork() if isinstance(self.development_provider,TogetherDevelopmentExplanation) else self.development_provider
                    if self.use_controls and isinstance(provider,TogetherDevelopmentExplanation):provider.transport=CancellableTransport(ctx,self.ledger,'explanation_generation')
                    packet['explanation']=explain_recorded_sources(self.verifier,packet['result'],provider)
                    error=getattr(provider,'last_error_code',None)
                    if type(error) is str and packet['explanation']['reason']=='provider_unavailable':packet['explanation']['failure_code']=error
            ctx.check();packet['total_query_ms']=(time.perf_counter()-start)*1000
            packet['request_id']=rid;packet['schema_version']='1.0';packet['network_requests']=[dict(x) for x in ctx.calls]
            if self.use_controls and isinstance(self.development_provider,TogetherDevelopmentExplanation):packet['explanation']['llm_calls']=sum(c['stage'] in {'explanation_generation','explanation_support','reviewed_explanation'} for c in ctx.calls)
            if self.use_controls and isinstance(self.normalizer.provider,TogetherProvider) and packet.get('normalization'):packet['normalization']['llm_calls']=sum(c['stage']=='normalization' for c in ctx.calls)
            packet['history']={'saved':False};decorate(packet,self.verifier,self._labels)
            packet['response']=response_for(packet,self.verifier,packet['result']['question_text'] if packet.get('result') else effective)
            if payload.get('save_history'):
                if self.history_store is None:packet['history']['error']='Encrypted local history is unavailable.'
                else:
                    try:packet['history']={'saved':True,**self.history_store.save(session,packet,payload.get('conversation_id'))}
                    except (ValueError,OSError):packet['history']['error']='The response could not be saved. The analysis is still available.'
            if self.use_controls:self.registry.finish(ctx,packet)
            return packet
        except RequestError as error:
            if self.use_controls and error.code=='server_busy':self.registry.abandon(ctx)
            raise
        finally:self._slots.release()

    def cancel(self,session,rid):
        validate_request({'question_text':'cancel','request_id':rid})
        return self.registry.cancel(session,rid)

    def history(self,session,conversation=None):
        store=self.history_store
        if conversation:
            data=store.get(session,conversation) if store else None
            if data is None:raise RequestError('not_found','Saved questions were not found for this browser.',404)
            return {'schema_version':'1.0','conversation':data}
        return {'schema_version':'1.0','available':bool(store and store.available),'retention_days':store.retention_days if store else None,'conversations':store.list(session) if store else []}

    def delete_history(self,session,conversation=None):
        return {'schema_version':'1.0','deleted_turns':self.history_store.delete(session,conversation) if self.history_store else 0}

    def status(self):return {'schema_version':'1.0','health':self.health(),'usage':self.ledger.summary() if self.ledger else None}
    def performance(self):return performance_report()
