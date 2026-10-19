"""Bounded spelling features for concern detection, never a legal fact generator.

Vocabulary is declared from existing scope patterns and language structure.
No evaluation questions, labels or clear references are loaded by inference.
Only a unique spelling candidate is used; original input stays in the API.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from functools import lru_cache
import re
import unicodedata
from typing_vocabulary import PRESERVED_WORDS

VERSION = "scope-typing-v1.2.0"
ANCHORS = frozenset("""private pribado government municipal employee employer company
    employment worker workers workplace work job trabaho salary salaries sahod sweldo
    wage wages paid unpaid overtime undertime holiday regular rest rules probation
    termination notice dismissal dismissed thirteenth final certificate contract
    seafarer overseas deployment recruitment kasambahay household domestic union
    compensation disability illness injury pension retirement minimum exact amount
    current today ngayon magkano mismo city town region regional banking bank account
    credit loan insurance insurer investments privacy personal data information
    address identity posted pinost inilabas published online public photo permission
    consent criminal fraud police investigation telecom telephone mobile plan
    utility electricity water medical hospital doctor condo housing developer airline
    flight passenger transport safety technical chemical ventilation standards hearing
    pending arguments appeal prediction predict result outcome consumer retail retailer
    store shop seller grocery appliance product warranty refund repair replacement
    defective defect faulty unsafe broken quality transaction purchase purchased bought
    binili biniling nabili binayaran nabayaran bayad bayaran charge charges charged singil price
    label fee quote order delivery service laundry complaint concern issue problem
    problema reklamo hiwalay separate separately delayed withheld refuses refused
    pay payment payslip notice probationary promotion spouse sister brother kapatid
    pinsan cousin cooker rice kettle vacuum toaster furniture table chair cord
    weekly daily monthly annual rights benefit benefits process compensation factory
    shelf net quantity return returned hazard damage manufacturer liability edge
    workday hours oras keyboard post publish leak share expose delete deletion
    retained retention document kept cashier security tenure letter bargaining unit
    explain raise
    company employer employee account court tribunal rule rules shelf
    """.split())
STRUCTURE = frozenset("""a an the my our your his her their i we you he she they it
    am is are was were be been being and or but also with for from by in on at to
    of do does did have has had can could would should will what when where how
    ang mga sa na ng ni kay ako ko ka mo kami namin tayo natin siya niya sila nila
    kong naming mong iyong yung itong nitong may din rin naman lang pa po at
    gusto gusto ko dahil kaya para kung ba ito nito bawat parehong dalawang
    hiwalay another separate separately also too then tapos saka tsaka
    kailan salon compliant edging nabayaran nabayarran kompanya kumpanya
    home
    """.split())
PROTECTED = frozenset("""not no never without cannot can't won't don't didn't doesn't
    hindi hinde inde hnd hndi ndi nd di d wala walang ofw dti dole sena nlrc sss
    gsis pnp nbi bir ra pd php id ot coe ec osh osha""".split())
VOCABULARY = ANCHORS | STRUCTURE | PROTECTED
BOUNDARY_ANCHORS = ANCHORS | frozenset("dti dole nlrc sss gsis ofw sena osh osha".split())
WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
LITERAL = re.compile(r'https?://[^\s]+|[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}|["“][^"”\n]+["”]')


def key(word):
    text = unicodedata.normalize("NFKC", word).casefold()
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    for old, new in [("ph", "p"), ("f", "p"), ("v", "b"), ("c", "k"), ("q", "k")]:
        text = text.replace(old, new)
    return text.translate(str.maketrans("eo", "iu"))


def consonants(word):
    return re.sub(r"[aeiou]", "", key(word))


BY_CONSONANTS = {}
for _term in sorted(ANCHORS):
    BY_CONSONANTS.setdefault(consonants(_term), []).append(_term)


@lru_cache(maxsize=8192)
def candidate(word):
    if word in VOCABULARY or word in PRESERVED_WORDS or not word.isalpha() or len(word) < 3:
        return word
    collapsed = re.sub(r"(.)\1{2,}", r"\1", word)
    if collapsed in VOCABULARY:
        return collapsed
    if collapsed != word:
        # A real word may contain a legitimate double consonant (seller).
        # Repair a run of 3+ against a unique whole declared word, without
        # inserting a syllable or changing the collapsed character sequence.
        once = re.sub(r"(.)\1+", r"\1", key(word))
        repeated = [term for term in ANCHORS if re.sub(r"(.)\1+", r"\1", key(term)) == once]
        if len(repeated) == 1:
            return repeated[0]
    options = [term for term in BY_CONSONANTS.get(consonants(word), [])
               if key(word)[:1] == key(term)[:1]
               and (key(word) == key(term) or len(re.findall(r"[aeiou]", word)) < len(re.findall(r"[aeiou]", term)))
               and (len(consonants(term)) >= 3 or SequenceMatcher(None, key(word), key(term)).ratio() >= .8)]
    if len(options) == 1:
        return options[0]
    # Distinguish a pure i/e or o/u sound substitution from vowel deletion.
    exact = [term for term in options if key(word) == key(term)]
    return exact[0] if len(exact) == 1 else word


@lru_cache(maxsize=8192)
def split_word(word):
    if word in VOCABULARY or word in PRESERVED_WORDS or not word.isalpha() or len(word) > 48:
        return word
    options = []
    approximate_pieces = (len(re.findall(r"[aeiou]", word)) / len(word) < .34
                          or any(len(term) >= 5 and term in word for term in ANCHORS))
    whole = candidate(word)
    if whole != word:
        options.append((1.001, whole))
    def extend(start, parts, cost):
        if start == len(word):
            if (len(parts) >= 2 and any(p in BOUNDARY_ANCHORS and len(p) >= 3 for p in parts)
                    and not (len(parts) == 3 and cost > .3 and not approximate_pieces)):
                options.append((cost + .001 * len(parts), " ".join(parts)))
            return
        if len(parts) >= 3:
            return
        for end in range(start + 1, len(word) + 1):
            source = word[start:end]
            term = source if source in VOCABULARY else candidate(source)
            if term not in VOCABULARY or (len(source) == 1 and source not in {"a", "i"}):
                continue
            if term != source and not approximate_pieces and key(source) != key(term):
                continue
            extend(end, parts + [term], cost + (0 if term == source else 1) + (.1 if len(source) == 1 else 0))
    extend(0, [], 0)
    if not options:
        return word
    best = min(cost for cost, _ in options)
    winners = {text for cost, text in options if cost == best}
    return next(iter(winners)) if len(winners) == 1 else word


def matching_text(text):
    """Return scope-matching features, preserving numbers, literals and names."""
    original = unicodedata.normalize("NFKC", text)
    literals = [(m.start(), m.end()) for m in LITERAL.finditer(original)]
    matches = list(WORD.finditer(original))
    edits = []
    for index, match in enumerate(matches):
        value, lower = match.group(), match.group().casefold()
        if (lower in PROTECTED or value.isnumeric() or (value.isupper() and len(value) > 1)
                or any(a <= match.start() < b for a, b in literals)
                or (index and matches[index - 1].group().casefold() in {"si", "ni", "kay", "named", "mr", "ms", "dr"})):
            continue
        replacement = split_word(lower)
        if replacement == lower:
            replacement = candidate(lower)
        if replacement != lower:
            edits.append((match.start(), match.end(), replacement))
    for start, end, replacement in reversed(edits):
        original = original[:start] + replacement + original[end:]
    return original
