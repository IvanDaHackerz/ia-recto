"""Explicit personal-harm notice; no diagnosis, legal advice or provider call."""
import re
from dataset.pipelines.item10.scope_constraints import literal_concern_text, historical_background

def safety_notice(question):
    # This is a best-effort notice, not an emergency-service classifier. Do not
    # suppress a present threat just because another sentence recalls the past.
    pattern = r'\b(?:i|we)\s+(?:also\s+)?(?:got|was|were|am being|are being|have been)\s+(?:stabbed|shot|assaulted|attacked)\b|\b(?:someone|stranger|employer|boss)\s+(?:stabbed|shot|attacked)\s+(?:me|us)\b|\b(?:sinaksak|nasaksak|binaril|binugbog)\s+(?:ako|kami)\b|\bmay\s+nanaksak\s+sa\s+(?:akin|amin)\b|\bthreaten\w*\s+to\s+(?:stab|shoot|kill|hurt)\s+(?:me|us)\b'
    active=False
    for clause in re.split(r'[.!?\n;]+',literal_concern_text(question)):
        if historical_background(clause):continue
        for match in re.finditer(pattern,clause,re.I):
            prefix=clause[max(0,match.start()-24):match.start()]
            if re.search(r"\b(?:not|never|hindi|didn't|doesn't)\s+$",prefix,re.I):continue
            active=True
    if not active:return None
    return {"kind": "personal_safety", "heading": "Your safety comes first",
        "text": "If you are injured or in immediate danger, call 911 in the Philippines or seek emergency help now. This assistant cannot provide emergency assistance.",
        "source_url": "https://ehotlines.e.gov.ph/", "emergency_number": "911"}
