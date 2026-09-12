"""
Patch 27: speech-register column in the DeepL translation-glossary table
(Переклад -> Глосарій, the table with Оригінал/Переклад/Коментар/Рід/
Незмінюваний columns Катя actually uses day-to-day — distinct from the
references/project catalog forms patched in patch 26).

Draft rows in this table always resolve into real glossary_entries rows via
resolveDraftGlossaryEntryIds() (create or sync-to-catalog), so wiring
speechRegister through here persists it the same way gender/indeclinable
already do. Backend column (storage.py) landed in patch 25.

Run from the repo root (same folder as frontend/index.html, frontend/app.js):
    python apply_patch27.py
"""
from pathlib import Path

INDEX_HTML_PATH = Path("frontend/index.html")
APP_JS_PATH = Path("frontend/app.js")


def apply(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    occurrences = text.count(old)
    if occurrences != count:
        raise SystemExit(
            f"Expected {count} occurrence(s) of snippet in {path}, found {occurrences}.\n"
            f"--- snippet ---\n{old}\n---------------"
        )
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def main() -> None:
    # 1. Table header: new column between "Коментар / контекст" and "Рід"
    apply(
        INDEX_HTML_PATH,
        '<thead><tr><th>Оригінал</th><th>Переклад</th><th>Коментар / контекст</th><th class="col-gender">Рід</th><th class="col-indeclinable">Незмінюваний</th><th></th></tr></thead>',
        '<thead><tr><th>Оригінал</th><th>Переклад</th><th>Коментар / контекст</th><th class="col-speech-register">Мовний регістр</th><th class="col-gender">Рід</th><th class="col-indeclinable">Незмінюваний</th><th></th></tr></thead>',
    )

    # 2. Loading an existing glossary version into the draft: carry speechRegister
    apply(
        APP_JS_PATH,
        '''            translationGlossaryDraft = materialized.entries.map((entry, index) => ({
                draftId: crypto.randomUUID(),
                glossaryEntryId: currentVersion.glossaryEntryIds[index] || null,
                source: entry.source || '',
                target: entry.target || '',
                context: entry.context || '',
                characterGender: entry.characterGender || '',
                indeclinable: Boolean(entry.indeclinable),
            }));''',
        '''            translationGlossaryDraft = materialized.entries.map((entry, index) => ({
                draftId: crypto.randomUUID(),
                glossaryEntryId: currentVersion.glossaryEntryIds[index] || null,
                source: entry.source || '',
                target: entry.target || '',
                context: entry.context || '',
                characterGender: entry.characterGender || '',
                speechRegister: entry.speechRegister || '',
                indeclinable: Boolean(entry.indeclinable),
            }));''',
    )

    # 3. Row rendering: new text-input cell between the context field and the gender select
    apply(
        APP_JS_PATH,
        '''            cell.append(input);
            row.append(cell);
        });

        const genderCell = document.createElement('td');''',
        '''            cell.append(input);
            row.append(cell);
        });

        const speechRegisterCell = document.createElement('td');
        speechRegisterCell.className = 'col-speech-register';
        const speechRegisterInput = document.createElement('input');
        speechRegisterInput.type = 'text';
        speechRegisterInput.placeholder = 'Напр. "постійна лайка"';
        speechRegisterInput.value = draftItem.speechRegister || '';
        speechRegisterInput.dataset.glossaryEntryField = 'speechRegister';
        speechRegisterInput.addEventListener('input', () => {
            draftItem.speechRegister = speechRegisterInput.value;
        });
        speechRegisterCell.append(speechRegisterInput);
        row.append(speechRegisterCell);

        const genderCell = document.createElement('td');''',
    )

    # 4. Adding an entry from the catalog picker, and adding a blank new row:
    #    carry/default speechRegister in both push() payloads
    apply(
        APP_JS_PATH,
        '''    translationGlossaryDraft.push({
        draftId: crypto.randomUUID(),
        glossaryEntryId: entry.glossaryEntryId,
        source: entry.source,
        target: entry.target,
        context: entry.note || '',
        characterGender: entry.characterGender || '',
        indeclinable: Boolean(entry.indeclinable),
    });
    renderTranslationGlossaryDraft();
}

function addTranslationGlossaryEntry(entry = {}) {
    translationGlossaryDraft.push({
        draftId: crypto.randomUUID(),
        glossaryEntryId: entry.glossaryEntryId || null,
        source: entry.source || '',
        target: entry.target || '',
        context: entry.context || '',
        characterGender: entry.characterGender || '',
        indeclinable: Boolean(entry.indeclinable),
    });
    renderTranslationGlossaryDraft();
}''',
        '''    translationGlossaryDraft.push({
        draftId: crypto.randomUUID(),
        glossaryEntryId: entry.glossaryEntryId,
        source: entry.source,
        target: entry.target,
        context: entry.note || '',
        characterGender: entry.characterGender || '',
        speechRegister: entry.speechRegister || '',
        indeclinable: Boolean(entry.indeclinable),
    });
    renderTranslationGlossaryDraft();
}

function addTranslationGlossaryEntry(entry = {}) {
    translationGlossaryDraft.push({
        draftId: crypto.randomUUID(),
        glossaryEntryId: entry.glossaryEntryId || null,
        source: entry.source || '',
        target: entry.target || '',
        context: entry.context || '',
        characterGender: entry.characterGender || '',
        speechRegister: entry.speechRegister || '',
        indeclinable: Boolean(entry.indeclinable),
    });
    renderTranslationGlossaryDraft();
}''',
    )

    # 5. syncGlossaryEntryFactsIfNeeded: also push speechRegister to the shared
    #    catalog entry when it changed (same pattern as gender/indeclinable)
    apply(
        APP_JS_PATH,
        '''async function syncGlossaryEntryFactsIfNeeded(catalogEntry, characterGender, indeclinable) {
    const needsGenderUpdate = Boolean(characterGender) && catalogEntry.characterGender !== characterGender;
    const needsIndeclinableUpdate = Boolean(indeclinable) && !catalogEntry.indeclinable;
    if (!needsGenderUpdate && !needsIndeclinableUpdate) {
        return;
    }
    const updated = await WorkbenchApi.updateGlossaryEntry(catalogEntry.glossaryEntryId, {
        ...catalogEntry,
        characterGender: needsGenderUpdate ? characterGender : catalogEntry.characterGender,
        indeclinable: needsIndeclinableUpdate ? true : catalogEntry.indeclinable,
    });
    Object.assign(catalogEntry, updated);
}''',
        '''async function syncGlossaryEntryFactsIfNeeded(catalogEntry, characterGender, indeclinable, speechRegister) {
    const needsGenderUpdate = Boolean(characterGender) && catalogEntry.characterGender !== characterGender;
    const needsIndeclinableUpdate = Boolean(indeclinable) && !catalogEntry.indeclinable;
    const needsRegisterUpdate = Boolean(speechRegister) && catalogEntry.speechRegister !== speechRegister;
    if (!needsGenderUpdate && !needsIndeclinableUpdate && !needsRegisterUpdate) {
        return;
    }
    const updated = await WorkbenchApi.updateGlossaryEntry(catalogEntry.glossaryEntryId, {
        ...catalogEntry,
        characterGender: needsGenderUpdate ? characterGender : catalogEntry.characterGender,
        indeclinable: needsIndeclinableUpdate ? true : catalogEntry.indeclinable,
        speechRegister: needsRegisterUpdate ? speechRegister : catalogEntry.speechRegister,
    });
    Object.assign(catalogEntry, updated);
}''',
    )

    # 6. resolveDraftGlossaryEntryIds: read speechRegister off the draft row and
    #    thread it through both the sync path and the brand-new-entry path
    apply(
        APP_JS_PATH,
        '''        const characterGender = item.characterGender || null;
        const indeclinable = Boolean(item.indeclinable);

        const exactCatalogEntry = translationGlossaryCatalog.find((entry) => (
            entry.source === source && entry.target === target && (entry.note || '') === context
        ));
        if (item.glossaryEntryId && exactCatalogEntry?.glossaryEntryId === item.glossaryEntryId) {
            await syncGlossaryEntryFactsIfNeeded(exactCatalogEntry, characterGender, indeclinable);
            ids.push(item.glossaryEntryId);
            continue;
        }
        if (exactCatalogEntry) {
            await syncGlossaryEntryFactsIfNeeded(exactCatalogEntry, characterGender, indeclinable);
            ids.push(exactCatalogEntry.glossaryEntryId);
            item.glossaryEntryId = exactCatalogEntry.glossaryEntryId;
            continue;
        }

        const created = await WorkbenchApi.createGlossaryEntry({
            source,
            target,
            note: context,
            characterGender,
            indeclinable,
            active: true,
        });''',
        '''        const characterGender = item.characterGender || null;
        const indeclinable = Boolean(item.indeclinable);
        const speechRegister = String(item.speechRegister || '').trim() || null;

        const exactCatalogEntry = translationGlossaryCatalog.find((entry) => (
            entry.source === source && entry.target === target && (entry.note || '') === context
        ));
        if (item.glossaryEntryId && exactCatalogEntry?.glossaryEntryId === item.glossaryEntryId) {
            await syncGlossaryEntryFactsIfNeeded(exactCatalogEntry, characterGender, indeclinable, speechRegister);
            ids.push(item.glossaryEntryId);
            continue;
        }
        if (exactCatalogEntry) {
            await syncGlossaryEntryFactsIfNeeded(exactCatalogEntry, characterGender, indeclinable, speechRegister);
            ids.push(exactCatalogEntry.glossaryEntryId);
            item.glossaryEntryId = exactCatalogEntry.glossaryEntryId;
            continue;
        }

        const created = await WorkbenchApi.createGlossaryEntry({
            source,
            target,
            note: context,
            characterGender,
            indeclinable,
            speechRegister,
            active: true,
        });''',
    )

    print("Patch 27 applied successfully.")


if __name__ == "__main__":
    main()
