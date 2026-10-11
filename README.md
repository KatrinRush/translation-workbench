# translation-workbench
Private translation workflow tool with AI-assisted analysis, translation, terminology, rules and project management.

## Connections

Connections stores provider credentials with authenticated encryption. Generate a Fernet key once:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set the generated value before starting Workbench:

```bash
export WORKBENCH_CREDENTIALS_KEY='generated-key'
python -m backend.server
```

The key is not stored in SQLite or the repository. Keep it in the environment or a secret manager. Workbench starts normally without it, but creating, editing, and testing Connections is disabled. Existing encrypted Connections appear locked. Losing or replacing the key makes existing credentials unreadable; credential rotation is not implemented yet.

## Server log viewer

Workbench mirrors stdout/stderr (including `[DEEPL DEBUG]` lines) into a rotating log file at `logs/workbench.log`,
redacting anything that looks like a credential or API key. The **⚙️ Налаштування** screen has a **🪵 Лог сервера**
button that opens the last log lines via `GET /api/logs` and refreshes them automatically while open.

To add DeepL, open **Налаштування**, find **Connections**, select **Налаштувати** for DeepL, enter the API key, and save. **Перевірити** calls only the DeepL usage endpoint to validate access; translation is not implemented.

## Translation engines: DeepL, Claude, GPT, Gemini

DeepL is the default engine. To compare engines, add the Claude / OpenAI / Gemini connections in **Connections**, then
pick the engine in the **DeepL / Claude / GPT / Gemini** switch next to **Перекласти розділ** (or in the project settings
under **AI connections → Переклад**). The choice is stored per project in `aiConfiguration.translationConnectionId` and
applies to both chapter and single-paragraph translation. Without a usable connection the switch says so and links to
**Connections**.

### Models

- The **⚙** button next to the switch opens **Налаштування перекладу**: per engine the connection status, a searchable
  model list fetched from the provider through the stored connection (`GET /api/connections/{id}/models`, text models
  only, cached for 10 minutes, keys never reach the browser) and an **Інша модель** field for any other model ID.
  DeepL always uses `quality_optimized`.
- The choice is saved in `aiConfiguration.translationModels = {claude, openai, gemini}`; an empty value means the
  default. Resolution: project setting → `CLAUDE_TRANSLATION_MODEL` / `OPENAI_TRANSLATION_MODEL` /
  `GEMINI_TRANSLATION_MODEL` env var → the model the provider's chapter analysis already uses (Claude:
  `claude-sonnet-5-5`). The older `aiConfiguration.translationModel` still counts for Claude.
- The model a variant was made with is stored on the variant and shown in its tab.

### Variants

- Every engine writes its own **variant** of a paragraph (`paragraph_translation_variants`: engine, text, model, date).
  `translation_text` stays the text that goes to the file, so QA, search, export, undo and review work as before;
  `book_paragraphs.selected_variant_id` says which variant it came from. Existing translations were migrated to the
  variant **Поточний**, which stays chosen.
- A new variant becomes the chosen text only when the paragraph has none yet; otherwise the chosen text is never
  touched by an engine run. Per engine only the newest and the chosen variant are kept.
- Above each translation field are tabs for the existing variants plus **Вручну** (the editor). **У файл** makes a
  variant the chosen text (one per paragraph); for a proofread paragraph it asks once and clears **Перевірено**.
  Footnote markers missing from the chosen variant are moved to the end of the paragraph (footnotes are never deleted
  by a choice). Undo of **У файл** restores the previous choice, text, review flag and footnotes on the server.
- A real edit of the chosen text is saved as the variant **Вручну** and becomes the chosen one; just opening the tab
  records nothing.

### Batches, prompt and logs

- LLM engines translate a chapter in small batches, one HTTP request each, so no request hits Cloudflare's 524 timeout.
  They share one implementation (`backend/integrations/llm_translation.py`): same prompt, same `<chunk>`/`<p id>` XML
  contract with the strict `chunk_mapping_failed` check. A refusal, safety block (Gemini `promptFeedback` /
  `finishReason`, OpenAI `refusal` / `incomplete`), empty reply or non-XML reply fails the batch without saving.
- **Перекласти розділ** skips paragraphs marked **Перевірено**; the per-paragraph button always translates.
- The prompt carries the project glossary (catalog ∪ the active EN→UK translation glossary synced to DeepL, catalog
  wins on duplicates), characters (gender, speech register), per-paragraph narrator gender, project rules and the
  preceding source/translated paragraphs. The system part is identical for every batch, so it is cached (explicitly for
  Claude, automatically for OpenAI and Gemini).
- Every API call logs one `[CLAUDE USAGE]` / `[OPENAI USAGE]` / `[GEMINI USAGE] {...}` JSON line (input, output, cache
  read/write tokens; input excludes cache reads), and every batch a `[… PROMPT] {...}` line with the glossary term
  count and source forms, character and rule counts and the terms found in the batch.

## Tests

```bash
npm test
```

Backend provider tests use an injected fake HTTP transport and never call the real DeepL, Claude, OpenAI or Gemini APIs; `e2e/server.py` answers those providers locally. E2E tests require `WORKBENCH_CREDENTIALS_KEY` to be set before Playwright starts the server.

## Deployment

`.github/workflows/deploy.yml` runs the full test suite (`npm test`) on every push to `main`. Deployment to the
production VPS only runs if the tests pass. Deployment does `git fetch`/`git reset --hard` to `origin/main`,
updates dependencies in the existing `.venv`, and restarts the `translation-workbench` systemd service. It never
touches `.env`, other secrets, or the SQLite database, since those are untracked/gitignored and `git reset --hard`
only affects files tracked by git.

### One-time VPS setup (manual, not automated)

- Create a dedicated, unprivileged deploy user (do **not** use `root` or your personal account).
- Give that user a checked-out clone of this repo at `/opt/translation-workbench` (`git clone` + `git checkout main`),
  with `.venv` already created (`python -m venv .venv`) and `.env` / `WORKBENCH_CREDENTIALS_KEY` already configured
  on the box.
- Create a shared `workbench-db` group and set setgid on the `database/` directory so SQLite WAL/SHM files always inherit group permissions:
  ```bash
  sudo groupadd workbench-db
  sudo usermod -aG workbench-db workbench
  sudo usermod -aG workbench-db deployuser
  sudo chown -R workbench:workbench-db /opt/translation-workbench/database
  sudo chmod 2775 /opt/translation-workbench/database
  sudo chmod 664 /opt/translation-workbench/database/workbench.sqlite3*
  ```
- Allow the deploy user to restart the service and execute diagnostic scripts without a password prompt, scoped to only those commands, e.g. via
  `visudo -f /etc/sudoers.d/translation-workbench-deploy`:
  ```
  deployuser ALL=(root) NOPASSWD: /usr/bin/systemctl restart translation-workbench
  deployuser ALL=(workbench) NOPASSWD: ALL
  ```
- Generate a dedicated SSH key pair for deployments (do not reuse a personal key), and authorize the public key for
  the deploy user (`~deployuser/.ssh/authorized_keys`).

### Database backup on the VPS

Run the **Diagnose production SQLite database** workflow with `action: backup`. It makes a consistent copy of
`database/workbench.sqlite3` with SQLite's online backup API (`sqlite3.Connection.backup`, safe while the service keeps
writing; commits still in `-wal` are included) into `database/workbench-YYYY-MM-DD_HH-MM-SSUTC.sqlite3` next to the
original. The copy is a single standalone file (rollback journal, no `-wal`/`-shm`). The run logs the source/WAL/copy
sizes and the result of `PRAGMA integrity_check` on the copy, refuses to overwrite an existing file or to start without
enough free space, and never deletes older copies — remove them by hand when disk space matters. To restore, stop the
service, remove `workbench.sqlite3-wal`/`-shm`, and put the copy in place as `workbench.sqlite3`.

### SQLite Database Permissions & WAL Mode (Incident Notes)

In SQLite WAL mode (`PRAGMA journal_mode=wal`), SQLite creates `workbench.sqlite3-wal` and `workbench.sqlite3-shm` files on the fly.
If diagnostic/maintenance scripts are executed on the VPS as `deployuser` instead of `workbench`, SQLite can create these files owned by `deployuser:deployuser` with `644` permissions. As a result, the `translation-workbench` systemd service (which runs as `workbench`) loses write permissions and encounters `OperationalError: attempt to write a readonly database`.

**Prevention measures implemented:**
1. **Directory setgid (`2775`) with `workbench-db` group**: The `database/` directory has `2775` permissions with group `workbench-db`. Any newly created files (including `-wal` and `-shm`) automatically inherit the `workbench-db` group.
2. **Diagnostic execution**: Workflows (`.github/workflows/diagnose.yml`) run scripts as the `workbench` user whenever possible (`sudo -u workbench`) to ensure proper process ownership.

### Required GitHub secrets

| Secret            | Description                                                  |
|--------------------|---------------------------------------------------------------|
| `DEPLOY_SSH_KEY`   | Private key of the dedicated deploy SSH key pair.             |
| `DEPLOY_HOST`      | VPS hostname or IP address.                                   |
| `DEPLOY_USER`      | Dedicated deploy user on the VPS (not `root`).                |
| `DEPLOY_PORT`      | Optional; SSH port, defaults to `22` if unset.                |

Configure these under Repository Settings → Secrets and variables → Actions.
