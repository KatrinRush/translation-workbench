from pathlib import Path

def patch(file_path, old, new, label):
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[{label}] Очікував 1 збіг, знайшов {count}. Нічого не змінено.")
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"OK: {label}")

# 1) api.js — новий метод
patch(
    "frontend/api.js",
    '''    translateChapter(projectId, chapterId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/translate`, {
            method: 'POST',
            body: JSON.stringify({})
        });
    },''',
    '''    translateChapter(projectId, chapterId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/translate`, {
            method: 'POST',
            body: JSON.stringify({})
        });
    },

    checkChapterGenderAgreement(projectId, chapterId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/check-gender-agreement`, {
            method: 'POST',
            body: JSON.stringify({})
        });
    },''',
    "api.js: checkChapterGenderAgreement",
)

# 2) app.js — кнопка
patch(
    "frontend/app.js",
    '''translateChapterButton.addEventListener('click', translateCurrentChapter);''',
    '''translateChapterButton.addEventListener('click', translateCurrentChapter);

const checkGenderAgreementButton = document.createElement('button');
checkGenderAgreementButton.type = 'button';
checkGenderAgreementButton.className = 'secondary-btn';
checkGenderAgreementButton.id = 'check-gender-agreement-button';
checkGenderAgreementButton.textContent = 'Перевірити узгодження';
translateChapterButton.insertAdjacentElement('afterend', checkGenderAgreementButton);
checkGenderAgreementButton.addEventListener('click', checkCurrentChapterGenderAgreement);

const genderAgreementStatus = document.createElement('span');
genderAgreementStatus.className = 'paragraph-status';
genderAgreementStatus.id = 'gender-agreement-status';
checkGenderAgreementButton.insertAdjacentElement('afterend', genderAgreementStatus);''',
    "app.js: button + status element",
)

# 3) app.js — disabled state sync
patch(
    "frontend/app.js",
    '''    translateChapterButton.disabled = !chapter.chapterId;
    chapterExportCheckbox.checked = Boolean(chapter.excludeFromExport);''',
    '''    translateChapterButton.disabled = !chapter.chapterId;
    checkGenderAgreementButton.disabled = !chapter.chapterId;
    genderAgreementStatus.textContent = '';
    chapterExportCheckbox.checked = Boolean(chapter.excludeFromExport);''',
    "app.js: disabled state sync + reset stale status",
)

# 4) app.js — самі функції перевірки/рендеру
patch(
    "frontend/app.js",
    '''    } finally {
        translateChapterButton.disabled = false;
        translateChapterButton.textContent = previousText;
    }
}

function undoTranslation() {''',
    '''    } finally {
        translateChapterButton.disabled = false;
        translateChapterButton.textContent = previousText;
    }
}

async function checkCurrentChapterGenderAgreement() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId) {
        return;
    }
    const previousText = checkGenderAgreementButton.textContent;
    checkGenderAgreementButton.disabled = true;
    checkGenderAgreementButton.textContent = 'Перевіряємо…';
    genderAgreementStatus.textContent = '';
    clearGenderAgreementIssues();
    try {
        const result = await WorkbenchApi.checkChapterGenderAgreement(currentProject.projectId, chapter.chapterId);
        renderGenderAgreementResults(result);
    } catch (error) {
        genderAgreementStatus.textContent = `Помилка перевірки: ${error.message}`;
    } finally {
        checkGenderAgreementButton.disabled = false;
        checkGenderAgreementButton.textContent = previousText;
    }
}

function clearGenderAgreementIssues() {
    translationRows.querySelectorAll('.gender-issues').forEach((panel) => panel.remove());
}

function renderGenderAgreementResults(result) {
    clearGenderAgreementIssues();
    const paragraphResults = result.paragraphResults || [];
    if (paragraphResults.length === 0) {
        genderAgreementStatus.textContent = 'Узгодження перевірено — розбіжностей не знайдено.';
        return;
    }
    const totalIssues = paragraphResults.reduce((sum, item) => sum + item.issues.length, 0);
    genderAgreementStatus.textContent = `Знайдено ${totalIssues} можливих розбіжностей роду у ${paragraphResults.length} абзацах.`;

    const genderLabels = { femn: 'жін.', masc: 'чол.', plur: 'мн. (на «ви»)' };

    paragraphResults.forEach((paragraphResult) => {
        const row = translationRows.querySelector(`.translation-row[data-paragraph-id="${CSS.escape(paragraphResult.paragraphId)}"]`);
        if (!row) {
            return;
        }
        const textarea = row.querySelector('.translation-paragraph');
        const panel = document.createElement('div');
        panel.className = 'gender-issues';
        paragraphResult.issues.forEach((issue) => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'gender-issue-chip';
            const expectedLabel = genderLabels[issue.expectedGender] || issue.expectedGender;
            const foundLabel = genderLabels[issue.foundGender] || issue.foundGender;
            chip.textContent = `«${issue.word}» — ${foundLabel}, очікували ${expectedLabel} (${issue.name})`;
            chip.addEventListener('click', () => {
                if (!textarea) {
                    return;
                }
                textarea.focus();
                textarea.setSelectionRange(issue.wordStart, issue.wordEnd);
                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            });
            panel.append(chip);
        });
        const translationControl = row.querySelector('.translation-control');
        if (translationControl) {
            translationControl.insertAdjacentElement('afterend', panel);
        } else {
            row.append(panel);
        }
    });
}

function undoTranslation() {''',
    "app.js: check/render functions",
)

print("\\nГотово, всі 4 патчі застосовано.")
