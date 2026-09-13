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

## Tests

```bash
npm test
```

Backend provider tests use an injected fake HTTP transport and never call the real DeepL API. E2E tests require `WORKBENCH_CREDENTIALS_KEY` to be set before Playwright starts the server.

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
