"""Inspection-layer follow-ups; never change classifier labels or admit evidence.

These are questions about explicit payment/employer words, not inferred facts.
The pinned classifier/verifier result is retained verbatim in the packet.
"""
import re

VERSION = "inspection-clarification-v1.0.0"
EMPLOYER = re.compile(r"\b(?:amo|boss|employer)\b", re.IGNORECASE)
PAYMENT = re.compile(r"\b(?:bayad|binayad|binayaran|nabayaran|payment|paid|unpaid|salary|wages?|sahod|sweldo)\b", re.IGNORECASE)
EMPLOYMENT_CATEGORY = re.compile(
    r"\b(?:private|pribado|government|gobyerno|gobierno|govt|municipal|civil\s+service|"
    r"kasambahay|household|domestic\s+worker|ofw|overseas|seafarer)\b", re.IGNORECASE)
GENERIC_REASONS = {"no_reliable_component_evidence", "no_identified_concern", "low_confidence"}


def payment_follow_up(question, routing):
    if (routing["routing_action"] != "clarify" or routing["reason"] not in GENERIC_REASONS
            or not EMPLOYER.search(question) or not PAYMENT.search(question)):
        return None
    prompt = "Ang tinutukoy mong bayad mula sa amo ay sahod para sa trabaho, o ibang uri ng bayad?"
    if not EMPLOYMENT_CATEGORY.search(question):
        prompt += (" Kung sahod ito, private company, gobyerno, kasambahay, OFW, o seafarer ba ang trabaho mo?")
    prompt += " Pakisulat muli ang buong tanong kasama ang detalyeng ito."
    return {"version": VERSION, "reason": "employer_payment_context_unconfirmed",
            "question": prompt, "changes_classifier_prediction": False}
