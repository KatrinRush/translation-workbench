"""
Patch 26: character speech-register field in the glossary UI (app.js).

Adds a free-text "Мовний регістр" input next to the existing gender select
and indeclinable checkbox in attachGlossaryExtraFields (used by both the
references-glossary and project-glossary forms), wires it through
createGlossaryEntry / addReferencesGlossaryEntry / createProjectGlossaryEntry,
and adds it to the prompt()-based editGlossaryEntry flow. Backend support
(storage.py speech_register column) landed in patch 25.

Run from the repo root (same folder as frontend/app.js):
    python apply_patch26.py
"""
from pathlib import Path

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
    # 1. attachGlossaryExtraFields: add the speech-register text input,
    #    inserted between the note and the indeclinable/gender fields so
    #    the visual order is note -> speech register -> gender -> indeclinable.
    apply(
        APP_JS_PATH,
        '''    indeclinableLabel.append(indeclinableCheckbox, indeclinableText);

    noteInput.insertAdjacentElement('afterend', indeclinableLabel);
    noteInput.insertAdjacentElement('afterend', genderLabel);

    return { genderSelect, indeclinableCheckbox };
}''',
        '''    indeclinableLabel.append(indeclinableCheckbox, indeclinableText);

    const speechRegisterLabel = document.createElement('label');
    speechRegisterLabel.className = 'field-label';
    speechRegisterLabel.textContent = 'Мовний регістр (напр. "постійна лайка", "формальна мова")';
    const speechRegisterInput = document.createElement('input');
    speechRegisterInput.type = 'text';
    speechRegisterInput.id = `${idPrefix}-speech-register`;
    speechRegisterLabel.append(speechRegisterInput);

    noteInput.insertAdjacentElement('afterend', indeclinableLabel);
    noteInput.insertAdjacentElement('afterend', genderLabel);
    noteInput.insertAdjacentElement('afterend', speechRegisterLabel);

    return { genderSelect, indeclinableCheckbox, speechRegisterInput };
}''',
    )

    # 2. Module-level references-glossary form: also grab speechRegisterInput
    apply(
        APP_JS_PATH,
        '''const { genderSelect: referencesGlossaryGenderSelect, indeclinableCheckbox: referencesGlossaryIndeclinableCheckbox } = attachGlossaryExtraFields(referencesGlossaryNoteInput, 'references-glossary');''',
        '''const { genderSelect: referencesGlossaryGenderSelect, indeclinableCheckbox: referencesGlossaryIndeclinableCheckbox, speechRegisterInput: referencesGlossarySpeechRegisterInput } = attachGlossaryExtraFields(referencesGlossaryNoteInput, 'references-glossary');''',
    )

    # 3. Module-level project-glossary form: same
    apply(
        APP_JS_PATH,
        '''const { genderSelect: projectGlossaryGenderSelect, indeclinableCheckbox: projectGlossaryIndeclinableCheckbox } = attachGlossaryExtraFields(projectGlossaryNoteInput, 'project-glossary');''',
        '''const { genderSelect: projectGlossaryGenderSelect, indeclinableCheckbox: projectGlossaryIndeclinableCheckbox, speechRegisterInput: projectGlossarySpeechRegisterInput } = attachGlossaryExtraFields(projectGlossaryNoteInput, 'project-glossary');''',
    )

    # 4. createGlossaryEntry: accept + send the new field
    apply(
        APP_JS_PATH,
        '''async function createGlossaryEntry(source, target, note, characterGender, indeclinable) {
    const entry = await WorkbenchApi.createGlossaryEntry({
        source,
        target,
        note,
        characterGender: characterGender || null,
        indeclinable: Boolean(indeclinable),
        active: true,
    });
    mockGlossaryEntries.push(entry);
    return entry;
}''',
        '''async function createGlossaryEntry(source, target, note, characterGender, indeclinable, speechRegister) {
    const entry = await WorkbenchApi.createGlossaryEntry({
        source,
        target,
        note,
        characterGender: characterGender || null,
        indeclinable: Boolean(indeclinable),
        speechRegister: speechRegister || null,
        active: true,
    });
    mockGlossaryEntries.push(entry);
    return entry;
}''',
    )

    # 5. addReferencesGlossaryEntry: pass + reset the new field
    apply(
        APP_JS_PATH,
        '''        const entry = await createGlossaryEntry(
            source,
            target,
            referencesGlossaryNoteInput.value.trim() || null,
            referencesGlossaryGenderSelect.value || null,
            referencesGlossaryIndeclinableCheckbox.checked
        );
        referencesDraft.glossaryEntryIds.push(entry.glossaryEntryId);
        renderReferencesGlossary();
        referencesGlossarySourceInput.value = '';
        referencesGlossaryTargetInput.value = '';
        referencesGlossaryNoteInput.value = '';
        referencesGlossaryGenderSelect.value = '';
        referencesGlossaryIndeclinableCheckbox.checked = false;
        toggleInlineForm(referencesGlossaryForm, false);''',
        '''        const entry = await createGlossaryEntry(
            source,
            target,
            referencesGlossaryNoteInput.value.trim() || null,
            referencesGlossaryGenderSelect.value || null,
            referencesGlossaryIndeclinableCheckbox.checked,
            referencesGlossarySpeechRegisterInput.value.trim() || null
        );
        referencesDraft.glossaryEntryIds.push(entry.glossaryEntryId);
        renderReferencesGlossary();
        referencesGlossarySourceInput.value = '';
        referencesGlossaryTargetInput.value = '';
        referencesGlossaryNoteInput.value = '';
        referencesGlossaryGenderSelect.value = '';
        referencesGlossaryIndeclinableCheckbox.checked = false;
        referencesGlossarySpeechRegisterInput.value = '';
        toggleInlineForm(referencesGlossaryForm, false);''',
    )

    # 6. createProjectGlossaryEntry: pass + reset the new field
    apply(
        APP_JS_PATH,
        '''    const entry = await createGlossaryEntry(
        source,
        target,
        projectGlossaryNoteInput.value.trim() || null,
        projectGlossaryGenderSelect.value || null,
        projectGlossaryIndeclinableCheckbox.checked
    );
    newProjectDraft.projectGlossaryEntryIds.push(entry.glossaryEntryId);
    renderProjectGlossary();
    projectGlossarySourceInput.value = '';
    projectGlossaryTargetInput.value = '';
    projectGlossaryNoteInput.value = '';
    projectGlossaryGenderSelect.value = '';
    projectGlossaryIndeclinableCheckbox.checked = false;
    toggleInlineForm(projectGlossaryForm, false);''',
        '''    const entry = await createGlossaryEntry(
        source,
        target,
        projectGlossaryNoteInput.value.trim() || null,
        projectGlossaryGenderSelect.value || null,
        projectGlossaryIndeclinableCheckbox.checked,
        projectGlossarySpeechRegisterInput.value.trim() || null
    );
    newProjectDraft.projectGlossaryEntryIds.push(entry.glossaryEntryId);
    renderProjectGlossary();
    projectGlossarySourceInput.value = '';
    projectGlossaryTargetInput.value = '';
    projectGlossaryNoteInput.value = '';
    projectGlossaryGenderSelect.value = '';
    projectGlossaryIndeclinableCheckbox.checked = false;
    projectGlossarySpeechRegisterInput.value = '';
    toggleInlineForm(projectGlossaryForm, false);''',
    )

    # 7. editGlossaryEntry: prompt for + persist the new field
    apply(
        APP_JS_PATH,
        '''    const indeclinable = window.confirm('Це незмінюваний термін? OK — так, Скасувати — ні.');
    try {
        const updated = await WorkbenchApi.updateGlossaryEntry(entry.glossaryEntryId, {
            ...entry,
            source,
            target,
            note,
            characterGender: genderInput || null,
            indeclinable,
        });''',
        '''    const indeclinable = window.confirm('Це незмінюваний термін? OK — так, Скасувати — ні.');
    const speechRegister = window.prompt('Мовний регістр (напр. "постійна лайка", порожньо — немає):', entry.speechRegister || '')?.trim() || null;
    try {
        const updated = await WorkbenchApi.updateGlossaryEntry(entry.glossaryEntryId, {
            ...entry,
            source,
            target,
            note,
            characterGender: genderInput || null,
            indeclinable,
            speechRegister,
        });''',
    )

    print("Patch 26 applied successfully.")


if __name__ == "__main__":
    main()
