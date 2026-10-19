# Local release and deployment handoff

This release is a local development preview. `deployment_allowed` remains false. A working loopback website is not evidence of independent legal accuracy or public-service readiness.

## Reproduce the local environment

Use Windows, Python 3.12 and Node.js 24 with npm. `CURRENT_ARTIFACTS.json` selects immutable classifier/retrieval/verifier packages. From a complete release folder, run `setup-project.ps1` for a new environment only. It installs the package's pinned Python dependencies and `npm ci`, then checks the actual runtime hashes. It never overwrites an environment, retrains the classifier, approves sources or changes thresholds.

The local multilingual encoder must match `models/embedding_backbone_manifest.json`. A release made with `--include-model` preserves its exact bytes. Otherwise `setup-project.ps1 -DownloadEmbeddingModel` can download public model files; the subsequent integrity check must pass. A newer upstream model cannot silently replace this release's model. Restore the archived exact cache if hashes differ.

Run `check-project.ps1` for offline software checks and metric reconciliation; its HTTP tests bind temporary loopback ports. Dependency advisory checks need internet. Run `start-website.ps1`, then use the printed URL. Occupied ports are skipped and only an API with the current project/runtime signature is reused. The launcher stops only its own child API on exit. An already running Vite process may keep its original proxy target; restart that session after upgrading the runtime.

## Private state and recovery

`scripts/release_snapshot.py` creates a checksummed source/runtime ZIP from an explicit allowlist. By default it omits credentials, history, usage databases, `.git`, installed dependencies, discovery bulk data and model caches. `--include-model` adds only files pinned in the embedding manifest. Extraction verification does not replace a fresh dependency installation.

Stop the local API before a private-state backup. If history recovery is desired, separately copy `.local/website/history.sqlite3` **and** `.local/website/session.key.dpapi` to a protected location. Both require the original Windows-user DPAPI identity; copying to another machine/account may not decrypt them. The original browser's signed cookie is also required. Test a private backup under that identity before relying on it. Do not add it to source control or a shareable release. There is no cloud backup or account recovery.

History is opt-in, capped at 500 turns per browser owner, and expires after 30 days; expiry cleanup occurs on store access. Exported JSON is plaintext. Deletion and expiry are application/SQLite operations, not a guarantee of forensic erasure from OS/disk backups. Temporary deduplication entries have a five-minute reuse window and are discarded on subsequent registry cleanup or restart.

The usage ledger is local and can be reset by an operator; it is not provider billing enforcement. Configure provider-side spending limits too. Existing requests may already have been processed or billed when canceled. The key previously pasted into chat should be replaced in the Together account and reconfigured with `python -m backend.normalizer_credentials`; rotation has not been performed or claimed by this release.

## Before public deployment

The standard-library loopback API and Vite dev server must not be exposed directly. A production design needs a supported application server, HTTPS reverse proxy, secure cookies, authenticated history ownership, exact origins, per-user and global abuse controls, request cancellation propagation, protected secrets, approved retention/consent, monitoring without raw question logs, and tested backup/restore. Keep model/joblib files server-owned and checksum-pinned. Serve frontend assets and API on the same origin; no browser API key.

Complete the source/currentness and claim-support review queues, fresh independent-human evaluation, legal-professional review, user/accessibility assessment and owner/adviser acceptance before opening the legal-answer/deployment gates. A same-model support judge and successful software tests cannot grant those approvals. Required sign-offs and actual hosting credentials remain owner/expert work; no public deployment was performed.
