import { sourceSnapshot } from "./source-snapshot";
export interface SourceProvision {
  id: string; label: string; heading: string; text: string;
  answerEligible: boolean; useMode: string; qualityFlags: string[];
  locator: {
    pdf_page_start: number | null; pdf_page_end: number | null;
    printed_page_start: string | null; printed_page_end: string | null;
    html_anchor: string | null; source_region: string | null;
    source_char_start: number | null; source_char_end: number | null;
  };
}
export interface SourceDocument {
  id: string; citation: string; title: string; documentType: string;
  domain: "labor" | "consumer"; issuer: string; date: string;
  officialUrl: string; retrievalUrl: string; verificationStatus: string;
  answerCandidate: boolean; legalStatus: string; lastChecked: string;
  freshness: string; notes: string; provisions: SourceProvision[];
}
export const libraryDocuments = sourceSnapshot;
export function sourceLink(documentId: string, provisionId?: string) {
  const params = new URLSearchParams({ doc: documentId });
  if (provisionId) params.set("provision", provisionId);
  return "/library?" + params;
}
export function locatorText(provision: SourceProvision) {
  const loc = provision.locator;
  if (loc.pdf_page_start) {
    const pdf = loc.pdf_page_end !== loc.pdf_page_start ? `${loc.pdf_page_start}–${loc.pdf_page_end}` : `${loc.pdf_page_start}`;
    const printed = loc.printed_page_start ? `; printed page ${loc.printed_page_start}${loc.printed_page_end !== loc.printed_page_start ? `–${loc.printed_page_end}` : ""}` : "";
    return `PDF page ${pdf}${printed}`;
  }
  if (loc.source_char_start !== null) return `Stored text characters ${loc.source_char_start}–${loc.source_char_end}`;
  return loc.source_region || "Exact source locator not recorded";
}
export function documentUrl(doc: SourceDocument, provision?: SourceProvision) {
  if (provision?.locator.pdf_page_start && /\.pdf(?:\?|$)/i.test(doc.retrievalUrl)) {
    return `${doc.retrievalUrl}#page=${provision.locator.pdf_page_start}`;
  }
  return doc.officialUrl;
}
