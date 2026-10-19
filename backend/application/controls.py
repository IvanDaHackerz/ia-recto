"""Local request identity, cancellation, provider quotas and bounded spending estimates."""
from collections import deque
from dataclasses import dataclass,field
from datetime import datetime,timezone
import hashlib
import http.client
import json
from pathlib import Path
import socket
import sqlite3
import threading
import time
import math
from contextlib import contextmanager
from urllib.parse import urlsplit
from backend.classifier.contracts import RequestError,strict_json
from backend.normalization import NormalizationUnavailable

ROOT=Path(__file__).resolve().parents[2]

class ProviderStopped(NormalizationUnavailable):
    def __init__(self,code):super().__init__('Provider request was not completed');self.safe_code=code

@dataclass
class RequestContext:
    owner:str
    request_id:str
    deadline:float=field(default_factory=lambda:time.monotonic()+55)
    canceled:threading.Event=field(default_factory=threading.Event)
    connections:list=field(default_factory=list)
    calls:list=field(default_factory=list)
    lock:threading.Lock=field(default_factory=threading.Lock)

    def check(self):
        if self.canceled.is_set():raise RequestError('request_canceled','Request canceled.',499)
        if time.monotonic()>self.deadline:raise RequestError('request_timeout','The request reached its time limit. Please retry a shorter question.',408)

    def cancel(self):
        self.canceled.set()
        with self.lock:
            for connection in self.connections:
                try:
                    if connection.sock:connection.sock.shutdown(socket.SHUT_RDWR)
                except OSError:pass
                connection.close()

class UsageLedger:
    # Official Together serverless list prices checked 2026-10-19. This is an
    # estimate/cap at these configured rates, not access to account billing.
    PRICES={'openai/gpt-oss-120b':(.15,.60),'Qwen/Qwen3.5-9B':(.17,.25)}
    def __init__(self,path=None,*,maximum_calls=100,maximum_usd=.50):
        self.path=Path(path) if path else ROOT/'.local/website/usage.sqlite3'
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.maximum_calls=maximum_calls;self.maximum_usd=maximum_usd
        if type(maximum_calls) is not int or not 0<=maximum_calls<=10000 or not math.isfinite(maximum_usd) or not 0<=maximum_usd<=100:
            raise ValueError('Use bounded nonnegative daily call and estimated-cost limits')
        self._failures=deque();self._lock=threading.Lock()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, day TEXT NOT NULL, stage TEXT NOT NULL, model TEXT NOT NULL, estimate REAL NOT NULL, input_tokens INTEGER, output_tokens INTEGER, outcome TEXT NOT NULL)')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5)
        try:
            with db:yield db
        finally:db.close()

    def reserve(self,stage,model,input_bytes,maximum_output):
        import uuid
        if model not in self.PRICES:raise ProviderStopped('model_pricing_not_configured')
        with self._lock:
            now=time.monotonic()
            while self._failures and now-self._failures[0]>60:self._failures.popleft()
            if len(self._failures)>=3:raise ProviderStopped('provider_circuit_open')
        ir,orr=self.PRICES[model]
        estimate=((input_bytes+4096)*ir+maximum_output*orr)/1000000
        day=datetime.now(timezone.utc).date().isoformat();rid=uuid.uuid4().hex
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            count,cost=db.execute('SELECT COUNT(*),COALESCE(SUM(estimate),0) FROM calls WHERE day=?',(day,)).fetchone()
            if count>=self.maximum_calls or cost+estimate>self.maximum_usd:raise ProviderStopped('daily_provider_limit')
            db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?,?)',(rid,day,stage,model,estimate,None,None,'reserved'))
        return rid

    def settle(self,rid,model,usage,outcome):
        inp=usage.get('prompt_tokens',usage.get('input_tokens')) if type(usage) is dict else None
        out=usage.get('completion_tokens',usage.get('output_tokens')) if type(usage) is dict else None
        if type(inp) is not int or type(out) is not int or inp<0 or out<0:inp=out=None
        ir,orr=self.PRICES[model]
        with self.connect() as db:
            if inp is not None:db.execute('UPDATE calls SET estimate=?,input_tokens=?,output_tokens=?,outcome=? WHERE id=?',((inp*ir+out*orr)/1000000,inp,out,outcome,rid))
            else:db.execute('UPDATE calls SET outcome=? WHERE id=?',(outcome,rid))
        if outcome not in {'completed','canceled'}:
            with self._lock:self._failures.append(time.monotonic())
        elif outcome=='completed':
            # A healthy reply breaks the consecutive-failure streak. Citation
            # rejection is a content check, not a provider outage.
            with self._lock:self._failures.clear()

    def summary(self):
        day=datetime.now(timezone.utc).date().isoformat()
        with self.connect() as db:
            count,cost,inp,out=db.execute('SELECT COUNT(*),COALESCE(SUM(estimate),0),COALESCE(SUM(input_tokens),0),COALESCE(SUM(output_tokens),0) FROM calls WHERE day=?',(day,)).fetchone()
        return {'day_utc':day,'provider_requests':count,'estimated_usd':cost,'input_tokens':inp,'output_tokens':out,'maximum_calls':self.maximum_calls,'maximum_estimated_usd':self.maximum_usd,'billing_verified':False}

class CancellableTransport:
    def __init__(self,context,ledger,stage):self.context=context;self.ledger=ledger;self.stage=stage
    def __call__(self,request,timeout):
        ctx=self.context;ctx.check()
        parsed=urlsplit(request.full_url)
        if parsed.scheme!='https' or parsed.hostname not in {'api.together.ai','api.openai.com'} or parsed.port or parsed.username or parsed.query or parsed.fragment:
            raise ProviderStopped('provider_host_rejected')
        body=strict_json(request.data.decode('utf-8'));model=body['model']
        stage='explanation_support' if body.get('response_format',{}).get('json_schema',{}).get('name')=='explanation_support' else self.stage
        rid=self.ledger.reserve(stage,model,len(request.data),body.get('max_tokens',body.get('max_output_tokens',3072)))
        connection=http.client.HTTPSConnection(parsed.hostname,timeout=min(8,timeout,max(.1,ctx.deadline-time.monotonic())))
        with ctx.lock:ctx.connections.append(connection)
        outcome='unavailable';usage={}
        try:
            ctx.check();connection.connect();ctx.check()
            connection.sock.settimeout(min(timeout,max(.1,ctx.deadline-time.monotonic())))
            ctx.calls.append({'stage':stage,'model':model})
            connection.request('POST',parsed.path,body=request.data,headers=dict(request.header_items()))
            response=connection.getresponse()
            if response.status!=200:
                code='provider_auth_failed' if response.status in {401,403} else 'provider_rate_limited' if response.status==429 else 'provider_http_'+str(response.status)
                raise ProviderStopped(code)
            raw=response.read(131073);ctx.check()
            if len(raw)>131072:raise ProviderStopped('provider_response_limit')
            data=strict_json(raw.decode('utf-8'))
            if type(data) is not dict:raise ProviderStopped('provider_invalid_response')
            usage=data.get('usage',{});outcome='completed';return data
        except RequestError:
            outcome='canceled' if ctx.canceled.is_set() else 'timeout';raise ProviderStopped('request_canceled' if ctx.canceled.is_set() else 'request_timeout') from None
        except ProviderStopped:raise
        except (OSError,ValueError,http.client.HTTPException):
            outcome='canceled' if ctx.canceled.is_set() else 'unavailable';raise ProviderStopped('request_canceled' if ctx.canceled.is_set() else 'provider_unavailable') from None
        finally:
            connection.close()
            with ctx.lock:
                if connection in ctx.connections:ctx.connections.remove(connection)
            self.ledger.settle(rid,model,usage,outcome)

class RequestRegistry:
    def __init__(self):self.lock=threading.Lock();self.jobs={};self.rate={};self.tombstones={}
    def begin(self,owner,rid,payload):
        fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        now=time.monotonic();key=(owner,rid)
        with self.lock:
            self.jobs={k:v for k,v in self.jobs.items() if now-v['created']<300}
            self.tombstones={k:t for k,t in self.tombstones.items() if now-t<300}
            self.rate={k:[t for t in values if now-t<60] for k,values in self.rate.items() if any(now-t<60 for t in values)}
            old=self.jobs.get(key)
            if old:
                if old['fingerprint']!=fingerprint:raise RequestError('request_id_conflict','This request ID belongs to different input.',409)
                if old.get('packet') is not None:return old['context'],old['packet']
                raise RequestError('request_in_progress','This request is already running or was canceled. Use a new request ID.',409)
            if key in self.tombstones:raise RequestError('request_canceled','Request canceled.',499)
            recent=[t for t in self.rate.get(owner,[]) if now-t<60]
            if len(recent)>=12:raise RequestError('request_rate_limit','Too many questions. Please wait a minute.',429)
            self.rate[owner]=recent+[now]
            if len(self.jobs)>=64:
                completed=[(k,v) for k,v in self.jobs.items() if v.get('packet') is not None]
                if not completed:raise RequestError('server_busy','The local request cache is full. Please retry shortly.',503)
                self.jobs.pop(min(completed,key=lambda item:item[1]['created'])[0])
            ctx=RequestContext(owner,rid);self.jobs[key]={'context':ctx,'fingerprint':fingerprint,'created':now}
            return ctx,None

    def finish(self,ctx,packet):
        import copy
        with self.lock:self.jobs[(ctx.owner,ctx.request_id)]['packet']=copy.deepcopy(packet)

    def cancel(self,owner,rid):
        with self.lock:
            now=time.monotonic();self.tombstones={k:t for k,t in self.tombstones.items() if now-t<300}
            key=(owner,rid);job=self.jobs.get(key);self.tombstones[key]=time.monotonic()
            if len(self.tombstones)>1024:
                oldest=min(self.tombstones,key=self.tombstones.get)
                if oldest not in self.jobs:self.tombstones.pop(oldest,None)
            if job:job['context'].cancel()
        return {'schema_version':'1.0','status':'canceled','request_id':rid}

    def abandon(self,ctx):
        with self.lock:
            if not ctx.calls and not ctx.canceled.is_set():self.jobs.pop((ctx.owner,ctx.request_id),None)
