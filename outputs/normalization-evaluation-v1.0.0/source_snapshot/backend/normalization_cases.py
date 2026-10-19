"""Prediction-blind selection and reversible synthetic typing perturbations."""
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import hashlib
import json
import random
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "outputs/item13-evaluation-v1.0.1/cases.jsonl"
SEED = 20261019
PROFILES = ["missing_vowels", "phonetic_spelling", "repeated_letters", "joined_words", "mixed_typing"]
QUOTAS = {("labor", "fully_supported"): 24, ("consumer", "fully_supported"): 24,
          ("mixed", "fully_supported"): 12, ("mixed", "partially_supported"): 15,
          ("out_of_scope", "unsupported"): 20, (None, None): 5}
TOKEN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
# Avoid deleting/negating facts when constructing a spelling-only challenge.
KEEP = set("""not no never without cannot can't didn't doesn't don't hasn't haven't
    wasn't weren't isn't aren't won't hindi hndi ndi di wala walang dti
    dole sss gsis nlrc nwpc ofw sena coe ra pd ot id php en tl""".split())


def load_source():
    return [json.loads(line) for line in (ROOT / SOURCE).read_text(encoding="utf-8").splitlines() if line.strip()]


def select_sources(records):
    selected, families, counts = [], set(), Counter()

    def add(row):
        key = (row["expected_primary"], row["expected_scope"])
        if row["family_id"] in families or counts[key] >= QUOTAS[key]:
            return
        selected.append(row)
        families.add(row["family_id"])
        counts[key] += 1

    # Prefer Taglish within a retrieval family; all expectations already exist.
    retrieval = sorted((r for r in records if r["suite"] == "retrieval"),
                       key=lambda r: (r["family_id"], r["language"] != "en_tl", r["case_id"]))
    for row in retrieval:
        add(row)
    for row in sorted((r for r in records if r["suite"] == "system"),
                      key=lambda r: (r["family_id"], r["language"] != "en_tl", r["case_id"])):
        add(row)
    for row in records:
        if row["suite"] == "typing" and row["expected_primary"] is None:
            add(row)
    for row in records:
        if row["suite"] == "general":
            add(row)
    if counts != Counter(QUOTAS) or len(selected) != 100 or len(families) != 100:
        raise ValueError("Source selection did not satisfy frozen quotas")
    # Round-robin strata prevent typing style from simply encoding a class.
    buckets = {key: [r for r in selected if (r["expected_primary"], r["expected_scope"]) == key] for key in QUOTAS}
    ordered = []
    while any(buckets.values()):
        for bucket in buckets.values():
            if bucket:
                ordered.append(bucket.pop(0))
    return ordered


def perturb(text, profile, seed):
    rng = random.Random(seed)
    tokens = list(TOKEN.finditer(text))
    eligible = [m for m in tokens if len(m.group()) >= 4 and m.group().isalpha()
                and m.group().casefold() not in KEEP and not m.group().isupper()
                and not any(c.isupper() for c in m.group()[1:])]
    rng.shuffle(eligible)
    edits = []
    selected = sorted(eligible[:max(1, min(5, len(eligible) // 2))], key=lambda m: m.start())
    for index, match in enumerate(selected):
        word = match.group()
        style = profile if profile != "mixed_typing" else ["missing_vowels", "phonetic_spelling", "repeated_letters"][index % 3]
        replacement = word
        if style == "missing_vowels":
            positions = [i for i, c in enumerate(word[1:-1], 1) if c.casefold() in "aeiou"]
            for i in reversed(positions[:2]):
                replacement = replacement[:i] + replacement[i + 1:]
        elif style == "phonetic_spelling":
            alternatives = {"i": "e", "e": "i", "u": "o", "o": "u", "v": "b", "f": "p"}
            positions = [i for i, c in enumerate(word) if c.casefold() in alternatives]
            if positions:
                i = rng.choice(positions)
                other = alternatives[word[i].casefold()]
                replacement = word[:i] + (other.upper() if word[i].isupper() else other) + word[i + 1:]
        elif style == "repeated_letters":
            i = rng.randrange(1, len(word))
            replacement = word[:i] + word[i] * 3 + word[i + 1:]
        if replacement != word:
            edits.append((match.start(), match.end(), replacement))
    if profile in {"joined_words", "mixed_typing"}:
        spaces = [m for m in re.finditer(r"(?<=[a-zA-Z]) (?=[a-zA-Z])", text)
                  if not any(a <= m.start() < b for a, b, _ in edits)]
        rng.shuffle(spaces)
        edits += [(m.start(), m.end(), "") for m in spaces[:2]]
    if not edits and eligible:
        match = eligible[0]
        edits = [(match.start(), match.end(), match.group() + match.group()[-1])]
    noisy = text
    for start, end, replacement in sorted(edits, reverse=True):
        noisy = noisy[:start] + replacement + noisy[end:]
    if noisy == text:
        raise ValueError("Synthetic variant must differ from original")
    # Character alignment is reversible and explicitly records the intended source.
    ledger = [{"source_start": a, "source_end": b, "source_text": text[a:b],
               "noisy_start": c, "noisy_end": d, "noisy_text": noisy[c:d]}
              for op, a, b, c, d in SequenceMatcher(None, text, noisy, autojunk=False).get_opcodes() if op != "equal"]
    recovered = noisy
    for edit in reversed(ledger):
        recovered = recovered[:edit["noisy_start"]] + edit["source_text"] + recovered[edit["noisy_end"]:]
    if recovered != text:
        raise ValueError("Variant ledger is not reversible")
    return noisy, ledger


def build_cases(records=None):
    result = []
    for index, source in enumerate(select_sources(records if records is not None else load_source())):
        profile = PROFILES[index % len(PROFILES)]
        seed = SEED + int(hashlib.sha256(source["case_id"].encode()).hexdigest()[:8], 16)
        noisy, ledger = perturb(source["question_text"], profile, seed)
        for variation, question, changes in [("clear", source["question_text"], []), ("noisy", noisy, ledger)]:
            result.append({"case_id": source["case_id"] + "__" + variation,
                           "base_case_id": source["case_id"], "family_id": source["family_id"],
                           "variation": variation, "noise_profile": profile if variation == "noisy" else None,
                           "question_text": question, "reference_question": source["question_text"],
                           "source_case": source, "perturbation_ledger": changes,
                           "origin": "existing_AI_development_question" if variation == "clear" else "synthetic_AI_authored_rule_based_variant",
                           "is_independent_human_gold": False})
    if len({r["case_id"] for r in result}) != 200:
        raise ValueError("Expected 200 unique inputs")
    return result
