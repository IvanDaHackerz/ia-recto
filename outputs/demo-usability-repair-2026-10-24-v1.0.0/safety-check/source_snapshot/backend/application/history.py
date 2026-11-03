"""Opt-in history, scoped by a random HttpOnly browser cookie and DPAPI encrypted.

This is local device storage, not authentication for a public multiuser service.
"""
from datetime import datetime,timezone,timedelta
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import uuid
from contextlib import contextmanager
from backend.normalizer_credentials import protect

ROOT=Path(__file__).resolve().parents[2]
ID=re.compile(r'^[a-f0-9]{32}$')

def session_key(path=None):
    """Stable local cookie-signing secret; never an API credential or public token."""
    path=Path(path) if path else ROOT/'.local/website/session.key.dpapi'
    if os.name!='nt':return os.urandom(32) # History is unavailable without an encryption backend.
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        value=protect(os.urandom(32))
        try:
            with path.open('xb') as f:f.write(value)
        except FileExistsError:pass
    value=protect(path.read_bytes(),decrypt=True)
    if len(value)!=32:raise ValueError('Invalid local session secret')
    return value

class HistoryStore:
    def __init__(self,path=None,*,codec=protect,retention_days=30,maximum_turns=500):
        self.path=Path(path) if path else ROOT/'.local/website/history.sqlite3'
        self.codec=codec;self.retention_days=retention_days;self.maximum_turns=maximum_turns
        self.available=codec is not protect or os.name=='nt'
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS turns (id TEXT PRIMARY KEY, owner TEXT NOT NULL, conversation TEXT NOT NULL, created TEXT NOT NULL, expires TEXT NOT NULL, payload BLOB NOT NULL)')
            db.execute('CREATE INDEX IF NOT EXISTS owner_conversation ON turns(owner, conversation, created)')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA secure_delete=ON')
        try:
            with db:yield db
        finally:db.close()

    @staticmethod
    def owner(session):return hashlib.sha256(session.encode()).hexdigest()

    def _prune(self,db):db.execute('DELETE FROM turns WHERE expires < ?', (datetime.now(timezone.utc).isoformat(),))

    def save(self,session,packet,conversation=None):
        if not self.available:raise ValueError('Encrypted local history is unavailable on this system')
        if conversation is not None and not ID.fullmatch(conversation):raise ValueError('Invalid conversation identifier')
        conversation=conversation or uuid.uuid4().hex;owner=self.owner(session)
        now=datetime.now(timezone.utc);turn=uuid.uuid4().hex
        # The encrypted record must contain its actual saved state as well.
        packet={**packet,'history':{'saved':True,'conversation_id':conversation,'turn_id':turn,'retention_days':self.retention_days,'encrypted':True}}
        raw=json.dumps(packet,ensure_ascii=False,allow_nan=False).encode('utf-8')
        if len(raw)>4*1024*1024:raise ValueError('Response is too large to save')
        encrypted=self.codec(gzip.compress(raw))
        with self.connect() as db:
            self._prune(db)
            existing=db.execute('SELECT owner FROM turns WHERE conversation=? LIMIT 1',(conversation,)).fetchone()
            if existing and existing['owner']!=owner:raise ValueError('Conversation is unavailable')
            db.execute('INSERT INTO turns VALUES(?,?,?,?,?,?)',(turn,owner,conversation,now.isoformat(),(now+timedelta(days=self.retention_days)).isoformat(),encrypted))
            db.execute('DELETE FROM turns WHERE id IN (SELECT id FROM turns WHERE owner=? ORDER BY created DESC LIMIT -1 OFFSET ?)',(owner,self.maximum_turns))
        return {'conversation_id':conversation,'turn_id':turn,'retention_days':self.retention_days,'encrypted':True}

    def _decode(self,row):
        try:
            compressed=self.codec(bytes(row['payload']),decrypt=True)
            # A corrupt/tampered store cannot turn into an unbounded gzip read.
            import io
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as f:raw=f.read(4*1024*1024+1)
            if len(raw)>4*1024*1024:raise ValueError('Oversized history')
            packet=json.loads(raw.decode('utf-8'))
            return packet if type(packet) is dict and packet.get('schema_version')=='1.0' else None
        except (ValueError,OSError,UnicodeError,TypeError):return None

    def list(self,session):
        result={}
        with self.connect() as db:
            self._prune(db)
            rows=db.execute('SELECT * FROM turns WHERE owner=? ORDER BY created',(self.owner(session),)).fetchall()
        for r in rows:
            packet=self._decode(r)
            if packet is None:continue
            cid=r['conversation']
            if cid not in result:result[cid]={'id':cid,'title':packet.get('original_question_text','Saved question')[:100],'created_at':r['created'],'updated_at':r['created'],'turns':0}
            result[cid]['updated_at']=r['created'];result[cid]['turns']+=1
        return sorted(result.values(),key=lambda r:r['updated_at'],reverse=True)

    def get(self,session,conversation):
        if not ID.fullmatch(conversation):return None
        with self.connect() as db:
            self._prune(db)
            rows=db.execute('SELECT * FROM turns WHERE owner=? AND conversation=? ORDER BY created',(self.owner(session),conversation)).fetchall()
        turns=[{'id':r['id'],'created_at':r['created'],'packet':p} for r in rows if (p:=self._decode(r)) is not None]
        return {'id':conversation,'turns':turns} if turns else None

    def delete(self,session,conversation=None):
        if conversation is not None and not ID.fullmatch(conversation):return 0
        with self.connect() as db:
            if conversation is None:cursor=db.execute('DELETE FROM turns WHERE owner=?',(self.owner(session),))
            else:cursor=db.execute('DELETE FROM turns WHERE owner=? AND conversation=?',(self.owner(session),conversation))
            return cursor.rowcount
