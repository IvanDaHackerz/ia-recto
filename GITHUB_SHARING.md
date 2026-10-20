# Share the runnable project with the group

Use a **private GitHub repository** for the current development prototype. The
curated list includes application code, trained artifacts and required provenance,
canonical sources, recorded evaluation files, dependency locks and setup scripts.
It omits the bulk discovery corpus and some historical research. Keep a separate
research backup if reproducing data collection/training is needed later.

Never upload `.local`, API credentials, saved questions, virtual environments,
`node_modules`, the downloaded encoder cache or ZIP backups. Do not globally
ignore logs: some versioned output logs are required by integrity manifests.

## Owner: publish from C:\IA

The main repository is initialized on `main` and linked to the group's GitHub
repository. The UI is tracked as ordinary files in this same repository. Its
previous nested Git history is preserved locally under
`.local/github-share/ui-app-git-backup-20261020` and is not uploaded.

Generate a fresh upload list in the VS Code PowerShell terminal:

```powershell
cd C:\IA
.\.venv-item10\Scripts\python.exe -m scripts.release_snapshot github-list .local/github-share/files.txt
```

This checks the runtime, required dependencies, known provider-key patterns,
ignore rules and GitHub's 100 MiB per-file limit. It does not stage or upload.
The adjacent `files.json` records file hashes and sizes. Review the selected files;
pattern matching cannot guarantee arbitrary personal information is absent.

Stage **only** that list, review it, then commit:

```powershell
git --literal-pathspecs add --pathspec-from-file=.local/github-share/files.txt
.\.venv-item10\Scripts\python.exe -m scripts.release_snapshot github-check .local/github-share/files.txt
git diff --cached --stat
git diff --cached --name-only
git commit -m "Add runnable Recto development checkpoint"
```

Do not substitute `git add .`. Remaining untracked research files are expected.
If Git requests an identity, set `git config user.name "Your name"` and
`git config user.email "Your GitHub email"`, then repeat the commit.
The root `.gitattributes` preserves exact bytes during checkout: model/runtime
validation depends on these hashes, including source and artifact log bytes.

On GitHub, create an **empty private repository**, for example `ia-recto`.
Leave README, gitignore and license initialization unchecked. Replace the
placeholder username and repository below, then publish:

```powershell
git remote add origin https://github.com/YOUR-USERNAME/ia-recto.git
git push -u origin main
```

Git may prompt for browser sign-in. Invite your groupmate through repository
Settings > Collaborators and have them accept. Share the clone URL and this guide.
This uploads the project; each person runs the website on their own computer.

References: [GitHub import instructions](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github),
[file limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).
The original Parquet files exceed regular Git's limit. Plan separate LFS/release
storage if the group needs those later; they are unnecessary for running the app.

## Groupmate: clone and run on Windows

For an existing clone with Python dependencies already installed, stop the website,
update, install any frontend lockfile changes and restart from the project root:

```powershell
git pull --ff-only
npm.cmd --prefix UI/UX/app ci
.\start-website.ps1
```

Use the URL the launcher prints. The launcher now includes saved provider
configuration and AI feature settings in its reuse check; it will not reuse an
API process that was started before key setup. Previously configured keys remain
local and do not need to be committed or re-entered after a pull.

Install Git, **Python 3.12** with the `py` launcher, and **Node.js 24** with npm.
Open PowerShell in the desired parent directory and run:

```powershell
git clone https://github.com/YOUR-USERNAME/ia-recto.git
cd ia-recto
.\setup-project.ps1 -DownloadEmbeddingModel
.\start-website.ps1
```

Open the exact URL printed by the launcher. Ports may differ between computers.
Setup installs locked dependencies, downloads the public encoder and verifies
runtime integrity. It does not retrain the classifier. First setup needs internet.
Confirm the fresh encoder download on the groupmate's machine; if its exact hash
fails, restore the pinned public cache from a verified release rather than editing
the integrity hashes. See [recovery](DEPLOYMENT_AND_RECOVERY.md).

Setup creates `.venv-item10` once and refuses to overwrite an existing environment.
After later pulls, use the existing environment unless dependency locks changed.
If Windows blocks a script, use
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal,
then rerun it. This affects only that terminal process.

For local classification/retrieval, choose **AI off** in the website. For AI
wording/explanations, stop the launcher, configure the groupmate's own Together.ai
key with the hidden prompt, then restart:

```powershell
.\.venv-item10\Scripts\python.exe -m backend.normalizer_credentials
.\start-website.ps1
```

Never put keys in code, frontend environment variables, commits or group chat.
The credential is encrypted for that Windows user and ignored by Git. AI uses
that person's provider credits; explanations may be withheld by checks or provider
failures. Configure a new key rather than copying the owner's encrypted credential.

For software verification without sending questions to the LLM provider:

```powershell
$env:RECTO_ENABLE_NORMALIZATION = '0'
$env:RECTO_ENABLE_EXPLANATIONS = '0'
.\check-project.ps1
```

Use a new terminal afterward to restore default feature settings. The optional
Windows GitHub Actions workflow is supplied but has not run on GitHub yet.

For the progress report, describe a connected local development prototype with
synthetic development metrics. Independent human testing, legal source/currentness
review, live AI acceptance and public deployment remain pending.
