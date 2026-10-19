# Design Guide — [Project Name] (Legal Rights Assistant)

## Purpose of this doc
This is not a generic "clean UI" checklist. Every choice below is made *because* of what this
product is: a trust-critical, government-adjacent, citation-driven tool for ordinary Filipinos
who may be stressed, confused, or skeptical when they arrive. Design decisions should trace
back to that, not to "what looks like a nice app."

---

## The 5 AI-slop patterns to actively avoid

Before anything else, actively check your design against these. They are the most common
tells of a templated, unconsidered layout — not because they're bad in isolation, but because
they show up regardless of the subject matter, which means they weren't actually chosen for
this one:

1. **Warm cream background + high-contrast serif + terracotta/clay accent** (~#F4F1EA bg,
   ~#D97757 accent). This is a specific, recognizable AI-generated-page signature. Avoid it here.
2. **Near-black background with one acid-green or vermilion accent.**
3. **Broadsheet/newspaper look**: hairline rules, zero border-radius, dense identical columns —
   wrong register for this product anyway (we are not a magazine, we are a public service tool).
4. **The SaaS-card kit**: everything chopped into identical rounded cards, one border-radius
   used everywhere with no hierarchy, the same soft grey box-shadow under each card, gradient
   washes as pure decoration.
5. **Template chrome**: ALL-CAPS tracked-out eyebrow labels above every heading, meta text
   joined with middle dots ("A · B · C"), "WORD — fragment" labels with em dashes, fake-black
   (#0B0B0B/#111) instead of real black, monospace for small data labels, "→" tacked onto every
   button/link.

If you catch yourself reaching for any of these because "that's just what a modern web app
looks like" — stop. That's exactly the reflex this list exists to interrupt.

---

## Ground the design in what this actually is

This is **not** a SaaS product, a startup landing page, or a chatbot novelty app. It is closer
in spirit to a **public service counter** — like a well-run government window, a legal aid
clinic, or a library reference desk. The person arriving may be anxious (just got fired,
scammed, or denied a refund) and needs to feel: *this is credible, this is calm, this will
not waste my time or mislead me.*

Design cues to draw from (for inspiration, not literal copying):
- Philippine government service portals that are done well (clear hierarchy, plain language)
- Legal aid / public library reference interfaces — quiet, functional, text-respecting
- Reference/documentation tools (the citation panel is core UI, not an afterthought)

Avoid cues from: consumer AI chat apps, startup pitch decks, crypto/fintech dashboards. Those
carry the wrong emotional register for someone asking "can my employer fire me without notice."

---

## Color

Pick 4–6 named hex values *deliberately*, not defaults. Suggested direction (adjust to taste,
but keep the reasoning):

- A **grounded, non-neon primary** — deep blue, forest green, or ink navy reads as institutional
  trust without being cold. Avoid bright "tech blue" (#0066FF-style) — reads as generic SaaS.
- A **neutral paper-like background** — not stark white (#FFFFFF, harsh), not cream-AI-slop
  (#F4F1EA). Try an off-white with a very slight cool or warm cast, e.g. #FAFAF8 or #F7F8F7 —
  test both, pick by what suits your primary color, not by which sounds nicer as a hex.
- A **real black or near-black for text** — #1A1A1A or similar, not pure #000, not fake-black.
- **One accent color, used sparingly** — for the "in force" / verified / active states.
  Avoid orange/terracotta (see slop list). Consider a warm gold or amber for "verified/cited"
  moments specifically — ties visually to the idea of an official stamp or seal.
- A **distinct, unmistakable color for the out-of-scope / decline state** — this state matters
  a lot in your system (graceful refusal), so it deserves its own visual treatment, not just a
  grey "error" box. Should read as "helpful redirect," not "failure."

## Typography

- One or two typefaces, clearly distinct if two.
- For a legal/civic tool, a **well-set serif for body/reading content** is a legitimate,
  justified choice (not a slop default here) — it signals "this is meant to be read carefully,"
  which fits legal text. Pair with a clean, plain sans-serif for UI chrome (buttons, labels, nav).
- Avoid decorative or "friendly startup" typefaces (rounded geometric sans like Poppins/Quicksand-
  style) — wrong tone for legal content.
- Line length under ~80 characters for body text; slightly more line-height for serif body copy.
- **Do not** use ALL-CAPS labels, single-word bold/italic/color accents inside headlines, or
  unnecessary eyebrow labels above headings — these are on the slop list above.

## Layout

- The **query input** should be the clear hero — simple, generous, uncluttered. Not a hero
  image, not a marketing headline. The product's job starts the moment someone can type.
- The **response + citation side panel** is core structural content, not a "feature card."
  Treat it like a reading interface (think: annotated legal reference), not a chat bubble UI.
- Avoid identical rounded cards for everything. Structure should reflect actual content
  hierarchy: a legal citation is not visually the same "kind of thing" as a chat history item —
  don't let them default to the same card treatment just because that's the templated pattern.
- Left-aligned, text-respecting layout is likely right for this content (legal reading, forms) —
  avoid heavy centered/marketing-style layout blocks.

## Motion

- Minimal. One deliberate moment (e.g., the response appearing after a query) is enough.
- No fade-and-slide-up on every section, no hover-lift on every card — this is the most common
  AI-generated-page tell in motion design specifically.
- Motion should answer something the user did (submitted a query, expanded a citation) —
  not decorate the page on load or scroll.

## Writing / copy inside the UI

- Plain, calm, active voice. "Ask your question" not "Get Started Now."
- The decline/out-of-scope message should sound like a helpful redirect, not an apology or
  a system error. E.g., "This is outside labor and consumer law — try [PAO/DOLE/DTI] for this."
  Not: "Sorry! I couldn't process that request. ⚠️"
- Never editorialize or oversell. No "empowering," "revolutionary," "AI-powered legal genius"
  language — undermines the trust register this product needs. Say what it does, plainly.
- Citations and legal text should look and read as *quoted source material*, distinct
  typographically from the plain-language explanation around them.

## Accessibility (non-negotiable, not decorative)

- Real semantic HTML — headings, labels, buttons as actual elements, not styled `<div>`s.
- Visible keyboard focus states on every interactive element.
- Sufficient color contrast (check your palette against WCAG AA at minimum — especially your
  accent color against your background).
- Respect `prefers-reduced-motion`.
- Adjustable text size and a high-contrast mode toggle, as already scoped in the proposal.

## Before you ship any screen, ask:
1. Would this design look the same if the subject were a recipe app instead of a legal tool?
   If yes — it's not grounded in the actual content, go back.
2. Did I pick this color/font/layout because of this brief, or because it's what I'd reach
   for on autopilot?
3. Is there one clear "memorable" element, with everything else quiet around it — or is
   everything competing for attention equally (a sign of no real hierarchy)?