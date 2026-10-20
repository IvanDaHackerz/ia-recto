# Recto & Co. Legal

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary users are ordinary Filipino workers and consumers who need understandable information about everyday Philippine employment and consumer concerns. The app serves the general public, including persons with disabilities, rather than requiring legal training.

People may arrive anxious about unpaid wages, termination, a defective purchase, or a refused refund. They need to understand what the system can handle, inspect the basis of an explanation, and identify an appropriate next contact when an issue is outside its scope.

## Product Purpose

Provide accessible, source-grounded general information within a deliberately limited Philippine labor and consumer scope. Help users understand the supported parts of a question and inspect the legal material behind an explanation.

This is the web-based intelligent-agent project described in the whole IA workspace, not an isolated UI exercise. Product decisions must remain consistent with the proposal, approved scope, source registry, data contract, review workflow, and evaluation plan.

Success means correct domain and scope handling, relevant verified evidence, citations that support the explanation, clear limitations when evidence is insufficient, and an interface people can use and read. The app does not provide professional legal advice or predict case outcomes.

## Positioning

The product combines a separately evaluated question classifier with source retrieval, legal-status checks, and citation verification. Its defining commitment is that a substantive explanation must be supported by eligible legal provisions, and its evidence must be inspectable alongside the explanation.

The system distinguishes a fully supported labor-and-consumer question from a question containing both supported and excluded issues. It also distinguishes a verified answer source from an unverified discovery result. Neither distinction may be hidden by a simplified UI.

## Operating Context

The primary workflow is to ask a question, read a plain-language explanation, inspect its exact legal text and citations, and receive a clear limitation or referral where appropriate. History lets users revisit questions and answers. A library supports source inspection. Settings expose text sizing and high contrast.

The existing app routes are Ask (`/`), saved live responses (`/saved/:savedId`), archived scripted conversations (`/chat/:conversationId`), History (`/history`), Library (`/library`), Performance (`/performance`, with `?view=details` for the detailed report), Settings (`/settings`), and Scope & limitations (`/about`). These are existing application surfaces, not a requirement to add marketing pages or a new onboarding flow.

The current runtime keeps the original English or Taglish question locally, with recognized credentials masked even in that retained wording. Its initial local routing/classification pass uses wording after best-effort identifier masking. When AI is enabled, conditional interpretation can supply effective wording for a second classifier/retrieval pass; the interface exposes an accepted interpretation so the user can check it. It does not silently replace the displayed original question. Retrieval supplies recorded provisions; eligibility, citation and automated support checks run before a development explanation is displayed. Currentness and independent legal approval remain separate closed gates.

The existing local development command is `npm.cmd run dev` from `C:\IA\UI\UX\app`. The stack is React, TypeScript, Vite, Tailwind CSS, Radix primitives, and React Router. Read the actual package manifest for versions; the older UI plan contains a historical React version.

## Capabilities and Constraints

### Approved scope

The authoritative scope is [project_legal_scope.md](../../../project_legal_scope.md), supported by the [topic taxonomy](../../../dataset/data_contract/topic_taxonomy.csv). The following summary must not broaden it.

- **Labor included:** basic wages and wage-payment rules; hours of work; rest days; overtime; holiday and premium pay; 13th-month pay; basic employment-contract concerns; termination and procedural due process; final pay and certificates of employment; basic complaint procedures and agency referrals. Coverage is for selected private-sector employment concerns.
- **Labor excluded:** exact regional minimum-wage amounts; OFWs; seafarers; government employees; kasambahays; union elections and complex collective bargaining disputes; workers' compensation and disability computations; occupational-safety compliance; retirement and pension computations; pending court cases; personalized case-outcome predictions.
- **Consumer included:** defective products; warranties; repair, replacement, and refund rights; deceptive or unfair sales practices; misleading advertisements; price tags and displayed prices; product safety; basic service complaints; ordinary online consumer transactions covered by the Internet Transactions Act; DTI complaint procedures and referrals.
- **Consumer excluded:** banking, lending, and credit-card disputes; insurance; investments and securities; telecommunications; data privacy; medical malpractice; real-estate transactions; transportation regulation; utility billing; online fraud requiring criminal investigation. Online matters requiring a specialized regulator are outside the ordinary online-transaction coverage.

The MVP classifier languages are English and conversational Taglish. Full Filipino and regional-language support are not established by the existing reviewed-data plan; do not imply that they are evaluated capabilities.

### Classification and response behavior

- Primary labels are `labor`, `consumer`, `mixed`, and `out_of_scope`.
- Separate scope labels are `fully_supported`, `partially_supported`, and `unsupported`.
- `mixed` can mean supported labor plus supported consumer issues, or supported issues combined with excluded issues. Scope determines whether a partial answer is needed.
- Fully supported questions still require sufficient eligible evidence before an answer.
- Partially supported questions require an explicit boundary between the supported explanation and the excluded portion, with permitted referrals where appropriate.
- Unsupported questions receive a helpful limitation/referral rather than a fabricated substantive answer or a generic system error.
- Uncertain classification or insufficient evidence requires clarification, abstention, or a limitation notice. Confidence must not be invented.

### Source and data constraints

- The canonical collection and the wider BetterGov discovery corpus are separate tiers. Discovery matches, generated summaries, and relevance scores do not establish current law or answer eligibility.
- Retrieval must respect document and provision eligibility, scope, extraction quality, legal status, amendments, repeals, renumbering, and time restrictions.
- Citation displays must preserve the legal text and source locators. Search chunks link to complete parent provisions; generated explanations cannot replace source text.
- Show recorded source-check dates honestly. Do not imply continuous verification or current legal review merely because the interface is newly built.
- Raw source snapshots must remain intact. Upstream changes require new versions and review, not silent replacement.
- Referrals come from the verified directory and its subject-specific routing. Do not invent agencies, contact details, or verification marks.

### Current implementation versus planned system

The local development website is connected to the custom classifier, filtered retrieval and evidence verifier. CURRENT_ARTIFACTS.json selects the active immutable packages. The Performance page reads measured, checksum-pinned AI development evaluations. These are reused development inputs, not independent human accuracy or legal-answer certification.

The current question path is local redaction and safety/routing checks, optional conditional wording interpretation, classifier/retrieval, and optional recorded-source explanation. Exact quotations and a same-model automated support check must pass before a development explanation appears. Source currentness, professional legal review and public deployment permissions remain closed. The UI keeps original wording locally and shows an accepted interpretation. Each question is independent; include the full concern again.

History now stores live question/response packets only after explicit opt-in. SQLite payloads and browser-session signing keys use Windows-user DPAPI encryption under ignored .local/website. History is isolated by a signed browser token, expires after 30 days, and supports opening, JSON export and deletion. Clearing browser cookies loses access; this is not account authentication. Temporary request deduplication caches responses in memory for five minutes. Archived scripted design examples remain clearly separate. The saved route is /saved/:savedId; /chat/:conversationId contains archived examples.

Reading, AI and saving preferences persist in browser local storage when available. AI can be disabled per question for local classification/retrieval only. Identifier masking is best effort, never a complete privacy guarantee. Together receives the redacted question and selected sources/drafts when enabled. External provider retention is governed by its policy. Request attempts and estimated spending have bounded local daily limits; cancellation closes active upstream sockets without promising refund of already processed work.

The Library remains a generated source-inspection snapshot. Complete legal text, extraction restrictions, recorded dates and publication links stay inspectable. Referral links show only field-confirmed directory values. Missing final-pay or 13th-month related-source approvals remain visible rather than being treated as answer evidence.

All five original reviewer returns were imported earlier. AI-authored development and AI-reviewed question sets remain separate from the empty fresh independent-human intake. Required independent human, legal-professional, accessibility/user and owner/adviser acceptance cannot be supplied by generated artifacts.

### Open decisions

Public hosting/TLS, deployed authentication and privacy governance, broader language/device support, fresh independent testing and legal/currentness approval remain release decisions. The loopback API and Vite launcher are development services. Source review gates, software tests and a same-model support judge do not establish current legal correctness.

## Brand Commitments

The product name is **Recto & Co. Legal**. Preserve that identity, approved legal boundaries, and plain-language purpose. Communication should be calm, understandable, and candid about limitations; it must not imply government affiliation, professional representation, or guaranteed legal outcomes.

This setup does not authorize a redesign. Existing visual choices remain in the implementation and the prior design guide; this product record does not replace them with a new palette or typography system.

The owner subsequently authorized a stronger navy top masthead, improved example-question rows, and restrained, professional motion: quiet, precise, smooth, and selectively bold. Evidence spotlight is the chosen signature interaction. It identifies the provision reached from a citation; it must never imply that the provision or sample answer has newly passed legal verification. State feedback remains clear with reduced-motion preferences.

## Evidence on Hand

Use the full IA workspace as the product evidence base. Begin with these maintained records rather than reading the entire bulk corpus into design context:

- [Concept proposal](../../../paper.md): objectives, beneficiaries, required capabilities, accessibility, and legal-professional evaluation.
- [Whole-project preparation and roadmap](../../../README.md): Items 1–14, completed data work, known limitations, and future integration.
- [Approved legal scope](../../../project_legal_scope.md): included and excluded topics.
- [Authoritative-source registry](../../../dataset/authoritative_source_registry.csv), [canonical-source policy](../../../dataset/canonical_sources/README.md), and its [manifests](../../../dataset/canonical_sources/manifests/): provenance, verification, eligibility, and legal relationships.
- [Data contract](../../../dataset/data_contract/README.md), schemas, and taxonomy: document snapshots, provisions, retrieval chunks, text fidelity, and safety gates.
- [Item 7](../../../dataset/pipelines/item7/README.md), [Item 8](../../../dataset/pipelines/item8/README.md), and [Item 9](../../../dataset/pipelines/item9/README.md): processed canonical records, gated discovery candidates, and classifier/referral seeds. Consult `dataset/processed/` reports for recorded run evidence.
- [Item 10 plan](../../../dataset/pipelines/item10/README.md), [annotation guide](../../../dataset/pipelines/item10/ANNOTATION_GUIDE.md), and [group workbook guide](../../../outputs/item10-review-workbooks/GROUP_REVIEW_GUIDE.md): review and training requirements.
- [UI plan](../plan.md), [prior design guide](../design_guide.md), and `src/`: incumbent routes, behavior, components, and prototype data. The approved root scope takes precedence over abbreviated UI copy.
- `outputs/`: supporting assignment, study-guide, and reviewer artifacts. These are project artifacts, not evidence of deployed functionality or independently measured performance.

The documented foundation contains 20 canonical documents, a 182-document discovery queue, and 672 synthetic questions across 42 taxonomy topics. These are recorded dataset counts, not claims that all documents are answer eligible or all questions are human approved.

Measured classifier and retrieval development results are available in the pinned reports. There are no established deployment metrics, user testimonials, endorsements or independent human/legal acceptance results to use as product claims.

## Product Principles

1. Make supporting evidence as inspectable as the explanation.
2. Enforce scope and evidence limits before making substantive claims.
3. Preserve original questions, source text, provenance, and review history.
4. Help people understand the next step without requiring legal expertise.
5. Represent prototype behavior, verified data, and planned capabilities honestly.

## Accessibility & Inclusion

Adjustable text size and high contrast are confirmed requirements for PWD accessibility. Preserve access to these controls across the app. Keyboard navigation, visible focus, semantic controls, readable legal passages, and layouts that tolerate enlarged text are part of making those features useful.

The existing UI plan targets WCAG AA contrast and responsive behavior. Treat these as design and verification requirements, not a claim of certified compliance. English/Taglish terminology and plain explanations should reduce comprehension barriers without changing legal meaning.

The owner subsequently requested a full-width chat workspace: sticky masthead, pinned question composer, independently scrolling conversation, and ordered source blocks in a persistent desktop pane. On narrower screens the pane has an explicit Sources/Back to chat path. References remain attached to a named response; source selection never implies legal verification. Preserve readable prose measures within the wider working area, exact stored provisions, extraction notes, answer-use restrictions, and Library navigation.
