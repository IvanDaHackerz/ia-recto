# Classifier-only backend

This is a local classifier API around `item10-classifier-v1.5.15`. It preserves the original English/Taglish question and returns the primary and scope labels, their existing calibrated probabilities, supported/excluded components, routing, clarification and referral candidates. Conservative local spelling/boundary features precede concern detection; the original message is not replaced in API output. It performs no legal retrieval, LLM calls, answer generation, website changes or conversation persistence.

The implementation repairs were informed by inspected development cases. A 424-input development comparison now reports F1, accuracy, calibration, routing and retrieval checks separately from software tests. The application adapter now connects classification to the website, retrieval and optional development explanations; this classifier-only API remains a separate contract. Fresh independent human questions and formal acceptance remain pending. [Current results and limitations](../../outputs/normalization-repair-v2.0.0/REPORT.md).

## Python interface

`ClassifierService.classify({"question_text": "Original wording", "request_id": "optional-id"})` is the integration entry point. The optional ID contains at most 64 letters/digits/dots/colons/underscores/hyphens. Other input fields are rejected. User input cannot choose models, files, labels, thresholds, approvals or permissions.

`config.json` pins the trusted model manifest, runtime/source hashes, exact dependencies and inherited thresholds. The model loads once. Every call checks integrity again; changed files require an explicit rebuild/restart. The original source datasets and learned weights are preserved. Do not load client-supplied pickle/joblib files.

## HTTP interface

| Endpoint | Purpose |
|---|---|
| `GET /health` | Current classifier readiness/version; no evaluation claim |
| `GET /v1/contract` | Versioned request/response JSON schemas |
| `POST /v1/classify` | Classify a strictly validated JSON request |

The server binds only `127.0.0.1`. Browser origins are denied unless the operator supplies exact allowed origins. Connections are bounded and request reads have a timeout. It rejects duplicate/non-finite JSON, unknown fields, invalid UTF-8/control characters, oversized input, ambiguous content lengths and unsupported encodings. Questions are not written to access logs or error messages. Responses are not cached. This development adapter needs an agreed deployment/authentication/retention design before later external hosting.

The 8,000-character and 65,536-byte limits are input limits, not evidence or confidence thresholds. Empty input is accepted and returns clarification. Missing deciding facts, unresolved concerns, excessive complexity and insufficient confidence remain clarification routes. Classification never grants permission to display a substantive legal answer.

## Response semantics

`classification` carries label probabilities, not legal-answer confidence. `scope_constraint` is the name of a matching transparent scope rule; positive context rules are not invented taxonomy-topic predictions. Uncalibrated atomic evidence scores are not published as confidence metrics.

`routing.retrieval_requests` contains only supported component queries and domains when the classifier admits retrieval. Each request retains a local `component_id`. Excluded components have `retrieval_allowed=false`. Clarification and referral-only routes emit no retrieval requests. An admitted retrieval request still requires the separate retrieval/evidence/verifier stages before any answer.

Referral objects remain candidates with their original contact-check dates and `requires_contact_refresh=true`. The adapter does not promote them to newly verified contact details. `permissions.answer_generation_allowed`, `display_answer_allowed` and `deployment_allowed` stay false.

## Operator commands saved for later use

Use the pinned environment from the project root. These are documentation, not a request to start testing or integration now.

```powershell
.venv-item10/Scripts/python.exe -m backend.classifier.server
.venv-item10/Scripts/python.exe -m backend.classifier.server --allow-origin http://localhost:5173
```

No persistent server is started by installation or packaging. Software tests start temporary loopback servers and shut them down afterward. The website has not been connected.

`build_config.py` generates a new operator configuration from a trusted checksummed classifier. `check_implementation.py` writes API software-test logs into a new check directory. Formal evaluation and metric presentation are later steps; no per-question F1 score or combined legal-confidence score is supplied.
