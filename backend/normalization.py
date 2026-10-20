"""Conditional, provider-independent shorthand normalization before classification.

The gate is a conservative heuristic, not a perfect readability classifier.
The provider can repair the whole sentence; local checks reject observable fact
changes. The original message is always retained.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field

from backend.classifier.contracts import validate_request
from backend.normalization_validation import validate_rewrite, FUNCTION_WORDS, FACT_WORDS

VERSION = "conditional-normalization-v3.0.1"
TOKEN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
# Readability hints only: no candidate replacements or edit whitelist.
SHORTHAND_HINTS = set("""prng gn2 gnto d2 aq q kmi kme kau nmn kc ksi bkt bkit
    pde pwde hnd hndi ndi nd d wla wlang walng bnyrn bnyran nbyrn nabayrn byad
    bnyad nbli binli swld swldo swhldo prvt prvate pribdo cmpny emplyr emplyado
    nla lng mron mrn bngko insrns gvrnment""".split())
SPELLING_HINTS = set("inde hinde nakoha nkuha nakua amu anu sahud suwldo gagawen".split())
PROTECTED = set("""dti dole sss gsis nlrc nwpc ra pd eo dao coe ot ofw po ko
    sa ng na ni mo ka ba di hindi wala walang not no never without cannot can't
    didn't doesn't don't private privado pribado government govt municipal
    overseas seafarer kasambahay household domestic union bank banking bangko
    insurance insurer landlord tenant privacy criminal fraud loan salary wage
    refund warranty overtime termination consumer labor labour""".split())
VALIDATION_CODES = set("""invalid_normalization_contract unexpected_rewrite
    invalid_rewrite_length normalization_word_limit numeric_facts_changed
    literal_fact_changed agency_changed name_changed participant_changed
    negation_removed negation_added original_concern_not_preserved
    unsupported_new_content unsupported_new_fact repeat_repair_changed_word
    lexical_polarity_changed ambiguous_short_content_replaced syllable_reduplication_changed scope_anchor_changed""".split())


@dataclass
class Completion:
    payload: dict
    usage: dict = field(default_factory=dict)


class NormalizationUnavailable(RuntimeError):
    """Safe provider failure: messages must never contain credentials or request text."""


FAMILIAR = FUNCTION_WORDS | FACT_WORDS | PROTECTED | set("""amo boss trabaho company
    employee employer nakuha binayaran nabayaran bayad binayad sahod sweldo tanong
    binili nabili bumili tindahan product defective store cashier charged more than
    displayed price paid payment salary wage overtime benefit benefits work working
    information advice rights transaction purchase service specific happened involved
    money delayed unpaid refused refuses refuses refund hasn't allow allowed need
    withheld deductions dismissal termination contract ended fee charge concern
    consumer labor labour bank banking loan insurance court law question concern
    notebook computer phone delivery item return seller shop nakatanggap natanggap
    sira sirang ayaw ibalik pera bawas kulang sumobra nahuli problema karapatan
    humingi mabayaran gusto gusto naming nitong noong mag type full words""".split())
FALLBACK_REASONS = {"no_reliable_component_evidence", "no_identified_concern"}


def assess_text(question, routing=None):
    if routing and routing["routing_action"] != "clarify":
        return {"needed": False, "reason": "raw_question_understood", "trigger_spans": [],
                "mode": "whole_question_interpretation"}
    tokens = list(TOKEN.finditer(question))
    spans = []
    for match in tokens:
        word = match.group().casefold()
        if word in PROTECTED or word.isnumeric():
            continue
        if word in SHORTHAND_HINTS:
            spans.append({"start": match.start(), "end": match.end(), "text": match.group(),
                          "signal": "compressed_token"})
        elif word in SPELLING_HINTS and (match.start() == tokens[0].start() or match.group().islower()):
            spans.append({"start": match.start(), "end": match.end(), "text": match.group(),
                          "signal": "spelling_variant"})
        elif (len(word) >= 5 and word.isalpha() and not re.search(r"[aeiouy]", word)
              and not match.group().isupper()):
            spans.append({"start": match.start(), "end": match.end(), "text": match.group(),
                          "signal": "dense_consonants"})
        elif (word not in FAMILIAR and len(word) >= 3 and not match.group().isupper() and
              (re.search(r"(.)\1{2,}", word) or
               (re.search(r"[a-z]", word) and re.search(r"\d", word) and not re.fullmatch(r"\d+(?:st|nd|rd|th)", word)) or
               re.search(r"q(?!u)", word) or re.search(r"[bcdfghjklmnpqrstvwxz]{4,}", word))):
            spans.append({"start": match.start(), "end": match.end(), "text": match.group(),
                          "signal": "nonstandard_spelling_shape"})
    # One ordinary abbreviation/typo alone need not pay for an LLM call.
    strong = any(s["signal"] in {"dense_consonants", "nonstandard_spelling_shape"} for s in spans)
    needed = len(spans) >= 2 or strong
    reason = "compressed_or_corrupted_wording" if needed else "local_path"
    if not needed and routing and routing["routing_action"] == "clarify" and routing["reason"] in FALLBACK_REASONS:
        # A clear specialized-scope question can need context rather than a
        # wording rewrite. A small vocabulary is not proof of misspelling.
        # This never changes its classification/route. Observed corruption
        # still takes the normal conditional-provider path above.
        if not spans and re.search(r'\b(?:seafarer|ofw|kasambahay|pension|insurance|telecommunications|investment|privacy)\b',question,re.I):
            return {'needed':False,'reason':'recognized_scope_context_needed','trigger_spans':[],
                    'mode':'whole_question_interpretation'}
        candidates = [m.group().casefold() for m in tokens if len(m.group()) >= 3 and m.group().islower()]
        unfamiliar = [w for w in candidates if w not in FAMILIAR]
        if len(unfamiliar) >= 2 and len(unfamiliar) / max(1, len(candidates)) >= .3:
            needed, reason = True, "unresolved_unfamiliar_wording"
    return {"needed": needed, "reason": reason, "trigger_spans": spans if needed else [],
            "mode": "whole_question_interpretation"}


class ConditionalNormalizer:
    def __init__(self, provider=None, *, capture_diagnostics=False):
        self.provider = provider
        # Explicit development opt-in. Ordinary terminal requests never retain
        # rejected provider wording or write chat logs.
        self.capture_diagnostics = capture_diagnostics

    def prepare(self, question, routing=None):
        validate_request({"question_text": question})
        assessment = assess_text(question, routing=routing)
        result = {"version": VERSION, "original_question_text": question,
                  "normalized_question_text": None, "effective_question_text": question,
                  "gate": assessment, "status": "bypassed", "reason": assessment["reason"],
                  "llm_calls": 0, "elapsed_ms": 0.0, "edits": [], "usage": {},
                  "provider": None, "model": None, "clarification_question": None,
                  "performance_evaluation_completed": False,
                  "meaning_preservation_guaranteed": False, "validation_failure": None}
        if not assessment["needed"]:
            return result
        result["effective_question_text"] = None
        result["clarification_question"] = "Could you retype this using fuller words so I can understand the concern accurately?"
        if len(TOKEN.findall(question)) > 400:
            result.update(status="clarify", reason="normalization_word_limit")
            result["clarification_question"] = "Please split this into shorter questions, keeping each separate concern and its details."
            return result
        if self.provider is None:
            result.update(status="unconfigured", reason="normalizer_provider_not_configured")
            return result
        result.update(llm_calls=1, provider=self.provider.name, model=self.provider.model)
        start = time.perf_counter()
        try:
            completion = self.provider.complete(question, assessment)
            result["usage"] = completion.usage
            if self.capture_diagnostics:
                payload = completion.payload
                if (type(payload) is dict and set(payload) == {"status", "normalized_question"}
                        and type(payload["status"]) is str and type(payload["normalized_question"]) is str):
                    result["development_diagnostic"] = {
                        "proposed_status": payload["status"][:32],
                        "proposed_question_text": payload["normalized_question"][:8000],
                        "accepted_for_inference": False}
            normalized, edits = validate_rewrite(question, completion.payload)
            if completion.payload["status"] == "unclear":
                result.update(status="clarify", reason="wording_still_ambiguous")
            else:
                result.update(status="applied" if edits else "unchanged", reason="validated_sentence_interpretation" if edits else "provider_understood_original",
                              effective_question_text=normalized, normalized_question_text=normalized if edits else None,
                              edits=edits, clarification_question=None)
        except NormalizationUnavailable:
            result.update(status="unavailable", reason="normalizer_request_failed")
        except ValueError as error:
            result.update(status="clarify", reason="normalization_did_not_pass_validation",
                          validation_failure=str(error) if str(error) in VALIDATION_CODES else "invalid_normalization_contract")
        except (TypeError, KeyError):
            result.update(status="clarify", reason="normalization_did_not_pass_validation")
        if "development_diagnostic" in result:
            result["development_diagnostic"]["accepted_for_inference"] = result["effective_question_text"] is not None
        result["elapsed_ms"] = (time.perf_counter() - start) * 1000
        return result


def from_environment():
    from backend.normalizer_credentials import read_local_config, read_key
    local = read_local_config()
    provider_name = os.environ.get("RECTO_NORMALIZER_PROVIDER", local.get("provider", "")).strip().lower()
    if not provider_name:
        return ConditionalNormalizer()
    if provider_name not in {"openai", "together"}:
        raise ValueError("Unsupported normalizer provider; configure an installed adapter")
    from backend.normalization_provider import OpenAIProvider, TogetherProvider
    model = os.environ.get("RECTO_NORMALIZER_MODEL", local.get("model", "") if local.get("provider") == provider_name else "").strip()
    key_name = "TOGETHER_API_KEY" if provider_name == "together" else "OPENAI_API_KEY"
    key = os.environ.get(key_name, "").strip() or read_key(provider_name)
    if not model or not key:
        return ConditionalNormalizer()
    provider_type = TogetherProvider if provider_name == "together" else OpenAIProvider
    return ConditionalNormalizer(provider_type(model=model, api_key=key))
