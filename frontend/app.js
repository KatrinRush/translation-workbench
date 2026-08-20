const fileInput = document.querySelector('#file-input');
const uploadButton = document.querySelector('#upload-button');
const uploadStatus = document.querySelector('#upload-status');
const workspaceContent = document.querySelector('#workspace-content');
const chapterBrowser = document.querySelector('#chapter-browser');
const chapterList = document.querySelector('#chapter-list');
const chapterPagination = document.querySelector('#chapter-pagination');
const chapterText = document.querySelector('#chapter-text');
const chapterTitle = document.querySelector('#chapter-title');
const chapterNumber = document.querySelector('#chapter-number');
const chapterName = document.querySelector('#chapter-name');
const chapterWordCount = document.querySelector('#chapter-word-count');
const chapterParagraphCount = document.querySelector('#chapter-paragraph-count');
const translationRows = document.querySelector('#translation-rows');
const saveTranslationButton = document.querySelector('#save-translation');
const undoTranslationButton = document.querySelector('#undo-translation');
const redoTranslationButton = document.querySelector('#redo-translation');
const bookReplacementDialog = document.querySelector('#book-replacement-dialog');
const archiveAndUploadButton = document.querySelector('#archive-and-upload');
const replaceWithoutArchiveButton = document.querySelector('#replace-without-archive');
const cancelBookReplacementButton = document.querySelector('#cancel-book-replacement');
const mainScreenView = document.querySelector('#main-screen-view');
const settingsView = document.querySelector('#settings-view');
const projectWorkspaceView = document.querySelector('#project-workspace-view');
const projectPageTitle = document.querySelector('#project-page-title');
const projectPageSummary = document.querySelector('#project-page-summary');
const projectInformation = document.querySelector('#project-information');
const editCurrentProjectButton = document.querySelector('#edit-current-project');
const projectList = document.querySelector('.project-list');
const newProjectButton = document.querySelector('#new-project-button');
const settingsButton = document.querySelector('#settings-button');
const catalogAuthorSearch = document.querySelector('#catalog-author-search');
const catalogSeriesSearch = document.querySelector('#catalog-series-search');
const catalogAuthors = document.querySelector('#catalog-authors');
const catalogSeries = document.querySelector('#catalog-series');
const addCatalogAuthorButton = document.querySelector('#add-catalog-author');
const addCatalogSeriesButton = document.querySelector('#add-catalog-series');
const newProjectDialog = document.querySelector('#new-project-dialog');
const newProjectForm = document.querySelector('#new-project-form');
const closeNewProjectButton = document.querySelector('#close-new-project');
const cancelNewProjectButton = document.querySelector('#cancel-new-project');
const projectTitleInput = document.querySelector('#project-title-input');
const projectBookNumberInput = document.querySelector('#project-book-number-input');
const projectStatusSelect = document.querySelector('#project-status-select');
const authorSearchInput = document.querySelector('#author-search-input');
const projectAuthorSelect = document.querySelector('#project-author-select');
const editAuthorButton = document.querySelector('#edit-author');
const deleteAuthorButton = document.querySelector('#delete-author');
const showNewAuthorButton = document.querySelector('#show-new-author');
const newAuthorForm = document.querySelector('#new-author-form');
const newAuthorNameInput = document.querySelector('#new-author-name');
const cancelNewAuthorButton = document.querySelector('#cancel-new-author');
const addNewAuthorButton = document.querySelector('#add-new-author');
const seriesSearchInput = document.querySelector('#series-search-input');
const projectSeriesSelect = document.querySelector('#project-series-select');
const editSeriesButton = document.querySelector('#edit-series');
const deleteSeriesButton = document.querySelector('#delete-series');
const showNewSeriesButton = document.querySelector('#show-new-series');
const newSeriesForm = document.querySelector('#new-series-form');
const newSeriesNameInput = document.querySelector('#new-series-name');
const newSeriesAuthorSelect = document.querySelector('#new-series-author');
const cancelNewSeriesButton = document.querySelector('#cancel-new-series');
const addNewSeriesButton = document.querySelector('#add-new-series');
const inheritedContent = document.querySelector('#inherited-content');
const inheritedRulesTitle = document.querySelector('#inherited-rules-title');
const inheritedRulesList = document.querySelector('#inherited-rules-list');
const inheritedGlossaryTitle = document.querySelector('#inherited-glossary-title');
const inheritedGlossaryList = document.querySelector('#inherited-glossary-list');
const projectRulesList = document.querySelector('#project-rules-list');
const showProjectRuleFormButton = document.querySelector('#show-project-rule-form');
const projectRuleForm = document.querySelector('#project-rule-form');
const projectRuleTextInput = document.querySelector('#project-rule-text');
const projectRuleCategoryInput = document.querySelector('#project-rule-category');
const cancelProjectRuleButton = document.querySelector('#cancel-project-rule');
const addProjectRuleButton = document.querySelector('#add-project-rule');
const projectGlossaryList = document.querySelector('#project-glossary-list');
const showProjectGlossaryFormButton = document.querySelector('#show-project-glossary-form');
const projectGlossaryForm = document.querySelector('#project-glossary-form');
const projectGlossarySourceInput = document.querySelector('#project-glossary-source');
const projectGlossaryTargetInput = document.querySelector('#project-glossary-target');
const projectGlossaryNoteInput = document.querySelector('#project-glossary-note');
const cancelProjectGlossaryButton = document.querySelector('#cancel-project-glossary');
const addProjectGlossaryButton = document.querySelector('#add-project-glossary');
const newProjectError = document.querySelector('#new-project-error');
const createProjectButton = document.querySelector('#create-project-button');
const backToProjectsButton = document.querySelector('#back-to-projects');
const navigationDialog = document.querySelector('#navigation-dialog');
const saveAndNavigateButton = document.querySelector('#save-and-navigate');
const discardAndNavigateButton = document.querySelector('#discard-and-navigate');
const stayOnChapterButton = document.querySelector('#stay-on-chapter');
const chaptersPerPage = 25;
const projectPositionStoragePrefix = 'translation-workbench:project-position:';
let loadedChapters = [];
let selectedChapterIndex = null;
let currentChapterPage = 1;
let currentParagraphId = null;
let translationStates = new Map();
let pendingNavigation = null;
let newProjectDraft = null;
let currentProject = null;
let editingProjectId = null;
let pendingUploadFile = null;

const labels = {
    filename: 'Файл',
    title: 'Назва',
    author: 'Автор',
    sections: 'Розділів',
    wordCount: 'Приблизна кількість слів',
    paragraphCount: 'Абзаців',
    language: 'Мова',
    analysisStatus: 'Статус аналізу'
};

const mockProjects = [
    {
        projectId: 'project-wind-city',
        title: 'Місто вітру',
        authorId: 'author-olena-kravets',
        seriesId: 'series-north-chronicles',
        status: 'translation',
        progress: {
            progress: 42,
            analysisProgress: 100,
            translationProgress: 42,
            auditProgress: 0
        },
        chapterCount: 0,
        fileName: null,
        createdAt: null,
        updatedAt: null,
        sourceFile: null,
        inheritedRules: [],
        inheritedGlossary: [],
        projectRuleIds: [],
        projectGlossaryEntryIds: [],
        styleNotes: [],
        characterNotes: [],
        contextNotes: []
    }
];

let mockAuthors = [
    { authorId: 'author-olena-kravets', name: 'Олена Кравець' },
    { authorId: 'author-hanna-harp', name: 'Hanna Harp' },
    { authorId: 'author-ariana-nash', name: 'Ariana Nash' }
];

let mockRules = [
    { ruleId: 'rule-character-names', text: 'Імена персонажів', category: 'Персонажі', active: true },
    { ruleId: 'rule-forms-of-address', text: 'Форми звертання', category: 'Стиль', active: true },
    { ruleId: 'rule-dialogue-style', text: 'Особливості діалогів', category: 'Стиль', active: true },
    { ruleId: 'rule-city-names', text: 'Назви міст', category: 'Термінологія', active: true },
    { ruleId: 'rule-world-terms', text: 'Особливості термінології', category: 'Термінологія', active: true },
    { ruleId: 'rule-profanity', text: 'Лайка', category: 'Стиль', active: true },
    { ruleId: 'rule-narrative-style', text: 'Стиль оповіді', category: 'Стиль', active: true },
    { ruleId: 'rule-other', text: 'Інші правила', category: 'Інше', active: true }
];

let mockGlossaryEntries = [
    { glossaryEntryId: 'glossary-snowdrop', source: 'Snowdrop', target: 'Пролісок', active: true },
    { glossaryEntryId: 'glossary-north-sea', source: 'North Sea', target: 'Північне море', active: true },
    { glossaryEntryId: 'glossary-old-house', source: 'Old House', target: 'Старий будинок', active: true },
    { glossaryEntryId: 'glossary-emma', source: 'Emma', target: 'Емма', active: true }
];

let mockSeries = [
    {
        seriesId: 'series-north-chronicles',
        name: 'Хроніки Півночі'
    },
    {
        seriesId: 'series-sos-hotel',
        name: 'SOS Hotel'
    },
    {
        seriesId: 'series-new-species',
        name: 'Нові види'
    }
];

let mockSeriesAuthorContexts = [
    {
        seriesId: 'series-north-chronicles',
        authorId: 'author-olena-kravets',
        ruleIds: mockRules.map((rule) => rule.ruleId),
        glossaryEntryIds: mockGlossaryEntries.map((entry) => entry.glossaryEntryId)
    },
    {
        seriesId: 'series-north-chronicles',
        authorId: 'author-hanna-harp',
        ruleIds: ['rule-character-names', 'rule-narrative-style'],
        glossaryEntryIds: ['glossary-emma']
    },
    {
        seriesId: 'series-sos-hotel',
        authorId: 'author-hanna-harp',
        ruleIds: [],
        glossaryEntryIds: []
    },
    {
        seriesId: 'series-new-species',
        authorId: 'author-ariana-nash',
        ruleIds: [],
        glossaryEntryIds: []
    }
];

const projectStatusLabels = {
    new: 'Новий',
    analysis: 'Аналіз',
    translation: 'У перекладі',
    audit: 'На перевірці',
    completed: 'Завершено'
};

uploadButton.addEventListener('click', () => fileInput.click());
saveTranslationButton.addEventListener('click', saveCurrentTranslation);
undoTranslationButton.addEventListener('click', undoTranslation);
redoTranslationButton.addEventListener('click', redoTranslation);
archiveAndUploadButton.addEventListener('click', archiveAndUploadNewBook);
replaceWithoutArchiveButton.addEventListener('click', replaceWithoutArchive);
cancelBookReplacementButton.addEventListener('click', cancelBookReplacement);
newProjectButton.addEventListener('click', openNewProjectDialog);
settingsButton.addEventListener('click', showSettingsView);
catalogAuthorSearch.addEventListener('input', renderAuthorCatalog);
catalogSeriesSearch.addEventListener('input', renderSeriesCatalog);
addCatalogAuthorButton.addEventListener('click', addCatalogAuthor);
addCatalogSeriesButton.addEventListener('click', addCatalogSeries);
closeNewProjectButton.addEventListener('click', closeNewProjectDialog);
cancelNewProjectButton.addEventListener('click', closeNewProjectDialog);
newProjectForm.addEventListener('submit', (event) => {
    event.preventDefault();
    createProject();
});
projectTitleInput.addEventListener('input', updateCreateProjectButton);
projectAuthorSelect.addEventListener('change', handleAuthorSelection);
authorSearchInput.addEventListener('input', renderAuthorSelect);
editAuthorButton.addEventListener('click', editSelectedAuthor);
deleteAuthorButton.addEventListener('click', deleteSelectedAuthor);
projectSeriesSelect.addEventListener('change', handleSeriesSelection);
seriesSearchInput.addEventListener('input', renderSeriesSelect);
editSeriesButton.addEventListener('click', editSelectedSeries);
deleteSeriesButton.addEventListener('click', deleteSelectedSeries);
showNewAuthorButton.addEventListener('click', () => toggleInlineForm(newAuthorForm, true));
cancelNewAuthorButton.addEventListener('click', () => toggleInlineForm(newAuthorForm, false));
addNewAuthorButton.addEventListener('click', createAuthor);
newSeriesNameInput.addEventListener('input', updateAddSeriesButton);
showNewSeriesButton.addEventListener('click', () => {
    renderNewSeriesAuthorSelect();
    toggleInlineForm(newSeriesForm, true);
});
cancelNewSeriesButton.addEventListener('click', () => toggleInlineForm(newSeriesForm, false));
addNewSeriesButton.addEventListener('click', createSeries);
newSeriesAuthorSelect.addEventListener('change', updateAddSeriesButton);
showProjectRuleFormButton.addEventListener('click', () => toggleInlineForm(projectRuleForm, true));
cancelProjectRuleButton.addEventListener('click', () => toggleInlineForm(projectRuleForm, false));
addProjectRuleButton.addEventListener('click', createProjectRule);
showProjectGlossaryFormButton.addEventListener('click', () => toggleInlineForm(projectGlossaryForm, true));
cancelProjectGlossaryButton.addEventListener('click', () => toggleInlineForm(projectGlossaryForm, false));
addProjectGlossaryButton.addEventListener('click', createProjectGlossaryEntry);
projectList.addEventListener('click', (event) => {
    const openButton = event.target.closest('[data-action="open-project"]');
    if (openButton) {
        const project = mockProjects.find((item) => item.projectId === openButton.dataset.projectId);
        if (project) {
            showProjectWorkspace(project);
        }
    }
    const editButton = event.target.closest('[data-action="edit-project"]');
    if (editButton) {
        const project = mockProjects.find((item) => item.projectId === editButton.dataset.projectId);
        if (project) {
            openNewProjectDialog(project);
        }
    }
});
editCurrentProjectButton.addEventListener('click', () => {
    if (currentProject) {
        openNewProjectDialog(currentProject);
    }
});
backToProjectsButton.addEventListener('click', () => requestNavigation(showMainScreen));
saveAndNavigateButton.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    finishNavigation(true);
});
discardAndNavigateButton.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    finishNavigation(false);
});
stayOnChapterButton.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    cancelNavigation();
});

navigationDialog.addEventListener('click', (event) => {
    const button = event.target.closest('button');
    if (button) {
        const actionNames = {
            'save-and-navigate': 'save-and-go',
            'discard-and-navigate': 'discard-and-go',
            'stay-on-chapter': 'stay'
        };
        console.log('[modal click]', actionNames[button.id] || button.id);
    }
});

initializeWorkbenchData();

fileInput.addEventListener('change', async () => {
    const [file] = fileInput.files;
    if (!file) {
        return;
    }

    if (currentProject && await hasSavedBook(currentProject.projectId)) {
        pendingUploadFile = file;
        bookReplacementDialog.hidden = false;
        return;
    }

    await uploadBookFile(file);
});

async function hasSavedBook(projectId) {
    try {
        await WorkbenchApi.getProjectBookStructure(projectId);
        return true;
    } catch (error) {
        return false;
    }
}

async function uploadBookFile(file) {

    uploadButton.disabled = true;
    uploadStatus.className = 'upload-status';
    uploadStatus.textContent = 'Оброблення файлу...';

    try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
            headers: currentProject ? { 'X-Project-Id': currentProject.projectId } : {}
        });
        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Не вдалося обробити файл.');
        }

        renderFileDetails(result.data);
        uploadStatus.className = 'upload-status success';
        uploadStatus.textContent = getUploadMessage(file.name, true);
    } catch (error) {
        uploadStatus.className = 'upload-status error';
        uploadStatus.textContent = getUploadMessage(file.name, false, error.message);
    } finally {
        uploadButton.disabled = false;
        fileInput.value = '';
    }
}

function translationSnapshot() {
    return Object.fromEntries(loadedChapters.map((chapter, chapterIndex) => [
        chapterIndex,
        chapter.paragraphs.map((rawParagraph, paragraphIndex) => {
            const paragraph = typeof rawParagraph === 'string' ? {} : rawParagraph;
            const state = translationStates.get(chapterIndex);
            const draft = state?.draft[paragraphIndex];
            return {
                paragraphId: draft?.paragraphId || paragraph.paragraphId || null,
                translationText: draft?.translationText ?? paragraph.translationText ?? null,
                reviewed: draft?.reviewed ?? Boolean(paragraph.reviewed)
            };
        })
    ]));
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}

async function archiveAndUploadNewBook() {
    try {
        archiveAndUploadButton.disabled = true;
        const archive = await WorkbenchApi.downloadProjectBookArchive(currentProject.projectId, translationSnapshot());
        downloadBlob(archive.blob, archive.filename);
        bookReplacementDialog.hidden = true;
        const file = pendingUploadFile;
        pendingUploadFile = null;
        await uploadBookFile(file);
    } catch (error) {
        uploadStatus.className = 'upload-status error';
        uploadStatus.textContent = error.message;
    } finally {
        archiveAndUploadButton.disabled = false;
    }
}

async function replaceWithoutArchive() {
    bookReplacementDialog.hidden = true;
    const file = pendingUploadFile;
    pendingUploadFile = null;
    await uploadBookFile(file);
}

function cancelBookReplacement() {
    pendingUploadFile = null;
    bookReplacementDialog.hidden = true;
}

function renderFileDetails(data) {
    data = normalizeBookStructure(data);
    workspaceContent.replaceChildren();
    const details = document.createElement('dl');
    details.className = 'file-details';

    for (const [key, label] of Object.entries(labels)) {
        if (data[key] === undefined) {
            continue;
        }

        const item = document.createElement('div');
        const term = document.createElement('dt');
        const description = document.createElement('dd');
        term.textContent = label;
        description.textContent = key === 'analysisStatus'
            ? ({ completed: 'Аналіз завершено', failed: 'Помилка аналізу', processing: 'Аналіз триває', pending: 'Очікує аналізу' }[data[key]] || data[key])
            : data[key] || 'Не вказано';
        item.append(term, description);
        details.append(item);
    }

    if (data.chapters) {
        const structureButton = document.createElement('button');
        structureButton.type = 'button';
        structureButton.className = 'secondary-btn structure-button';
        structureButton.textContent = 'Переглянути структуру книги';
        structureButton.addEventListener('click', () => {
            chapterBrowser.hidden = false;
            structureButton.hidden = true;
        });
        workspaceContent.append(details, structureButton, chapterBrowser);
        const restoredPosition = renderChapters(data.chapters);
        chapterBrowser.hidden = !restoredPosition;
        structureButton.hidden = restoredPosition;
    } else {
        chapterBrowser.hidden = true;
        workspaceContent.append(details);
    }
}

function normalizeBookStructure(data) {
    if (!data?.chapters) {
        return data;
    }

    return {
        ...data,
        chapters: data.chapters.map((chapter) => ({
            ...chapter,
            paragraphs: chapter.paragraphs.map((rawParagraph) => {
                if (typeof rawParagraph !== 'string') {
                    return {
                        paragraphId: rawParagraph.paragraphId || null,
                        originalText: rawParagraph.originalText || '',
                        translationText: rawParagraph.translationText || null,
                        reviewed: Boolean(rawParagraph.reviewed),
                    };
                }
                return {
                    paragraphId: null,
                    originalText: rawParagraph,
                    translationText: null,
                    reviewed: false,
                };
            }),
        })),
    };
}

function renderChapters(chapters) {
    loadedChapters = chapters;
    translationStates = new Map();
    const savedPosition = readProjectPosition(currentProject?.projectId, chapters.length);
    selectedChapterIndex = savedPosition?.chapterIndex ?? null;
    currentChapterPage = savedPosition?.chapterPage ?? 1;
    currentParagraphId = savedPosition?.paragraphId ?? null;
    renderChapterPage();
    clearChapterText();
    chapterBrowser.hidden = false;
    if (selectedChapterIndex !== null) {
        renderChapterText(loadedChapters[selectedChapterIndex], selectedChapterIndex + 1);
        return true;
    }
    return false;
}

function projectPositionStorageKey(projectId) {
    return `${projectPositionStoragePrefix}${encodeURIComponent(projectId)}`;
}

function getChapterPageCount(chapterCount) {
    return Math.max(1, Math.ceil(chapterCount / chaptersPerPage));
}

function readProjectPosition(projectId, chapterCount) {
    if (!projectId || chapterCount <= 0) {
        return null;
    }

    let rawPosition;
    try {
        rawPosition = localStorage.getItem(projectPositionStorageKey(projectId));
    } catch (error) {
        console.warn('Не вдалося прочитати позицію проєкту:', error);
        return null;
    }
    if (!rawPosition) {
        return null;
    }

    let parsedPosition;
    try {
        parsedPosition = JSON.parse(rawPosition);
    } catch (error) {
        return persistProjectPosition(projectId, 0, 1);
    }

    const pageCount = getChapterPageCount(chapterCount);
    const validChapterIndex = Number.isInteger(parsedPosition?.chapterIndex)
        && parsedPosition.chapterIndex >= 0
        && parsedPosition.chapterIndex < chapterCount;
    const validChapterPage = Number.isInteger(parsedPosition?.chapterPage)
        && parsedPosition.chapterPage >= 1
        && parsedPosition.chapterPage <= pageCount;
    const position = validChapterIndex && validChapterPage
        ? {
            chapterIndex: parsedPosition.chapterIndex,
            chapterPage: parsedPosition.chapterPage,
            paragraphId: typeof parsedPosition?.paragraphId === 'string' && parsedPosition.paragraphId
                ? parsedPosition.paragraphId
                : null,
        }
        : { chapterIndex: 0, chapterPage: 1, paragraphId: null };
    if (
        parsedPosition?.chapterIndex !== position.chapterIndex
        || parsedPosition?.chapterPage !== position.chapterPage
        || parsedPosition?.paragraphId !== position.paragraphId
    ) {
        persistProjectPosition(projectId, position.chapterIndex, position.chapterPage, position.paragraphId);
    }
    return position;
}

function persistProjectPosition(projectId, chapterIndex, chapterPage, paragraphId = null) {
    const position = { chapterIndex, chapterPage, paragraphId };
    if (!projectId) {
        return position;
    }
    try {
        localStorage.setItem(projectPositionStorageKey(projectId), JSON.stringify(position));
    } catch (error) {
        console.warn('Не вдалося зберегти позицію проєкту:', error);
    }
    return position;
}

function persistCurrentProjectPosition() {
    if (!currentProject || selectedChapterIndex === null) {
        return;
    }
    persistProjectPosition(currentProject.projectId, selectedChapterIndex, currentChapterPage, currentParagraphId);
}

function renderChapterPage() {
    chapterList.replaceChildren();
    chapterPagination.replaceChildren();
    const pageCount = Math.ceil(loadedChapters.length / chaptersPerPage);
    const pageStart = (currentChapterPage - 1) * chaptersPerPage;
    const pageChapters = loadedChapters.slice(pageStart, pageStart + chaptersPerPage);

    pageChapters.forEach((chapter, pageIndex) => {
        const chapterIndex = pageStart + pageIndex;
        const chapterButton = document.createElement('button');
        chapterButton.type = 'button';
        chapterButton.className = 'chapter-button';
        chapterButton.textContent = `${String(chapterIndex + 1).padStart(2, '0')} · ${chapter.title || `part${String(chapterIndex + 1).padStart(4, '0')}`}`;
        if (chapterIndex === selectedChapterIndex) {
            chapterButton.classList.add('active');
        }
        chapterButton.addEventListener('click', () => {
            requestNavigation(() => selectChapter(chapterIndex));
        });
        chapterList.append(chapterButton);
    });

    for (let page = 1; page <= pageCount; page += 1) {
        const pageButton = document.createElement('button');
        pageButton.type = 'button';
        pageButton.className = 'page-button';
        pageButton.textContent = page;
        pageButton.setAttribute('aria-label', `Сторінка ${page}`);
        if (page === currentChapterPage) {
            pageButton.classList.add('active');
        }
        pageButton.addEventListener('click', () => {
            requestNavigation(() => selectChapterPage(page));
        });
        chapterPagination.append(pageButton);
    }
}

function clearChapterText() {
    chapterTitle.textContent = '';
    chapterNumber.textContent = '';
    chapterName.textContent = '';
    chapterWordCount.textContent = '';
    chapterParagraphCount.textContent = '';
    translationRows.replaceChildren();
    chapterText.hidden = true;
}

function requestNavigation(navigate) {
    syncCurrentDraft();
    if (selectedChapterIndex !== null && isTranslationDirty(selectedChapterIndex)) {
        pendingNavigation = navigate;
        navigationDialog.removeAttribute('hidden');
        return;
    }

    navigate();
}

function showProjectWorkspace(project) {
    currentProject = project || currentProject;
    renderProjectInformation(currentProject);
    mainScreenView.hidden = true;
    settingsView.hidden = true;
    projectWorkspaceView.hidden = false;
    backToProjectsButton.hidden = false;
    void restoreProjectBook(project);
}

async function restoreProjectBook(project) {
    try {
        const structure = await WorkbenchApi.getProjectBookStructure(project.projectId);
        renderFileDetails(structure);
        uploadStatus.className = 'upload-status success';
        uploadStatus.textContent = 'Збережену структуру книги відновлено.';
    } catch (error) {
        if (!error.message.includes('Book structure not found')) {
            console.error('Не вдалося відновити структуру книги:', error);
        }
    }
}

function showMainScreen() {
    projectWorkspaceView.hidden = true;
    settingsView.hidden = true;
    mainScreenView.hidden = false;
    backToProjectsButton.hidden = true;
}

function showSettingsView() {
    mainScreenView.hidden = true;
    projectWorkspaceView.hidden = true;
    settingsView.hidden = false;
    backToProjectsButton.hidden = false;
    renderAuthorCatalog();
    renderSeriesCatalog();
}

function renderAuthorCatalog() {
    const query = catalogAuthorSearch.value.trim().toLocaleLowerCase();
    catalogAuthors.replaceChildren();
    mockAuthors
        .filter((author) => author.name.toLocaleLowerCase().includes(query))
        .forEach((author) => {
            const projects = mockProjects.filter((project) => project.authorId === author.authorId);
            const seriesNames = [...new Set(projects
                .filter((project) => project.seriesId)
                .map((project) => mockSeries.find((series) => series.seriesId === project.seriesId)?.name)
                .filter(Boolean))];
            const standaloneBooks = projects
                .filter((project) => !project.seriesId)
                .map((project) => project.title);
            catalogAuthors.append(createCatalogEntry(author.name, [
                `Серії: ${seriesNames.length ? seriesNames.join(', ') : 'немає'}`,
                `Книги без серії: ${standaloneBooks.length ? standaloneBooks.join(', ') : 'немає'}`
            ], () => editCatalogAuthor(author), () => deleteCatalogAuthor(author)));
        });
}

function renderSeriesCatalog() {
    const query = catalogSeriesSearch.value.trim().toLocaleLowerCase();
    catalogSeries.replaceChildren();
    mockSeries
        .filter((series) => series.name.toLocaleLowerCase().includes(query))
        .forEach((series) => {
            const projects = mockProjects.filter((project) => project.seriesId === series.seriesId);
            const authorNames = [...new Set(projects
                .map((project) => mockAuthors.find((author) => author.authorId === project.authorId)?.name)
                .filter(Boolean))];
            catalogSeries.append(createCatalogEntry(series.name, [
                `${authorNames.length > 1 ? 'Автори' : 'Автор'}: ${authorNames.length ? authorNames.join(', ') : 'немає'}`,
                `Книги: ${projects.length ? projects.map((project) => project.title).join(', ') : 'немає'}`
            ], () => editCatalogSeries(series), () => deleteCatalogSeries(series)));
        });
}

function createCatalogEntry(name, contextLines, onEdit, onDelete) {
    const entry = document.createElement('article');
    entry.className = 'management-item';
    const title = document.createElement('strong');
    title.textContent = name;
    const usageText = document.createElement('p');
    usageText.className = 'muted';
    usageText.replaceChildren();
    contextLines.forEach((line) => {
        const lineElement = document.createElement('span');
        lineElement.textContent = line;
        usageText.append(lineElement, document.createElement('br'));
    });
    const actions = document.createElement('div');
    actions.className = 'entity-actions';
    const editButton = document.createElement('button');
    editButton.className = 'text-btn';
    editButton.type = 'button';
    editButton.textContent = 'Редагувати';
    editButton.addEventListener('click', onEdit);
    const deleteButton = document.createElement('button');
    deleteButton.className = 'text-btn danger-btn';
    deleteButton.type = 'button';
    deleteButton.textContent = 'Видалити';
    deleteButton.addEventListener('click', onDelete);
    actions.append(editButton, deleteButton);
    entry.append(title, usageText, actions);
    return entry;
}

async function addCatalogAuthor() {
    const name = window.prompt('Ім’я авторки:')?.trim();
    if (!name) return;
    try {
        const author = await WorkbenchApi.createAuthor({ name });
        mockAuthors.push(author);
        renderAuthorCatalog();
    } catch (error) {
        window.alert(error.message);
    }
}

async function addCatalogSeries() {
    const name = window.prompt('Назва серії:')?.trim();
    if (!name) return;
    try {
        const series = await WorkbenchApi.createSeries({ name });
        mockSeries.push(series);
        renderSeriesCatalog();
    } catch (error) {
        window.alert(error.message);
    }
}

async function editCatalogAuthor(author) {
    const name = window.prompt('Нова назва авторки:', author.name)?.trim();
    if (!name || name === author.name) return;
    try {
        Object.assign(author, await WorkbenchApi.updateAuthor(author.authorId, { name }));
        renderAuthorCatalog();
        renderProjects(mockProjects);
    } catch (error) {
        window.alert(error.message);
    }
}

async function editCatalogSeries(series) {
    const name = window.prompt('Нова назва серії:', series.name)?.trim();
    if (!name || name === series.name) return;
    try {
        Object.assign(series, await WorkbenchApi.updateSeries(series.seriesId, { name }));
        renderSeriesCatalog();
        renderProjects(mockProjects);
    } catch (error) {
        window.alert(error.message);
    }
}

async function deleteCatalogAuthor(author) {
    if (!window.confirm(`Видалити авторку «${author.name}»?`)) return;
    try {
        await WorkbenchApi.deleteAuthor(author.authorId);
        mockAuthors.splice(mockAuthors.indexOf(author), 1);
        renderAuthorCatalog();
    } catch (error) {
        window.alert(error.message);
    }
}

async function deleteCatalogSeries(series) {
    if (!window.confirm(`Видалити серію «${series.name}»?`)) return;
    try {
        await WorkbenchApi.deleteSeries(series.seriesId);
        mockSeries.splice(mockSeries.indexOf(series), 1);
        renderSeriesCatalog();
    } catch (error) {
        window.alert(error.message);
    }
}

function renderProjectInformation(project) {
    if (!project) {
        return;
    }
    const author = mockAuthors.find((item) => item.authorId === project.authorId);
    const series = mockSeries.find((item) => item.seriesId === project.seriesId);
    const bookNumber = project.bookNumber ? `книга №${project.bookNumber}` : 'номер книги не вказано';
    projectPageTitle.textContent = project.title;
    projectPageSummary.textContent = `${author?.name || 'Авторку не вказано'} · ${series?.name || 'Серію не вказано'} · ${bookNumber}`;
    projectInformation.replaceChildren(
        createProjectMetadata('Назва', project.title),
        createProjectMetadata('Авторка', author ? author.name : 'Не вказано'),
        createProjectMetadata('Серія', series ? series.name : 'Не вказано'),
        createProjectMetadata('Номер книги', project.bookNumber || 'Не вказано'),
        createProjectMetadata('Статус', projectStatusLabels[project.status] || project.status),
        createProjectMetadata('Файл', project.fileName || 'Не завантажено'),
        createProjectMetadata('Прогрес', `${project.progress?.progress || 0}%`)
    );
}

function renderProjects(projects) {
    projectList.replaceChildren();
    projects.forEach((project) => {
        const card = document.createElement('article');
        card.className = 'project-card';

        const details = document.createElement('div');
        details.className = 'project-card-details';
        const label = document.createElement('p');
        label.className = 'project-label';
        label.textContent = 'Книжковий проєкт';
        const title = document.createElement('h3');
        title.textContent = project.title;
        const metadata = document.createElement('dl');
        metadata.className = 'project-metadata';
        const author = mockAuthors.find((item) => item.authorId === project.authorId);
        const series = mockSeries.find((item) => item.seriesId === project.seriesId);
        metadata.append(
            createProjectMetadata('Авторка', author ? author.name : null),
            createProjectMetadata('Серія', series ? series.name : null),
            createProjectMetadata('Статус', projectStatusLabels[project.status] || project.status, 'project-status')
        );
        details.append(label, title, metadata);

        const progress = document.createElement('div');
        progress.className = 'project-progress';
        const progressHeading = document.createElement('div');
        progressHeading.className = 'progress-heading';
        const progressLabel = document.createElement('span');
        progressLabel.textContent = 'Прогрес перекладу';
        const progressValue = project.progress?.progress || 0;
        const progressPercent = document.createElement('strong');
        progressPercent.textContent = `${progressValue}%`;
        progressHeading.append(progressLabel, progressPercent);
        const progressTrack = document.createElement('div');
        progressTrack.className = 'progress-track';
        progressTrack.setAttribute('role', 'progressbar');
        progressTrack.setAttribute('aria-label', `Прогрес перекладу: ${progressValue}%`);
        progressTrack.setAttribute('aria-valuemin', '0');
        progressTrack.setAttribute('aria-valuemax', '100');
        progressTrack.setAttribute('aria-valuenow', String(progressValue));
        const progressBar = document.createElement('span');
        progressBar.className = 'progress-value';
        progressBar.style.width = `${progressValue}%`;
        progressTrack.append(progressBar);
        const openButton = document.createElement('button');
        openButton.className = 'primary-btn';
        openButton.type = 'button';
        openButton.dataset.action = 'open-project';
        openButton.dataset.projectId = project.projectId;
        openButton.textContent = 'Відкрити проєкт';
        const editButton = document.createElement('button');
        editButton.className = 'secondary-btn';
        editButton.type = 'button';
        editButton.dataset.action = 'edit-project';
        editButton.dataset.projectId = project.projectId;
        editButton.textContent = 'Редагувати';
        progress.append(progressHeading, progressTrack, openButton, editButton);

        card.append(details, progress);
        projectList.append(card);
    });
}

function createProjectMetadata(labelText, valueText, valueClass) {
    const item = document.createElement('div');
    const label = document.createElement('dt');
    label.textContent = labelText;
    const value = document.createElement('dd');
    if (valueClass) {
        const valueElement = document.createElement('span');
        valueElement.className = valueClass;
        valueElement.textContent = valueText || 'Не вказано';
        value.append(valueElement);
    } else {
        value.textContent = valueText || 'Не вказано';
    }
    item.append(label, value);
    return item;
}

function openNewProjectDialog(project = null) {
    editingProjectId = project ? project.projectId : null;
    newProjectDraft = {
        authorId: project?.authorId || '',
        seriesId: project?.seriesId || null,
        inheritedRules: project?.inheritedRules || [],
        inheritedGlossary: project?.inheritedGlossary || [],
        projectRuleIds: project?.projectRuleIds || [],
        projectGlossaryEntryIds: project?.projectGlossaryEntryIds || []
    };
    newProjectForm.reset();
    projectTitleInput.value = project?.title || '';
    projectBookNumberInput.value = project?.bookNumber || '';
    projectStatusSelect.value = project?.status || 'new';
    toggleInlineForm(newAuthorForm, false);
    toggleInlineForm(newSeriesForm, false);
    toggleInlineForm(projectRuleForm, false);
    toggleInlineForm(projectGlossaryForm, false);
    inheritedContent.hidden = true;
    newProjectError.hidden = true;
    renderAuthorSelect();
    renderSeriesSelect();
    renderNewSeriesAuthorSelect();
    renderProjectRules();
    renderProjectGlossary();
    updateCreateProjectButton();
    newProjectDialog.hidden = false;
    if (newProjectDraft.seriesId) {
        void handleSeriesSelection();
    }
    projectTitleInput.focus();
}

function closeNewProjectDialog() {
    newProjectDialog.hidden = true;
    newProjectDraft = null;
    editingProjectId = null;
}

function renderAuthorSelect() {
    if (!newProjectDraft) {
        return;
    }
    const selectedAuthorId = newProjectDraft.authorId;
    const query = authorSearchInput.value.trim().toLocaleLowerCase();
    projectAuthorSelect.replaceChildren(new Option('Обрати авторку', ''));
    mockAuthors
        .filter((author) => author.name.toLocaleLowerCase().includes(query))
        .forEach((author) => {
            const option = new Option(author.name, author.authorId);
            option.selected = author.authorId === selectedAuthorId;
            projectAuthorSelect.append(option);
        });
    projectAuthorSelect.value = selectedAuthorId;
}

function renderSeriesSelect() {
    if (!newProjectDraft) {
        return;
    }
    const selectedSeriesId = newProjectDraft.seriesId || '';
    const query = seriesSearchInput.value.trim().toLocaleLowerCase();
    projectSeriesSelect.replaceChildren(new Option('Без серії', ''));
    mockSeries
        .filter((series) => series.name.toLocaleLowerCase().includes(query))
        .forEach((series) => {
            const option = new Option(series.name, series.seriesId);
            option.selected = series.seriesId === selectedSeriesId;
            projectSeriesSelect.append(option);
        });
    projectSeriesSelect.value = selectedSeriesId;
}

function renderNewSeriesAuthorSelect() {
    const selectedAuthorId = (newProjectDraft && newProjectDraft.authorId) || '';
    newSeriesAuthorSelect.replaceChildren(new Option('Обрати авторку', ''));
    mockAuthors.forEach((author) => {
        const option = new Option(author.name, author.authorId);
        option.selected = author.authorId === selectedAuthorId;
        newSeriesAuthorSelect.append(option);
    });
    newSeriesAuthorSelect.value = selectedAuthorId;
    updateAddSeriesButton();
}

async function handleAuthorSelection() {
    newProjectDraft.authorId = projectAuthorSelect.value;
    if (newProjectDraft.seriesId) {
        await handleSeriesSelection();
    } else {
        newProjectDraft.inheritedRules = [];
        newProjectDraft.inheritedGlossary = [];
        inheritedContent.hidden = true;
    }
    renderSeriesSelect();
    renderNewSeriesAuthorSelect();
    updateCreateProjectButton();
}

async function handleSeriesSelection() {
    newProjectDraft.seriesId = projectSeriesSelect.value || null;
    const context = await ensureSeriesAuthorContext(newProjectDraft.seriesId, newProjectDraft.authorId);
    newProjectDraft.inheritedRules = context
        ? context.ruleIds.map((ruleId) => ({ ruleId, confirmed: false, confirmedAt: null }))
        : [];
    newProjectDraft.inheritedGlossary = context
        ? context.glossaryEntryIds.map((glossaryEntryId) => ({ glossaryEntryId, confirmed: false, confirmedAt: null }))
        : [];
    renderInheritedRules();
    renderInheritedGlossary();
    inheritedContent.hidden = !context;
}

function getSelectedSeries() {
    return mockSeries.find((series) => series.seriesId === newProjectDraft.seriesId) || null;
}

function getSelectedSeriesAuthorContext() {
    if (!newProjectDraft || !newProjectDraft.seriesId || !newProjectDraft.authorId) {
        return null;
    }
    return mockSeriesAuthorContexts.find((context) => (
        context.seriesId === newProjectDraft.seriesId
        && context.authorId === newProjectDraft.authorId
    )) || null;
}

function hasSeriesAuthorContext(seriesId, authorId) {
    if (!seriesId || !authorId) {
        return false;
    }
    return mockSeriesAuthorContexts.some((context) => (
        context.seriesId === seriesId && context.authorId === authorId
    ));
}

async function ensureSeriesAuthorContext(seriesId, authorId) {
    if (!seriesId || !authorId) {
        return null;
    }
    let context = await WorkbenchApi.getSeriesAuthorContext(seriesId, authorId).catch((error) => {
        if (error.message === 'Context not found.') {
            return null;
        }
        throw error;
    });
    if (!context) {
        context = { seriesId, authorId, ruleIds: [], glossaryEntryIds: [] };
        await WorkbenchApi.saveSeriesAuthorContext(seriesId, authorId, context);
    }
    const existingIndex = mockSeriesAuthorContexts.findIndex((item) => (
        item.seriesId === seriesId && item.authorId === authorId
    ));
    if (existingIndex >= 0) {
        mockSeriesAuthorContexts[existingIndex] = context;
    } else {
        mockSeriesAuthorContexts.push(context);
    }
    return context;
}

function renderInheritedRules() {
    const series = getSelectedSeries();
    const context = getSelectedSeriesAuthorContext();
    inheritedRulesList.replaceChildren();
    if (!series || !context || context.ruleIds.length === 0) {
        inheritedRulesTitle.textContent = 'У цієї серії поки немає правил.';
        return;
    }
    inheritedRulesTitle.textContent = `Правила серії «${series.name}». Для цієї авторки доступно ${context.ruleIds.length} правил.`;
    context.ruleIds.forEach((ruleId) => {
        const rule = mockRules.find((item) => item.ruleId === ruleId);
        const reference = newProjectDraft.inheritedRules.find((item) => item.ruleId === ruleId);
        if (!rule || !reference) {
            return;
        }
        const label = document.createElement('label');
        label.className = 'checkbox-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = reference.confirmed;
        checkbox.addEventListener('change', () => {
            reference.confirmed = checkbox.checked;
            reference.confirmedAt = checkbox.checked ? new Date().toISOString() : null;
        });
        const text = document.createElement('span');
        text.textContent = rule.text;
        label.append(checkbox, text);
        inheritedRulesList.append(label);
    });
}

function renderInheritedGlossary() {
    const series = getSelectedSeries();
    const context = getSelectedSeriesAuthorContext();
    inheritedGlossaryList.replaceChildren();
    if (!series || !context || context.glossaryEntryIds.length === 0) {
        inheritedGlossaryTitle.textContent = 'У цієї серії поки немає записів глосарію.';
        return;
    }
    inheritedGlossaryTitle.textContent = `Глосарій серії «${series.name}». Для цієї авторки доступно ${context.glossaryEntryIds.length} записів.`;
    context.glossaryEntryIds.forEach((glossaryEntryId) => {
        const entry = mockGlossaryEntries.find((item) => item.glossaryEntryId === glossaryEntryId);
        const reference = newProjectDraft.inheritedGlossary.find((item) => item.glossaryEntryId === glossaryEntryId);
        if (!entry || !reference) {
            return;
        }
        const label = document.createElement('label');
        label.className = 'checkbox-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = reference.confirmed;
        checkbox.addEventListener('change', () => {
            reference.confirmed = checkbox.checked;
            reference.confirmedAt = checkbox.checked ? new Date().toISOString() : null;
        });
        const text = document.createElement('span');
        text.textContent = `${entry.source} → ${entry.target}`;
        label.append(checkbox, text);
        inheritedGlossaryList.append(label);
    });
}

function renderProjectRules() {
    projectRulesList.replaceChildren();
    if (!newProjectDraft || newProjectDraft.projectRuleIds.length === 0) {
        projectRulesList.append(createEmptyEntry('Поки немає власних правил'));
        return;
    }
    newProjectDraft.projectRuleIds.forEach((ruleId) => {
        const rule = mockRules.find((item) => item.ruleId === ruleId);
        if (rule) {
            projectRulesList.append(createEntry(
                `${rule.text}${rule.category ? ` · ${rule.category}` : ''}`,
                () => editRule(rule),
                () => deleteRule(rule)
            ));
        }
    });
}

function renderProjectGlossary() {
    projectGlossaryList.replaceChildren();
    if (!newProjectDraft || newProjectDraft.projectGlossaryEntryIds.length === 0) {
        projectGlossaryList.append(createEmptyEntry('Поки немає власних термінів'));
        return;
    }
    newProjectDraft.projectGlossaryEntryIds.forEach((glossaryEntryId) => {
        const entry = mockGlossaryEntries.find((item) => item.glossaryEntryId === glossaryEntryId);
        if (entry) {
            projectGlossaryList.append(createEntry(
                `${entry.source} → ${entry.target}`,
                () => editGlossaryEntry(entry),
                () => deleteGlossaryEntry(entry)
            ));
        }
    });
}

function createEmptyEntry(text) {
    const element = document.createElement('p');
    element.className = 'muted';
    element.textContent = text;
    return element;
}

function createEntry(text, onEdit, onDelete) {
    const element = document.createElement('div');
    element.className = 'entry-item';
    const label = document.createElement('span');
    label.textContent = text;
    element.append(label);
    if (onEdit) {
        const editButton = document.createElement('button');
        editButton.type = 'button';
        editButton.className = 'text-btn';
        editButton.textContent = 'Редагувати';
        editButton.addEventListener('click', onEdit);
        element.append(editButton);
    }
    if (onDelete) {
        const deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.className = 'text-btn danger-btn';
        deleteButton.textContent = 'Видалити';
        deleteButton.addEventListener('click', onDelete);
        element.append(deleteButton);
    }
    return element;
}

async function createAuthor() {
    const name = newAuthorNameInput.value.trim();
    if (!name) {
        return;
    }
    const normalizedName = normalizeEntityName(name);
    let author = mockAuthors.find((item) => normalizeEntityName(item.name) === normalizedName);
    if (!author) {
        author = await WorkbenchApi.createAuthor({ name });
        mockAuthors.push(author);
    }
    newProjectDraft.authorId = author.authorId;
    authorSearchInput.value = '';
    renderAuthorSelect();
    renderNewSeriesAuthorSelect();
    renderSeriesSelect();
    toggleInlineForm(newAuthorForm, false);
    newAuthorNameInput.value = '';
    updateCreateProjectButton();
}

async function editSelectedAuthor() {
    const author = mockAuthors.find((item) => item.authorId === projectAuthorSelect.value);
    if (!author) {
        return;
    }
    const name = window.prompt('Нова назва авторки:', author.name)?.trim();
    if (!name || name === author.name) {
        return;
    }
    try {
        const updated = await WorkbenchApi.updateAuthor(author.authorId, { name });
        Object.assign(author, updated);
        renderAuthorSelect();
        renderNewSeriesAuthorSelect();
        renderProjects(mockProjects);
    } catch (error) {
        window.alert(error.message);
    }
}

async function deleteSelectedAuthor() {
    const author = mockAuthors.find((item) => item.authorId === projectAuthorSelect.value);
    if (!author || !window.confirm(`Видалити авторку «${author.name}»?`)) {
        return;
    }
    try {
        await WorkbenchApi.deleteAuthor(author.authorId);
        mockAuthors.splice(mockAuthors.indexOf(author), 1);
        newProjectDraft.authorId = '';
        renderAuthorSelect();
        renderNewSeriesAuthorSelect();
        renderSeriesSelect();
        updateCreateProjectButton();
    } catch (error) {
        window.alert(error.message);
    }
}

async function createSeries() {
    const name = newSeriesNameInput.value.trim();
    const authorId = newSeriesAuthorSelect.value || newProjectDraft.authorId;
    if (!name || !authorId) {
        return;
    }
    const normalizedName = normalizeEntityName(name);
    const existingSeries = mockSeries.find((series) => normalizeEntityName(series.name) === normalizedName);
    const series = existingSeries || await WorkbenchApi.createSeries({ name });
    if (!existingSeries) {
        mockSeries.push(series);
    }
    newProjectDraft.seriesId = series.seriesId;
    await ensureSeriesAuthorContext(series.seriesId, authorId);
    seriesSearchInput.value = '';
    renderSeriesSelect();
    await handleSeriesSelection();
    toggleInlineForm(newSeriesForm, false);
    newSeriesNameInput.value = '';
}

async function editSelectedSeries() {
    const series = mockSeries.find((item) => item.seriesId === projectSeriesSelect.value);
    if (!series) {
        return;
    }
    const name = window.prompt('Нова назва серії:', series.name)?.trim();
    if (!name || name === series.name) {
        return;
    }
    try {
        const updated = await WorkbenchApi.updateSeries(series.seriesId, { name });
        Object.assign(series, updated);
        renderSeriesSelect();
        renderProjects(mockProjects);
    } catch (error) {
        window.alert(error.message);
    }
}

async function deleteSelectedSeries() {
    const series = mockSeries.find((item) => item.seriesId === projectSeriesSelect.value);
    if (!series || !window.confirm(`Видалити серію «${series.name}»?`)) {
        return;
    }
    try {
        await WorkbenchApi.deleteSeries(series.seriesId);
        mockSeries.splice(mockSeries.indexOf(series), 1);
        newProjectDraft.seriesId = null;
        renderSeriesSelect();
        renderProjects(mockProjects);
    } catch (error) {
        window.alert(error.message);
    }
}

async function createProjectRule() {
    const text = projectRuleTextInput.value.trim();
    if (!text) {
        return;
    }
    const rule = await WorkbenchApi.createRule({
        text,
        category: projectRuleCategoryInput.value.trim() || null,
        active: true
    });
    mockRules.push(rule);
    newProjectDraft.projectRuleIds.push(rule.ruleId);
    renderProjectRules();
    projectRuleTextInput.value = '';
    projectRuleCategoryInput.value = '';
    toggleInlineForm(projectRuleForm, false);
}

async function editRule(rule) {
    const text = window.prompt('Текст правила:', rule.text)?.trim();
    if (!text) {
        return;
    }
    const category = window.prompt('Категорія правила:', rule.category || '')?.trim() || null;
    try {
        const updated = await WorkbenchApi.updateRule(rule.ruleId, { ...rule, text, category });
        Object.assign(rule, updated);
        renderProjectRules();
    } catch (error) {
        window.alert(error.message);
    }
}

async function deleteRule(rule) {
    if (!window.confirm(`Видалити правило «${rule.text}»?`)) {
        return;
    }
    try {
        await WorkbenchApi.deleteRule(rule.ruleId);
        mockRules.splice(mockRules.indexOf(rule), 1);
        newProjectDraft.projectRuleIds = newProjectDraft.projectRuleIds.filter((id) => id !== rule.ruleId);
        renderProjectRules();
    } catch (error) {
        window.alert(error.message);
    }
}

async function createProjectGlossaryEntry() {
    const source = projectGlossarySourceInput.value.trim();
    const target = projectGlossaryTargetInput.value.trim();
    if (!source || !target) {
        return;
    }
    const entry = await WorkbenchApi.createGlossaryEntry({
        source,
        target,
        note: projectGlossaryNoteInput.value.trim() || null,
        active: true
    });
    mockGlossaryEntries.push(entry);
    newProjectDraft.projectGlossaryEntryIds.push(entry.glossaryEntryId);
    renderProjectGlossary();
    projectGlossarySourceInput.value = '';
    projectGlossaryTargetInput.value = '';
    projectGlossaryNoteInput.value = '';
    toggleInlineForm(projectGlossaryForm, false);
}

async function editGlossaryEntry(entry) {
    const source = window.prompt('Оригінал:', entry.source)?.trim();
    const target = window.prompt('Переклад:', entry.target)?.trim();
    if (!source || !target) {
        return;
    }
    const note = window.prompt('Примітка:', entry.note || '')?.trim() || null;
    try {
        const updated = await WorkbenchApi.updateGlossaryEntry(entry.glossaryEntryId, { ...entry, source, target, note });
        Object.assign(entry, updated);
        renderProjectGlossary();
    } catch (error) {
        window.alert(error.message);
    }
}

async function deleteGlossaryEntry(entry) {
    if (!window.confirm(`Видалити термін «${entry.source}»?`)) {
        return;
    }
    try {
        await WorkbenchApi.deleteGlossaryEntry(entry.glossaryEntryId);
        mockGlossaryEntries.splice(mockGlossaryEntries.indexOf(entry), 1);
        newProjectDraft.projectGlossaryEntryIds = newProjectDraft.projectGlossaryEntryIds.filter((id) => id !== entry.glossaryEntryId);
        renderProjectGlossary();
    } catch (error) {
        window.alert(error.message);
    }
}

async function createProject() {
    const title = projectTitleInput.value.trim();
    if (!title || !newProjectDraft.authorId) {
        newProjectError.textContent = 'Вкажіть назву книги та оберіть авторку.';
        newProjectError.hidden = false;
        updateCreateProjectButton();
        return;
    }
    const existingProject = editingProjectId
        ? mockProjects.find((item) => item.projectId === editingProjectId)
        : null;
    const projectData = {
        title,
        authorId: newProjectDraft.authorId,
        seriesId: newProjectDraft.seriesId,
        bookNumber: projectBookNumberInput.value ? Number(projectBookNumberInput.value) : null,
        status: projectStatusSelect.value,
        progress: {
            progress: 0,
            analysisProgress: 0,
            translationProgress: 0,
            auditProgress: 0
        },
        chapterCount: 0,
        fileName: null,
        fileFormat: null,
        fileSize: null,
        analysisResult: null,
        inheritedRules: newProjectDraft.inheritedRules.map((reference) => ({ ...reference })),
        inheritedGlossary: newProjectDraft.inheritedGlossary.map((reference) => ({ ...reference })),
        projectRuleIds: [...newProjectDraft.projectRuleIds],
        projectGlossaryEntryIds: [...newProjectDraft.projectGlossaryEntryIds],
    };
    const project = editingProjectId
        ? await WorkbenchApi.updateProject(editingProjectId, projectData)
        : await WorkbenchApi.createProject(projectData);
    if (editingProjectId) {
        const index = mockProjects.findIndex((item) => item.projectId === editingProjectId);
        if (index >= 0) {
            mockProjects[index] = project;
            if (currentProject?.projectId === editingProjectId) {
                currentProject = project;
                renderProjectInformation(currentProject);
            }
        }
    } else {
        mockProjects.push(project);
    }
    renderProjects(mockProjects);
    closeNewProjectDialog();
}

function updateCreateProjectButton() {
    const hasTitle = Boolean(projectTitleInput.value.trim());
    const hasAuthor = Boolean(newProjectDraft && newProjectDraft.authorId);
    createProjectButton.disabled = !(hasTitle && hasAuthor);
    if (hasTitle && hasAuthor) {
        newProjectError.hidden = true;
    }
}

function updateAddSeriesButton() {
    addNewSeriesButton.disabled = !(newSeriesNameInput.value.trim() && newSeriesAuthorSelect.value);
}

function toggleInlineForm(form, visible) {
    form.hidden = !visible;
    if (visible) {
        const firstInput = form.querySelector('input, select');
        if (firstInput) {
            firstInput.focus();
        }
    }
}

function normalizeEntityName(value) {
    return value.trim().replace(/\s+/g, ' ').toLocaleLowerCase();
}

async function initializeWorkbenchData() {
    showMainScreen();
    try {
        const [authors, series, rules, glossaryEntries, projects] = await Promise.all([
            WorkbenchApi.listAuthors(),
            WorkbenchApi.listSeries(),
            WorkbenchApi.listRules(),
            WorkbenchApi.listGlossary(),
            WorkbenchApi.listProjects()
        ]);
        mockAuthors.splice(0, mockAuthors.length, ...authors);
        mockSeries.splice(0, mockSeries.length, ...series);
        mockRules.splice(0, mockRules.length, ...rules);
        mockGlossaryEntries.splice(0, mockGlossaryEntries.length, ...glossaryEntries);
        mockProjects.splice(0, mockProjects.length, ...projects);
        mockSeriesAuthorContexts.splice(0, mockSeriesAuthorContexts.length);
        renderProjects(mockProjects);
        showMainScreen();
    } catch (error) {
        console.error('Не вдалося завантажити дані Workbench:', error);
        renderProjects([]);
        showMainScreen();
    }
}

function selectChapterPage(page) {
    currentChapterPage = page;
    renderChapterPage();
    if (selectedChapterIndex !== null) {
        renderChapterText(loadedChapters[selectedChapterIndex], selectedChapterIndex + 1);
    }
    persistCurrentProjectPosition();
}

function selectChapter(chapterIndex) {
    selectedChapterIndex = chapterIndex;
    currentChapterPage = Math.floor(chapterIndex / chaptersPerPage) + 1;
    currentParagraphId = null;
    renderChapterPage();
    renderChapterText(loadedChapters[chapterIndex], chapterIndex + 1);
    persistCurrentProjectPosition();
}

function renderChapterText(chapter, chapterIndex) {
    chapterTitle.textContent = `Вибраний розділ: ${chapter.title}`;
    chapterNumber.textContent = `Розділ ${chapterIndex} з ${loadedChapters.length}`;
    chapterName.textContent = `Назва: ${chapter.title}`;
    chapterWordCount.textContent = `Слів: ${formatNumber(chapter.wordCount)}`;
    chapterParagraphCount.textContent = `Абзаців: ${chapter.paragraphs.length}`;
    const state = getTranslationState(chapterIndex - 1, chapter);
    translationRows.replaceChildren();
    chapterText.hidden = false;

    chapter.paragraphs.forEach((rawParagraph, paragraphIndex) => {
        const paragraph = typeof rawParagraph === 'string'
            ? { paragraphId: null, originalText: rawParagraph, translationText: '', reviewed: false }
            : rawParagraph;
        const draft = state.draft[paragraphIndex];
        const row = document.createElement('div');
        row.className = 'translation-row';
        row.dataset.chapterIndex = String(chapterIndex - 1);
        row.dataset.paragraphIndex = String(paragraphIndex);
        row.dataset.paragraphId = paragraph.paragraphId || '';
        const original = document.createElement('div');
        original.className = 'original-paragraph';
        original.dataset.chapterIndex = String(chapterIndex - 1);
        original.dataset.paragraphIndex = String(paragraphIndex);
        original.textContent = paragraph.originalText;
        const translation = document.createElement('textarea');
        translation.className = 'translation-paragraph';
        translation.dataset.chapterIndex = String(chapterIndex - 1);
        translation.dataset.paragraphIndex = String(paragraphIndex);
        translation.dataset.paragraphId = paragraph.paragraphId || '';
        translation.rows = 4;
        translation.value = draft.translationText;
        translation.placeholder = 'Введіть переклад абзацу...';
        translation.addEventListener('focus', () => setCurrentParagraph(paragraph.paragraphId));
        translation.addEventListener('input', () => {
            updateDraftFromControls(state);
        });
        const review = document.createElement('label');
        review.className = 'paragraph-review';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.dataset.paragraphId = paragraph.paragraphId || '';
        checkbox.checked = draft.reviewed;
        checkbox.addEventListener('focus', () => setCurrentParagraph(paragraph.paragraphId));
        checkbox.addEventListener('change', () => {
            updateDraftFromControls(state);
        });
        const reviewText = document.createElement('span');
        reviewText.textContent = 'Перевірено';
        review.append(checkbox, reviewText);
        const status = document.createElement('span');
        status.className = 'paragraph-status';
        row.append(original, translation, review, status);
        translationRows.append(row);
        updateParagraphVisualState(row, draft);
    });
    restoreCurrentParagraphRow();
    updateTranslationButtons();
}

function setCurrentParagraph(paragraphId) {
    if (!paragraphId || !currentProject || selectedChapterIndex === null) {
        return;
    }
    currentParagraphId = paragraphId;
    markCurrentParagraphRow();
    persistCurrentProjectPosition();
}

function markCurrentParagraphRow() {
    translationRows.querySelectorAll('.translation-row').forEach((row) => {
        row.classList.toggle('paragraph-row-current', row.dataset.paragraphId === currentParagraphId);
    });
}

function restoreCurrentParagraphRow() {
    if (!currentParagraphId) {
        return;
    }
    const currentRow = [...translationRows.querySelectorAll('.translation-row')]
        .find((row) => row.dataset.paragraphId === currentParagraphId);
    if (!currentRow) {
        currentParagraphId = null;
        persistCurrentProjectPosition();
        return;
    }
    currentRow.classList.add('paragraph-row-current');
    currentRow.scrollIntoView?.({ behavior: 'auto', block: 'center' });
}

function createParagraphDraft(paragraph) {
    return {
        paragraphId: paragraph.paragraphId || null,
        translationText: paragraph.translationText || '',
        reviewed: Boolean(paragraph.reviewed),
    };
}

function cloneParagraphDrafts(paragraphs) {
    return paragraphs.map((paragraph) => ({ ...paragraph }));
}

function getTranslationState(chapterIndex, chapter) {
    if (!translationStates.has(chapterIndex)) {
        const initialDraft = chapter.paragraphs.map((rawParagraph) => createParagraphDraft(
            typeof rawParagraph === 'string'
                ? { paragraphId: null, translationText: '', reviewed: false }
                : rawParagraph
        ));
        translationStates.set(chapterIndex, {
            saved: cloneParagraphDrafts(initialDraft),
            draft: cloneParagraphDrafts(initialDraft),
            undo: [],
            redo: []
        });
    }
    return translationStates.get(chapterIndex);
}

function readTranslationDraft() {
    return Array.from(translationRows.querySelectorAll('.translation-row'), (row) => ({
        paragraphId: row.dataset.paragraphId || null,
        translationText: row.querySelector('.translation-paragraph').value,
        reviewed: row.querySelector('.paragraph-review input').checked,
    }));
}

function paragraphDraftsEqual(left, right) {
    return left.paragraphId === right.paragraphId
        && left.translationText === right.translationText
        && left.reviewed === right.reviewed;
}

function isTranslationDirty(chapterIndex) {
    const state = translationStates.get(chapterIndex);
    return state && state.draft.some((draft, index) => !paragraphDraftsEqual(draft, state.saved[index]));
}

function syncCurrentDraft() {
    if (selectedChapterIndex === null || !translationStates.has(selectedChapterIndex)) {
        return;
    }
    translationStates.get(selectedChapterIndex).draft = readTranslationDraft();
}

function updateDraftFromControls(state) {
    state.undo.push(cloneParagraphDrafts(state.draft));
    state.draft = readTranslationDraft();
    state.redo = [];
    updateParagraphVisualStates(state.draft);
    updateTranslationButtons();
}

function getParagraphStatus(paragraph) {
    if (!paragraph.translationText.trim()) {
        return { label: 'Не перекладено', className: 'untranslated' };
    }
    if (!paragraph.reviewed) {
        return { label: 'Не перевірено', className: 'translated' };
    }
    return { label: 'Перевірено', className: 'reviewed' };
}

function updateParagraphVisualState(row, paragraph) {
    const status = getParagraphStatus(paragraph);
    row.classList.remove('paragraph-untranslated', 'paragraph-translated', 'paragraph-reviewed');
    row.classList.add(`paragraph-${status.className}`);
    const statusElement = row.querySelector('.paragraph-status');
    statusElement.textContent = status.label;
}

function updateParagraphVisualStates(drafts) {
    translationRows.querySelectorAll('.translation-row').forEach((row, index) => {
        updateParagraphVisualState(row, drafts[index]);
    });
}

async function saveCurrentTranslation() {
    if (selectedChapterIndex === null) {
        return;
    }
    const state = translationStates.get(selectedChapterIndex);
    state.draft = readTranslationDraft();
    const updates = state.draft.filter((draft, index) => (
        draft.paragraphId && !paragraphDraftsEqual(draft, state.saved[index])
    ));
    try {
        await Promise.all(updates.map((draft) => WorkbenchApi.updateParagraph(draft.paragraphId, {
            translationText: draft.translationText || null,
            reviewed: draft.reviewed,
        })));
        state.saved = cloneParagraphDrafts(state.draft);
        state.undo = [];
        state.redo = [];
        updateParagraphVisualStates(state.draft);
        updateTranslationButtons();
        return true;
    } catch (error) {
        updateTranslationButtons();
        window.alert(`Не вдалося зберегти розділ: ${error.message}`);
        return false;
    }
}

function undoTranslation() {
    const state = translationStates.get(selectedChapterIndex);
    if (!state || state.undo.length === 0) {
        return;
    }
    state.redo.push(cloneParagraphDrafts(state.draft));
    state.draft = cloneParagraphDrafts(state.undo.pop());
    renderTranslationFields(state.draft);
}

function redoTranslation() {
    const state = translationStates.get(selectedChapterIndex);
    if (!state || state.redo.length === 0) {
        return;
    }
    state.undo.push(cloneParagraphDrafts(state.draft));
    state.draft = cloneParagraphDrafts(state.redo.pop());
    renderTranslationFields(state.draft);
}

function renderTranslationFields(values) {
    translationRows.querySelectorAll('.translation-row').forEach((row, index) => {
        row.querySelector('.translation-paragraph').value = values[index].translationText;
        row.querySelector('.paragraph-review input').checked = values[index].reviewed;
        updateParagraphVisualState(row, values[index]);
    });
    updateTranslationButtons();
}

function updateTranslationButtons() {
    const state = translationStates.get(selectedChapterIndex);
    saveTranslationButton.disabled = !state || !isTranslationDirty(selectedChapterIndex);
    undoTranslationButton.disabled = !state || state.undo.length === 0;
    redoTranslationButton.disabled = !state || state.redo.length === 0;
}

function finishNavigation(saveChanges) {
    if (saveChanges) {
        saveAndNavigateButton.disabled = true;
        saveCurrentTranslation().then((saved) => {
            saveAndNavigateButton.disabled = false;
            if (saved) {
                completeNavigation();
            }
        });
        return;
    }
    if (selectedChapterIndex !== null) {
        const state = translationStates.get(selectedChapterIndex);
        state.draft = cloneParagraphDrafts(state.saved);
        state.undo = [];
        state.redo = [];
        renderTranslationFields(state.draft);
    }
    completeNavigation();
}

function completeNavigation() {
    const navigation = pendingNavigation;
    pendingNavigation = null;
    navigationDialog.hidden = true;
    if (navigation) {
        navigation();
    }
}

function cancelNavigation() {
    pendingNavigation = null;
    navigationDialog.hidden = true;
}

function formatNumber(value) {
    return Number(value).toLocaleString('uk-UA');
}

function getUploadMessage(filename, successful, errorMessage) {
    const extension = filename.toLowerCase().split('.').pop();
    if (!successful) {
        if (extension !== 'epub') {
            return '⚠️ Ой-ой-ой! Цей файл не підходить для аналізу. Workbench працює з EPUB. Підготуй книгу у форматі EPUB і завантаж її ще раз. DOCX використовується як робочий/фінальний формат, але для аналізу книги потрібен EPUB.';
        }
        return errorMessage || 'Не вдалося завантажити файл.';
    }

    if (extension === 'epub') {
        return 'EPUB успішно завантажено. Виконано повний структурний аналіз книги локально.';
    }
    return 'DOCX завантажено. Для повного структурного аналізу книги підготуйте EPUB. DOCX залишено для подальшої роботи або експорту.';
}
