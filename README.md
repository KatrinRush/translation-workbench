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
  variant is the chosen text (one per paragraph); for a paragraph marked **Перевірено** or **Вичитано** it asks once and, if the text changes, clears both marks.
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
  пропущено перевірених чи вичитаних K» (plus «вже обрано L» when L > 0). Everything is one database transaction: it applies completely or
  not at all.
- **Paragraphs marked «Перевірено» (reviewed) or «Вичитано» (proofread)** are skipped by default. The checkbox **включно з перевіреними й вичитаними** includes them; if the
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

- **What is translated:** a range of chapters («від–до») or «усі без перекладу». Always skipped: chapters marked «Не експортувати», paragraphs marked «Перевірено» or «Вичитано». By default paragraphs that already have a translation are skipped too; the only option, «перекласти й ті, що мають переклад», adds them. The plan (paragraph ids per chapter) is fixed when the queue starts.
- **Results:** the same batches, 90 s timeout and paragraph-id check as «Перекласти розділ». A new variant becomes the chosen one only for paragraphs that had none; existing translations are not changed (for the others the new text is just one more variant/version).
- **Estimate before the start:** from the average cost per source character of this engine/model in `translation_usage` (`source_chars`; old rows without it use the chapter's variant characters as a stand-in), otherwise from tokens × `model_prices`. The dialog reminds to check the balance in the provider's console and warns when the estimate is over $5.
- **«Максимум $»:** checked before every batch against the spent cost of this queue (from `translation_usage`, rows carry `queue_id`) plus the estimated cost of the next batch. When it would be passed the queue stops **at the batch boundary**, the chapter in progress is marked «частково», the rest «пропущено». A model without a price can only start without a limit and with an explicit confirmation.
- **Control:** progress «розділ 12/30 · батч 3/9 · ≈ $0.41» with Пауза / Продовжити / Зупинити; pause and stop take effect after the batch that is already running (its result is saved). One queue can be active per project.
- **Errors:** a failed batch is repeated once; if it fails again the chapter is marked «error», the queue goes on, and the problem chapters are listed in the summary. Calls that returned a response (even an unusable one) are billed and recorded; HTTP failures have no usage row.
- **Restart/deploy:** state lives in `translation_queues` / `translation_queue_items` / `translation_queue_variants`. A batch and its counters are saved in one transaction; after a restart the worker continues queues in `running` status from the next unsaved batch (a batch that was in flight at the moment of the restart is sent again, and may be paid twice). Paused queues stay paused.
- **Summary:** chapters (done/partial/error/skipped), paragraphs, cost, time. «Скасувати перекладене чергою…» deletes only variants created by this queue that were not chosen by hand, and un-chooses those that became chosen automatically (only if the text is untouched and the paragraph is not proofread). It shows the counts first; the money already spent stays in the cost records.
- **API:** `POST /api/projects/{id}/translation-queues/estimate`, `POST /api/projects/{id}/translation-queues`, `GET /api/projects/{id}/translation-queues/latest`, `GET /api/translation-queues/{id}`, `POST /api/translation-queues/{id}/pause|resume|stop|undo` (`undo` with `{"dryRun": true}` only counts).
- **Tests:** `tests/test_translation_queue.py` (mock transport, the executor is stepped synchronously), `e2e/translation-queue.spec.ts` (`[[slow]]` in the project's translation rules makes the fake LLM take ~0.6 s per call).

### Dictionary in the original column

The **«📖 Словник»** button in the pinned chapter actions turns the dictionary mode on (remembered in `localStorage`, off by default). While it is on a bar above the columns says «Режим словника: торкніться слова в оригіналі» (button «Вийти»; Esc also leaves). A tap on a word of the **original** column opens the window; selecting several words (up to 8 words / 80 characters) opens it for the phrase once the selection is finished. With the mode off nothing changes: selecting and copying work as before and no window opens; on a computer **Alt+click** opens the dictionary without the mode. The translation column, editing, checkboxes and paragraph buttons are not affected. The word is found from the touch point with the browser's caret API and a `Range` (letters, apostrophes `' ’ ‘ ʼ`, hyphens) — words are not wrapped in tags.

While the window is open the word or phrase stays **highlighted** in the original (CSS Custom Highlight API: a translucent background plus a 2 px underline, colours from the theme so the text stays readable in light and dark; where the API is missing, fixed rectangles with an outline from `Range.getClientRects()` that follow scroll and resize). The text DOM is never changed, and the highlight does not depend on the current selection, so a tap into the window does not lose it; it is removed when the window closes or a new lookup starts. The window has an «У реченні: …» line (the sentence with the word in bold) and a **«Показати в тексті»** button that scrolls the paragraph into the area between the pinned block and the bottom bars (the shared `scrollIntoWorkspaceView`) and blinks the highlight. On a computer (≥ 1100 px, fine pointer) the window is a fixed panel on the right (360 px, own scroll) and the page gets a right padding while it is open, so the translation column narrows instead of being covered; the panel stays put when the page scrolls. On a tablet or narrow screen it is a bottom sheet of at most 42vh and the page is scrolled so the word stays above it. It shows the term and part of speech, the meaning in this sentence, «Як перекладено тут», other meanings with register marks, examples and a «У глосарії» block when the project glossary has the term. Buttons: «Додати в глосарій» (a form with the lemma/phrase and a translation chosen from the list or typed; it creates a catalog entry and links it to the project through the existing glossary API), «Копіювати», «Ще значення» (up to 3 extra requests per word, each excluding what was shown), «Відкрити в Reverso Context», «Відкрити у Вікісловнику» (`target="_blank" rel="noopener noreferrer"`). A tap outside the window or Esc closes it; one request runs at a time.

`POST /api/dictionary/lookup` `{projectId, paragraphId, text, offsetStart, offsetEnd, mode: word|phrase|more}` (offsets count in the paragraph's plain text as the browser shows it). The answer also carries `sentence`, `termStart`, `termEnd` (worked out on every lookup, never cached or logged). Order:

1. **Project glossary** — whole-word, typographic-apostrophe-insensitive, longest match (as `glossary_check.py`). If a term covers the selection the answer is the «У глосарії» block with **no model call**. `mode=more` always asks the model.
2. **`dictionary_cache`** — key: normalized term + hash of the sentence + model + mode (no book text is stored in the key). A hit costs nothing. The model is part of the key; answers are not refreshed when the paragraph is retranslated.
3. **One model call** with the sentence (found on the server from the offsets: abbreviations such as Mr., Dr., St., etc., i.e. and initials do not end it; a stop followed by a closing quote does; if it cannot be told, or the term crosses a boundary, the whole paragraph is sent), the whole paragraph and the chosen translation. The answer is strict JSON (`term, lemma, pos, termType, expandedPhrase, meaningInContext, translations ≤5, registerNote, inThisTranslation, examples ≤2`), validated; one retry when it is not valid; 45 s timeout; at most 1500 output tokens. `expandedPhrase` is turned into a range in the sentence so the window can offer to look up the whole phrase.

**Model:** «Модель словника» in ⚙ (`aiConfiguration.dictionary = {connectionId, model}`; any connected Claude/GPT/Gemini connection and a model from its list or typed by hand). By default the cheapest priced model of the connection's own list (input + output price), the provider's default model if none is priced; no model name is hardcoded. A model without a price works but the window warns that the cost will not be counted. Every call (also a retry) is recorded in `translation_usage` with `kind='dictionary'` and shows in «Вартість» as «Словник». Old databases get the new kind through an idempotent rebuild of the `translation_usage` CHECK.

**Privacy:** the logs hold only lengths and token counts (`termChars`, `sentenceChars`, `inputTokens`, `outputTokens`), never sentences from the book.

**Tests:** `tests/test_dictionary.py` (mock transport: word, phrase, idiom with expansion, glossary without a call, cache, invalid JSON and the retry, usage kind, apostrophes and hyphens, sentence splitting, missing connection), `e2e/dictionary.spec.ts` (the fake LLM in `e2e/server.py` answers dictionary prompts with fixed JSON; each test uses its own model name because the cache is keyed by model).

### Proofread («Вичитано») and progress

A paragraph goes through three independent stages: **Перекладено** (it has a chosen translation) → **Перевірено** (`reviewed`) → **Вичитано** (`proofread`). «Вичитано» does not require «Перевірено». The existing «Перевірено» is unchanged; in the interface «вичитано» now means only the new stage (older messages that said «вичитаних» about «Перевірено» now say «перевірених»).

- **Data.** `book_paragraphs.proofread INTEGER NOT NULL DEFAULT 0` (idempotent migration). `PUT /api/paragraphs/{id}` accepts `proofread` (when it is missing the mark stays as it is). The box **«Вичитано»** sits next to «Перевірено» in the service bar (also in «Усі рушії»; ≥ 44 px on touch) and is saved, undone and redone with the chapter exactly like «Перевірено».
- **Protection (same as «Перевірено»).** A paragraph with either mark is skipped by whole-chapter translation, by the translation queue (and its plan) and by the bulk choice of a variant (unless «включно з перевіреними й вичитаними»). «У файл» and the bulk choice clear **both** marks when the chosen text changes (with a confirmation; undo restores them). Manual edits in the editor and **«Замінити все»** do **not** clear «Вичитано» (the confirmation counts «перевірених» and «вичитаних» paragraphs); undoing a queue's results leaves a proofread paragraph alone.
- **Marking a whole chapter.** The «Ще ▾» menu has four items: «Позначити весь розділ: Перевірено / Вичитано» and «Зняти «Перевірено» / «Вичитано» з розділу». They differ from the checkbox **«Всі абзаци»** (which only toggles «Перевірено» for every paragraph at once, service text included, without asking, and stays as it was): the menu items skip service text, count what they change («Позначити «Вичитано» 78 абзаців? Службовий текст пропускається (1)») and ask once; each is one undo step; the marks are saved with the chapter.
- **Progress** has four figures: **Перекладено**, **Перевірено**, **Вичитано** and **Загальне** = the arithmetic mean of the three percents (equal weights). The denominator is the paragraphs that have original text, are not service text and are in chapters without «Не експортувати»; it is counted in **paragraphs** (default) or in **words** of the original (the switch «Абзаци / Слова» in the header of the project list and in the project's «Прогрес» block; one remembered choice, `localStorage` `workbench.progressUnit`, used everywhere).
- **Where it is shown.** (a) **Chapter chips**: a thin 3 px bar at the bottom inside each chip (three equal parts: translated / reviewed / proofread; a part with a percent above 0 is at least 2 px wide), «✓» when the whole chapter is proofread, the numbers («Перекладено: 10 з 79 абзаців · …») in the chip's tooltip; the pinned row does not get taller; a chapter marked «Не експортувати» has no bar. (b) **Project page** («Інформація про проєкт»): the block «Прогрес» with four bars and «N з M · X %». (c) **Project cards** (the list of all projects): four compact bars with labels, different colours and the percent as text («Перекладено», «Перевірено», «Вичитано», «Загальне»; the tooltip has «N з M»), no horizontal scroll on a tablet or phone. «Загальне» replaces the old single «відсоток готовності» (which was reviewed ÷ all non-service paragraphs, without excluded chapters or empty originals); `progress.progress` in the project list stays as the overall percent in paragraphs for older clients.
- **Words in an opened chapter.** The page keeps `wordCount` of every paragraph (it had been dropped, so in the «Слова» unit the live figures of an opened chapter came out as 0 and the three parts of the chip's bar were grey; fixed, with a fallback that counts the words of the original), and a chip with nothing to count in the chosen unit shows no bar instead of three grey parts. The colours of the chips (none / partly / all «Перевірено») and the stripe at the left of a paragraph (untranslated / translated / reviewed) depend on «Перевірено» and the translation only, not on «Вичитано» or the unit; `e2e/status-colors.spec.ts` guards this (before and after ticking «Вичитано», in both units, before and after a reload).
- **How it is computed.** SQL aggregates on the server, no book text: `GET /api/projects` carries, for every project at once (one `GROUP BY` query, no N+1), `progress: {progress, paragraphs: {total, translated, reviewed, proofread, percent}, words: {…}}`; `GET /api/projects/{id}/progress` adds every chapter (with `excluded`). In an open project the chapters that have been opened are recomputed live from the drafts (a ticked box moves the bars at once; word counts come from `wordCount` of the paragraphs); after a save the server's figures are fetched again, so only the affected chapter and the totals change, the project is not reloaded.
- **Walking the book to the end.** The button **«Наступний невичитаний»** in the actions row focuses the next paragraph without «Вичитано» after the current one in the open chapter, then in the following chapters (chapters marked «Не експортувати» are skipped; service text and paragraphs without original text are not counted, as in the progress figures); it switches the chapter through the usual navigation (which asks about unsaved changes) and says so when everything to the end of the book is proofread. The checkbox **«Показати лише невичитані»** hides the proofread paragraphs of the open chapter and shows «(показано N з M)»; a jump to a hidden paragraph (search, QA, ‹ ›) shows it, and the filter applies to every chapter you open while it is on (it is not remembered after a reload).
- **Tests:** `tests/test_proofread.py` (migration, saving, protection in the queue and chapter translation, «У файл», bulk choice, replace, aggregates in paragraphs and words, service text, «Не експортувати», «Загальне» as the mean, one query for the project list), `e2e/proofread-progress.spec.ts` (the box, the chapter menu, chips, the project page, the cards at 1280 and 390 px, following a saved change), `e2e/next-unproofread.spec.ts` (the button across chapters, the end of the book, the filter).

### Search in the translation (🔍)

Plain search works in the **same docked side panel** as «Знайти й замінити»; there is no separate bottom bar any more.

- **Where.** On a computer (≥ 1100 px, fine pointer) the panel docks to the right and stays open while you navigate. On a tablet or phone it is the bottom sheet (≤ 48vh, buttons ≥ 44 px) that takes over the same functions.
- **Navigation.** The status «збіг 7 з 50» counts paragraphs; ‹ › buttons; Enter / Shift+Enter in the input go to the next / previous match; **← Повернутися** returns to where the search was started (remembered when a *new* search starts, not on each click on a match); ✕ closes. Esc closes the panel; in replace mode it first closes the «Замінити все» confirmation and open menus.
- **Results.** Clickable snippets with the chapter title, position in % and the highlighted match; the current one is marked. With the scope «Проєкт» / «Усі проєкти» they are grouped by chapter with a count. The list scrolls on its own; the navigation block (and the replace buttons) are pinned at the bottom of the panel.
- **In the text.** All matches of the open chapter are highlighted softly and the current one strongly, through the CSS Custom Highlight API (fallback: rectangles drawn over the text, like the dictionary). The paragraph DOM is not changed and matches are computed in chunks so long chapters keep scrolling smoothly.
- **Collapse.** » collapses the panel into a narrow vertical strip «Пошук 7/50»; a click expands it. The query and results are kept; the state is remembered in `localStorage` (`workbench.searchPanelCollapsed`).
- **One docked panel at a time.** Opening the search hides the dictionary and vice versa; the state of both (query, results, last word) is kept. The hidden panel does not come back by itself, only when opened explicitly (🔍 or a tap on a word in dictionary mode). Reopening 🔍 keeps the last query and results and selects the text in the input.
- **Geometry of the docked panels (computer, ≥ 1100 px).** Search, replace and the dictionary are `position: fixed`: the top is the **measured** bottom edge of the top bar with the project title and icons (`--topbar-h`, updated by a `ResizeObserver`, on density change and on zoom; 48 px is only the fallback) and the bottom is the bottom of the window (`100dvh − --topbar-h`), so the panel header is always visible and the pinned rows never go under it. The two pinned rows (chapters and actions) have exactly the left and right edge of the work area (`#chapter-browser`) with the panel closed, open, collapsed (56 px strip) or with the dictionary open: a `ResizeObserver` on the area re-syncs them; what does not fit scrolls inside the row and is clipped at the edge. Tablet and phone keep the bottom sheet. Test: `e2e/pinned-rows-geometry.spec.ts` (1280/1440/1920, both densities).
- **Tests:** `e2e/search-panel.spec.ts` (1280/1440/1920: no bottom bar, buttons, Enter / Shift+Enter, click, return, collapse persistence, Esc; 1024/820/390: the sheet, ≥ 44 px, nothing covered).

### All engines: compare and pick fragments («Усі рушії»)

A switch **«Усі рушії»** in the chapter's action row (next to «📖 Словник»; remembered in `localStorage`, off by default) turns every paragraph into a comparison grid.

- **Layout.** On a computer (≥ 1100 px, fine pointer) a 2×2 grid: the **original** (left) and the **editor** (right) on top, **panel A** (default Claude) under the original and **panel B** (default Gemini) under the editor; the two panels of a row are equally tall. On a tablet or phone (< 1100 px or a touch screen) a stack: original, editor with its service bar («Перекласти …», «Перевірено», «⋯»), panel A, panel B. The tabs of the variants are hidden in this mode (the panels replace them) and «Показувати весь розділ у варіанті» is disabled. With the switch off nothing changes.
- **The editor** is the usual text field for the file with all of its behaviour: manual edits become the variant «Вручну», undo/redo, unsaved changes, footnotes, «Перевірено», the service line.
- **Panels A and B are read-only.** The header has an engine choice (Claude, GPT, Gemini, DeepL, «Поточний», «Вручну»; the choice of each panel is remembered), the version switcher ‹ 2/3 ›, the caption «рушій · модель · дата · інструкції #хеш», the mark «✓ у файлі» / «≠ не у файлі» and «⤢» (the text of a panel is at most 40vh tall and scrolls inside; «⤢» lifts the limit). Buttons: **«У файл»** (the existing choice, with its confirmation for a reviewed paragraph and undo) and **«Копіювати все у Вручну»** (the editor takes the whole text as an ordinary edit; footnote markers the editor had and the copied text lacks are appended at the end with a note). With no variant the panel says «немає перекладу» and offers **«Перекласти {рушій}»** (the same request as under the paragraph, with that engine's connection).
- **«→ Вручну» for a fragment.** Select text in a panel and a floating button appears next to the selection (it works by touch). The editor loses focus when the button is pressed, so the last cursor or selection inside the editor is remembered (a live range). The fragment replaces that selection, or lands at that cursor; if the cursor was never placed it is appended at the end after a space. Plain text only (no formatting tags, no footnote numbers), and it is an ordinary editor edit: the paragraph becomes «unsaved» and undo works.
- **«Підсвітити відмінності»** (off by default, appears with the mode): words without a counterpart in another shown text (a word-level longest-common-subsequence between the editor and the panels) are marked with the CSS Custom Highlight API (`::highlight(compare-diff)`, no fallback; the switch is disabled in a browser without it). Only paragraphs near the screen are compared, and only up to a few hundred words.
- **Performance.** The panels are filled only for paragraphs near the screen (an `IntersectionObserver` with a margin), so long chapters keep scrolling smoothly.
- **Search.** The matches of a search are highlighted in the panels too (highlight only; replacing works on the editor). The dictionary works on the original. Bulk actions, the queue, the pinned rows, the chat, themes, density and the geometry of the side panels are unchanged.
- **Tests:** `e2e/compare-engines.spec.ts` (the mode and its memory; the grid at 1280/1440/1920 and the stack at 1024/820/390 with touch and ≥ 44 px buttons; engine and version choice; «У файл» with undo; «→ Вручну» at the cursor, over a selection and at the end, with undo and saving as «Вручну»; «Копіювати все»; the empty panel; the 40vh limit; the difference and search highlights).

### Find and replace (🔍)

«Знайти й замінити» in the search dialog works like Word, on the **translation text only** and only for a **Cyrillic query** (a Latin query still searches the original; the replace field is then off with an explanation). The scope is the chapter or the project ("all projects" is not offered for replacement). In replace mode the dialog docks to the right (a bottom sheet of at most 48vh on a narrow screen) and the page makes room, so the text stays visible; the current match is highlighted without changing the paragraph DOM and the status reads «збіг 3 з 14 · розділів · вичитаних абзаців».

- **Match modes:** «Початок слова (усі відмінкові форми)» (default), «Ціле слово», «Довільна частина» (any part, no limits); «Враховувати регістр» (off by default). *Початок слова* accepts a case ending after the stem (`ові еві єві ами ями ом ем єм ою ею ям ах ях ів ам а у і ю я и ї` or none): «Дрейвен» finds «Дрейвена», «Дрейвену», «Дрейвеном» but not «Дрейвенський» or «Дрейвен’с». Only the last word of a phrase is inflected. Names in -ій/-ей also find their oblique forms («Андрій» → «Андрія», «Андрієві», «Андрієм»), and the replacement follows the new name's ending (Андрій → Юрій: «Юрія»; Дрейвен → Андрій: «Андрія»). Apostrophes ’ ‘ ʼ ' are the same. With case off the replacement takes the case of the first letter of the match.
- **Only text changes.** The stored translation is split at tags (`<b>`, `<i>`) and footnote markers and a match is looked for inside one piece, so formatting, markers and `&amp; &lt; &gt;` stay byte for byte. A match that crosses a tag or a marker («Дрей<i>вен</i>») is **skipped and counted**; the confirmation says how many. The replacement is inserted as plain text.
- **Writing.** For each paragraph the result is a manual edit of the chosen text (the single «Вручну» variant is created or updated and chosen, footnotes stay). **«Перевірено» and «Вичитано» are never removed**; «Замінити все» tells how many reviewed («перевірених») and proofread («вичитаних») paragraphs change. «Також у варіантах рушіїв» (off by default) applies the same replacement to the text of the engine variants (every kept version, in place), so a later whole-chapter choice from an engine does not bring the old name back; ids, order and dates of the versions are not touched, so version pruning and «найновіша версія» behave as before. Everything is one transaction: all or nothing.
- **«Замінити»** replaces the current match and moves to the next one; **«Замінити все»** first shows «Замінити N збігів у X розділах?», the number of proofread paragraphs, the skipped ones and the first 5 matches (було → стане). Unsaved edits of the open chapter can be saved first (otherwise nothing happens); another chapter with unsaved edits must be saved by hand.
- **Undo/redo:** «Замінити» is one step, «Замінити все» one step for the whole action (even across chapters), on the open chapter's stack like the whole-chapter choice of a variant. Undo restores the chosen text, «Перевірено», the selected variant, the manual variant and the touched engine variants; redo applies exactly the same texts.
- **API:** `POST /api/projects/{id}/translation-find`, `translation-replace` (`target` for one match, `dryRun` for the preview), `translation-replace/restore`, `translation-replace/apply`. The matching engine is `backend/text_replace.py`.
- **Tests:** `tests/test_translation_replace.py`, `e2e/find-replace.spec.ts`.

### Layout: compact, dense, one screen wide

The chapter view is built to use the screen without crowding.

- **Heading and actions.** «Вибраний розділ: …» and its counters keep a readable width (at least 250 px) and sit above the actions row, which wraps under them. The action buttons never shrink or wrap their text (`flex: none`); only the «Модель: …» label is cut with an ellipsis first. While pinned the row is one line that scrolls sideways (the translate button and the engine switch come first). Secondary actions — «Обрати для файлу весь розділ з…», «Перекласти кілька розділів…» — are in the **«Ще ▾»** menu. The translation-queue panel is its own block in the flow, below the row.
- **Paragraph cell.** The original and the translation start at the same level. Everything service is **one compact bar under the translation text** (`.para-bar`): variant tabs, the ‹ 2/3 › version switcher, **«✓ у файлі» / «≠ У файл»** (state and action in one button), the paragraph's «Перекласти {рушій}» button, a small muted «рушій · модель · дата» caption (the full text is a tooltip), the «Перевірено» checkbox and the **«⋯»** menu (Службовий текст, У черзі на QA, Оповідач з цього абзаца). The bar wraps onto a second line when the column is narrow (also with a side panel open): the main controls stay first, the caption is cut first. The long «Редагування тексту для файлу…» sentence is a tooltip; only the open paragraph shows it. All bars have the same height.
- **Menus.** «Ще ▾» and «⋯» are plain dropdowns without libraries: `aria-haspopup`, `aria-expanded`, `position: fixed` (so the pinned row cannot clip them), Esc / click outside to close, arrows + Home/End to move, Enter to press.
- **Density** (⚙ → «Щільність інтерфейсу», stored in `localStorage` key `workbench.density`): «Компактно» (controls 32 px, tighter gaps) is the default for a mouse (`pointer: fine`), «Звичайно» (40 px) for touch; a choice is remembered. With `pointer: coarse` targets stay **at least 44 px** in both (`--control-h`).
- **Width.** The chapter view uses the available width up to 1600 px. With a side panel open (dictionary, search/replace) the content moves over and uses the rest of the width instead of staying a narrow centred strip.
- **Search / replace panel.** Scope («Розділ / Проєкт / Усі проєкти») and match mode («Початок слова / Ціле слово / Довільна частина») are segmented switches in one row; «Враховувати регістр» and «Також у варіантах рушіїв» share a line; «Знайти й замінити» is a link-style toggle. The match list has its own scroll (at least 160 px, 120 px on a bottom sheet) and the status line («21 збіг · розділів: 1») with ‹ › Замінити Замінити все is pinned at the bottom of the panel (on a bottom sheet the fields scroll and the buttons stay pinned). 
- **Fixes on the way:** the chapter strip no longer pins itself when its sentinel is below the viewport (a long page above the chapters, e.g. on a phone); on a 390 px screen the chapter card no longer overflows the screen sideways.
- **Tests:** `e2e/compact-layout.spec.ts` (1280/1440/1920 and 1024/820/390: action buttons have a size and do not overlap, heading ≥ 250 px, the bar under the text with equal heights, columns aligned at the top, ≥ 44 px targets with touch emulation in both densities, density persistence, menus with the keyboard, the search panel).

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

### Engine instructions (Claude, GPT, Gemini)

Own translation instructions per LLM engine, set in **⚙ → «Інструкції рушіїв»** (tabs Claude / GPT / Gemini; DeepL and the dictionary model are not touched).

- **Two scopes.** «Для всіх проєктів» (global) and «Лише для цього проєкту» (an addition). Plain text, at most **4000 characters** (the server answers 400 above that); line breaks are normalized and the ends trimmed; an empty text removes the row. Stored in the table `engine_instructions(engine, scope, project_id, text, updated_at)` (created idempotently; `project_id` is `''` for the global scope; a project's additions are deleted with the project). API: `GET/PUT /api/engine-instructions/{engine}`, `GET/PUT /api/projects/{id}/engine-instructions/{engine}`, `GET /api/projects/{id}/engine-prompt/{engine}`, `POST /api/projects/{id}/engine-prompt/{engine}/preview` (a draft).
- **In the prompt.** After the shared rules (format contract, dialogues, style, glossary rules, characters, project glossary, project rules) comes the block «ДОДАТКОВО ДЛЯ ЦЬОГО РУШІЯ»: the global text first, then the project's; empty parts are left out. After it a one-paragraph «ОБОВ'ЯЗКОВИЙ ФОРМАТ ВІДПОВІДІ» (one `<chunk>`, the same ids, nothing outside it, dialogues with a dash) has priority over the user's text. The block is in the system part and the same for every batch, so the Claude cache and the implicit OpenAI/Gemini caches keep working. **Without instructions the system prompt is byte-for-byte the shared one** (and no closing block is added); the queue (including its cost estimate), single paragraphs and whole chapters use the same prompt.
- **UI.** A counter «N / 4000 символів · ≈ M токенів» (≈ 3 characters per token), «Записати інструкції» saves every changed text, and the text is sent to the provider with each request (the hint says so). **«Показати фінальний промпт»** opens a read-only window with the system prompt for the open project and the selected engine with every layer and no book text, and «≈ N токенів». With no unsaved changes it shows the saved state; if the selected engine has unsaved text in the field (global and/or project), the prompt is built from that text by `POST /api/projects/{id}/engine-prompt/{engine}/preview` (body `{global?, project?}`; a scope that is missing keeps its saved text; the same 4000-character limit; **nothing is written**) and the window is marked «Чернетка — не збережено».
- **Tracking.** `promptHash` = the first 8 characters of SHA-256 over the engine name and the composed instruction block (the same text for two engines gives two hashes; the glossary and rules are not part of it); «—» for an empty block. It is written into the `[… PROMPT]` and `[… USAGE]` log lines, into `usageSummary.promptHash` and into the new column `paragraph_translation_variants.prompt_hash` (idempotent migration) of every version the engine makes, and shown in the version tooltip («інструкції #a1b2c3d4»; «інструкції —» for a version made without instructions or before this feature).
- **Tests:** `tests/test_engine_instructions.py` (empty instructions give the same bytes, the order of layers, the format reminder after the user's text, the hash, the limit, the migration, the real request and the preview), `e2e/engine-instructions.spec.ts` (saving, tabs and the scope switch, the final prompt, the hash in the tooltip).

## Tests

```bash
npm test
```

Backend provider tests use an injected fake HTTP transport and never call the real DeepL, Claude, OpenAI or Gemini APIs; `e2e/server.py` answers those providers locally. E2E tests require `WORKBENCH_CREDENTIALS_KEY` to be set before Playwright starts the server.

### Run the full suite the way CI does

CI (`.github/workflows/deploy.yml`) runs `npm test` on every pull request against `main` and on every push to `main`, with an
ephemeral `WORKBENCH_CREDENTIALS_KEY`. Do the same locally; anything else gives a misleading result:

```bash
# 1. Free port 8000: an old e2e server keeps the key it was started with (Playwright reuses a running server outside CI).
fuser -k 8000/tcp 2>/dev/null || true
# 2. An ephemeral key, exported before Playwright starts the server.
export WORKBENCH_CREDENTIALS_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
# 3. The same command as CI; CI=1 gives the CI retries (2) and a single worker.
CI=1 npm test
```

There is no step for the database: the e2e server never uses the application's own `database/workbench.sqlite3`.

- **The e2e server's data is throwaway.** `e2e/server.py` calls `e2e/e2e_db.py` before it imports the backend. Unless
  `WORKBENCH_DATABASE_PATH` and `WORKBENCH_LOG_DIR` are set, it makes a fresh `workbench-e2e-*` directory in the system temp
  directory (an empty database and its own logs) and removes that directory when the server exits normally or gets SIGTERM/SIGINT
  (a SIGKILL, for example from `fuser -k`, cannot be caught: the directory then stays in the system temp, which is harmless).
  Every server start begins clean, so a Connection left by an earlier run can never break the next one.
- **The application's data cannot be reached from there.** The backend reads `WORKBENCH_DATABASE_PATH` (default
  `database/workbench.sqlite3`; unset in production) and `WORKBENCH_LOG_DIR` (default `logs/`). `e2e_db.py` refuses to start if the
  database is, or lies inside, `database/` or `logs/` (symlinks and `..` are resolved first), or is not a `*.sqlite3` file, and
  the only thing it ever deletes is the temporary directory it created itself (checked again before deleting: in the system temp
  directory, the `workbench-e2e-` prefix, not a symlink). Covered by `tests/test_e2e_isolation.py`. Do not add `rm` of
  `database/` to any script or instruction.
- **Without the key** every test that creates a Connection fails with `Credential storage is unavailable` (about 40 tests at the
  time of writing). That list is an artefact of the environment, **not a baseline**: do not compare a change against it, because a
  real regression in those tests hides inside it.
- A single spec: `npx playwright test e2e/<name>.spec.ts`, with the same exported key (and `fuser -k 8000/tcp` when the key changes).
- Playwright browsers: `npx playwright install --with-deps chromium` (CI does this). If the sandbox only has a preinstalled Chromium of
  another build, point `launchOptions.executablePath` at it in a **throwaway** config outside the repository; do not commit that.
- Known flaky: `e2e/compare-engines.spec.ts` «→ Вручну» (text selection) failed once in CI and passed on retry; it has not been investigated.

## Deployment

`.github/workflows/deploy.yml` runs the full test suite (`npm test`) on every pull request against `main` and on every push to
`main`. Deployment to the production VPS only runs for a push to `main`, and only if the tests pass (never for a pull request). Deployment does `git fetch`/`git reset --hard` to `origin/main`,
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
