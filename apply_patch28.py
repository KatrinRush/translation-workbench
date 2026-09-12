"""
Patch 28: card-based UI for the DeepL translation-glossary editor
(Переклад -> Глосарій), replacing the always-editable table with:
  - view mode: "Оригінал -> Переклад" + badges for only the filled-in
    optional fields (context/speechRegister/gender/indeclinable) + a pencil
    (edit) icon + a x (delete) icon
  - edit mode: a compact stacked form (reusing the existing .inline-form
    look) with Зберегти/Скасувати
Скасувати reverts to the snapshot taken when editing started; for a
brand-new term (added via "+ Додати термін"), Скасувати removes it
entirely instead, since it never existed before. "+ Додати термін" now
opens straight into edit mode.

Depends on patch 27 already being applied (adds the "Мовний регістр"
column/field this patch's cards also show).

Run from the repo root (same folder as frontend/index.html, frontend/app.js,
frontend/styles.css):
    python apply_patch28.py
"""
from pathlib import Path

INDEX_HTML_PATH = Path("frontend/index.html")
APP_JS_PATH = Path("frontend/app.js")
STYLES_CSS_PATH = Path("frontend/styles.css")


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
    # 1. index.html: replace the <table> with a plain container div. Same id
    #    (translation-glossary-entries) so every existing JS lookup still works.
    apply(
        INDEX_HTML_PATH,
        '''                                                        <table class="translation-glossary-table">
                                                                <thead><tr><th>Оригінал</th><th>Переклад</th><th>Коментар / контекст</th><th class="col-speech-register">Мовний регістр</th><th class="col-gender">Рід</th><th class="col-indeclinable">Незмінюваний</th><th></th></tr></thead>
                                                                <tbody id="translation-glossary-entries"></tbody>
                                                        </table>''',
        '''                                                        <div id="translation-glossary-entries" class="translation-glossary-cards"></div>''',
    )

    # 2. styles.css: new rules for the card view/form
    apply(
        STYLES_CSS_PATH,
        '''.translation-glossary-table-wrap {
    overflow-x: auto;
}''',
        '''.translation-glossary-table-wrap {
    overflow-x: auto;
}

.translation-glossary-cards {
    display: grid;
    gap: 10px;
}

.translation-glossary-card {
    padding: 12px;
    background: var(--color-bg-surface);
    border: 1px solid var(--color-border);
    border-radius: 8px;
}

.translation-glossary-card-header {
    display: flex;
    align-items: center;
    gap: 4px;
}

.translation-glossary-card-title {
    flex: 1 1 auto;
    font-weight: 600;
    overflow-wrap: anywhere;
}

.translation-glossary-card-fields {
    margin: 10px 0 0;
}

.translation-glossary-card-fields > div {
    padding: 8px 10px;
    background: var(--color-bg-inset);
}

.translation-glossary-card-form {
    gap: 10px;
}''',
    )

    # 3. app.js: new editing-state variables next to the existing draft state
    apply(
        APP_JS_PATH,
        '''let editingTranslationGlossaryId = null;
let translationGlossaryDraft = [];
let translationGlossaryCatalog = [];''',
        '''let editingTranslationGlossaryId = null;
let translationGlossaryDraft = [];
let translationGlossaryCatalog = [];
let editingTranslationGlossaryDraftId = null;
let editingTranslationGlossaryDraftIsNew = false;
let editingTranslationGlossaryDraftSnapshot = null;''',
    )

    # 4. Reset the new editing state whenever the whole editor is opened/closed,
    #    so a leftover edit-in-progress can't bleed into the next time it opens.
    apply(
        APP_JS_PATH,
        '''    translationGlossaryEntries.replaceChildren();
    translationGlossaryDraft = [];

    try {
        translationGlossaryCatalog = await WorkbenchApi.listGlossary();''',
        '''    translationGlossaryEntries.replaceChildren();
    translationGlossaryDraft = [];
    editingTranslationGlossaryDraftId = null;
    editingTranslationGlossaryDraftIsNew = false;
    editingTranslationGlossaryDraftSnapshot = null;

    try {
        translationGlossaryCatalog = await WorkbenchApi.listGlossary();''',
    )
    apply(
        APP_JS_PATH,
        '''function closeTranslationGlossaryEditor() {
    editingTranslationGlossaryId = null;
    translationGlossaryDraft = [];
    translationGlossaryCatalog = [];''',
        '''function closeTranslationGlossaryEditor() {
    editingTranslationGlossaryId = null;
    translationGlossaryDraft = [];
    translationGlossaryCatalog = [];
    editingTranslationGlossaryDraftId = null;
    editingTranslationGlossaryDraftIsNew = false;
    editingTranslationGlossaryDraftSnapshot = null;''',
    )

    # 5. Replace the table-row renderer with the card view/form renderer.
    apply(
        APP_JS_PATH,
        '''function renderTranslationGlossaryDraft() {
    translationGlossaryEntries.replaceChildren();
    translationGlossaryDraft.forEach((draftItem) => {
        const row = document.createElement('tr');
        row.dataset.glossaryDraftId = draftItem.draftId;
        const fields = [
            ['source', 'Оригінальний термін', true],
            ['target', 'Бажаний переклад', true],
            ['context', 'Необов’язково', false],
        ];
        fields.forEach(([name, placeholder, required]) => {
            const cell = document.createElement('td');
            const input = document.createElement('input');
            input.type = 'text';
            input.placeholder = placeholder;
            input.value = draftItem[name] || '';
            input.required = required;
            input.dataset.glossaryEntryField = name;
            input.addEventListener('input', () => {
                draftItem[name] = input.value;
                draftItem.glossaryEntryId = null;
                renderTranslationGlossaryExistingEntryOptions();
            });
            cell.append(input);
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

        const genderCell = document.createElement('td');
        genderCell.className = 'col-gender';
        const genderSelect = document.createElement('select');
        populateGenderSelectOptions(genderSelect);
        genderSelect.value = draftItem.characterGender || '';
        genderSelect.dataset.glossaryEntryField = 'characterGender';
        genderSelect.addEventListener('change', () => {
            draftItem.characterGender = genderSelect.value;
        });
        genderCell.append(genderSelect);
        row.append(genderCell);

        const indeclinableCell = document.createElement('td');
        indeclinableCell.className = 'col-indeclinable';
        const indeclinableCheckbox = document.createElement('input');
        indeclinableCheckbox.type = 'checkbox';
        indeclinableCheckbox.className = 'indeclinable-checkbox';
        indeclinableCheckbox.checked = Boolean(draftItem.indeclinable);
        indeclinableCheckbox.dataset.glossaryEntryField = 'indeclinable';
        indeclinableCheckbox.addEventListener('change', () => {
            draftItem.indeclinable = indeclinableCheckbox.checked;
        });
        indeclinableCell.append(indeclinableCheckbox);
        row.append(indeclinableCell);

        const actionCell = document.createElement('td');
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'icon-btn';
        remove.setAttribute('aria-label', 'Видалити термін');
        remove.textContent = '×';
        remove.addEventListener('click', () => {
            translationGlossaryDraft = translationGlossaryDraft.filter((item) => item.draftId !== draftItem.draftId);
            renderTranslationGlossaryDraft();
        });
        actionCell.append(remove);
        row.append(actionCell);
        translationGlossaryEntries.append(row);
    });
    renderTranslationGlossaryExistingEntryOptions();
}''',
        '''const TRANSLATION_GLOSSARY_GENDER_LABELS = { femn: 'Жіночий', masc: 'Чоловічий', plur: 'На «ви» / небінарний' };

function renderTranslationGlossaryDraft() {
    translationGlossaryEntries.replaceChildren();
    translationGlossaryDraft.forEach((draftItem) => {
        const card = draftItem.draftId === editingTranslationGlossaryDraftId
            ? buildTranslationGlossaryCardForm(draftItem)
            : buildTranslationGlossaryCardView(draftItem);
        translationGlossaryEntries.append(card);
    });
    renderTranslationGlossaryExistingEntryOptions();
}

function startEditingTranslationGlossaryDraft(draftItem, isNew) {
    editingTranslationGlossaryDraftId = draftItem.draftId;
    editingTranslationGlossaryDraftIsNew = isNew;
    editingTranslationGlossaryDraftSnapshot = {
        source: draftItem.source,
        target: draftItem.target,
        context: draftItem.context,
        characterGender: draftItem.characterGender,
        speechRegister: draftItem.speechRegister,
        indeclinable: draftItem.indeclinable,
    };
    renderTranslationGlossaryDraft();
}

function stopEditingTranslationGlossaryDraft() {
    editingTranslationGlossaryDraftId = null;
    editingTranslationGlossaryDraftIsNew = false;
    editingTranslationGlossaryDraftSnapshot = null;
}

function buildTranslationGlossaryCardView(draftItem) {
    const card = document.createElement('div');
    card.className = 'translation-glossary-card';
    card.dataset.glossaryDraftId = draftItem.draftId;

    const header = document.createElement('div');
    header.className = 'translation-glossary-card-header';

    const title = document.createElement('span');
    title.className = 'translation-glossary-card-title';
    title.textContent = `${draftItem.source || '—'} → ${draftItem.target || '—'}`;
    header.append(title);

    const edit = document.createElement('button');
    edit.type = 'button';
    edit.className = 'icon-btn';
    edit.setAttribute('aria-label', 'Редагувати термін');
    edit.textContent = '✎';
    edit.addEventListener('click', () => startEditingTranslationGlossaryDraft(draftItem, false));
    header.append(edit);

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'icon-btn';
    remove.setAttribute('aria-label', 'Видалити термін');
    remove.textContent = '×';
    remove.addEventListener('click', () => {
        translationGlossaryDraft = translationGlossaryDraft.filter((item) => item.draftId !== draftItem.draftId);
        renderTranslationGlossaryDraft();
    });
    header.append(remove);

    card.append(header);

    const badgeFields = [
        ['Коментар / контекст', draftItem.context],
        ['Мовний регістр', draftItem.speechRegister],
        ['Рід', TRANSLATION_GLOSSARY_GENDER_LABELS[draftItem.characterGender] || ''],
        ['Незмінюваний', draftItem.indeclinable ? 'Так' : ''],
    ].filter(([, value]) => value);

    if (badgeFields.length > 0) {
        const dl = document.createElement('dl');
        dl.className = 'project-information translation-glossary-card-fields';
        badgeFields.forEach(([label, value]) => {
            const wrap = document.createElement('div');
            const dt = document.createElement('dt');
            dt.textContent = label;
            const dd = document.createElement('dd');
            dd.textContent = value;
            wrap.append(dt, dd);
            dl.append(wrap);
        });
        card.append(dl);
    }

    return card;
}

function buildTranslationGlossaryCardForm(draftItem) {
    const card = document.createElement('div');
    card.className = 'translation-glossary-card translation-glossary-card-form inline-form';
    card.dataset.glossaryDraftId = draftItem.draftId;

    const textFields = [
        ['source', 'Оригінал', 'Оригінальний термін', true],
        ['target', 'Переклад', 'Бажаний переклад', true],
        ['context', 'Коментар / контекст', 'Необов’язково', false],
        ['speechRegister', 'Мовний регістр', 'Напр. "постійна лайка"', false],
    ];
    textFields.forEach(([name, labelText, placeholder, required]) => {
        const label = document.createElement('label');
        label.textContent = labelText;
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = placeholder;
        input.value = draftItem[name] || '';
        input.required = required;
        input.dataset.glossaryEntryField = name;
        input.addEventListener('input', () => {
            draftItem[name] = input.value;
            draftItem.glossaryEntryId = null;
        });
        label.append(input);
        card.append(label);
    });

    const genderLabel = document.createElement('label');
    genderLabel.textContent = 'Рід персонажа (для перевірки узгодження)';
    const genderSelect = document.createElement('select');
    populateGenderSelectOptions(genderSelect);
    genderSelect.value = draftItem.characterGender || '';
    genderSelect.dataset.glossaryEntryField = 'characterGender';
    genderSelect.addEventListener('change', () => {
        draftItem.characterGender = genderSelect.value;
    });
    genderLabel.append(genderSelect);
    card.append(genderLabel);

    const indeclinableLabel = document.createElement('label');
    indeclinableLabel.className = 'checkbox-item';
    const indeclinableCheckbox = document.createElement('input');
    indeclinableCheckbox.type = 'checkbox';
    indeclinableCheckbox.className = 'indeclinable-checkbox';
    indeclinableCheckbox.checked = Boolean(draftItem.indeclinable);
    indeclinableCheckbox.dataset.glossaryEntryField = 'indeclinable';
    indeclinableCheckbox.addEventListener('change', () => {
        draftItem.indeclinable = indeclinableCheckbox.checked;
    });
    const indeclinableText = document.createElement('span');
    indeclinableText.textContent = 'Незмінюваний термін (не відмінюється)';
    indeclinableLabel.append(indeclinableCheckbox, indeclinableText);
    card.append(indeclinableLabel);

    const actions = document.createElement('div');
    actions.className = 'inline-form-actions';

    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.className = 'secondary-btn';
    cancel.textContent = 'Скасувати';
    cancel.addEventListener('click', () => {
        if (editingTranslationGlossaryDraftIsNew) {
            translationGlossaryDraft = translationGlossaryDraft.filter((item) => item.draftId !== draftItem.draftId);
        } else if (editingTranslationGlossaryDraftSnapshot) {
            Object.assign(draftItem, editingTranslationGlossaryDraftSnapshot);
        }
        stopEditingTranslationGlossaryDraft();
        renderTranslationGlossaryDraft();
    });
    actions.append(cancel);

    const save = document.createElement('button');
    save.type = 'button';
    save.className = 'primary-btn';
    save.textContent = 'Зберегти';
    save.addEventListener('click', () => {
        if (!String(draftItem.source || '').trim() || !String(draftItem.target || '').trim()) {
            window.alert('Оригінал і переклад терміна обов’язкові.');
            return;
        }
        stopEditingTranslationGlossaryDraft();
        renderTranslationGlossaryDraft();
    });
    actions.append(save);

    card.append(actions);
    return card;
}''',
    )

    # 6. "+ Додати термін" now opens the new row straight into edit mode.
    apply(
        APP_JS_PATH,
        '''function addTranslationGlossaryEntry(entry = {}) {
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
        '''function addTranslationGlossaryEntry(entry = {}) {
    const draftItem = {
        draftId: crypto.randomUUID(),
        glossaryEntryId: entry.glossaryEntryId || null,
        source: entry.source || '',
        target: entry.target || '',
        context: entry.context || '',
        characterGender: entry.characterGender || '',
        speechRegister: entry.speechRegister || '',
        indeclinable: Boolean(entry.indeclinable),
    };
    translationGlossaryDraft.push(draftItem);
    startEditingTranslationGlossaryDraft(draftItem, true);
}''',
    )

    print("Patch 28 applied successfully.")


if __name__ == "__main__":
    main()
