"""Item 7: normalize the 20 canonical sources into document/provision/chunk records."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import pdfplumber
from lxml import html
from pypdf import PdfReader

CONTRACT_VERSION = "1.0.0"
CLEANING_VERSION = "1.0.0"
CHUNKING_VERSION = "1.0.0"
STATUS_DATE = "2026-09-29"
OCR_DOCS = {"DOLE_LA_06_20", "DOLE_LA_16_25", "DTI_DAO_02_1993", "DTI_DAO_20_02"}

EFFECTIVITY_DATE = {
    # DOLE reported that DO 249-25 took effect on 3 March 2025 after
    # publication in a newspaper of general circulation on 15 February.
    "DOLE_DO_249_25": "2025-03-03",
}

SOURCE_ID = {
    "LAB_CODE_2022": "DOLE_LABOR_CODE",
    "PD_442_1974": "SCEL_LAWS", "PD_851_1975": "SCEL_LAWS", "MO_28_1986": "LAWPHIL",
    "RA_6727_1989": "SCEL_LAWS", "RA_10151_2011": "SCEL_LAWS", "RA_10396_2013": "SCEL_LAWS",
    "RA_7394_1992": "SCEL_LAWS", "RA_10909_2016": "SCEL_LAWS", "RA_11967_2023": "SCEL_LAWS",
    "LAB_IRR_1989": "SCEL_LAWS", "DOLE_DO_147_15": "SCEL_LAWS",
    "DOLE_DO_249_25": "DOLE_ISSUANCES", "DOLE_LA_06_20": "DOLE_ISSUANCES",
    "DOLE_LA_16_25": "DOLE_ISSUANCES", "DOLE_BWC_HANDBOOK_2024": "DOLE_ISSUANCES",
    "DTI_DAO_02_1993": "DTI_FTEB_LAWS", "DTI_DAO_16_03": "DTI_FTEB_LAWS",
    "DTI_DAO_20_02": "DTI_FTEB_LAWS", "DTI_JAO_24_03": "DTI_FTEB_LAWS",
}

STATUS_FAMILY = {
    "PD_442_1974": "historical", "MO_28_1986": "verification_pending", "RA_10151_2011": "current_with_conditions",
    "DOLE_LA_16_25": "time_bound", "DOLE_BWC_HANDBOOK_2024": "explanatory",
}

BASE_MODE = {
    "PD_442_1974": "historical_only", "MO_28_1986": "blocked_pending_verification",
    "RA_10151_2011": "historical_only", "DOLE_LA_16_25": "time_bound_only",
    "DOLE_BWC_HANDBOOK_2024": "explanatory_only",
}

DEFAULT_TOPIC = {
    "PD_851_1975": "labor.thirteenth_month_pay", "MO_28_1986": "labor.thirteenth_month_pay",
    "RA_6727_1989": "labor.wages_payment", "RA_10396_2013": "labor.complaint_referral",
    "DOLE_DO_147_15": "labor.termination_due_process", "DOLE_DO_249_25": "labor.complaint_referral",
    "DOLE_LA_06_20": "labor.final_pay_coe", "DOLE_LA_16_25": "labor.thirteenth_month_pay",
    "RA_10909_2016": "consumer.price_tags", "RA_11967_2023": "consumer.online_transactions",
    "DTI_DAO_16_03": "consumer.price_tags", "DTI_DAO_20_02": "consumer.complaint_referral",
    "DTI_JAO_24_03": "consumer.online_transactions",
}

TOPIC_PATTERNS = {
    "labor.wages_payment": r"\bwage|salary|pay day|payment of wages|deduction",
    "labor.hours_of_work": r"hours? of work|normal hours|eight \(8\) hours|work hours",
    "labor.rest_days": r"rest day|weekly rest",
    "labor.overtime_pay": r"overtime|beyond eight",
    "labor.holiday_premium_pay": r"holiday pay|regular holiday|special day|premium pay",
    "labor.thirteenth_month_pay": r"13th.month|thirteenth.month",
    "labor.employment_contracts": r"employment contract|probationary|regular employment|fixed.term",
    "labor.termination_due_process": r"termination|dismissal|just cause|authorized cause|notice of termination",
    "labor.final_pay_coe": r"final pay|last pay|back pay|certificate of employment",
    "labor.complaint_referral": r"conciliation|mediation|single entry|sena|labor dispute|referral",
    "consumer.general_framework": r"consumer act|consumer protection|consumer rights",
    "consumer.defective_products": r"defect|defective product",
    "consumer.warranties": r"warrant(?:y|ies)|guarantee",
    "consumer.repair_replace_refund": r"repair|replacement|refund",
    "consumer.deceptive_unfair_sales": r"deceptive|unfair sales|unfair practice",
    "consumer.misleading_advertising": r"advertis|misleading",
    "consumer.price_tags": r"price tag|shortchang|exact change|change less than",
    "consumer.product_safety": r"product safety|hazardous|unsafe product",
    "consumer.service_complaints": r"service complaint|consumer complaint",
    "consumer.online_transactions": r"online|internet transaction|e.commerce|digital platform|online merchant|e.marketplace",
    "consumer.complaint_referral": r"mediation|adjudication|file a complaint|consumer complaint|complainant",
}

EXCLUDED_PATTERNS = {
    "labor.regional_minimum_wage_amounts": r"current minimum wage|wage rate|wage order|regional minimum wage",
    "labor.ofw": r"overseas filipino|migrant worker|\bofw\b",
    "labor.seafarers": r"seafarer|seaman",
    "labor.government_employment": r"government employee|civil service",
    "labor.kasambahay": r"kasambahay|domestic worker",
    "labor.union_cba": r"collective bargaining|labor organization|trade union|union dues",
    "labor.workers_compensation": r"employees. compensation|workmen.s compensation",
    "labor.occupational_safety": r"occupational safety|workplace safety",
    "labor.retirement_pension": r"retirement|pension",
    "labor.pending_case": r"pending case|pending litigation",
    "consumer.banking_credit": r"banking|credit card|consumer credit",
    "consumer.insurance": r"insurance",
    "consumer.investments": r"investment|securities",
    "consumer.telecommunications": r"telecommunication|internet service provider",
    "consumer.data_privacy": r"data privacy|personal information",
    "consumer.medical_malpractice": r"medical malpractice",
    "consumer.real_estate": r"real estate|subdivision|condominium",
    "consumer.transportation": r"transportation|airline|shipping",
    "consumer.utility_billing": r"utility billing|electric bill|water bill",
    "consumer.criminal_online_fraud": r"criminal fraud|cybercrime|online scam",
}


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_") or "body"


def clean_text(text: str) -> tuple[str, list[dict]]:
    repairs: list[dict] = []
    text = text.replace("\u00ad", "").replace("\u00a0", " ")
    if re.search(r"(?i)conciliation\ufffdmediation", text):
        text = re.sub(r"(?i)conciliation\ufffdmediation", "conciliation-mediation", text)
        repairs.append({"field": "verbatim_text", "extracted_value": "conciliation�mediation", "corrected_value": "conciliation-mediation", "reason": "The rendered DO 249-25 page visibly confirms the missing character is a hyphen."})
    if "\ufffd" in text:
        text = text.replace("\ufffd", "[UNRESOLVED_GLYPH]")
        repairs.append({"field": "verbatim_text", "extracted_value": "�", "corrected_value": "[UNRESOLVED_GLYPH]", "reason": "The undecodable glyph was made explicit and remains blocked pending visual verification."})
    text = re.sub(r"(?<=\w)\s+-\s*(?=\w)", "-", text)
    text = re.sub(r"-\s*\n\s*(?=[a-z])", "", text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.replace("\r", "").split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text, repairs


def html_text(path: Path) -> tuple[str, bool]:
    doc = html.fromstring(path.read_bytes())
    for bad in doc.xpath("//script|//style|//noscript|//form|//nav|//header|//footer"):
        bad.drop_tree()
    candidates = doc.xpath("//*[contains(concat(' ', normalize-space(@class), ' '), ' single_content ')]")
    if candidates:
        node = max(candidates, key=lambda n: len(n.text_content()))
    else:
        blocks = doc.xpath("//blockquote")
        node = max(blocks, key=lambda n: len(n.text_content())) if blocks else doc.find("body") or doc
    for br in node.xpath(".//br"):
        br.tail = "\n" + (br.tail or "")
    for el in node.xpath(".//p|.//div|.//li|.//tr|.//h1|.//h2|.//h3|.//h4|.//center|.//blockquote"):
        el.tail = "\n" + (el.tail or "")
    # Ignore one-cell layout tables used by the source website itself.
    tables_present = bool(node.xpath(".//table[.//tr[count(th|td) >= 2]]"))
    text = node.text_content().replace("View printer friendly version", "")
    return clean_text(text)[0], tables_present


def load_ocr(path: Path) -> dict[str, list[dict]]:
    pages: dict[str, list[dict]] = defaultdict(list)
    if not path.exists():
        return pages
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            row["text"], row["repairs"] = clean_text(row.get("text", ""))
            row.setdefault("footnotes", [])
            row.setdefault("tables_present", False)
            pages[row["document_id"]].append(row)
    for rows in pages.values():
        rows.sort(key=lambda r: (r["pdf_page"], r.get("page_segment", 1)))
    return pages


def _printed_page_number(text: str) -> int | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines[-6:]):
        if re.fullmatch(r"[0-9]{1,4}", line):
            return int(line)
        match = re.fullmatch(r"(?i)page\s+([0-9]{1,4})(?:\s+of\s+[0-9]{1,4})?", line)
        if match:
            return int(match.group(1))
    return None


def _parse_footnotes(text: str) -> list[dict]:
    notes: list[dict] = []
    current: dict | None = None
    for line in [re.sub(r"\s+", " ", value).strip() for value in text.splitlines()]:
        if not line:
            continue
        match = re.match(r"^(\d{1,3})\s+(.+)$", line)
        if match:
            current = {"marker": match.group(1), "text": match.group(2)}
            notes.append(current)
        elif current:
            current["text"] += " " + line
    return notes


def pdf_pages(path: Path, document_id: str) -> list[dict]:
    """Extract positioned PDF text; separate Labor Code footnotes and printed pages."""
    rows: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            full_text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            printed_page = _printed_page_number(full_text)
            footnotes: list[dict] = []
            body_text = full_text
            if document_id == "LAB_CODE_2022" and page.chars:
                main_tops = [float(char.get("top") or 0) for char in page.chars if float(char.get("size") or 0) >= 7]

                def near_body_baseline(obj: dict) -> bool:
                    top = float(obj.get("top") or 0)
                    return any(abs(top - main_top) <= 4 for main_top in main_tops)

                def is_body_char(obj: dict) -> bool:
                    if obj.get("object_type") != "char" or float(obj.get("top") or 0) >= page.height - 45:
                        return False
                    if float(obj.get("size") or 0) >= 7:
                        return True
                    # Keep superscript footnote markers that share a body-text
                    # baseline; exclude the small-font footnote body itself.
                    return near_body_baseline(obj)

                body_text = page.filter(is_body_char).extract_text(x_tolerance=2, y_tolerance=3) or ""
                footnote_text = page.filter(
                    lambda obj: obj.get("object_type") == "char"
                    and float(obj.get("size") or 99) <= 6.2
                    and float(obj.get("top") or 0) < page.height - 45
                    and not near_body_baseline(obj)
                ).extract_text(x_tolerance=2, y_tolerance=3) or ""
                footnotes = _parse_footnotes(footnote_text)
            elif printed_page is not None:
                lines = body_text.splitlines()
                if lines and (lines[-1].strip() == str(printed_page) or re.fullmatch(r"(?i)page\s+\d+(?:\s+of\s+\d+)?", lines[-1].strip())):
                    body_text = "\n".join(lines[:-1])
            text, repairs = clean_text(body_text)
            tables_present = bool(page.find_tables())
            rows.append({
                "pdf_page": index, "printed_page": printed_page, "text": text,
                "confidence": None, "rotation_degrees_clockwise": 0,
                "repairs": repairs, "footnotes": footnotes,
                "tables_present": tables_present,
            })
    return rows


def page_spans(pages: list[dict]) -> tuple[str, list[tuple[int, int, dict]]]:
    chunks, spans, cursor = [], [], 0
    for page in pages:
        text = page["text"].strip()
        if not text:
            continue
        if chunks:
            chunks.append("\n\n")
            cursor += 2
        start = cursor
        chunks.append(text)
        cursor += len(text)
        spans.append((start, cursor, page))
    return "".join(chunks), spans


BOUNDARY = re.compile(r"(?im)^(?P<label>(?:ART(?:ICLE)?\.?|SECTION|SEC\.)\s*[0-9](?:\s*[0-9])*(?:\.[0-9]+)*(?:-[A-Z])?)\s*[.\-–:]?\s*(?P<head>[^\n]{0,180})")
ROMAN_BOUNDARY = re.compile(r"(?m)^(?P<label>[IVXLC]{1,8})\.\s+(?P<head>[A-Z][A-Z0-9 ,()'\-/]{2,100})$")
HIER = re.compile(
    r"(?im)^(?P<kind>BOOK|TITLE|CHAPTER|PART|RULE)\s+"
    r"(?P<num>ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|[IVXLC]+|[0-9]+(?:-[A-Z])?)"
    r"(?:\s*[-–.:]\s*|\s+)(?P<head>[^\n]{0,160})"
)


def normalize_label(label: str) -> str:
    match = re.match(r"(?i)^(ART(?:ICLE)?\.?|SECTION|SEC\.)\s*(.+)$", label.strip())
    if not match:
        return re.sub(r"\s+", " ", label).strip()
    number = re.sub(r"(?<=\d)\s+(?=\d)", "", match.group(2))
    prefix = match.group(1).upper()
    return f"{prefix} {number}"


def clean_heading(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip(" .–—-")
    # A legal heading normally ends before a period/dash separator. Attached
    # superscript footnote numbers are removed from the heading only.
    match = re.match(r"^(.{1,120}?)\.\s*\d{0,3}\s*[–—-]\s+", value)
    if match:
        value = match.group(1)
    else:
        sentence = value.split(".", 1)[0].strip()
        if len(sentence) <= 100 and len(sentence.split()) <= 14 and sentence:
            value = sentence
        else:
            return None
    value = re.sub(r"\.\d{1,3}$", "", value).strip()
    return value if value and len(value) <= 100 else None


def hierarchy_at(text: str, pos: int) -> dict[str, Any]:
    out = {"book": None, "title": None, "chapter": None, "part": None, "rule": None}
    for match in HIER.finditer(text, 0, pos):
        out[match.group("kind").lower()] = re.sub(r"\s+", " ", match.group(0)).strip()
    return out


def locate_page(spans: list[tuple[int, int, dict]], start: int, end: int) -> tuple[dict | None, dict | None]:
    touched = [p for a, b, p in spans if b > start and a < end]
    return (touched[0], touched[-1]) if touched else (None, None)


def extract_units(doc_id: str, text: str, spans: list[tuple[int, int, dict]], is_html: bool) -> list[dict]:
    matches = list(BOUNDARY.finditer(text))
    if not matches and doc_id in {"DOLE_LA_06_20", "DOLE_LA_16_25"}:
        matches = list(ROMAN_BOUNDARY.finditer(text))
    if not matches or doc_id == "DOLE_BWC_HANDBOOK_2024":
        units = []
        if spans:
            for a, b, page in spans:
                units.append({"label": f"Page {page['pdf_page']}", "head": None, "start": a, "end": b, "hierarchy": {"book": None, "title": None, "chapter": None, "part": None, "rule": None}})
        else:
            units.append({"label": "Document body", "head": None, "start": 0, "end": len(text), "hierarchy": {"book": None, "title": None, "chapter": None, "part": None, "rule": None}})
        return units
    units = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        trailing_hierarchy = HIER.search(text, match.end(), end)
        if trailing_hierarchy:
            end = trailing_hierarchy.start()
        segment = text[match.start():end].strip()
        if len(segment) < 35:
            continue
        units.append({"label": normalize_label(match.group("label")), "head": clean_heading(match.groupdict().get("head")),
                      "start": match.start(), "end": end, "hierarchy": hierarchy_at(text, match.start())})
    return units


def topics_for(doc_id: str, domain: str, text: str) -> tuple[str, list[str], list[str]]:
    lowered = text.lower()
    supported = sorted({topic for topic, pattern in TOPIC_PATTERNS.items() if topic.startswith(domain + ".") and re.search(pattern, lowered, re.I)})
    excluded = sorted({topic for topic, pattern in EXCLUDED_PATTERNS.items() if topic.startswith(domain + ".") and re.search(pattern, lowered, re.I)})
    if not supported and doc_id in DEFAULT_TOPIC:
        supported = [DEFAULT_TOPIC[doc_id]]
    if supported and excluded:
        status = "partial"
    elif excluded:
        status = "excluded"
    elif supported:
        status = "supported"
    else:
        status = "review_required"
    return status, supported, excluded


def former_locators(label: str, text: str) -> list[str]:
    if not re.match(r"(?i)^ART", label):
        return []
    match = re.match(r"(?is)^ART(?:ICLE)?\.?\s*\d+\s*\.\s*\[\s*(\d+)\s*\]", text)
    return [f"ART. {match.group(1)}"] if match else []


def suspicious_extraction(label: str, heading: str | None, text: str, hierarchy: dict[str, Any]) -> bool:
    if heading and (len(heading) > 100 or re.match(r"^\d+[.\s]", heading)):
        return True
    if any(value and re.search(r"(?i)\bshall\b|\bprovided\b", value) for value in hierarchy.values()):
        return True
    if re.search(r"(?i)\b(?:re st|em ploy|emplo yment|t he|pro vided|differenti al)\b", text):
        return True
    if re.search(r"\w\s+-\s*\w", text):
        return True
    if re.search(r"(?i)^(?:ART(?:ICLE)?\.?|SECTION|SEC\.)\s*\d+\s+\d+[.]", text):
        return True
    return False


def source_locator(spans: list[tuple[int, int, dict]], start: int, end: int, is_html: bool) -> dict:
    first, last = locate_page(spans, start, end)
    return {
        "pdf_page_start": first.get("pdf_page") if first else None,
        "pdf_page_end": last.get("pdf_page") if last else None,
        "printed_page_start": str(first.get("printed_page")) if first and first.get("printed_page") else None,
        "printed_page_end": str(last.get("printed_page")) if last and last.get("printed_page") else None,
        "html_anchor": None,
        "source_region": "main legal text" if is_html else "PDF page text",
        "source_char_start": start if is_html else None,
        "source_char_end": end if is_html else None,
    }


def context_prefix(doc: dict, provision: dict) -> str:
    parts = [doc["title"]]
    for key in ("book", "title", "chapter", "part", "rule"):
        if provision["hierarchy"][key]:
            parts.append(provision["hierarchy"][key])
    parts.append(provision["locator_label"] + ((" - " + provision["heading"]) if provision["heading"] else ""))
    return " > ".join(parts)


def chunk_record(doc: dict, provision: dict, sequence: int, start: int, end: int, method: str) -> dict:
    display = provision["normalized_text"][start:end]
    prefix = context_prefix(doc, provision)
    return {
        "contract_version": CONTRACT_VERSION, "chunking_version": CHUNKING_VERSION,
        "chunk_id": f"{provision['provision_id']}__chunk_{sequence:04d}", "document_id": doc["document_id"],
        "provision_id": provision["provision_id"], "chunk_sequence": sequence, "chunk_method": method,
        "subdivision_label": None, "context_prefix": prefix, "display_text": display,
        "retrieval_text": prefix + "\n" + display, "normalized_char_start": start, "normalized_char_end": end,
        "character_count": len(display), "token_count": None, "tokenizer_name": None, "overlap_previous_tokens": 0,
        "domains": provision["domains"], "scope_status": provision["scope_status"],
        "supported_topics": provision["supported_topics"], "excluded_topics": provision["excluded_topics"],
        "answer_eligible": provision["provision_answer_eligible"], "answer_use_mode": provision["answer_use_mode"],
        "legal_status": provision["legal_status"], "status_family": provision["status_family"],
        "status_as_of": provision["status_as_of"], "citation_display": provision["citation_display"],
        "quality_flags": provision["quality_flags"],
    }


def make_chunks(doc: dict, provision: dict) -> list[dict]:
    text = provision["normalized_text"]
    if len(text) <= 3500:
        return [chunk_record(doc, provision, 1, 0, len(text), "whole_provision")]
    chunks, start, sequence = [], 0, 1
    while start < len(text):
        target = min(start + 3000, len(text))
        if target < len(text):
            choices = [text.rfind("\n\n", start + 1200, target), text.rfind(". ", start + 1200, target)]
            cut = max(choices)
            if cut > start:
                target = cut + (2 if text[cut:cut + 2] == ". " else 0)
        chunks.append(chunk_record(doc, provision, sequence, start, target, "natural_subdivision" if "\n\n" in text[start:target] else "token_window_fallback"))
        sequence += 1
        start = target
        while start < len(text) and text[start].isspace():
            start += 1
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--ocr-output", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    root, output = Path(args.project_root), Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    canonical = list(csv.DictReader((root / "dataset/canonical_sources/manifests/canonical_documents.csv").open(encoding="utf-8-sig", newline="")))
    statuses = {r["document_id"]: r for r in csv.DictReader((root / "dataset/canonical_sources/manifests/legal_status_review.csv").open(encoding="utf-8-sig", newline=""))}
    registry = {r["source_id"]: r for r in csv.DictReader((root / "dataset/authoritative_source_registry.csv").open(encoding="utf-8-sig", newline=""))}
    relationships: dict[str, list[str]] = defaultdict(list)
    for rel in csv.DictReader((root / "dataset/canonical_sources/manifests/legal_status_relationships.csv").open(encoding="utf-8-sig", newline="")):
        if rel["source_document_id"]:
            relationships[rel["source_document_id"]].append(rel["relationship_id"])
        if rel["target_document_id"]:
            relationships[rel["target_document_id"]].append(rel["relationship_id"])
    ocr_pages = load_ocr(Path(args.ocr_output))

    documents, provisions, chunks, report = [], [], [], []
    for row in canonical:
        doc_id, domain = row["document_id"], row["domain"]
        status = statuses[doc_id]
        source_id = SOURCE_ID[doc_id]
        source = registry[source_id]
        family = STATUS_FAMILY.get(doc_id, "current_with_conditions")
        doc = {
            "contract_version": CONTRACT_VERSION, "document_id": doc_id, "domains": [domain], "citation": row["citation"],
            "title": row["title"], "document_type": row["document_type"], "issuer": row["issuer"],
            "approval_or_edition_date": row["approval_or_edition_date"], "effectivity_date": EFFECTIVITY_DATE.get(doc_id), "jurisdiction": "Philippines",
            "source_id": source_id, "authority_level": source["authority_level"], "permitted_use": source["permitted_use"],
            "official_source_url": row["official_source_url"], "retrieval_url": row["retrieval_url"],
            "raw_local_path": "dataset/canonical_sources/" + row["local_path"].replace("\\", "/"), "raw_file_format": row["file_format"],
            "verification_status": row["verification_status"],
            "document_answer_eligible_candidate": row["answer_eligible_candidate"].lower() == "true",
            "collection_role": row["collection_role"], "legal_status": status["legal_status"], "status_family": family,
            "status_as_of": status["status_as_of"], "retrieval_use_policy": status["retrieval_use_policy"],
            "freshness_rule": status["freshness_rule"], "languages": ["en"], "version_label": row["approval_or_edition_date"],
            "notes": row["notes"], "processing_state": "validated",
        }
        documents.append(doc)
        raw = root / "dataset/canonical_sources" / row["local_path"]
        if not raw.is_file():
            raise FileNotFoundError(f"Raw source file is missing: {doc_id} ({raw})")
        is_html = row["file_format"].lower() == "html"
        if is_html:
            text, html_tables_present = html_text(raw)
            page_rows: list[dict] = []
            spans: list[tuple[int, int, dict]] = []
            extraction = "html_structural"
        elif doc_id in OCR_DOCS:
            page_rows = ocr_pages.get(doc_id, [])
            if not page_rows:
                raise ValueError(f"Missing OCR output for {doc_id}")
            text, spans = page_spans(page_rows)
            extraction = "ocr"
        else:
            page_rows = pdf_pages(raw, doc_id)
            text, spans = page_spans(page_rows)
            extraction = "pdf_text"
        units = extract_units(doc_id, text, spans, is_html)
        seen: dict[str, int] = defaultdict(int)
        doc_provisions = []
        for unit in units:
            segment, repairs = clean_text(text[unit["start"]:unit["end"]])
            if len(segment) < 20:
                continue
            locator_base = slug(unit["label"])
            rule = unit["hierarchy"].get("rule")
            locator = (slug(rule) + "__" + locator_base) if rule and locator_base.startswith(("section_", "sec_")) else locator_base
            seen[locator] += 1
            if seen[locator] > 1:
                locator += f"__occ_{seen[locator]}"
            provision_id = f"{doc_id}__{locator}"
            first, last = locate_page(spans, unit["start"], unit["end"])
            page_rows_touched = [p for a, b, p in spans if b > unit["start"] and a < unit["end"]]
            for page_row in page_rows_touched:
                for repair in page_row.get("repairs", []):
                    corrected = repair.get("corrected_value", "")
                    if corrected and corrected in segment and repair not in repairs:
                        repairs.append(repair)
            ocr = doc_id in OCR_DOCS
            confidence = min((p.get("confidence") or 0 for p in page_rows_touched), default=None) if ocr else None
            flags = []
            if ocr:
                flags += ["image_only_pdf", "official_text_comparison_pending"]
                if doc_id == "DTI_DAO_02_1993": flags += ["rotated_page", "multiple_printed_pages_per_pdf_page"]
                if confidence is not None and confidence < 0.85: flags.append("ocr_low_confidence_critical_text")
            if "[UNRESOLVED_GLYPH]" in segment:
                flags.append("unresolved_replacement_character")
            if (is_html and html_tables_present) or any(p.get("tables_present") for p in page_rows_touched):
                flags.append("table_structure_present")
            provision_footnotes: list[dict] = []
            for page_row in page_rows_touched:
                for note in page_row.get("footnotes", []):
                    if re.search(rf"(?<!\d){re.escape(note['marker'])}(?!\d)", segment) and note not in provision_footnotes:
                        provision_footnotes.append(note)
            if provision_footnotes:
                flags.append("footnotes_present")
            if suspicious_extraction(unit["label"], unit["head"], segment, unit["hierarchy"]):
                flags.append("provision_boundary_uncertain")
            scope, supported, excluded = topics_for(doc_id, domain, segment)
            mode = BASE_MODE.get(doc_id, "default_answer")
            if ocr: mode = "manual_review_required"
            elif scope in {"excluded", "partial"}: mode = "scope_excluded"
            elif scope == "review_required": mode = "manual_review_required"
            # PD 851 Section 1 contains the original salary-threshold coverage language.
            # MO 28 later modified that section, and the stored MO 28 full-text copy is
            # not yet official-copy verified, so the original provision must not answer
            # a present-law question in isolation.
            if doc_id == "PD_851_1975" and locator_base in {"section_1", "sec_1"}:
                mode = "historical_only"
            blocking_flags = {"official_text_comparison_pending", "ocr_low_confidence_critical_text", "provision_boundary_uncertain", "unresolved_replacement_character"}
            eligible = bool(doc["document_answer_eligible_candidate"] and scope == "supported" and mode == "default_answer" and not (set(flags) & blocking_flags))
            level = "article" if re.match(r"(?i)art", unit["label"]) else "section" if re.match(r"(?i)(section|sec\.)", unit["label"]) else "other"
            citation_display = f"{row['citation']}, {unit['label']}"
            provision = {
                "contract_version": CONTRACT_VERSION, "cleaning_version": CLEANING_VERSION, "provision_id": provision_id,
                "document_id": doc_id, "parent_provision_id": None, "sequence_number": len(doc_provisions) + 1,
                "provision_level": level, "locator_label": unit["label"], "locator_normalized": locator.replace("__", "_"),
                "former_locator_labels": former_locators(unit["label"], segment), "heading": unit["head"], "hierarchy": unit["hierarchy"],
                "citation_display": citation_display, "verbatim_text": segment, "normalized_text": segment,
                "search_text": re.sub(r"[^a-z0-9]+", " ", (row["title"] + " " + citation_display + " " + segment).lower()).strip(),
                "footnotes": provision_footnotes, "source_locator": source_locator(spans, unit["start"], unit["end"], is_html),
                "domains": [domain], "scope_status": scope, "supported_topics": supported, "excluded_topics": excluded,
                "exclusion_reason": "Contains or concerns a topic excluded from the locked MVP scope." if excluded else None,
                "responsible_agencies": [a.strip() for a in row["issuer"].split(";")],
                "provision_answer_eligible": eligible, "answer_use_mode": mode, "legal_status": status["legal_status"],
                "status_family": family, "status_as_of": status["status_as_of"], "effective_from": EFFECTIVITY_DATE.get(doc_id), "effective_to": None,
                "relationship_ids": sorted(set(relationships.get(doc_id, []))),
                "extraction_method": extraction, "ocr_used": ocr, "ocr_confidence": confidence,
                "rotation_degrees_clockwise": (first or {}).get("rotation_degrees_clockwise", 0),
                "quality_flags": sorted(set(flags)), "manual_repairs": repairs,
                "review_status": "human_review_required" if ocr or (set(flags) & blocking_flags) else "machine_validated", "reviewed_at": None,
            }
            provisions.append(provision)
            doc_provisions.append(provision)
            chunks.extend(make_chunks(doc, provision))
        report.append({"document_id": doc_id, "format": row["file_format"], "extraction_method": extraction,
                       "characters": len(text), "provisions": len(doc_provisions), "chunks": sum(1 for c in chunks if c["document_id"] == doc_id),
                       "answer_eligible_provisions": sum(1 for p in doc_provisions if p["provision_answer_eligible"]),
                       "human_review_required": sum(1 for p in doc_provisions if p["review_status"] == "human_review_required")})

    for name, records in (("documents.jsonl", documents), ("provisions.jsonl", provisions), ("retrieval_chunks.jsonl", chunks)):
        with (output / name).open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    with (output / "extraction_report.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(report[0]))
        writer.writeheader(); writer.writerows(report)
    review_rows = [{
        "provision_id": p["provision_id"], "document_id": p["document_id"],
        "citation_display": p["citation_display"],
        "pdf_page_start": p["source_locator"]["pdf_page_start"],
        "pdf_page_end": p["source_locator"]["pdf_page_end"],
        "printed_page_start": p["source_locator"]["printed_page_start"],
        "printed_page_end": p["source_locator"]["printed_page_end"],
        "ocr_confidence": p["ocr_confidence"], "quality_flags": ";".join(p["quality_flags"]),
        "review_status": p["review_status"],
    } for p in provisions if p["ocr_used"] and p["review_status"] == "human_review_required"]
    with (output / "ocr_review_queue.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review_rows[0]) if review_rows else ["provision_id"])
        writer.writeheader(); writer.writerows(review_rows)
    all_review_rows = [{
        "provision_id": p["provision_id"], "document_id": p["document_id"],
        "citation_display": p["citation_display"], "extraction_method": p["extraction_method"],
        "pdf_page_start": p["source_locator"]["pdf_page_start"],
        "pdf_page_end": p["source_locator"]["pdf_page_end"],
        "printed_page_start": p["source_locator"]["printed_page_start"],
        "printed_page_end": p["source_locator"]["printed_page_end"],
        "quality_flags": ";".join(p["quality_flags"]), "review_status": p["review_status"],
        "text_preview": re.sub(r"\s+", " ", p["normalized_text"])[:300],
    } for p in provisions if p["review_status"] == "human_review_required"]
    with (output / "human_review_queue.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_review_rows[0]) if all_review_rows else ["provision_id"])
        writer.writeheader(); writer.writerows(all_review_rows)
    print(f"Wrote {len(documents)} documents, {len(provisions)} provisions, and {len(chunks)} chunks to {output}")


if __name__ == "__main__":
    main()
