# Item 10 question-review guide

## What this review is for

The five reviewer workbooks contain all 672 synthetic questions created in Item 9. Each question already has a proposed classification. Reviewers check two things:

1. Does the question sound clear and natural in English or Taglish?
2. Does the proposed classification correctly describe what the Recto & Co. Legal MVP may handle?

Reviewers are **not** answering the legal question. They are reviewing the quality of the question and its labels.

The approved MVP languages are English and Taglish. The original Item 9 dataset must remain unchanged. Human decisions are recorded only in the Item 10 reviewer workbooks.

## Files and assignments

There are five files:

- `item10_reviewer_1.xlsx`
- `item10_reviewer_2.xlsx`
- `item10_reviewer_3.xlsx`
- `item10_reviewer_4.xlsx`
- `item10_reviewer_5.xlsx`

Each group member edits only the workbook assigned to them. Related versions of the same scenario remain in the same workbook.

Do not move individual questions between files. Do not create another editable copy of an assigned workbook.

## Workbook tabs

Each workbook contains:

- `Review Queue` — the questions and reviewer-input fields;
- `Instructions` — the reviewer-name field and short instructions;
- `Progress` — assigned, completed, discussion, and rejected counts;
- `Topic Guide` — supported and excluded project topics;
- `Referrals` — permitted government referral destinations; and
- `Source Data` — the untouched Item 9 records for reference.

Reviewers normally edit only:

- the yellow reviewer-name cell in `Instructions`; and
- the yellow fields in `Review Queue`.

Do not edit `Progress`, `Topic Guide`, `Referrals`, or `Source Data`.

## Step 1: Enter the reviewer name

Open `Instructions` and type the reviewer's full name in the yellow cell beside **Reviewer name**.

Enter the name once. The workbook automatically places it on every review row.

Do not type a name directly into the `Reviewer` column in `Review Queue`.

## Step 2: Read the proposed question and classification

Open `Review Queue` and read the reference fields on the left:

- Question ID
- Original question
- Language
- Proposed label
- Proposed scope
- Proposed topics, action, and referral

These fields describe the Item 9 machine-generated proposal. Read them, but do not change them directly.

Only use the yellow fields to record corrections.

## Step 3: Choose the wording decision

Complete **Wording decision** for every row.

### Choose `Keep as written`

Use this when the question:

- is understandable;
- sounds reasonably natural;
- clearly expresses its concern;
- is acceptable English or Taglish; and
- does not need rewriting.

If you choose `Keep as written`, leave **Revised question** blank.

Example:

> The seller refuses to honor the warranty. What should I do?

Informal wording is acceptable when it resembles how a real user might speak. Do not rewrite every informal question into formal legal English.

### Choose `Revise wording`

Use this when the intended situation is understandable, but the wording is awkward, unnatural, confusing, or grammatically poor.

If you choose `Revise wording`, enter the **complete replacement question** under **Revised question**.

Original:

> Allowed po ba ito: seller no give warranty even product broken?

Acceptable revision:

> Allowed po ba na hindi i-honor ng seller ang warranty kahit defective ang product?

Do not write only an editing instruction such as “change no give to refuses.” Write the complete final question.

Preserve the original situation. Do not add a new legal issue, remove an important issue, or invent facts.

### Choose `Reject wording`

Use this when the question cannot be repaired without changing its purpose.

Possible reasons include:

- its meaning is completely unclear;
- it duplicates another question without adding a useful variation;
- it is nonsensical or unrealistic;
- it is outside the approved English-and-Taglish language scope;
- it contains contradictory situations; or
- rewriting it would create a different question.

If you choose `Reject wording`:

- normally leave **Revised question** blank;
- choose `Rejected` as the final Review outcome; and
- explain the reason in **Notes**.

Do not reject a question only because it uses informal grammar or ordinary Taglish.

## Step 4: Choose the label decision

Complete **Label decision** for every row.

### Choose `Labels correct`

Use this when the proposed primary label, scope, topics, action, and referral correctly describe the question.

When the labels are correct, leave these fields blank:

- Correct primary label
- Correct scope label
- Topic or referral corrections

Do not re-enter the same labels.

### Choose `Change labels`

Use this when the proposed classification is wrong and you know the correction.

Complete:

- **Correct primary label**; and
- **Correct scope label**.

If the proposed topic or referral is also wrong, explain the correction under **Topic or referral corrections**.

Example:

The question concerns unpaid salary but was proposed as `consumer`.

- Correct primary label: `labor`
- Correct scope label: `fully_supported`
- Topic or referral corrections: `This is an unpaid wage concern and should use the wage-payment topic and DOLE referral.`

Plain language is enough. Reviewers do not need to memorize technical topic or referral IDs.

### Choose `Unsure`

Use this when you cannot confidently determine the correct classification.

Then:

- leave the corrected-label fields blank;
- choose `Needs group discussion` as the Review outcome; and
- explain the exact uncertainty in **Notes**.

Example note:

> I am unsure whether this is an ordinary online consumer complaint or criminal online fraud because the seller disappeared after receiving payment.

Do not guess merely to finish a row.

## Step 5: Understand the primary labels

### `labor`

Use when the question contains only supported private-sector labor issues.

Examples include unpaid wages, hours of work, rest days, overtime, holiday pay, thirteenth-month pay, employment contracts, basic termination procedure, final pay, and labor-complaint referrals.

### `consumer`

Use when the question contains only supported consumer issues.

Examples include defective products, warranties, repair or replacement, refunds, misleading advertising, displayed prices, product safety, service complaints, ordinary online purchases, and DTI complaint procedures.

### `mixed`

Use in either situation:

1. supported labor and supported consumer issues appear together; or
2. a supported issue appears together with an excluded issue.

Example of fully supported mixed:

> My employer did not pay my overtime, and a shop refuses to replace my defective appliance.

Example of partially supported mixed:

> An online seller refuses my refund, and my bank also charged an unauthorized fee.

### `out_of_scope`

Use when no supported issue appears.

Examples include banking-only disputes, insurance, investments, government employment, OFW concerns, seafarer concerns, pending-case strategy, pension computations, medical malpractice, data privacy, telecommunications, and requests to predict whether someone will win a case.

Do not use `out_of_scope` merely because a question is vague. If its meaning is unclear, use `Needs group discussion` or reject the wording instead of inventing a classification.

## Step 6: Understand the scope labels

### `fully_supported`

Every important issue in the question falls within the approved MVP scope.

A question containing supported labor and supported consumer issues can still be fully supported.

### `partially_supported`

At least one issue is supported and at least one issue is excluded.

Example:

> The online seller refuses my refund and also exposed my personal information.

The refund issue may be supported, but data privacy is excluded.

### `unsupported`

None of the important issues is covered by the MVP.

Example:

> How much will my SSS pension be?

## Step 7: Record topic or referral corrections only when needed

Complete **Topic or referral corrections** only when the proposed topic, action, or referral is wrong or incomplete.

Good examples:

> This should use product warranty, not misleading advertising.

> The banking portion should be referred to BSP.

> This concerns a government employee, so the referral should be CSC rather than DOLE.

Leave the field blank when no correction is needed.

Do not enter:

- the answer to the legal question;
- personal opinions;
- invented agencies;
- unverified telephone numbers, email addresses, or links;
- case-outcome predictions; or
- long legal explanations.

## Step 8: Choose the final Review outcome

Complete **Review outcome** for every row.

### Choose `Approved`

Use when the wording and labels are correct without changes.

Normal combination:

- Wording decision: `Keep as written`
- Revised question: blank
- Label decision: `Labels correct`
- Corrected labels: blank
- Review outcome: `Approved`
- Notes: blank unless a short explanation is useful

### Choose `Revised approved`

Use when the reviewer corrected the wording or labels and the row is now usable.

Wording revision example:

- Wording decision: `Revise wording`
- Revised question: complete replacement question
- Label decision: `Labels correct`
- Review outcome: `Revised approved`

Label correction example:

- Wording decision: `Keep as written`
- Label decision: `Change labels`
- Correct primary and scope labels: completed
- Review outcome: `Revised approved`

### Choose `Needs group discussion`

Use when a genuine uncertainty remains.

Explain the uncertainty in **Notes**. Do not use this merely because a question takes time to read.

### Choose `Rejected`

Use when the question should not be included in classifier training.

Explain the reason in **Notes**.

Examples:

> Duplicate of another question with no meaningful wording difference.

> The wording is too unclear to determine the intended issue.

> The question is outside the approved English-and-Taglish scope.

## Step 9: Follow the Row check message

The final column is calculated automatically. Do not type into it.

It may display:

- `Set reviewer name`
- `Choose wording decision`
- `Choose label decision`
- `Choose outcome`
- `Add revised question`
- `Use Rejected outcome`
- `Add corrected labels`
- `Use group discussion`
- `Mark what changed`
- `Add decision note`
- `Ready`

A row is finished only when **Row check** says `Ready`.

If it displays another message, complete or correct the field identified by that message.

## What must be blank and when

| Situation | Fields that should stay blank |
|---|---|
| Wording is kept | Revised question |
| Labels are correct | Correct primary label, Correct scope label, Topic or referral corrections |
| Reviewer is unsure about labels | Correct primary label and Correct scope label |
| No topic or referral correction is needed | Topic or referral corrections |
| Simple approval with no special concern | Notes |
| Wording is rejected rather than repaired | Revised question |

Do not type filler such as `N/A`, `none`, `same`, or `okay` into fields that should remain blank.

## Four common completed-row examples

### Example 1: Everything is correct

- Wording decision: `Keep as written`
- Revised question: blank
- Label decision: `Labels correct`
- Correct primary label: blank
- Correct scope label: blank
- Topic or referral corrections: blank
- Review outcome: `Approved`
- Notes: blank

### Example 2: Only the wording needs correction

- Wording decision: `Revise wording`
- Revised question: complete rewritten question
- Label decision: `Labels correct`
- Correct labels: blank
- Review outcome: `Revised approved`
- Notes: optional

### Example 3: The classification is wrong

- Wording decision: `Keep as written`
- Revised question: blank
- Label decision: `Change labels`
- Correct primary label: completed
- Correct scope label: completed
- Topic or referral corrections: completed only if needed
- Review outcome: `Revised approved`

### Example 4: The reviewer is uncertain

- Wording decision: the honest wording assessment
- Label decision: `Unsure`
- Correct labels: blank
- Review outcome: `Needs group discussion`
- Notes: explain the uncertainty

## Things reviewers must not do

Reviewers must not:

- answer the user's legal question;
- provide legal advice;
- predict whether someone will win a case;
- add names, employers, addresses, account numbers, case numbers, or other identifying information;
- change the Question ID;
- edit the original question directly;
- edit the proposed labels directly;
- delete or add rows;
- alter the Source Data tab;
- translate every Taglish question into formal English;
- invent government agencies or contact details;
- force a label when genuinely uncertain; or
- mark a row complete while Row check still shows a required action.

## Finishing and returning a workbook

Before returning a workbook:

1. Open `Progress` and confirm that every assigned row is ready.
2. Resolve straightforward missing fields.
3. Leave genuine discussion rows marked for group discussion; do not guess.
4. Keep the original filename.
5. If reviewing in Google Sheets, download the finished file as Microsoft Excel (`.xlsx`).
6. Return the downloaded workbook to the project owner.

The project owner will collect all five files. A consolidation pipeline will verify the Question IDs, collect discussion rows, exclude rejected rows from training, and create the frozen reviewed Item 10 dataset.

## Quick consistency table

| Primary label | Supported issues | Excluded issues | Scope label | Normal system action |
|---|---|---|---|---|
| `labor` | Labor only | None | `fully_supported` | Answer supported labor issue |
| `consumer` | Consumer only | None | `fully_supported` | Answer supported consumer issue |
| `mixed` | Labor and consumer | None | `fully_supported` | Answer both supported parts |
| `mixed` | One or more | One or more | `partially_supported` | Answer supported part and refer the rest |
| `out_of_scope` | None | One or more | `unsupported` | Decline substantive answer and refer |

## Final reviewer checklist

Before considering a row finished, confirm:

- The wording decision is selected.
- A complete revised question is present when wording was revised.
- The label decision is selected.
- Correct primary and scope labels are present when labels were changed.
- Topic or referral corrections are included only when needed.
- The final Review outcome is selected.
- Discussion and rejected rows contain an explanation.
- The Reviewer field shows the correct name.
- Row check says `Ready`.
