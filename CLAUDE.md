# translation-workbench: notes for coding sessions

## Tests: run them like CI, never against a "baseline of failures"

`npm test` only means something with an ephemeral `WORKBENCH_CREDENTIALS_KEY` and a clean e2e database. Without the key about 40
e2e tests fail with `Credential storage is unavailable`; that list hides real regressions, so do not treat it as a baseline.

```bash
fuser -k 8000/tcp 2>/dev/null || true               # an old e2e server keeps its old key
rm -f database/workbench.sqlite3                     # e2e uses the app's own DB: throwaway sandbox only, else move it aside
export WORKBENCH_CREDENTIALS_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
CI=1 npm test                                        # the same as .github/workflows/deploy.yml (retries 2, one worker)
```

A database left from an earlier run holds Connections encrypted with that run's key and breaks the translation specs: start clean
whenever the key changes. Details and the reasons: README, section «Tests».

## CI and deploy

`.github/workflows/deploy.yml` runs on pushes to `main` only (no CI on pull requests). Deploy to production runs only when the tests
pass, so run the full suite locally as above before merging.

## Layout of the front end

`frontend/` is plain HTML/CSS/JS (`index.html`, `styles.css`, `app.js`). The phone layout is `@media (max-width: 720px)` at the end
of `styles.css` plus `singleColumnMedia` in `app.js`: secondary controls move (the same DOM nodes) into «⋯» menus and go back on a
wide screen. Phone e2e: `e2e/mobile-layout.spec.ts`. Desktop (> 720 px) must not change.
