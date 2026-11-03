# Before the presentation

1. From the VS Code PowerShell terminal in `C:\IA`, run `.\start-website.ps1`. Use the exact URL printed by the launcher; it skips an occupied port.
2. Confirm **Use AI explanations** is on. Keep **Save questions** off for fictional practice questions.
3. Try a labor question, a consumer question, a mixed question and an outside-scope question. English, Taglish and noisy forms are in [QUESTIONS.md](QUESTIONS.md).
4. Open a citation and inspect the complete stored provision. Explain that a checked quotation proves the stored span matches; it does not certify all current law or the person's legal outcome.
5. Open the question's diagnostic details. Topic and coverage confidence measure label certainty. Accuracy and F1 require a labeled batch; a single new question has neither score.
6. Show that outside-scope parts are identified rather than answered using unrelated labor/consumer sources. A mixed question may receive an explanation only for its supported parts.
7. If the provider fails or a draft fails checks, show the recorded-source fallback and diagnostic reason. Do not present a fallback as a generated, verified legal answer.
8. Before submission, have another person try their own questions and record any surprising result. This engineering study uses AI-authored questions and cannot replace independent human or professional legal review.

The report and all original failures are retained in this folder. Repeated testing after a repair is a development regression result, not an untouched test-set score. No publishing or Git push was performed as part of this task.
