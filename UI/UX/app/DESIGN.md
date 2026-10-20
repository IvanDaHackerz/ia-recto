---
name: Recto & Co. Legal
description: A calm reference desk for source-grounded Philippine labor and consumer information.
colors:
  ink: "#1a1a17"
  ink-soft: "#50534b"
  paper: "#f6f7f4"
  paper-raised: "#ffffff"
  border: "#dcded6"
  border-strong: "#909586"
  primary: "#1e3350"
  primary-hover: "#16263d"
  primary-wash: "#e7ecf1"
  verified: "#755816"
  verified-wash: "#f3ead2"
  caution: "#854d0e"
  caution-wash: "#f6e9d7"
  redirect: "#345f5c"
  redirect-wash: "#e6eeed"
  masthead: "#1e3350"
  masthead-ink: "#f6f7f4"
  masthead-muted: "#ccd6e1"
  masthead-hover: "#2b4361"
  masthead-rule: "#536781"
  active-rule: "#d8bc72"
typography:
  headline:
    fontFamily: '"Literata", ui-serif, Georgia, serif'
    fontSize: "1.85rem"
    fontWeight: 500
    lineHeight: 1.3
  title:
    fontFamily: '"Literata", ui-serif, Georgia, serif'
    fontSize: "1.3rem"
    fontWeight: 500
    lineHeight: 1.3
  question:
    fontFamily: '"Literata", ui-serif, Georgia, serif'
    fontSize: "1.4rem"
    fontWeight: 500
    lineHeight: 1.3
  body:
    fontFamily: '"Public Sans", ui-sans-serif, system-ui, sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  legal-text:
    fontFamily: '"Literata", ui-serif, Georgia, serif'
    fontSize: ".95rem"
    fontWeight: 400
    lineHeight: 1.9
  control:
    fontFamily: '"Public Sans", ui-sans-serif, system-ui, sans-serif'
    fontSize: ".9rem"
    fontWeight: 600
    lineHeight: 1.5
  label:
    fontFamily: '"Public Sans", ui-sans-serif, system-ui, sans-serif'
    fontSize: ".85rem"
    fontWeight: 600
    lineHeight: 1.6
  metadata:
    fontFamily: '"Public Sans", ui-sans-serif, system-ui, sans-serif'
    fontSize: ".8rem"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  control: "4px"
  reference: "6px"
  source-block: "12px"
  segment: "3px"
  segment-group: "5px"
  switch: "24px"
spacing:
  sm: ".5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
  section: "2.5rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.paper-raised}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: ".6rem 1.2rem"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.primary}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: ".6rem 1.2rem"
  button-secondary-hover:
    backgroundColor: "{colors.primary-wash}"
  button-text:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    padding: "0"
  question-input:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: ".6rem .8rem"
  masthead-navigation:
    backgroundColor: "{colors.masthead}"
    textColor: "{colors.masthead-muted}"
    padding: ".65rem .8rem"
  reference-chip:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.primary}"
    rounded: "{rounded.reference}"
    padding: ".4rem .65rem .4rem .4rem"
  source-block:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.source-block}"
  example-question:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    padding: ".85rem .7rem"
  metric-segment:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    rounded: "{rounded.segment}"
    padding: ".55rem 1rem"
  metric-segment-selected:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.paper-raised}"
  history-row:
    textColor: "{colors.ink}"
    padding: "1.2rem 0"
---

# Design System: Recto & Co. Legal

## Overview

**Creative North Star: "The Public Service Reference Desk"**

Recto uses the calm, text-respecting reference-desk character established in the incumbent design guide. A navy masthead frames pale paper, serif questions and legal material, and plain sans-serif controls. The identity belongs to an accessible Philippine labor and consumer information tool; it does not imply government affiliation or professional representation.

The built system favors readable passages, precise rules and explicit controls over decorative surfaces. Questions, explanations and complete stored provisions have different typographic roles. Evidence stays close to the relevant response; its selection and quoted-text highlight describe a reading relationship, never a new legal approval.

**Key Characteristics:**

- Navy chrome and pale paper, with restrained amber and teal status treatments.
- Literata for headings, questions and quoted legal reading; Public Sans for controls and explanations.
- Flat rows and fine rules, with bounded source accordions where evidence needs containment.
- Deliberate state feedback, visible keyboard focus, and persistent reading preferences.

This is a scan of the existing implementation, not a new visual direction. Normative primitives above come from `src/index.css`; the component examples and extensions in `.impeccable/design.json` also sample `src/pages/performance.css`. Reading adaptations continue to use the implemented `html.high-contrast` overrides rather than a second identity.

## Colors

The palette is a restrained navy and paper system, with contextual warm and cool status colors.

### Primary

- **Reference Navy** (`primary`, `primary-hover`, `primary-wash`): actions, headings, selected controls, source-pane ground and active report states.
- **Masthead Navy** (`masthead`, `masthead-hover`, `masthead-rule`): the persistent institutional frame and its navigation states. The independent masthead tokens preserve readable chrome when the reading palette changes.
- **Masthead Paper and Muted Blue** (`masthead-ink`, `masthead-muted`): wordmark, selected navigation and quieter links against navy.
- **Active Gold** (`active-rule`): a short active/focus navigation rule, not a decorative fill across the page.

### Secondary

- **Recorded Amber** (`verified`, `verified-wash`): incumbent recorded/check and report-provenance treatments. The legacy token name is not permission to label an unreviewed explanation legally verified.
- **Caution Amber** (`caution`, `caution-wash`): unresolved checks, restrictions and highlighted exact quotations. The live source highlight means “cited in this explanation.”

### Tertiary

- **Referral Teal** (`redirect`, `redirect-wash`): helpful out-of-scope/referral notices.

### Neutral

- **Reading Ink** (`ink`) and **Quiet Ink** (`ink-soft`): primary text and supporting metadata.
- **Paper** (`paper`) and **Raised Paper** (`paper-raised`): page ground and bounded reading/control surfaces. “Raised” is a color distinction; it does not require a shadow.
- **Fine Rule** (`border`) and **Strong Rule** (`border-strong`): list separation, control boundaries and pane division.

**The Evidence Meaning Rule.** Color marks selection, provenance or a disclosed check state. A highlighted passage or selected source never establishes legal currentness or independent approval.

## Typography

**Reading and heading font:** Literata, with the frontmatter's serif fallbacks. **Interface font:** Public Sans, with the frontmatter's sans-serif fallbacks. Both families are self-hosted through the imports in `src/index.css`.

Literata makes questions and complete legal text feel deliberate and readable. Public Sans keeps explanatory copy, navigation, controls and numeric reporting direct. There is no separate display or metadata monospace face.

### Hierarchy

- **Headline:** the base page heading. Small screens reduce the base heading to (1.55rem); the report uses its own observed (2rem), reduced to (1.65rem) at its narrow breakpoint.
- **Title:** the base section heading; smaller workspace and report headings retain their component-specific sizes.
- **Question:** the active workspace question; its mobile variant is (1.2rem).
- **Body:** default interface and explanatory text. Generated explanation paragraphs increase their line-height to (1.8).
- **Legal text:** complete provision reading, normally constrained to (70ch). Source-pane legal text uses (.85rem) with line-height (1.85); the Library keeps the frontmatter role.
- **Control, label and metadata:** separate practical roles for actions, field labels and supporting detail. Component-level metadata may be smaller; that is not a new global body size.

Root reading sizes are standard (17px), larger (19px) and largest (22px). Relative units preserve the user's preference. Report numbers use tabular numerals; they remain in Public Sans.

**The Reading Roles Rule.** Keep quoted legal text distinct from generated explanation and interface chrome; do not make every text surface inherit the serif reading style.

## Layout

General pages use lateral gutters (1.5rem), reduced to (1rem) at the small-screen breakpoint. The later workspace rule intentionally removes the old global (76rem) maximum; the Performance report retains its own (76rem) maximum and ordinary reading pages retain (48rem). Do not reintroduce the superseded global cap when extending the workspace.

The chat route occupies (100dvh) with sticky masthead, fixed-height chrome, independently scrolling conversation/source panes and a pinned composer. Desktop columns are `minmax(0, 1fr) minmax(20rem, 34%)`. Reading measures remain bounded within the wider workspace: the welcome is (72ch), a conversation turn (78ch), and legal text (70ch).

At (1000px) and below, the source pane and conversation become explicit alternate views with Sources and Back to chat controls. At (1119px) and below, navigation opens beneath the masthead; the desktop navigation begins at (1120px). At (540px) and below, workspace insets and controls compress while maintaining the implemented (44px) primary control targets. The Library switches between list and reader below (900px).

The report uses a sticky view/language bar, flat overview scores, and detailed tables in labeled horizontal-scroll regions. Its existing responsive thresholds are (1050px), (780px), (640px) and (480px). Rows, wrapping controls and stacked score groups preserve the same information hierarchy. The spacing entries in the frontmatter are recurrent observed intervals, not an instruction to replace the implementation's intermediate values with a new scale.

## Elevation & Depth

The implementation uses no box shadows. Paper/wash contrast, fine borders and spatial separation create depth; source cards do not float above the reading surface. Sticky stacking is functional: masthead (z-index 40), skip link (60), and report view bar (10).

**The Flat Surface Rule.** Use tonal ground and rules to distinguish regions; do not add a shadow to every list row or container.

## Shapes

Most controls and notices have compact, gently curved corners. Citation chips are slightly rounder, and bounded source blocks have the most visible radius. The report's segment controls use smaller nested corners. The high-contrast switch has the observed capsule shape and circular thumb; this is a specific control, not a general pill style.

Use (1px) rules for boundaries and a visible keyboard outline (3px, normally offset 4px). Source-block and pane controls adjust the offset locally so focus remains visible in clipped or scrolling regions. Text fields use strong borders, paper backgrounds and the navy caret. Icons are drawn inline SVG through Lucide; they do not replace accessible text labels.

## Components

### Buttons

Primary and secondary controls share the frontmatter's control typography, compact corner and padding, with a minimum target height (44px). Primary uses navy with white text and deepens on hover; secondary uses paper with navy text and a pale navy hover. Text actions remain underlined. Disabled buttons have reduced opacity (.55) and a disabled cursor. The global visible-focus outline applies to each variant.

State transitions use feedback timing (160ms), with an active press of (1px) over (100ms). Reduced-motion rules remove the press movement. Wider toolbars and the compact composer use their actual component padding rather than forcing the base button dimensions.

### Inputs / Fields

Search, select and composer fields use the existing strong boundary, paper ground and control corner. The pinned workspace textarea uses Public Sans, the frontmatter's input padding, line-height (1.55), minimum height (3.6rem) and maximum height (20dvh). Privacy options are a named disclosure below it; checked state is visible in native controls with navy accent.

### Navigation

The navy masthead carries muted links; hover and active links use the lighter navy surface and paper text. Active weight (600) and a short gold rule work together. The rule appears on keyboard focus too. The narrow menu is an explicit toggle rather than squeezed desktop links. The Performance page has its own underlined Overview / Detailed results navigation and preserves selected filters across those views.

### Chips

Reference chips are outlined, compact actions with a numbered pale-navy square. They open a specific response's candidate/source block. The number, document label, focus and source context make the relationship visible without implying a verification badge.

### Cards / Containers

Bounded source blocks use raised paper, strong border, the source-block radius and no shadow. A full-width header toggles the content, rotates its drawn chevron, and exposes a persistent recorded/unreviewed status. Expanded border color changes to navy. Diagnostics and use restrictions remain named disclosures. History uses flat ruled rows; it does not inherit the source card treatment.

### Example questions

Examples are ruled rows with serif question text and a quiet topic line. Hover/focus adds the navy wash and advances a drawn action icon (4px); selected rows retain the wash without movement. The workspace uses the frontmatter's compact row padding. These are reusable query starters, not repeated feature cards.

### Citation and quotation reading

Generated explanations reveal by word with a Show full answer control. Screen readers receive the full paragraph immediately; a reduced-motion preference or hidden document completes the reveal. Citation controls stay available and select the response, concern and matching chunk. Mobile source navigation restores focus to the invoking control when returning.

Exact quote spans are highlighted inside the complete stored provision, using the caution wash and reading ink. The Library's arrival spotlight is a separate, temporary navigation cue (1600ms), with a static wash under reduced motion. Neither cue changes the recorded check status. Keep source dates, use restrictions and full legal text visible within the existing reading pattern.

### Report controls

Report segments select topic/coverage or counts/row percentages. Correct matrix cells use navy; confused cells use caution wash; selected cells add an outline. Plain-language scores precede detailed class tables, routing and confidence inspection. Development provenance belongs beside the metrics; operational replay counts and cost must remain distinct from accuracy.

## Do's and Don'ts

### Do:

- Do retain the navy/paper identity and the Literata/Public Sans reading roles.
- Do use fine rules and spacing to structure history, reports and long-form reading.
- Do preserve complete source text, named response context and visible limitations when adding evidence interactions.
- Do keep keyboard focus, enlarged text, high contrast and reduced-motion behavior usable in every added state.
- Do bind component previews to the existing CSS variables so reading preferences remain effective.

### Don't:

- Don't turn citation selection, amber highlighting or the legacy verified token name into a claim of current legal approval.
- Don't add decorative eyebrow labels, gradient lettering, hard offset shadows or a repeated identical-card layout.
- Don't use ornamental load/scroll motion; motion should respond to a control or explain a state change.
- Don't replace the full-width workspace with the superseded global maximum-width rule.
- Don't present generated development checks, availability or estimated provider spending as independent legal-answer accuracy.
