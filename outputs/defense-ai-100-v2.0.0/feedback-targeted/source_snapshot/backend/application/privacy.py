"""Best-effort local redaction before provider export; never a privacy guarantee."""
import re

PATTERNS = [
    ('credential',r'\b(?:tgp_v1_[A-Za-z0-9_-]{16,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,})\b'),
    ('email',r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b'),
    ('phone',r'(?<!\w)(?:\+?63[ -]?9\d{2}[ -]?\d{3}[ -]?\d{4}|09\d{2}[ -]?\d{3}[ -]?\d{4})(?!\w)'),
    ('account',r'\b(?:account\s*(?:number|no\.?|#)|bank\s+account(?:\s*(?:number|no\.?|#))?|card\s*(?:number|no\.?|#)|tin|sss\s*(?:number|no\.?)|gsis\s*(?:number|no\.?))\s*(?:is\s+|ay\s+)?[:#=-]?\s*\d[\d -]{4,30}\d'),
    ('name',r'\b(?i:my\s+name\s+is|ang\s+pangalan\s+ko\s+ay|pangalan\s*:)\s+[A-Z][\w-]*(?:\s+(?:[A-Z]\.(?=\s+[A-Z])|[A-Z][\w-]*)){0,3}'),
    ('address',r'\b(?:my\s+(?:home\s+)?address\s+is|address\s*:)\s*[^;\n.!?]{4,100}?(?=;|\n|[.!?]|,?\s+(?:and|but|pero)\b|$)'),
]

def redact(question):
    text=question;counts={}
    for label,pattern in PATTERNS:
        flags=re.I if label in {'email','phone','account','address'} else 0
        def replace(match):
            if label=='account':return re.sub(r'[\d -]{5,30}\d\s*$',' [redacted account]',match.group())
            return ' [redacted '+label+'] '
        text,count=re.subn(pattern,replace,text,flags=flags)
        if count:counts[label]=count
    return {'text':text,'redacted':bool(counts),'categories':counts,
        'guaranteed_complete':False,'note':'Known identifiers are removed locally; avoid personal details. Names and indirect identifiers may still be missed.'}
