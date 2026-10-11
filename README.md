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

## Pinned chapter controls

While scrolling a chapter, three rows stay pinned at the top of the project workspace: the quick-actions bar, a compact
chapter strip (one-line chips, scrolls sideways, the active chapter is centred in it) and the chapter actions row —
**Перекласти розділ**, **Перевірити узгодження**, the DeepL / Claude / GPT / Gemini switch and **⚙**. The actions row
never wraps; when it does not fit it scrolls sideways. The engine's model is a small caption in that row on wide
screens and always in the tooltip of **⚙**. Controls are at least 40 px high and the pinned block stays within ~140 px.
The chapter heading, word/paragraph counters and the **Всі абзаци** / **Не експортувати** checkboxes stay in the page
flow. The **▴ / ▾** button in the quick-actions bar collapses / expands the pinned rows; the choice is kept in
`localStorage` (`workbench.stickyPanelsCollapsed`) when the browser allows it.

Jumps to a paragraph (search results, ‹ ›, **← Повернутися**, AI QA findings, gender-agreement chips) scroll it into
the area not covered by the pinned block or the bottom bars. `e2e/fixtures/make_long_chapter_epub.py` builds
`test-data/long-chapter.epub`, the long-chapter fixture used by `e2e/sticky-chapter-actions.spec.ts`, and
`test-data/many-long-chapters.epub` (12 chapters × 40 paragraphs) for `e2e/chapter-strip-autoscroll.spec.ts`.

**The chapter strip follows the active chapter.** Opening a project (or the **Переклад** tab) scrolls the strip itself —
not the page — so the active chip is centred. This is done instantly from the layout as it is at that moment, and again
once the strip has a size (its tab was hidden before). When the strip is pinned or released (the chips change size and
the strip its width) the chip that was nearest to the centre is put back there. A smooth `scrollIntoView` was used
before; it was planned against the unpinned layout and was cut short as soon as the page scrolled to the remembered
paragraph and the strip got pinned, leaving the strip at its left edge.

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
  touched by an engine run.
- **Versions.** Every engine run adds a new *version* of the variant for (paragraph, engine) and overwrites nothing; text
  identical to that engine's newest version adds no version (an older, different text does). The newest
  `VARIANT_VERSIONS_KEPT` (`backend/storage.py`, 10) versions per (paragraph, engine) are kept, plus the chosen variant
  even when it is older; only what is beyond that and not chosen is deleted (after a run and after a choice).
  **Вручну** and **Поточний** stay a single row each. Warnings about unused glossary terms belong to their version. No
  migration: earlier deletions are not restored, the rule only applies from now on.
- Above each translation field are tabs for the engines that have variants plus **Вручну** (the editor). A tab shows one
  version: the open one, else the one in the file, else the newest. With several versions a switcher **‹ 3/5 ›** steps
  through them (1 = oldest); the tab's tooltip and the caption show engine, model and date of the version on screen,
  **✓** marks the version in the file (and the tab that has it). **У файл** acts on the version on screen, one
  variant is the chosen text (one per paragraph); for a proofread paragraph it asks once and clears **Перевірено**.
  Footnote markers missing from the chosen variant are moved to the end of the paragraph (footnotes are never deleted
  by a choice). Undo of **У файл** restores the previous choice, text, review flag and footnotes on the server.
- After an engine run (the button under a paragraph or **Перекласти розділ**) the tab of every translated paragraph
  switches to that engine's newest variant. This is interface state only: the chosen variant and `translation_text`
  do not change, nothing is stored, and a reloaded page opens the default tabs again. Switching tabs by hand afterwards
  is respected when the chapter is re-rendered (`e2e/variant-tab-follows-translation.spec.ts`).
- **The whole chapter at once.** **Обрати для файлу весь розділ з…** (next to the engine switch) opens a dialog with the
  engines that have variants in the open chapter (Claude, GPT, Gemini, DeepL, Поточний; with the number of paragraphs that
  have one). For every paragraph with a variant of the chosen engine its **newest version** becomes the chosen text, exactly as
  with **У файл** (same code: footnote markers the old text had are carried to the end, never lost; **Перевірено** is cleared
  only where the text really changes). Paragraphs without such a variant are not touched; a paragraph that already has that
  version chosen is left alone. The dialog first shows the counts and three examples «було → стане» (shortened, from a dry
  run on the server that writes nothing); after the action the line under the actions row reads «Змінено N, без варіанта M,
  пропущено вичитаних K» (plus «вже обрано L» when L > 0). Everything is one database transaction: it applies completely or
  not at all.
- **Proofread paragraphs** (**Перевірено**) are skipped by default. The checkbox **включно з вичитаними** includes them; if the
  text of some of them will change, the dialog warns and asks once more, because **Перевірено** is cleared on those.
- **One undo step** (↩, and ↪ for redo) takes the whole action back: `POST /api/chapters/{id}/restore-selection` restores the
  chosen variant, text, reviewed flag and footnote markers of every changed paragraph (a selected version pruned meanwhile is
  re-created, as for the single undo); redo `POST /api/chapters/{id}/apply-selection` re-applies the very same variants, not
  "the newest" again. Unsaved edits: the action offers to save the chapter first and does nothing if you decline (the same
  guard protects undo/redo of the bulk step). Typing adds its own undo steps on top of the bulk one, so they are undone first,
  and saving the chapter empties the undo stack, as for every other step.
- **«Показувати весь розділ у варіанті X»** (above the chapter text) is a view mode only: it opens, next to every paragraph, the
  **newest version of engine X** (the label says so), changes nothing for the file, sends nothing to the server and does not
  make the chapter dirty. A paragraph without a variant of X shows the chosen text; a paragraph whose shown version is not the
  one in the file is marked «≠ у файлі інша версія» (and a bar at its left edge). The mode is kept while you move between
  chapters in the session and is gone after a reload.
- A real edit of the chosen text is saved as the variant **Вручну** and becomes the chosen one; just opening the tab
  records nothing.
- Saving never touches variants: the project save (`PUT /api/projects/{id}`) only `UPDATE`s `book_projects`, the chapter
  save (💾) writes `PUT /api/paragraphs/{id}` per changed paragraph (a real text change adds/updates **Вручну**, other
  engines' variants are kept), and the start-up migration only gives a **Поточний** variant to translated paragraphs
  that have no variants at all (safe to run on every deploy). Only uploading a replacement EPUB (the UI asks first)
  creates a new book and with it new paragraphs.
- The variants arrive with the book structure (`GET /api/projects/{id}/book/structure`). The browser used to drop
  `translationVariants` / `selectedVariantId` while normalising that structure on project open, so the tabs
  disappeared after a page reload (while the data was intact in the database); `normalizeBookStructure` now keeps
  them. Covered by `tests/test_variants_survive_saves.py` (saves, restarts, migration idempotency, the report script)
  and `e2e/variants-persist.spec.ts` (create variants, save project and chapter, reload, tabs still there).

### Batches, prompt and logs

- LLM engines translate a chapter in small batches, one HTTP request each, so no request hits Cloudflare's 524 timeout.
  They share one implementation (`backend/integrations/llm_translation.py`): same prompt, same `<chunk>`/`<p id>` XML
  contract with the strict `chunk_mapping_failed` check. A refusal, safety block (Gemini `promptFeedback` /
  `finishReason`, OpenAI `refusal` / `incomplete`), empty reply or non-XML reply fails the batch without saving.
- **Перекласти розділ** skips paragraphs marked **Перевірено**; the per-paragraph button always translates.
- Glossary terms in a batch are found case-insensitively with typographic apostrophes and quotes normalized
  (`’ ‘ ʼ` → `'`), and the longest overlapping term wins ("Justice’s court" → `Justice's Court`, not `court` +
  `Justice`). The reminder next to the batch text lists each found term with its glossary translation.
- After a batch, every term found in a paragraph's original must have its equivalent in the translation (in any case
  or number, checked with pymorphy3: «Двору Правосуддя» satisfies «Двір Правосуддя»; for names pymorphy3 does not know,
  or reduces to a wrong lemma («Ларка» → «ларьок»), the stems are compared after cutting the common case endings
  а, у, ові, ом, і, е, ю, ою, ам, ами, ах, ів, ей, so «Ларк», «Ларка», «Ларку», «Ларком», «Ларкові» all satisfy «Ларк»
  while a synonym or another name does not). If one is missing, the batch is
  retried once with the misses spelled out; terms still missing are stored as warnings on that engine's variant and
  shown next to the paragraph, and logged as `[… GLOSSARY CHECK]`.
- The prompt carries the project glossary (catalog ∪ the active EN→UK translation glossary synced to DeepL, catalog
  wins on duplicates), characters (gender, speech register), per-paragraph narrator gender, project rules and the
  preceding source/translated paragraphs. The system part is identical for every batch, so it is cached (explicitly for
  Claude, automatically for OpenAI and Gemini).
- Every API call logs one `[CLAUDE USAGE]` / `[OPENAI USAGE]` / `[GEMINI USAGE] {...}` JSON line (input, output, cache
  read/write tokens; input excludes cache reads), and every batch a `[… PROMPT] {...}` line with the glossary term
  count and source forms, character and rule counts and the terms found in the batch. The usage line also carries
  `promptTokens` (all input), `kind` (`translate` / `retry`) and `reasoning`; the prompt line `reasoning` and
  `systemPromptChars`.

### Cost accounting

- **Every LLM API call that returns token counts is stored** in `translation_usage` (project, chapter, engine, model,
  `kind`, input / output / cache-read / cache-write tokens, time), apart from the variants. `kind` is `translate`
  (the first request of a batch or paragraph), `retry` (a repeat of the same batch: the retry after the glossary check
  and the second attempt after an unusable reply), `qa` (AI QA), `analysis` (chapter analysis) or `chat`. A batch that
  fails after the provider answered (truncated, refused, unusable XML) is recorded too — it was billed. A call that got
  no reply (network error, HTTP 4xx/5xx without usage) writes no row, only the log. DeepL is not counted.
- Providers report usage through `backend/usage.py` (`capture_usage()` / `report_usage()`), a context variable the
  callers set; `analyze()` still returns just text, so existing providers and test doubles keep working. Claude, OpenAI,
  Gemini and Grok all report. Gemini thinking tokens and OpenAI reasoning tokens count as output.
- **Prices** live in the table `model_prices` ($ per 1M tokens: input, output, cache read, cache write), edited in
  **⚙ → Ціни моделей** (global, shared by all projects; add a row for any model ID). Initial values, seeded once and
  never overwritten: `claude-sonnet-5-5` 2 / 10 / 0.20 / 2.50, `gpt-5.5` 5 / 30, `gemini-3.6-flash` 1.5 / 7.5.
  Only tokens are stored: the cost is computed from the *current* table whenever it is shown.
- The price is found by the exact model name, or the name with a trailing date (`-YYYY-MM-DD` or `-YYYYMMDD`) removed —
  never by an arbitrary prefix, so `gpt-5.5` does not match `gpt-5.5-pro` or `gpt-5.5-mini`. No price → «ціну не
  задано». Cache tokens without their own price are priced as input and marked «оцінка».
- After a chapter run the line under the actions row reads e.g. «≈ $0.08 · 9 батчів · 12 345 токенів» (also after a
  paragraph). **Вартість** opens the project report (`GET /api/projects/{id}/usage`): engine/model → calls and tokens
  and ≈$, per chapter, per kind of call, and the project total. Counts and chapter titles only, never book text.
- Migration: `CREATE TABLE IF NOT EXISTS` for the tables, idempotent. Tests: `tests/test_usage_accounting.py`,
  `e2e/translation-cost.spec.ts`.

### Price table rules

- **Every row has a source**: `seed` (initial value), `manual` (edited by the user — a row whose prices are saved
  unchanged keeps its source and date) or `list` (taken from the public list). A table made before the column existed is
  upgraded once: rows still holding the initial values become `seed`, the rest `manual`.
- **A row without any price does not exist.** Clearing all four prices of a row deletes it (the UI asks «Видалити ціну
  моделі X?» first) and no empty row is created automatically; the migration also drops empty rows left by older versions.
  Such a row used to shadow the undated model (`gpt-5.5-2026-04-23` without prices hid `gpt-5.5`); the lookup now ignores
  rows with no price anyway. A deleted initial model stays deleted across restarts (kept in `app_settings`), until
  **Відновити стандартні** puts back the initial prices of the initial models that are missing — rows that exist, whatever
  their source, are not touched.

### Updating prices from a public list

**⚙ → Ціни моделей → Оновити ціни** compares the table with a public price list and changes nothing until you confirm.

- **Source**: one fixed URL, the LiteLLM list (`raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json`,
  per-token USD in `input_cost_per_token`, `output_cost_per_token`, `cache_read_input_token_cost`,
  `cache_creation_input_token_cost`, converted to USD per 1M tokens); if it cannot be used, `https://openrouter.ai/api/v1/models`
  (`pricing.prompt` / `completion` / `input_cache_read` / `input_cache_write`). Nothing else is configurable: 20 s timeout, at
  most 8 MB, no redirects, no keys, cookies or authorization (`backend/price_list.py`). Entries without numeric input and output
  prices, with negative values or placeholders (`sample_spec`) are ignored.
- **Matching**: the exact name, or the name with a provider prefix as the list spells it (`gemini/…`, `openai/…`,
  `anthropic/…`, `xai/…`) — never a guess from an arbitrary prefix, so `gpt-5.5` does not match `gpt-5.5-pro` or
  `gpt-5.5-mini`. For Gemini the `gemini/<name>` key (the API we call) wins over the bare (Vertex) one.
- **The comparison** covers every model of the table and every model in `translation_usage` that has no price. For each it
  shows the list key that matched (or «немає в списку»), «було → стане» per price (a price the list does not have is kept,
  not blanked), the current source, and a warning when a new price differs by more than a factor of two from the current
  one (probably a wrong match): such rows, and rows with a manual price, are not selected by default.
- **Applying** takes the models you ticked, from the comparison kept on the server for 10 minutes (the browser never sends
  prices, the list is not fetched twice). `seed` and `list` rows are overwritten after confirmation; `manual` rows only with
  **Перезаписати й ручні**. Written rows get source `list`; the date and source of the last update are shown above the table.
- Tests use a mock transport only (`tests/test_price_updates_and_daily_usage.py`; `e2e/server.py` serves a small fixed list).

### Usage by day

- **По днях** in the project's **Вартість** dialog (and **Налаштування → Витрати** for all projects or one): range 7 / 30 / 90
  days, a bar chart of ≈$ per day (hatched when the day has calls without a price) and a table — date, ≈$, input / output /
  cache tokens, calls — with a per-day breakdown by engine and by kind (`translate`, `retry`, `qa`, `analysis`, `chat`),
  plus the same breakdown for the whole range. **Експорт CSV** downloads the selected range: one line per day, project,
  engine, model and kind with counts, tokens and ≈$ (empty with «no price» when the model has none). Names and counts only,
  never book text; text cells that start with `=`, `+`, `-` or `@` are prefixed with `'` so a spreadsheet does not run them.
- **Time zone**: days are counted in the zone from `app_settings` (default `Europe/Kyiv`, editable in Settings → Витрати and
  validated as an IANA name). `created_at` stays UTC in the database; a day is the local calendar day, so the 23- and 25-hour
  days at the clock changes are counted correctly, and changing the zone recounts the days without touching any data. A
  stored zone that is no longer valid falls back to `Europe/Kyiv` instead of failing.
- **Calls without a price are never dropped**: each day and the total show «N викликів без ціни» and the sum is marked
  incomplete (`≥ $…`; «ціну не задано» when nothing could be priced).

### Translating several chapters (queue)

«Перекласти кілька розділів…» in the chapter actions starts a **server-side background job** for Claude, GPT or Gemini (for DeepL the button only explains that the queue is not available). Engine, model and reasoning level are taken from the project's current choice when the queue starts and stay fixed for the whole run.

- **What is translated:** a range of chapters («від–до») or «усі без перекладу». Always skipped: chapters marked «Не експортувати», proofread paragraphs («Перевірено»). By default paragraphs that already have a translation are skipped too; the only option, «перекласти й ті, що мають переклад», adds them. The plan (paragraph ids per chapter) is fixed when the queue starts.
- **Results:** the same batches, 90 s timeout and paragraph-id check as «Перекласти розділ». A new variant becomes the chosen one only for paragraphs that had none; existing translations are not changed (for the others the new text is just one more variant/version).
- **Estimate before the start:** from the average cost per source character of this engine/model in `translation_usage` (`source_chars`; old rows without it use the chapter's variant characters as a stand-in), otherwise from tokens × `model_prices`. The dialog reminds to check the balance in the provider's console and warns when the estimate is over $5.
- **«Максимум $»:** checked before every batch against the spent cost of this queue (from `translation_usage`, rows carry `queue_id`) plus the estimated cost of the next batch. When it would be passed the queue stops **at the batch boundary**, the chapter in progress is marked «частково», the rest «пропущено». A model without a price can only start without a limit and with an explicit confirmation.
- **Control:** progress «розділ 12/30 · батч 3/9 · ≈ $0.41» with Пауза / Продовжити / Зупинити; pause and stop take effect after the batch that is already running (its result is saved). One queue can be active per project.
- **Errors:** a failed batch is repeated once; if it fails again the chapter is marked «error», the queue goes on, and the problem chapters are listed in the summary. Calls that returned a response (even an unusable one) are billed and recorded; HTTP failures have no usage row.
- **Restart/deploy:** state lives in `translation_queues` / `translation_queue_items` / `translation_queue_variants`. A batch and its counters are saved in one transaction; after a restart the worker continues queues in `running` status from the next unsaved batch (a batch that was in flight at the moment of the restart is sent again, and may be paid twice). Paused queues stay paused.
- **Summary:** chapters (done/partial/error/skipped), paragraphs, cost, time. «Скасувати перекладене чергою…» deletes only variants created by this queue that were not chosen by hand, and un-chooses those that became chosen automatically (only if the text is untouched and the paragraph is not proofread). It shows the counts first; the money already spent stays in the cost records.
- **API:** `POST /api/projects/{id}/translation-queues/estimate`, `POST /api/projects/{id}/translation-queues`, `GET /api/projects/{id}/translation-queues/latest`, `GET /api/translation-queues/{id}`, `POST /api/translation-queues/{id}/pause|resume|stop|undo` (`undo` with `{"dryRun": true}` only counts).
- **Tests:** `tests/test_translation_queue.py` (mock transport, the executor is stepped synchronously), `e2e/translation-queue.spec.ts` (`[[slow]]` in the project's translation rules makes the fake LLM take ~0.6 s per call).

### Reasoning level (GPT, Gemini)

Output tokens, thinking included, are the main cost of these engines. **⚙** has «Рівень роздумів» for GPT and Gemini:
Мінімальний / Низький (default) / Середній, kept per project (`aiConfiguration.translationReasoning`). Claude has no
such setting.

| Level | OpenAI (Responses API `reasoning.effort`) | Gemini 3.x (`generationConfig.thinkingConfig.thinkingLevel`) |
|---|---|---|
| Мінімальний | `none` | `minimal` |
| Низький | `low` | `low` |
| Середній | `medium` | `medium` |

Sent only to models that take it: OpenAI `gpt-5*`, `o1`, `o3`, `o4`; Gemini `gemini-3*` (Gemini 2.5 is steered with a
token budget and is left as it is). A model that answers 400 to a level is retried **once** with `low`; the rejection is
remembered in the process (per model and level), so later batches go straight to `low`; the log gets a warning, the
usage line `reasoning: {requested, used, fellBack}` and the UI line a «⚠ модель відхилила рівень…» note. The values
come from the vendors' documentation as found by search (the docs sites are not reachable from the CI sandbox):
gpt-5.5 takes none/low/medium/high/xhigh; Gemini 3 Flash takes minimal/low/medium/high, but newer Flash models reject
`minimal` — hence the fallback.

### Batch size

**⚙ → Розмір батча** (per project, `aiConfiguration.translationBatch`): max characters (500–6000, default 1500) and max
paragraphs (1–20, default 8) per request; empty means the default. The paragraph-id check and the 90 s request timeout
are unchanged. A bigger batch repeats the system prompt less often but makes each answer longer and a truncation costlier.

### Gemini cache

Gemini caches a repeated prompt prefix implicitly (on by default for 2.5 and 3.x; no storage fee; the discount shows up
as `cachedContentTokenCount`, which we store as cache-read tokens). A request is cached only if the shared prefix is at
least the model's minimum — 1024 tokens for 2.5 Flash, 2048–4096 for the Pro models; the figure for 3.6 Flash is not
confirmed — and the stable part comes first. Our request already has that shape: the project system prompt (glossary,
characters, rules) goes first as `systemInstruction`, the varying batch text follows. `cacheReadTokens: 0` therefore most
likely means the prefix is shorter than the minimum. Check it in the `[GEMINI PROMPT]` line (`systemPromptChars`, about
2–3 characters per Ukrainian token) against the `[GEMINI USAGE]` line (`promptTokens`, `cacheReadTokens`) and in the
«Кеш (читання)» column of **Вартість**. **Explicit caching is not implemented**: it adds a storage fee per token-hour and
a cache-creation call, and only pays off for a large prefix reused many times within the TTL — decide with the
collected usage data.

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

### Translation variants report on the VPS

Run the **Diagnose production SQLite database** workflow with `action: variants` (or
`bash scripts/diagnose_variants_db.sh [path/to/workbench.sqlite3]` on the VPS). It is read-only (the database is opened
with `mode=ro` and `PRAGMA query_only`) and prints counts only, never book or translation text: for every project and
chapter the number of paragraphs, paragraphs with a translation, paragraphs with `selected_variant_id` (and how many of
those point at a missing variant), and the rows of `paragraph_translation_variants` per engine
(`current`, `deepl`, `claude`, `openai`, `gemini`, `manual`), plus the total per engine and the number of variant rows
whose paragraph no longer exists. It answers "are the variants in the database?" when tabs look missing in the UI.

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
