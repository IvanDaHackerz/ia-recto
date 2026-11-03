# First-pass engineering reading

All 100 fictional responses were inspected. This is AI engineering review, not independent human or legal review. Frozen expectations and raw completions remain unchanged.

The initial run returned all 100 packets, with 41 generated, 6 partially generated and 53 withheld explanations. Withholding on an excluded concern is expected; these status counts are not accuracy. All 156 displayed citations had exact spans and source identities, yet the reading found substantive failures.

| Failure family | Examples | Repair direction |
| --- | --- | --- |
| Setup and follow-up split into extra concerns | 001, 002, 010, 013, 015, 023, 026, 028, 029, 031, 034, 036–038, 042, 043, 045, 047, 049 | Preserve fragment accounting; group the same scenario and its question; keep independent actors separate. |
| Words changed into other meanings | 024 accounting, 031 role, 035 charging, 041 proved; prior regression put | Preserve common words and inflections while retaining compressed scope aliases. |
| Wrong source regime | 006 waiting time; 017 project employment; 020 closure; 033 correction remedies; 034/050/064 safety versus quality; 045 online return versus warranty; 046 platform redress versus ODR development; 047 order change versus cash change; 051 shelf label; 059 overheated power strip; 074 dismissal procedure | Repair concept-level source relevance and context retention; do not promote held sources. |
| Incorrect scope or abstention | 018 seasonal; 019/055 hotel/clinic dismissal; 048 overheating; 062/079 government employment; 075 three-way concern; 076 exact minimum daily wage; 086 prediction-only; 093 privacy-only; 096 transport | Explicit relationship and scope constraints; preserve probabilities and uncertainty. |
| Accepted explanation omitted conditions | 021 Regional Director money-claim jurisdiction; 022 exceptions to mandatory conciliation; 074 just versus authorized causes | Preserve the source conditions in deterministic checks and generation instructions. |
| Accepted explanation crossed scope | 068 extended retail civil liability to a privacy complaint | Exclude unrelated allegations from supported explanation prompts; reject privacy advice in retail prose. |
| Accepted explanation treated allegation as finding | 041 unsubstantiated certification; 049 damaged seal therefore falls within prohibitions | Preserve conditional language and reject explicit case findings. Same-model checking remains fallible. |
| Avoidable mechanical withholding | 032 equivalent parties-may-adjust wording; 033/046 temporal first; 039 repeated prose locators | Accept equivalent source wording, distinguish procedural adverbs from quantities, instruct citation fields only. |

Case PH2_057 is also ambiguous: its construction-contract fragment does not establish an employment relationship. The original frozen expectation assumes employment. Its mismatch stays in the original score; the repair asks for clarification instead of silently dropping the fragment. See expectation-review.json.

Known evidence gaps (counted briefing/waiting time, meal-break rule, final pay, COE and the required related 13th-month authority) remain source limitations. They are not resolved by lowering a classifier threshold. Provider timeouts in 011 and 047 are retained as failures to complete AI responses; useful local material remained available.
