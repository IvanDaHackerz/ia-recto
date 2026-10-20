export type Domain = "labor" | "consumer" | "mixed" | "out_of_scope";
export type Scope = "fully_supported" | "partially_supported" | "unsupported";
export interface Citation {
  id: string; citation: string; title: string; sourceId: string; provisionIds: string[];
}
export interface AnswerScenario {
  id: string; query: string; domain: Domain; scope: Scope;
  supportedDomains: ("labor" | "consumer")[];
  evidenceStatus: "illustrative" | "insufficient" | "not_applicable";
  supportedAnswer?: string; unsupportedTopic?: string; declineMessage?: string;
  referralIds?: string[]; citations: Citation[];
}
const terminationSources: Citation[] = [
  { id: "termination-grounds", citation: "Labor Code, Articles 297–299", title: "Labor Code", sourceId: "LAB_CODE_2022",
    provisionIds: ["LAB_CODE_2022__art_297", "LAB_CODE_2022__art_298", "LAB_CODE_2022__art_299"] },
  { id: "termination-procedure", citation: "DOLE Department Order 147-15, Rule I-A, Section 5", title: "Termination procedure",
    sourceId: "DOLE_DO_147_15", provisionIds: ["DOLE_DO_147_15__rule_i_a__section_5"] },
];
export const answerScenarios: AnswerScenario[] = [
  {
    id: "labor-termination", query: "Can my employer fire me without notice?",
    domain: "labor", scope: "fully_supported", supportedDomains: ["labor"], evidenceStatus: "illustrative",
    supportedAnswer: "This example points to two separate questions: the ground for ending employment and the procedure followed. The references list termination grounds and procedural requirements. An omitted step does not, by itself, let this prototype determine whether a dismissal is illegal or what remedy applies. Read the actual provisions and seek case-specific assistance when needed.",
    citations: terminationSources, referralIds: ["REF_DOLE_ARMS"],
  },
  {
    id: "consumer-warranty", query: "The store won't honor my warranty. What are my rights?",
    domain: "consumer", scope: "fully_supported", supportedDomains: ["consumer"], evidenceStatus: "illustrative",
    supportedAnswer: "This example directs a warranty concern to the Consumer Act's warranty provisions. The applicable obligation or remedy depends on the warranty, the defect, and the facts. Inspect the complete stored provision rather than treating this sample as a decision about your purchase. DTI's complaint service is listed below for assistance.",
    citations: [{ id: "warranties", citation: "Consumer Act, Article 68", title: "Consumer Act of the Philippines", sourceId: "RA_7394_1992", provisionIds: ["RA_7394_1992__art_68"] }],
    referralIds: ["REF_DTI_CARE"],
  },
  {
    id: "mixed-termination-deposit", query: "I was fired without due process and now my landlord won't return my security deposit.",
    domain: "mixed", scope: "partially_supported", supportedDomains: ["labor"], evidenceStatus: "illustrative",
    supportedAnswer: "The employment issue falls within the project's selected labor topics. This sample points to termination grounds and procedural requirements for inspection; it cannot decide the facts or predict a remedy.",
    unsupportedTopic: "The landlord and security-deposit issue concerns a lease dispute. Real-estate transactions and lease matters are outside this MVP's scope. A legal-assistance office can help identify the appropriate route.",
    citations: terminationSources, referralIds: ["REF_PAO"],
  },
  {
    id: "decline-pension", query: "What is the exact retirement pension computation for my SSS contributions?",
    domain: "out_of_scope", scope: "unsupported", supportedDomains: [], evidenceStatus: "not_applicable",
    declineMessage: "Retirement and pension computations are excluded from the MVP. This is a scope limit, not a low-confidence labor answer. Contact SSS for information based on your contribution records.",
    referralIds: ["REF_SSS"], citations: [],
  },
  {
    id: "out-of-scope-malpractice", query: "Can I get compensation for a medical malpractice case?",
    domain: "out_of_scope", scope: "unsupported", supportedDomains: [], evidenceStatus: "not_applicable",
    declineMessage: "Medical malpractice is outside the project's selected labor and consumer topics. The prototype cannot determine compensation or case outcomes.",
    referralIds: ["REF_PAO"], citations: [],
  },
  {
    id: "insufficient-evidence", query: "Can you explain the notice requirement for my employment contract?",
    domain: "labor", scope: "fully_supported", supportedDomains: ["labor"], evidenceStatus: "insufficient",
    declineMessage: "This scripted example demonstrates an evidence gap within a supported topic. No matching provision is mapped to this example, so it gives no substantive answer. In the completed system, a clarification or additional verified evidence would be needed.",
    referralIds: ["REF_DOLE_ARMS"], citations: [],
  },
];
