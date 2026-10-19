# Local question inspector

Current bindings: classifier v1.5.15, retrieval v1.3.1 and verifier v1.0.9. This terminal inspector checks classification, optional wording interpretation and sources. The website application adds source-selected explanations/support checking, privacy choices and optional encrypted history; terminal results do not claim that those website stages ran.

From PowerShell:

```powershell
Set-Location C:\IA
& .\.venv-item10\Scripts\python.exe -m backend.terminal_test
```

Wait for **Ready**, then type a question at `Question>`. The pinned local classifier, retrieval index and verifier load once. No web server or browser is required. Clear questions work locally without an API key. The default conditional wording layer can interpret whole sentences with unfamiliar spelling, joined words and messy grammar. It can also activate after an unresolved local inspection with several unfamiliar words. Its setup and limits are in [NORMALIZATION.md](NORMALIZATION.md). Without configuration, flagged shorthand asks for fuller wording. Use `--normalization off` for the original local-only baseline. The inspector uses the normal current-guidance preflight; it does not supply approvals or bypass source checks.

It shows topic and scope label confidence, retrieval/clarification/referral routing, excluded concerns, up to five candidate provisions per supported concern, source links, recorded status dates, source-gate reasons, and measured total query time. Timing includes classification, retrieval and preflight integrity checks, excludes initial model loading, and is not classifier-only latency. When conditional normalization runs, total time also includes that request and the normalizer time is reported separately.

If the route is clarification, model topic/coverage labels are marked **tentative**. A low-confidence `Out of scope` label on that route is not a final exclusion. Explicit employer/payment wording can select a more relevant follow-up about salary and work arrangement; `/json` keeps the pinned verifier result unchanged and records that follow-up separately. The wording layer cannot supply a missing private-sector employment fact.

Try these in separate turns:

```text
The cashier charged more than the displayed price.
Private employee ako. Hindi binabayaran yung overtime ko.
My employer hasn't paid my salary. What can I do?
A store refuses my warranty. Separately, it published my home address online.
Municipal employee ako. Delayed ang sahod ko. Ano ang civil service remedy?
```

These are inspected development examples, not independent holdout questions. Questions are processed independently; the tool is not a conversational memory system. If clarification is requested, submit the full question again with the missing facts supplied.

For example, `inde ako nakoha yung bayad ako sa amu ako... anu pwede gawin.,?` should correct the known spellings and ask what payment and employment arrangement you mean. If the true facts are private-company employment and unpaid salary, a full follow-up could be `Private employee ako. Hindi ko nakuha ang sahod ko. Ano ang puwede kong gawin?` Supply your actual facts. Restart an already-running inspector after code updates: `/quit`, then run the command above again.

Commands:

| Command | Purpose |
|---|---|
| `/full 1` | Complete stored provision for result 1 from the last question |
| `/json` | Complete last inspection, including source metadata and gate reasons |
| `/help` | Help |
| `/quit` | Exit; Ctrl+C also works |

The initial excerpt is a shortened preview, not the whole provision. A retrieval score is a ranking value, not a confidence percentage. Confidence is for predicted labels, not legal-answer correctness. Finding a provision does not establish sufficient/current support. `scoped_currentness_review_missing` is expected while the real trusted-review store is empty. The inspector does not generate or approve legal answers.

No conversations or results are automatically written to disk, no training occurs, and existing versioned artifacts are not changed. If conditional normalization is configured and triggered, the LLM provider receives the original question for context; otherwise this path stays local. Terminal scrollback remains visible. Explicit shell redirection saves what you choose to redirect.

One-question commands:

```powershell
& .\.venv-item10\Scripts\python.exe -m backend.terminal_test --query "The cashier charged more than the displayed price."
& .\.venv-item10\Scripts\python.exe -m backend.terminal_test --query "The cashier charged more than the displayed price." --json
```

## Aggregate metrics are a separate evaluation

A newly typed question has no known expected label/provision judgment, so the inspector does not manufacture accuracy, F1 or retrieval relevance scores. For aggregate metrics, run the existing pinned evaluator against labeled cases. Each run requires a new directory:

```powershell
$terminalEvalPath = "C:\IA\outputs\terminal-development-eval-$(Get-Date -Format 'yyyyMMdd-HHmmss-fff')"
& .\.venv-item10\Scripts\python.exe .\dataset\pipelines\item13\runner.py --output $terminalEvalPath
```

This prepares/freezes inputs before inference and evaluates the current compatible stack on 291 reused AI-authored development cases. It writes `metrics.json`, `results.csv`, `predictions.jsonl` and `error_log.jsonl`; original runs are preserved. It measures classification accuracy/F1, calibration, routing, judged retrieval and system checks with the recorded development uncertainty method. It makes no LLM calls, adds no independent human gold and does not measure generated-answer accuracy. The interactive tool's software checks are separate:

```powershell
& .\.venv-item10\Scripts\python.exe -m unittest backend.test_terminal_test -v
```


For the latest comparison and remaining cases, see [the repair report](../outputs/normalization-repair-v2.0.0/REPORT.md). The classifier now uses local spelling/boundary features before checking the original question; only unresolved wording can trigger the LLM. Restart the inspector to load the repaired stack and v3.0.0 normalizer. The ordinary terminal does not enable rejected-proposal capture; explicit development batch studies do. A failed payment rewrite can receive a targeted Tagalog context question without accepting or classifying the unsafe wording. Website integration and formal acceptance remain pending.
