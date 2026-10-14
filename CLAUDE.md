# translation-workbench: notes for coding sessions

## Merging: only after a green «Run test suite» on the pull request itself

A pull request is merged only after the check **«Run test suite» on that pull request** has finished green, never before it.
Pushes to `main` deploy to production, so a red `main` costs a deploy. After the merge, watch the workflow on `main` until the
deploy job finishes. (Branch protection is deliberately not enabled; this rule replaces it.)

## Tests: run them like CI, never against a "baseline of failures"

`npm test` only means something with an ephemeral `WORKBENCH_CREDENTIALS_KEY`. Without it about 40 e2e tests fail with
`Credential storage is unavailable`; that list hides real regressions, so do not treat it as a baseline.

```bash
fuser -k 8000/tcp 2>/dev/null || true                # an old e2e server keeps its old key
export WORKBENCH_CREDENTIALS_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
CI=1 npm test                                         # the same as .github/workflows/deploy.yml (retries 2, one worker)
```

The e2e server uses a throwaway database and log directory (`e2e/e2e_db.py`, a fresh `workbench-e2e-*` directory in the system
temp directory, removed on exit; `WORKBENCH_DATABASE_PATH` / `WORKBENCH_LOG_DIR` override it). It refuses to start on the
application's own `database/` or `logs/`. Never delete or move `database/workbench.sqlite3` for a test run and never add an `rm` of
it to a script; there is nothing to clean. Details and reasons: README, section «Tests».

## CI and deploy

`.github/workflows/deploy.yml`: the test job runs on pull requests against `main` and on pushes to `main`; the deploy job runs only
for a push to `main` after green tests. A new push to a pull request cancels that pull request's older run; a run on `main` is
never cancelled.

## Layout of the front end

`frontend/` is plain HTML/CSS/JS (`index.html`, `styles.css`, `app.js`). The phone layout is `@media (max-width: 720px)` at the end
of `styles.css` plus `singleColumnMedia` in `app.js`: secondary controls move (the same DOM nodes) into «⋯» menus and go back on a
wide screen. Phone e2e: `e2e/mobile-layout.spec.ts`. Desktop (> 720 px) must not change.
