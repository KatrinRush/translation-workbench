const fileInput = document.querySelector('#file-input');
const uploadButton = document.querySelector('#upload-button');
const downloadProjectArchiveButton = document.querySelector('#download-project-archive');
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
const translateChapterButton = document.querySelector('#translate-chapter-button');
const chapterAIAnalysisCategories = document.querySelector('#chapter-ai-analysis-categories');
const chapterAIAnalysisPrompt = document.querySelector('#chapter-ai-analysis-prompt');
const chapterAIAnalysisConnections = document.querySelector('#chapter-ai-analysis-connections');
const selectAllChapterAICategoriesButton = document.querySelector('#select-all-chapter-ai-categories');
const clearChapterAICategoriesButton = document.querySelector('#clear-chapter-ai-categories');
const runChapterAIAnalysisButton = document.querySelector('#run-chapter-ai-analysis');
const chapterAIAnalysisStatus = document.querySelector('#chapter-ai-analysis-status');
const chapterAIAnalysisResults = document.querySelector('#chapter-ai-analysis-results');
const translationRows = document.querySelector('#translation-rows');
const chapterTitleTranslation = document.querySelector('#chapter-title-translation');
const translationRulesInput = document.querySelector('#translation-rules-input');
const saveTranslationRulesButton = document.querySelector('#save-translation-rules');
const translationRulesStatus = document.querySelector('#translation-rules-status');
const addTranslationGlossaryButton = document.querySelector('#add-translation-glossary');
const translationGlossaryList = document.querySelector('#translation-glossary-list');
const translationGlossaryEditor = document.querySelector('#translation-glossary-editor');
const translationGlossarySourceLanguage = document.querySelector('#translation-glossary-source-language');
const translationGlossaryTargetLanguage = document.querySelector('#translation-glossary-target-language');
const translationGlossaryEntries = document.querySelector('#translation-glossary-entries');
const addTranslationGlossaryEntryButton = document.querySelector('#add-translation-glossary-entry');
const translationGlossaryExistingEntrySelect = document.querySelector('#translation-glossary-existing-entry');
const addTranslationGlossaryExistingEntryButton = document.querySelector('#add-translation-glossary-existing-entry');
const saveTranslationGlossaryButton = document.querySelector('#save-translation-glossary');
const cancelTranslationGlossaryButton = document.querySelector('#cancel-translation-glossary');
const translationGlossaryStatus = document.querySelector('#translation-glossary-status');
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
const bookInfoModeButton = document.querySelector('[data-project-mode="book-info"]');
const analysisModeButton = document.querySelector('[data-project-mode="analysis"]');
const translationModeButton = document.querySelector('[data-project-mode="translation"]');
const bookInfoWorkspace = document.querySelector('#book-info-workspace');
const projectInformationCard = document.querySelector('.project-information-card');
const projectFileCard = document.querySelector('#project-file-card');
const projectBriefCard = document.querySelector('#project-brief-card');
const projectReferencesCard = document.querySelector('#project-references-card');
const analysisWorkspaceCard = document.querySelector('#analysis-workspace-card');
const translationWorkspaceCard = document.querySelector('#translation-workspace-card');
const projectInformation = document.querySelector('#project-information');
const projectInformationCover = document.querySelector('#project-information-cover');
const editCurrentProjectButton = document.querySelector('#edit-current-project');
const selectedReferencesInfo = document.querySelector('#selected-references-info');
const manageReferencesButton = document.querySelector('#manage-references-button');
const referencesDialog = document.querySelector('#references-dialog');
const referencesDialogProject = document.querySelector('#references-dialog-project');
const closeReferencesDialogButton = document.querySelector('#close-references-dialog');
const cancelReferencesButton = document.querySelector('#cancel-references');
const saveReferencesButton = document.querySelector('#save-references');
const referencesRulesList = document.querySelector('#references-rules-list');
const referencesGlossaryList = document.querySelector('#references-glossary-list');
const referencesInheritedRulesList = document.querySelector('#references-inherited-rules-list');
const referencesInheritedGlossaryList = document.querySelector('#references-inherited-glossary-list');
const referencesShowRuleFormButton = document.querySelector('#references-show-rule-form');
const referencesRuleForm = document.querySelector('#references-rule-form');
const referencesRuleTextInput = document.querySelector('#references-rule-text');
const referencesRuleCategoryInput = document.querySelector('#references-rule-category');
const referencesCancelRuleButton = document.querySelector('#references-cancel-rule');
const referencesAddRuleButton = document.querySelector('#references-add-rule');
const referencesShowGlossaryFormButton = document.querySelector('#references-show-glossary-form');
const referencesGlossaryForm = document.querySelector('#references-glossary-form');
const referencesGlossarySourceInput = document.querySelector('#references-glossary-source');
const referencesGlossaryTargetInput = document.querySelector('#references-glossary-target');
const referencesGlossaryNoteInput = document.querySelector('#references-glossary-note');
const referencesCancelGlossaryButton = document.querySelector('#references-cancel-glossary');
const referencesAddGlossaryButton = document.querySelector('#references-add-glossary');
const projectList = document.querySelector('.project-list');
const newProjectButton = document.querySelector('#new-project-button');
const settingsButton = document.querySelector('#settings-button');
const catalogAuthorSearch = document.querySelector('#catalog-author-search');
const catalogSeriesSearch = document.querySelector('#catalog-series-search');
const catalogAuthors = document.querySelector('#catalog-authors');
const catalogSeries = document.querySelector('#catalog-series');
const addCatalogAuthorButton = document.querySelector('#add-catalog-author');
const addCatalogSeriesButton = document.querySelector('#add-catalog-series');
const connectionsNotice = document.querySelector('#connections-notice');
const connectionsList = document.querySelector('#connections-list');
const connectionDialog = document.querySelector('#connection-dialog');
const connectionForm = document.querySelector('#connection-form');
const connectionDialogTitle = document.querySelector('#connection-dialog-title');
const connectionDisplayName = document.querySelector('#connection-display-name');
const connectionCredentialFields = document.querySelector('#connection-credential-fields');
const connectionCredentialHint = document.querySelector('#connection-credential-hint');
const connectionError = document.querySelector('#connection-error');
const closeConnectionDialogButton = document.querySelector('#close-connection-dialog');
const cancelConnectionDialogButton = document.querySelector('#cancel-connection-dialog');
const newProjectDialog = document.querySelector('#new-project-dialog');
const newProjectForm = document.querySelector('#new-project-form');
const newProjectDialogTitle = document.querySelector('#new-project-dialog-title');
const closeNewProjectButton = document.querySelector('#close-new-project');
const cancelNewProjectButton = document.querySelector('#cancel-new-project');
const projectTitleInput = document.querySelector('#project-title-input');
const projectBookNumberInput = document.querySelector('#project-book-number-input');
const projectStatusSelect = document.querySelector('#project-status-select');
const projectTranslationConnectionSelect = document.querySelector('#project-translation-connection');
const projectOrchestrationConnectionSelect = document.querySelector('#project-orchestration-connection');
const projectAnalysisConnectionsSelect = document.querySelector('#project-analysis-connections');
const projectQaConnectionsSelect = document.querySelector('#project-qa-connections');
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
const projectCoverEditor = document.querySelector('#project-cover-editor');
const projectCoverPreview = document.querySelector('#project-cover-preview');
const uploadProjectCoverButton = document.querySelector('#upload-project-cover');
const deleteProjectCoverButton = document.querySelector('#delete-project-cover');
const projectCoverFileInput = document.querySelector('#project-cover-file');
const newProjectError = document.querySelector('#new-project-error');
const createProjectButton = document.querySelector('#create-project-button');
const backToProjectsButton = document.querySelector('#back-to-projects');
const navigationDialog = document.querySelector('#navigation-dialog');
const saveAndNavigateButton = document.querySelector('#save-and-navigate');
const discardAndNavigateButton = document.querySelector('#discard-and-navigate');
const stayOnChapterButton = document.querySelector('#stay-on-chapter');
const openBriefDialogButton = document.querySelector('#open-brief-dialog');
const briefDialog = document.querySelector('#brief-dialog');
const briefDialogProject = document.querySelector('#brief-dialog-project');
const closeBriefDialogButton = document.querySelector('#close-brief-dialog');
const briefMessages = document.querySelector('#brief-messages');
const briefMessageInput = document.querySelector('#brief-message-input');
const addBriefMessageButton = document.querySelector('#add-brief-message');
const briefAgreedList = document.querySelector('#brief-agreed-list');
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
let currentBriefEntries = [];
let referencesDraft = null;
let integrationProviders = [];
let integrationConnections = [];
let credentialStorageAvailable = false;
let projectTranslationGlossaries = [];
let editingTranslationGlossaryId = null;
let translationGlossaryDraft = [];
let translationGlossaryCatalog = [];

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

const chapterAICategories = [
    'POV / оповідач',
    'Атмосфера',
    'Тон і манера мовлення персонажів',
    'Персонажі',
    'Стиль автора',
    'Імена та термінологія',
    'Мова та особливості тексту',
    'Контекст і важливі деталі для перекладу'
];

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
downloadProjectArchiveButton.addEventListener('click', downloadCurrentProjectArchive);
saveTranslationButton.addEventListener('click', saveCurrentTranslation);
undoTranslationButton.addEventListener('click', undoTranslation);
redoTranslationButton.addEventListener('click', redoTranslation);
bookInfoModeButton.addEventListener('click', showBookInfoMode);
analysisModeButton.addEventListener('click', showAnalysisMode);
translationModeButton.addEventListener('click', showTranslationMode);
translateChapterButton.addEventListener('click', translateCurrentChapter);
selectAllChapterAICategoriesButton.addEventListener('click', () => setChapterAICategories(true));
clearChapterAICategoriesButton.addEventListener('click', () => setChapterAICategories(false));
runChapterAIAnalysisButton.addEventListener('click', runChapterAIAnalysis);
saveTranslationRulesButton.addEventListener('click', saveTranslationRules);
addTranslationGlossaryButton.addEventListener('click', () => openTranslationGlossaryEditor());
addTranslationGlossaryEntryButton.addEventListener('click', () => addTranslationGlossaryEntry());
addTranslationGlossaryExistingEntryButton.addEventListener('click', addExistingTranslationGlossaryEntryToDraft);
saveTranslationGlossaryButton.addEventListener('click', saveTranslationGlossary);
cancelTranslationGlossaryButton.addEventListener('click', closeTranslationGlossaryEditor);
translationGlossaryList.addEventListener('click', (event) => {
    const button = event.target.closest('[data-edit-translation-glossary]');
    if (!button) return;
    openTranslationGlossaryEditor(projectTranslationGlossaries.find((item) => item.glossaryRuleId === button.dataset.editTranslationGlossary));
});
archiveAndUploadButton.addEventListener('click', archiveAndUploadNewBook);
replaceWithoutArchiveButton.addEventListener('click', replaceWithoutArchive);
cancelBookReplacementButton.addEventListener('click', cancelBookReplacement);
newProjectButton.addEventListener('click', openNewProjectDialog);
settingsButton.addEventListener('click', showSettingsView);
catalogAuthorSearch.addEventListener('input', renderAuthorCatalog);
catalogSeriesSearch.addEventListener('input', renderSeriesCatalog);
addCatalogAuthorButton.addEventListener('click', addCatalogAuthor);
addCatalogSeriesButton.addEventListener('click', addCatalogSeries);
connectionsList.addEventListener('click', handleConnectionAction);
connectionForm.addEventListener('submit', saveConnection);
closeConnectionDialogButton.addEventListener('click', closeConnectionDialog);
cancelConnectionDialogButton.addEventListener('click', closeConnectionDialog);
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
uploadProjectCoverButton.addEventListener('click', () => projectCoverFileInput.click());
projectCoverFileInput.addEventListener('change', uploadManualProjectCover);
deleteProjectCoverButton.addEventListener('click', deleteManualProjectCover);
projectList.addEventListener('click', async (event) => {
    const openButton = event.target.closest('[data-action="open-project"]');
    if (openButton) {
        try {
            const projectId = openButton.dataset.projectId;
            const projectPromise = loadProjectDetail(projectId);
            const structurePromise = WorkbenchApi.getProjectBookStructure(projectId);
            const project = await projectPromise;
            showProjectWorkspace(project, structurePromise);
        } catch (error) {
            window.alert(error.message);
        }
    }
    const editButton = event.target.closest('[data-action="edit-project"]');
    if (editButton) {
        try {
            const project = await loadProjectDetail(editButton.dataset.projectId);
            openNewProjectDialog(project);
        } catch (error) {
            window.alert(error.message);
        }
    }
    const deleteButton = event.target.closest('[data-action="delete-project"]');
    if (deleteButton) {
        const project = mockProjects.find((item) => item.projectId === deleteButton.dataset.projectId);
        if (project) await deleteBookProject(project);
    }
});

async function loadProjectDetail(projectId) {
    const project = await WorkbenchApi.getProject(projectId);
    const index = mockProjects.findIndex((item) => item.projectId === projectId);
    if (index >= 0) mockProjects[index] = project;
    return project;
}

async function deleteBookProject(project) {
    if (!window.confirm(`Видалити проєкт «${project.title}» разом із завантаженою книгою та всіма напрацюваннями?`)) return;
    try {
        await WorkbenchApi.deleteProject(project.projectId);
        const index = mockProjects.findIndex((item) => item.projectId === project.projectId);
        if (index >= 0) mockProjects.splice(index, 1);
        renderProjects(mockProjects);
    } catch (error) {
        window.alert(error.message);
    }
}
editCurrentProjectButton.addEventListener('click', () => {
    if (currentProject) {
        openNewProjectDialog(currentProject);
    }
});
manageReferencesButton.addEventListener('click', () => {
    if (currentProject) {
        openReferencesDialog();
    }
});
closeReferencesDialogButton.addEventListener('click', closeReferencesDialog);
cancelReferencesButton.addEventListener('click', closeReferencesDialog);
saveReferencesButton.addEventListener('click', saveReferences);
referencesShowRuleFormButton.addEventListener('click', () => toggleInlineForm(referencesRuleForm, true));
referencesCancelRuleButton.addEventListener('click', () => toggleInlineForm(referencesRuleForm, false));
referencesAddRuleButton.addEventListener('click', addReferencesRule);
referencesShowGlossaryFormButton.addEventListener('click', () => toggleInlineForm(referencesGlossaryForm, true));
referencesCancelGlossaryButton.addEventListener('click', () => toggleInlineForm(referencesGlossaryForm, false));
referencesAddGlossaryButton.addEventListener('click', addReferencesGlossaryEntry);
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
openBriefDialogButton.addEventListener('click', openBriefDialog);
closeBriefDialogButton.addEventListener('click', closeBriefDialog);
addBriefMessageButton.addEventListener('click', addBriefMessage);

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
        if (currentProject) {
            currentProject = await WorkbenchApi.getProject(currentProject.projectId);
            const projectIndex = mockProjects.findIndex((project) => project.projectId === currentProject.projectId);
            if (projectIndex >= 0) mockProjects[projectIndex] = currentProject;
            renderProjects(mockProjects);
            renderProjectInformation(currentProject);
        }
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
        chapter.elements.filter((element) => element.type === 'paragraph').map((rawParagraph, paragraphIndex) => {
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

async function downloadCurrentProjectArchive() {
    if (!currentProject) return;
    downloadProjectArchiveButton.disabled = true;
    try {
        const archive = await WorkbenchApi.downloadProjectBookArchive(currentProject.projectId, translationSnapshot());
        downloadBlob(archive.blob, archive.filename);
    } catch (error) {
        window.alert(error.message);
    } finally {
        downloadProjectArchiveButton.disabled = false;
    }
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
    downloadProjectArchiveButton.hidden = false;
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
            elements: (chapter.elements || (chapter.paragraphs || []).map((paragraph) => ({ type: 'paragraph', ...(typeof paragraph === 'string' ? { originalText: paragraph } : paragraph) }))).map((rawElement) => {
                if (rawElement.type === 'image') {
                    return rawElement;
                }
                const rawParagraph = rawElement;
                if (typeof rawParagraph !== 'string') {
                    return {
                        type: 'paragraph',
                        paragraphId: rawParagraph.paragraphId || null,
                        originalText: rawParagraph.originalText || '',
                        translationText: rawParagraph.translationText || null,
                        reviewed: Boolean(rawParagraph.reviewed),
                    };
                }
                return {
                    type: 'paragraph',
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
        void loadChapterAIAnalysisConnections();
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
        chapterButton.textContent = `${String(chapterIndex + 1).padStart(2, '0')} · ${chapter.title || `Chapter ${chapterIndex + 1}`}`;
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
    chapterAIAnalysisConnections.replaceChildren();
    chapterAIAnalysisResults.replaceChildren();
    chapterAIAnalysisStatus.textContent = '';
    chapterText.hidden = true;
}

async function loadChapterAIAnalysisConnections() {
    if (!currentProject) return;
    try {
        integrationConnections = await WorkbenchApi.listConnections();
        renderChapterAIAnalysis(loadedChapters[selectedChapterIndex]);
    } catch (error) {
        chapterAIAnalysisStatus.textContent = error.message;
    }
}

function renderChapterAIAnalysis(chapter) {
    if (!chapter) return;
    chapterAIAnalysisCategories.querySelectorAll('input').forEach((checkbox) => {
        checkbox.checked = true;
    });
    chapterAIAnalysisConnections.replaceChildren();
    const configuredIds = new Set(
        (currentProject?.aiConfiguration?.analysisConnectionIds || [])
            .filter((connectionId) => typeof connectionId === 'string' && connectionId),
    );
    const providerNames = { openai: 'GPT', gemini: 'Gemini', claude: 'Claude' };
    integrationConnections
        .filter((connection) => (
            configuredIds.has(connection.connectionId)
            && connection.enabled
            && connection.statusCode === 'ok'
            && Object.hasOwn(providerNames, connection.providerId)
        ))
        .forEach((connection) => {
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = connection.connectionId;
            checkbox.checked = true;
            label.append(checkbox, document.createTextNode(`${providerNames[connection.providerId]} (${connection.displayName})`));
            checkbox.addEventListener('change', () => {
                renderChapterAIAnalysisResults(chapter.aiAnalysisResults || {}, getSelectedChapterAIProviderIds());
            });
            chapterAIAnalysisConnections.append(label);
        });
    renderChapterAIAnalysisResults(chapter.aiAnalysisResults || {}, getSelectedChapterAIProviderIds());
}

function setChapterAICategories(selected) {
    chapterAIAnalysisCategories.querySelectorAll('input').forEach((checkbox) => {
        checkbox.checked = selected;
    });
}

function getSelectedChapterAIProviderIds() {
    const selectedConnectionIds = new Set(
        [...chapterAIAnalysisConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value),
    );
    return new Set(
        integrationConnections
            .filter((connection) => selectedConnectionIds.has(connection.connectionId))
            .map((connection) => connection.providerId),
    );
}

function renderChapterAIAnalysisResults(results, selectedProviderIds = new Set()) {
    chapterAIAnalysisResults.replaceChildren();
    const providerNames = { openai: 'GPT', gemini: 'Gemini', claude: 'Claude' };
    Object.entries(results || {}).forEach(([resultKey, result]) => {
        const providerId = result?.providerId || resultKey;
        if (!selectedProviderIds.has(providerId) || !Object.hasOwn(providerNames, providerId) || !result || typeof result !== 'object') {
            return;
        }
        const section = document.createElement('section');
        section.className = 'chapter-ai-analysis-result';
        section.dataset.providerId = providerId;
        const heading = document.createElement('h5');
        heading.textContent = providerNames[providerId];
        const content = document.createElement('pre');
        content.textContent = result.status === 'completed' ? result.text : `Помилка: ${result.message}`;
        section.append(heading, content);
        chapterAIAnalysisResults.append(section);
    });
}

async function runChapterAIAnalysis() {
    if (!currentProject || selectedChapterIndex === null) return;
    const chapter = loadedChapters[selectedChapterIndex];
    const categories = [...chapterAIAnalysisCategories.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    const connectionIds = [...chapterAIAnalysisConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (!categories.length || !connectionIds.length) {
        chapterAIAnalysisStatus.textContent = 'Оберіть категорії та хоча б одну модель.';
        return;
    }
    runChapterAIAnalysisButton.disabled = true;
    chapterAIAnalysisStatus.textContent = 'Виконується аналіз…';
    try {
        const response = await WorkbenchApi.analyzeChapter(currentProject.projectId, chapter.chapterId, {
            categories,
            connectionIds,
            customPrompt: chapterAIAnalysisPrompt.value
        });
        chapter.aiAnalysisResults = response.savedResults;
        renderChapterAIAnalysisResults(chapter.aiAnalysisResults, getSelectedChapterAIProviderIds());
        chapterAIAnalysisStatus.textContent = 'Аналіз збережено.';
    } catch (error) {
        chapterAIAnalysisStatus.textContent = error.message;
    } finally {
        runChapterAIAnalysisButton.disabled = false;
    }
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

function showProjectWorkspace(project, structurePromise = null) {
    currentProject = project || currentProject;
    translationRulesInput.value = currentProject?.translationRules || '';
    translationRulesStatus.textContent = '';
    closeTranslationGlossaryEditor();
    void loadProjectTranslationGlossaries();
    downloadProjectArchiveButton.hidden = true;
    renderProjectInformation(currentProject);
    mainScreenView.hidden = true;
    settingsView.hidden = true;
    projectWorkspaceView.hidden = false;
    backToProjectsButton.hidden = false;
    showBookInfoMode();
    void restoreProjectBook(project, structurePromise);
}

async function loadProjectTranslationGlossaries() {
    if (!currentProject) return;
    try {
        projectTranslationGlossaries = await WorkbenchApi.listProjectTranslationGlossaries(currentProject.projectId);
        renderProjectTranslationGlossaries();
    } catch (error) {
        translationGlossaryList.textContent = error.message;
    }
}

function renderProjectTranslationGlossaries() {
    translationGlossaryList.replaceChildren();
    if (projectTranslationGlossaries.length === 0) {
        const empty = document.createElement('p');
        empty.className = 'muted';
        empty.textContent = 'Структурованих правил ще немає.';
        translationGlossaryList.append(empty);
        return;
    }
    projectTranslationGlossaries.forEach((glossary) => {
        const item = document.createElement('div');
        item.className = 'translation-glossary-item';
        const details = document.createElement('div');
        const title = document.createElement('strong');
        title.textContent = `Глосарій ${glossary.sourceLanguage} → ${glossary.targetLanguage}`;
        const summary = document.createElement('p');
        summary.className = 'muted';
        const synchronized = glossary.providerSync?.contentHash === glossary.contentHash;
        summary.textContent = `${glossary.entries.length} термінів · ${synchronized ? 'Синхронізовано з DeepL' : 'Потребує синхронізації'}`;
        const preview = document.createElement('div');
        preview.className = 'translation-glossary-preview';
        const previewEntries = glossary.entries.slice(0, 3);
        previewEntries.forEach((entry) => {
            const previewEntry = document.createElement('div');
            previewEntry.className = 'translation-glossary-preview-entry';
            const terms = document.createElement('span');
            terms.textContent = `${entry.source} → ${entry.target}`;
            previewEntry.append(terms);
            if (entry.context?.trim()) {
                const context = document.createElement('small');
                context.textContent = entry.context;
                previewEntry.append(context);
            }
            preview.append(previewEntry);
        });
        const remainingEntryCount = glossary.entries.length - previewEntries.length;
        if (remainingEntryCount > 0) {
            const remaining = document.createElement('span');
            remaining.className = 'translation-glossary-preview-more';
            remaining.textContent = `+ ще ${remainingEntryCount}`;
            preview.append(remaining);
        }
        details.append(title, summary, preview);
        const edit = document.createElement('button');
        edit.type = 'button';
        edit.className = 'secondary-btn';
        edit.textContent = 'Редагувати';
        edit.dataset.editTranslationGlossary = glossary.glossaryRuleId;
        item.append(details, edit);
        translationGlossaryList.append(item);
    });
}

async function openTranslationGlossaryEditor(glossary = null) {
    editingTranslationGlossaryId = glossary?.glossaryRuleId || null;
    translationGlossarySourceLanguage.value = glossary?.sourceLanguage || 'EN';
    translationGlossaryTargetLanguage.value = glossary?.targetLanguage || 'UK';
    translationGlossaryStatus.textContent = '';
    translationGlossaryEditor.hidden = false;
    translationGlossaryEntries.replaceChildren();
    translationGlossaryDraft = [];

    try {
        translationGlossaryCatalog = await WorkbenchApi.listGlossary();
        if (editingTranslationGlossaryId && currentProject) {
            const currentVersion = await WorkbenchApi.getProjectTranslationGlossaryCurrentVersion(
                currentProject.projectId,
                editingTranslationGlossaryId,
            );
            const materialized = await WorkbenchApi.materializeProjectTranslationGlossaryVersion(
                currentProject.projectId,
                editingTranslationGlossaryId,
                currentVersion.versionId,
            );
            translationGlossaryDraft = materialized.entries.map((entry, index) => ({
                draftId: crypto.randomUUID(),
                glossaryEntryId: currentVersion.glossaryEntryIds[index] || null,
                source: entry.source || '',
                target: entry.target || '',
                context: entry.context || '',
            }));
        }
        renderTranslationGlossaryDraft();
    } catch (error) {
        translationGlossaryStatus.textContent = error.message;
    }
}

function closeTranslationGlossaryEditor() {
    editingTranslationGlossaryId = null;
    translationGlossaryDraft = [];
    translationGlossaryCatalog = [];
    translationGlossaryEntries.replaceChildren();
    translationGlossaryExistingEntrySelect.replaceChildren();
    translationGlossaryStatus.textContent = '';
    translationGlossaryEditor.hidden = true;
}

function renderTranslationGlossaryDraft() {
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
}

function renderTranslationGlossaryExistingEntryOptions() {
    translationGlossaryExistingEntrySelect.replaceChildren();
    const selectedIds = new Set(
        translationGlossaryDraft
            .map((item) => item.glossaryEntryId)
            .filter(Boolean),
    );
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Оберіть термін із довідника';
    translationGlossaryExistingEntrySelect.append(placeholder);

    translationGlossaryCatalog
        .filter((entry) => !selectedIds.has(entry.glossaryEntryId))
        .forEach((entry) => {
            const option = document.createElement('option');
            option.value = entry.glossaryEntryId;
            option.textContent = `${entry.source} → ${entry.target}${entry.note ? ` (${entry.note})` : ''}`;
            translationGlossaryExistingEntrySelect.append(option);
        });
}

function addExistingTranslationGlossaryEntryToDraft() {
    const glossaryEntryId = translationGlossaryExistingEntrySelect.value;
    if (!glossaryEntryId) return;
    const entry = translationGlossaryCatalog.find((item) => item.glossaryEntryId === glossaryEntryId);
    if (!entry) return;
    translationGlossaryDraft.push({
        draftId: crypto.randomUUID(),
        glossaryEntryId: entry.glossaryEntryId,
        source: entry.source,
        target: entry.target,
        context: entry.note || '',
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
    });
    renderTranslationGlossaryDraft();
}

async function resolveDraftGlossaryEntryIds() {
    const ids = [];
    for (const item of translationGlossaryDraft) {
        const source = String(item.source || '').trim();
        const target = String(item.target || '').trim();
        const context = String(item.context || '').trim();
        if (!source || !target) {
            throw new Error('Оригінал і переклад терміна обов’язкові.');
        }

        const exactCatalogEntry = translationGlossaryCatalog.find((entry) => (
            entry.source === source && entry.target === target && (entry.note || '') === context
        ));
        if (item.glossaryEntryId && exactCatalogEntry?.glossaryEntryId === item.glossaryEntryId) {
            ids.push(item.glossaryEntryId);
            continue;
        }
        if (exactCatalogEntry) {
            ids.push(exactCatalogEntry.glossaryEntryId);
            item.glossaryEntryId = exactCatalogEntry.glossaryEntryId;
            continue;
        }

        const created = await WorkbenchApi.createGlossaryEntry({
            source,
            target,
            note: context,
            active: true,
        });
        translationGlossaryCatalog.push(created);
        item.glossaryEntryId = created.glossaryEntryId;
        ids.push(created.glossaryEntryId);
    }
    return ids;
}

async function saveTranslationGlossary() {
    if (!currentProject) return;
    saveTranslationGlossaryButton.disabled = true;
    translationGlossaryStatus.textContent = 'Збереження версії глосарію…';
    try {
        const glossaryEntryIds = await resolveDraftGlossaryEntryIds();
        const savedGlossary = await WorkbenchApi.commitProjectTranslationGlossaryDraft(currentProject.projectId, {
            glossaryRuleId: editingTranslationGlossaryId,
            sourceLanguage: translationGlossarySourceLanguage.value,
            targetLanguage: translationGlossaryTargetLanguage.value,
            glossaryEntryIds,
        });
        editingTranslationGlossaryId = savedGlossary.glossaryRuleId;
        await loadProjectTranslationGlossaries();
        const syncResult = savedGlossary.providerSyncResult;
        if (syncResult && syncResult.status !== 'synced') {
            translationGlossaryStatus.textContent = `Версію збережено локально, але синхронізація з DeepL не вдалася: ${syncResult.message}`;
            return;
        }
        closeTranslationGlossaryEditor();
    } catch (error) {
        translationGlossaryStatus.textContent = error.message;
    } finally {
        saveTranslationGlossaryButton.disabled = false;
    }
}

async function saveTranslationRules() {
    if (!currentProject) return;
    saveTranslationRulesButton.disabled = true;
    translationRulesStatus.textContent = 'Збереження…';
    try {
        currentProject = await WorkbenchApi.updateProjectTranslationRules(
            currentProject.projectId,
            translationRulesInput.value
        );
        translationRulesInput.value = currentProject.translationRules || '';
        translationRulesStatus.textContent = 'Правила збережено.';
    } catch (error) {
        translationRulesStatus.textContent = error.message;
    } finally {
        saveTranslationRulesButton.disabled = false;
    }
}

function showBookInfoMode() {
    bookInfoWorkspace.hidden = false;
    projectInformationCard.hidden = false;
    projectFileCard.hidden = false;
    projectBriefCard.hidden = true;
    projectReferencesCard.hidden = true;
    analysisWorkspaceCard.hidden = true;
    translationWorkspaceCard.hidden = true;
    bookInfoModeButton.classList.add('active');
    bookInfoModeButton.setAttribute('aria-current', 'page');
    translationModeButton.classList.remove('active');
    translationModeButton.removeAttribute('aria-current');
    analysisModeButton.classList.remove('active');
    analysisModeButton.removeAttribute('aria-current');
}

function showAnalysisMode() {
    bookInfoWorkspace.hidden = true;
    projectInformationCard.hidden = true;
    projectFileCard.hidden = true;
    projectBriefCard.hidden = false;
    projectReferencesCard.hidden = false;
    analysisWorkspaceCard.hidden = false;
    translationWorkspaceCard.hidden = true;
    analysisModeButton.classList.add('active');
    analysisModeButton.setAttribute('aria-current', 'page');
    bookInfoModeButton.classList.remove('active');
    bookInfoModeButton.removeAttribute('aria-current');
    translationModeButton.classList.remove('active');
    translationModeButton.removeAttribute('aria-current');
}

function showTranslationMode() {
    bookInfoWorkspace.hidden = true;
    projectInformationCard.hidden = true;
    projectFileCard.hidden = true;
    projectBriefCard.hidden = true;
    projectReferencesCard.hidden = true;
    analysisWorkspaceCard.hidden = true;
    translationWorkspaceCard.hidden = false;
    translationModeButton.classList.add('active');
    translationModeButton.setAttribute('aria-current', 'page');
    bookInfoModeButton.classList.remove('active');
    bookInfoModeButton.removeAttribute('aria-current');
    analysisModeButton.classList.remove('active');
    analysisModeButton.removeAttribute('aria-current');
}

async function restoreProjectBook(project, structurePromise = null) {
    try {
        const structure = structurePromise
            ? await structurePromise
            : await WorkbenchApi.getProjectBookStructure(project.projectId);
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
    closeBriefDialog();
}

function showSettingsView() {
    mainScreenView.hidden = true;
    projectWorkspaceView.hidden = true;
    settingsView.hidden = false;
    backToProjectsButton.hidden = false;
    renderAuthorCatalog();
    renderSeriesCatalog();
    void loadConnections();
}

async function loadConnections() {
    connectionsNotice.className = 'connection-notice muted';
    connectionsNotice.textContent = 'Завантаження підключень…';
    connectionsList.replaceChildren();
    try {
        const [providerPayload, connections] = await Promise.all([
            WorkbenchApi.listIntegrationProviders(),
            WorkbenchApi.listConnections()
        ]);
        integrationProviders = providerPayload.providers;
        integrationConnections = connections;
        credentialStorageAvailable = providerPayload.credentialStorage.available;
        connectionsNotice.textContent = credentialStorageAvailable
            ? ''
            : 'Захищене сховище credentials недоступне. Налаштуйте WORKBENCH_CREDENTIALS_KEY і перезапустіть Workbench.';
        connectionsNotice.className = credentialStorageAvailable
            ? 'connection-notice'
            : 'connection-notice warning';
        renderConnections();
    } catch (error) {
        connectionsNotice.className = 'connection-notice error';
        connectionsNotice.textContent = error.message;
    }
}

function renderConnections() {
    connectionsList.replaceChildren();
    integrationProviders.forEach((provider) => {
        const connection = integrationConnections.find((item) => item.providerId === provider.providerId);
        const item = document.createElement('article');
        item.className = 'connection-item';

        const details = document.createElement('div');
        details.className = 'connection-details';
        const title = document.createElement('h3');
        title.textContent = connection?.displayName || provider.displayName;
        const description = document.createElement('p');
        description.className = 'muted';
        description.textContent = provider.description;
        const status = document.createElement('span');
        status.className = `connection-status ${connection?.status || 'unconfigured'}`;
        status.textContent = connectionStatusLabel(connection?.status || 'unconfigured');
        details.append(title, description, status);

        if (connection?.statusMessage) {
            const statusMessage = document.createElement('p');
            statusMessage.className = 'connection-status-message';
            statusMessage.textContent = connection.statusMessage;
            details.append(statusMessage);
        }
        if (connection?.providerMetadata?.characterLimit != null) {
            const usage = document.createElement('p');
            usage.className = 'muted connection-usage';
            usage.textContent = `Використано ${connection.providerMetadata.characterCount ?? 0} із ${connection.providerMetadata.characterLimit} символів`;
            details.append(usage);
        }

        const actions = document.createElement('div');
        actions.className = 'connection-actions';
        actions.append(createConnectionButton(
            connection ? 'Редагувати' : provider.providerId === 'openai' ? '＋ Додати' : 'Налаштувати',
            'configure',
            provider.providerId,
            connection?.connectionId,
            !credentialStorageAvailable
        ));
        if (connection) {
            actions.append(
                createConnectionButton('Перевірити', 'test', provider.providerId, connection.connectionId, !credentialStorageAvailable),
                createConnectionButton('Видалити', 'delete', provider.providerId, connection.connectionId, false, true)
            );
        }
        item.append(details, actions);
        connectionsList.append(item);
    });
}

function createConnectionButton(label, action, providerId, connectionId, disabled, danger = false) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = danger ? 'text-btn danger-btn' : 'secondary-btn';
    button.textContent = label;
    button.dataset.connectionAction = action;
    button.dataset.providerId = providerId;
    if (connectionId) button.dataset.connectionId = connectionId;
    button.disabled = disabled;
    return button;
}

function connectionStatusLabel(status) {
    return {
        unconfigured: 'Не налаштовано',
        untested: 'Не перевірено',
        connected: 'Підключено',
        error: 'Помилка',
        locked: 'Заблоковано'
    }[status] || 'Невідомо';
}

function handleConnectionAction(event) {
    const button = event.target.closest('[data-connection-action]');
    if (!button) return;
    const provider = integrationProviders.find((item) => item.providerId === button.dataset.providerId);
    const connection = integrationConnections.find((item) => item.connectionId === button.dataset.connectionId);
    if (button.dataset.connectionAction === 'configure') openConnectionDialog(provider, connection);
    if (button.dataset.connectionAction === 'test' && connection) void testConnection(connection);
    if (button.dataset.connectionAction === 'delete' && connection) void deleteConnection(connection);
}

function openConnectionDialog(provider, connection) {
    if (!provider || !credentialStorageAvailable) return;
    connectionForm.dataset.providerId = provider.providerId;
    connectionForm.dataset.connectionId = connection?.connectionId || '';
    connectionDialogTitle.textContent = `${connection ? 'Редагувати' : 'Налаштувати'} ${provider.displayName}`;
    connectionDisplayName.value = connection?.displayName || provider.displayName;
    connectionCredentialFields.replaceChildren();
    provider.credentialFields.forEach((field) => {
        const label = document.createElement('label');
        label.htmlFor = `connection-field-${field.name}`;
        label.textContent = field.label;
        const input = document.createElement('input');
        input.id = label.htmlFor;
        input.type = field.secret ? 'password' : 'text';
        input.placeholder = field.placeholder || '';
        input.autocomplete = 'off';
        input.dataset.credentialField = field.name;
        input.required = field.required && !connection;
        connectionCredentialFields.append(label, input);
    });
    connectionCredentialHint.textContent = connection
        ? 'Залиште credentials порожніми, щоб зберегти поточні.'
        : 'Credentials зберігаються лише у зашифрованому вигляді.';
    connectionError.hidden = true;
    connectionError.textContent = '';
    connectionDialog.hidden = false;
    connectionDisplayName.focus();
}

function closeConnectionDialog() {
    connectionForm.reset();
    connectionForm.dataset.providerId = '';
    connectionForm.dataset.connectionId = '';
    connectionCredentialFields.replaceChildren();
    connectionError.textContent = '';
    connectionError.hidden = true;
    connectionDialog.hidden = true;
}

async function saveConnection(event) {
    event.preventDefault();
    const connectionId = connectionForm.dataset.connectionId;
    const credentials = {};
    connectionCredentialFields.querySelectorAll('[data-credential-field]').forEach((input) => {
        if (input.value) credentials[input.dataset.credentialField] = input.value;
    });
    const payload = {
        providerId: connectionForm.dataset.providerId,
        displayName: connectionDisplayName.value.trim()
    };
    if (!connectionId || Object.keys(credentials).length) payload.credentials = credentials;
    try {
        if (connectionId) {
            await WorkbenchApi.updateConnection(connectionId, payload);
        } else {
            await WorkbenchApi.createConnection(payload);
        }
        closeConnectionDialog();
        await loadConnections();
    } catch (error) {
        connectionCredentialFields.querySelectorAll('input').forEach((input) => { input.value = ''; });
        connectionError.textContent = error.message;
        connectionError.hidden = false;
    }
}

async function testConnection(connection) {
    connectionsNotice.className = 'connection-notice muted';
    connectionsNotice.textContent = `Перевірка ${connection.displayName}…`;
    try {
        await WorkbenchApi.testConnection(connection.connectionId);
        await loadConnections();
    } catch (error) {
        connectionsNotice.className = 'connection-notice error';
        connectionsNotice.textContent = error.message;
    }
}

async function deleteConnection(connection) {
    if (!window.confirm(`Видалити підключення «${connection.displayName}»?`)) return;
    try {
        await WorkbenchApi.deleteConnection(connection.connectionId);
        await loadConnections();
    } catch (error) {
        connectionsNotice.className = 'connection-notice error';
        connectionsNotice.textContent = error.message;
    }
}

async function openBriefDialog() {
    if (!currentProject) {
        return;
    }
    briefDialogProject.textContent = currentProject.title;
    briefMessageInput.value = '';
    briefMessages.replaceChildren(createEmptyEntry('Завантаження…'));
    briefAgreedList.replaceChildren(createEmptyEntry('Завантаження…'));
    briefDialog.hidden = false;
    try {
        currentBriefEntries = await WorkbenchApi.listProjectBrief(currentProject.projectId);
    } catch (error) {
        currentBriefEntries = [];
        window.alert(error.message);
    }
    renderBriefMessages();
    renderBriefAgreedList();
}

function closeBriefDialog() {
    briefDialog.hidden = true;
    currentBriefEntries = [];
}

function renderBriefMessages() {
    briefMessages.replaceChildren();
    if (currentBriefEntries.length === 0) {
        briefMessages.append(createEmptyEntry('Повідомлень поки немає.'));
        return;
    }
    currentBriefEntries.forEach((entry) => {
        const item = document.createElement('div');
        item.className = 'entry-item brief-message-item';
        const text = document.createElement('span');
        text.textContent = entry.text;
        const agreedLabel = document.createElement('label');
        agreedLabel.className = 'paragraph-review';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = entry.agreed;
        checkbox.addEventListener('change', () => toggleBriefEntryAgreed(entry, checkbox.checked));
        const checkboxText = document.createElement('span');
        checkboxText.textContent = 'Узгоджено';
        agreedLabel.append(checkbox, checkboxText);
        item.append(text, agreedLabel);
        briefMessages.append(item);
    });
}

function renderBriefAgreedList() {
    briefAgreedList.replaceChildren();
    const agreedEntries = currentBriefEntries.filter((entry) => entry.agreed);
    if (agreedEntries.length === 0) {
        briefAgreedList.append(createEmptyEntry('Поки немає узгоджених рішень'));
        return;
    }
    agreedEntries.forEach((entry) => {
        const item = document.createElement('div');
        item.className = 'entry-item';
        const text = document.createElement('span');
        text.textContent = entry.text;
        item.append(text);
        briefAgreedList.append(item);
    });
}

async function addBriefMessage() {
    const text = briefMessageInput.value.trim();
    if (!text || !currentProject) {
        return;
    }
    try {
        const entry = await WorkbenchApi.createProjectBriefEntry(currentProject.projectId, { text });
        currentBriefEntries.push(entry);
        briefMessageInput.value = '';
        renderBriefMessages();
        renderBriefAgreedList();
    } catch (error) {
        window.alert(error.message);
    }
}

async function toggleBriefEntryAgreed(entry, agreed) {
    try {
        const updated = await WorkbenchApi.updateProjectBriefEntry(currentProject.projectId, entry.entryId, { text: entry.text, agreed });
        Object.assign(entry, updated);
        renderBriefMessages();
        renderBriefAgreedList();
    } catch (error) {
        window.alert(error.message);
    }
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
    renderProjectInformationCover(project.projectId);
    renderSelectedReferencesSummary(project);
}

function renderProjectInformationCover(projectId) {
    projectInformationCover.replaceChildren();
    const image = document.createElement('img');
    image.alt = 'Обкладинка проєкту';
    image.src = `/api/projects/${projectId}/cover?v=${Date.now()}`;
    image.onerror = () => projectInformationCover.replaceChildren(createProjectCoverPlaceholder());
    projectInformationCover.append(image);
}

function renderSelectedReferencesSummary(project) {
    const customRuleCount = project.projectRuleIds?.length || 0;
    const customGlossaryCount = project.projectGlossaryEntryIds?.length || 0;
    const inheritedRuleCount = project.inheritedRules?.filter((item) => item.confirmed).length || 0;
    const inheritedGlossaryCount = project.inheritedGlossary?.filter((item) => item.confirmed).length || 0;
    const ruleCount = customRuleCount + inheritedRuleCount;
    const glossaryCount = customGlossaryCount + inheritedGlossaryCount;
    if (ruleCount === 0 && glossaryCount === 0) {
        selectedReferencesInfo.textContent = 'Нічого не обрано';
        return;
    }
    selectedReferencesInfo.textContent = `Правила: ${ruleCount} (${customRuleCount} власних, ${inheritedRuleCount} успадкованих) · Глосарій: ${glossaryCount} (${customGlossaryCount} власних, ${inheritedGlossaryCount} успадкованих)`;
}

function openReferencesDialog() {
    referencesDialogProject.textContent = currentProject.title;
    referencesDraft = {
        ruleIds: [...(currentProject.projectRuleIds || [])],
        glossaryEntryIds: [...(currentProject.projectGlossaryEntryIds || [])],
        inheritedRules: (currentProject.inheritedRules || []).map((item) => ({ ...item })),
        inheritedGlossary: (currentProject.inheritedGlossary || []).map((item) => ({ ...item })),
    };
    toggleInlineForm(referencesRuleForm, false);
    toggleInlineForm(referencesGlossaryForm, false);
    renderReferencesRules();
    renderReferencesGlossary();
    renderReferencesInheritedRules();
    renderReferencesInheritedGlossary();
    referencesDialog.hidden = false;
}

function closeReferencesDialog() {
    referencesDialog.hidden = true;
    referencesDraft = null;
}

function renderReferencesRules() {
    referencesRulesList.replaceChildren();
    if (mockRules.length === 0) {
        referencesRulesList.append(createEmptyEntry('Довідник правил поки порожній'));
        return;
    }
    const inheritedRuleIds = new Set(referencesDraft.inheritedRules.map((item) => item.ruleId));
    mockRules.filter((rule) => !inheritedRuleIds.has(rule.ruleId)).forEach((rule) => {
        const label = document.createElement('label');
        label.className = 'checkbox-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = referencesDraft.ruleIds.includes(rule.ruleId);
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                referencesDraft.ruleIds.push(rule.ruleId);
            } else {
                referencesDraft.ruleIds = referencesDraft.ruleIds.filter((id) => id !== rule.ruleId);
            }
        });
        const text = document.createElement('span');
        text.textContent = `${rule.text}${rule.category ? ` · ${rule.category}` : ''}`;
        label.append(checkbox, text);
        referencesRulesList.append(label);
    });
}

function renderReferencesGlossary() {
    referencesGlossaryList.replaceChildren();
    if (mockGlossaryEntries.length === 0) {
        referencesGlossaryList.append(createEmptyEntry('Глосарій поки порожній'));
        return;
    }
    const inheritedGlossaryIds = new Set(referencesDraft.inheritedGlossary.map((item) => item.glossaryEntryId));
    mockGlossaryEntries.filter((entry) => !inheritedGlossaryIds.has(entry.glossaryEntryId)).forEach((entry) => {
        const label = document.createElement('label');
        label.className = 'checkbox-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = referencesDraft.glossaryEntryIds.includes(entry.glossaryEntryId);
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                referencesDraft.glossaryEntryIds.push(entry.glossaryEntryId);
            } else {
                referencesDraft.glossaryEntryIds = referencesDraft.glossaryEntryIds.filter((id) => id !== entry.glossaryEntryId);
            }
        });
        const text = document.createElement('span');
        text.textContent = `${entry.source} → ${entry.target}`;
        label.append(checkbox, text);
        referencesGlossaryList.append(label);
    });
}

function renderReferencesInheritedRules() {
    referencesInheritedRulesList.replaceChildren();
    if (referencesDraft.inheritedRules.length === 0) {
        referencesInheritedRulesList.append(createEmptyEntry('Успадкованих правил немає'));
        return;
    }
    referencesDraft.inheritedRules.forEach((reference) => {
        const rule = mockRules.find((item) => item.ruleId === reference.ruleId);
        if (!rule) {
            return;
        }
        const label = document.createElement('label');
        label.className = 'checkbox-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = Boolean(reference.confirmed);
        checkbox.addEventListener('change', () => {
            reference.confirmed = checkbox.checked;
            reference.confirmedAt = checkbox.checked ? new Date().toISOString() : null;
        });
        const text = document.createElement('span');
        text.textContent = `${rule.text}${rule.category ? ` · ${rule.category}` : ''}`;
        label.append(checkbox, text);
        referencesInheritedRulesList.append(label);
    });
}

function renderReferencesInheritedGlossary() {
    referencesInheritedGlossaryList.replaceChildren();
    if (referencesDraft.inheritedGlossary.length === 0) {
        referencesInheritedGlossaryList.append(createEmptyEntry('Успадкованих термінів немає'));
        return;
    }
    referencesDraft.inheritedGlossary.forEach((reference) => {
        const entry = mockGlossaryEntries.find((item) => item.glossaryEntryId === reference.glossaryEntryId);
        if (!entry) {
            return;
        }
        const label = document.createElement('label');
        label.className = 'checkbox-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = Boolean(reference.confirmed);
        checkbox.addEventListener('change', () => {
            reference.confirmed = checkbox.checked;
            reference.confirmedAt = checkbox.checked ? new Date().toISOString() : null;
        });
        const text = document.createElement('span');
        text.textContent = `${entry.source} → ${entry.target}`;
        label.append(checkbox, text);
        referencesInheritedGlossaryList.append(label);
    });
}

async function addReferencesRule() {
    const text = referencesRuleTextInput.value.trim();
    if (!text) {
        return;
    }
    try {
        const rule = await createRuleEntry(text, referencesRuleCategoryInput.value.trim() || null);
        referencesDraft.ruleIds.push(rule.ruleId);
        renderReferencesRules();
        referencesRuleTextInput.value = '';
        referencesRuleCategoryInput.value = '';
        toggleInlineForm(referencesRuleForm, false);
    } catch (error) {
        window.alert(error.message);
    }
}

async function addReferencesGlossaryEntry() {
    const source = referencesGlossarySourceInput.value.trim();
    const target = referencesGlossaryTargetInput.value.trim();
    if (!source || !target) {
        return;
    }
    try {
        const entry = await createGlossaryEntry(source, target, referencesGlossaryNoteInput.value.trim() || null);
        referencesDraft.glossaryEntryIds.push(entry.glossaryEntryId);
        renderReferencesGlossary();
        referencesGlossarySourceInput.value = '';
        referencesGlossaryTargetInput.value = '';
        referencesGlossaryNoteInput.value = '';
        toggleInlineForm(referencesGlossaryForm, false);
    } catch (error) {
        window.alert(error.message);
    }
}

async function saveReferences() {
    try {
        const updated = await WorkbenchApi.updateProject(currentProject.projectId, {
            projectRuleIds: [...referencesDraft.ruleIds],
            projectGlossaryEntryIds: [...referencesDraft.glossaryEntryIds],
            inheritedRules: referencesDraft.inheritedRules.map((item) => ({ ...item })),
            inheritedGlossary: referencesDraft.inheritedGlossary.map((item) => ({ ...item })),
        });
        currentProject = updated;
        const index = mockProjects.findIndex((item) => item.projectId === updated.projectId);
        if (index >= 0) {
            mockProjects[index] = updated;
        }
        renderSelectedReferencesSummary(currentProject);
        closeReferencesDialog();
    } catch (error) {
        window.alert(error.message);
    }
}

function renderProjects(projects) {
    projectList.replaceChildren();
    projects.forEach((project) => {
        const card = document.createElement('article');
        card.className = 'project-card';

        // Cover image
        const coverDiv = document.createElement('div');
        coverDiv.className = 'project-cover';
        const img = document.createElement('img');
        img.alt = `Обкладинка: ${project.title}`;
        img.src = `/api/projects/${project.projectId}/cover?v=${Date.now()}`;
        img.onerror = () => {
            // Show placeholder on error or if cover doesn't exist
            coverDiv.replaceChildren();
            const placeholder = document.createElement('div');
            placeholder.className = 'project-cover-placeholder';
            placeholder.textContent = '📚\nНема обкладинки';
            coverDiv.append(placeholder);
        };
        coverDiv.append(img);

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
        const deleteButton = document.createElement('button');
        deleteButton.className = 'text-btn danger-btn';
        deleteButton.type = 'button';
        deleteButton.dataset.action = 'delete-project';
        deleteButton.dataset.projectId = project.projectId;
        deleteButton.textContent = 'Видалити';
        progress.append(progressHeading, progressTrack, openButton, editButton, deleteButton);

        card.append(coverDiv, details, progress);
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
    newProjectDialogTitle.textContent = project ? 'Редагувати проєкт' : 'Новий книжковий проєкт';
    newProjectDraft = {
        authorId: project?.authorId || '',
        seriesId: project?.seriesId || null,
        inheritedRules: (project?.inheritedRules || []).map((item) => ({ ...item })),
        inheritedGlossary: (project?.inheritedGlossary || []).map((item) => ({ ...item })),
        inheritedContextSeriesId: project?.seriesId || null,
        inheritedContextAuthorId: project?.authorId || '',
        projectRuleIds: project?.projectRuleIds || [],
        projectGlossaryEntryIds: project?.projectGlossaryEntryIds || [],
        aiConfiguration: project?.aiConfiguration || {}
    };
    newProjectForm.reset();
    projectTitleInput.value = project?.title || '';
    projectBookNumberInput.value = project?.bookNumber || '';
    projectStatusSelect.value = project?.status || 'new';
    renderProjectAIConnectionOptions(newProjectDraft.aiConfiguration);
    void loadProjectAIConnections();
    projectCoverEditor.hidden = !project;
    projectCoverFileInput.value = '';
    if (project) {
        renderProjectCoverEditor(project.projectId);
    }
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

async function loadProjectAIConnections() {
    try {
        integrationConnections = await WorkbenchApi.listConnections();
        if (newProjectDialog.hidden || !newProjectDraft) return;
        renderProjectAIConnectionOptions(newProjectDraft.aiConfiguration);
    } catch (error) {
        newProjectError.textContent = error.message;
        newProjectError.hidden = false;
    }
}

function renderProjectAIConnectionOptions(configuration = {}) {
    const selectedIds = new Set([
        configuration.translationConnectionId,
        configuration.orchestrationConnectionId,
        ...(configuration.analysisConnectionIds || []),
        ...(configuration.qaConnectionIds || [])
    ].filter(Boolean));
    const connections = integrationConnections.filter((connection) => (
        ['deepl', 'openai', 'gemini', 'claude'].includes(connection.providerId)
        && (connection.status === 'connected' || selectedIds.has(connection.connectionId))
    ));
    const analysisConnections = connections.filter((connection) => (
        ['openai', 'gemini', 'claude'].includes(connection.providerId)
    ));
    const appendOptions = (select, multiple) => {
        select.replaceChildren();
        if (!multiple) {
            const empty = document.createElement('option');
            empty.value = '';
            empty.textContent = 'Не обрано';
            select.append(empty);
        }
        connections.forEach((connection) => {
            const option = document.createElement('option');
            option.value = connection.connectionId;
            option.textContent = `${connection.displayName} (${connection.providerId})`;
            select.append(option);
        });
    };
    appendOptions(projectTranslationConnectionSelect, false);
    appendOptions(projectOrchestrationConnectionSelect, false);
    projectAnalysisConnectionsSelect.replaceChildren();
    analysisConnections.forEach((connection) => {
        const label = document.createElement('label');
        label.className = 'project-analysis-connection-option';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = connection.connectionId;
        checkbox.checked = (configuration.analysisConnectionIds || []).includes(connection.connectionId);
        label.append(checkbox, document.createTextNode(`${connection.providerId === 'openai' ? 'GPT' : connection.providerId === 'gemini' ? 'Gemini' : 'Claude'} (${connection.displayName})`));
        projectAnalysisConnectionsSelect.append(label);
    });
    appendOptions(projectQaConnectionsSelect, true);
    projectTranslationConnectionSelect.value = configuration.translationConnectionId || '';
    projectOrchestrationConnectionSelect.value = configuration.orchestrationConnectionId || '';
    [...projectQaConnectionsSelect.options].forEach((option) => {
        option.selected = (configuration.qaConnectionIds || []).includes(option.value);
    });
}

function readProjectAIConfiguration() {
    return {
        translationConnectionId: projectTranslationConnectionSelect.value || null,
        orchestrationConnectionId: projectOrchestrationConnectionSelect.value || null,
        analysisConnectionIds: [...projectAnalysisConnectionsSelect.querySelectorAll('input:checked')].map((input) => input.value),
        qaConnectionIds: [...projectQaConnectionsSelect.selectedOptions].map((option) => option.value)
    };
}

function closeNewProjectDialog() {
    newProjectDialog.hidden = true;
    newProjectDraft = null;
    editingProjectId = null;
}

function renderProjectCoverEditor(projectId) {
    projectCoverPreview.replaceChildren();
    const image = document.createElement('img');
    image.alt = 'Обкладинка проєкту';
    image.src = `/api/projects/${projectId}/cover?v=${Date.now()}`;
    image.onerror = () => {
        projectCoverPreview.replaceChildren(createProjectCoverPlaceholder());
        deleteProjectCoverButton.hidden = true;
    };
    image.onload = () => {
        deleteProjectCoverButton.hidden = false;
    };
    projectCoverPreview.append(image);
}

function createProjectCoverPlaceholder() {
    const placeholder = document.createElement('div');
    placeholder.className = 'project-cover-placeholder';
    placeholder.textContent = '📚\nНема обкладинки';
    return placeholder;
}

async function uploadManualProjectCover() {
    const [file] = projectCoverFileInput.files;
    if (!file || !editingProjectId) {
        return;
    }
    try {
        await WorkbenchApi.uploadProjectCover(editingProjectId, file);
        renderProjectCoverEditor(editingProjectId);
        renderProjects(mockProjects);
    } catch (error) {
        window.alert(error.message);
    } finally {
        projectCoverFileInput.value = '';
    }
}

async function deleteManualProjectCover() {
    if (!editingProjectId || !window.confirm('Видалити обкладинку?')) {
        return;
    }
    try {
        await WorkbenchApi.deleteProjectCover(editingProjectId);
        renderProjectCoverEditor(editingProjectId);
        renderProjects(mockProjects);
    } catch (error) {
        window.alert(error.message);
    }
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
        newProjectDraft.inheritedContextSeriesId = null;
        newProjectDraft.inheritedContextAuthorId = '';
        inheritedContent.hidden = true;
    }
    renderSeriesSelect();
    renderNewSeriesAuthorSelect();
    updateCreateProjectButton();
}

async function handleSeriesSelection() {
    newProjectDraft.seriesId = projectSeriesSelect.value || null;
    const context = await ensureSeriesAuthorContext(newProjectDraft.seriesId, newProjectDraft.authorId);
    const keepConfirmations = context
        && newProjectDraft.inheritedContextSeriesId === newProjectDraft.seriesId
        && newProjectDraft.inheritedContextAuthorId === newProjectDraft.authorId;
    const previousRules = new Map(newProjectDraft.inheritedRules.map((item) => [item.ruleId, item]));
    const previousGlossary = new Map(newProjectDraft.inheritedGlossary.map((item) => [item.glossaryEntryId, item]));
    newProjectDraft.inheritedRules = context
        ? context.ruleIds.map((ruleId) => ({
            ruleId,
            confirmed: keepConfirmations ? Boolean(previousRules.get(ruleId)?.confirmed) : false,
            confirmedAt: keepConfirmations ? previousRules.get(ruleId)?.confirmedAt || null : null,
        }))
        : [];
    newProjectDraft.inheritedGlossary = context
        ? context.glossaryEntryIds.map((glossaryEntryId) => ({
            glossaryEntryId,
            confirmed: keepConfirmations ? Boolean(previousGlossary.get(glossaryEntryId)?.confirmed) : false,
            confirmedAt: keepConfirmations ? previousGlossary.get(glossaryEntryId)?.confirmedAt || null : null,
        }))
        : [];
    newProjectDraft.inheritedContextSeriesId = context ? newProjectDraft.seriesId : null;
    newProjectDraft.inheritedContextAuthorId = context ? newProjectDraft.authorId : '';
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

async function createRuleEntry(text, category) {
    const rule = await WorkbenchApi.createRule({ text, category, active: true });
    mockRules.push(rule);
    return rule;
}

async function createGlossaryEntry(source, target, note) {
    const entry = await WorkbenchApi.createGlossaryEntry({ source, target, note, active: true });
    mockGlossaryEntries.push(entry);
    return entry;
}

async function createProjectRule() {
    const text = projectRuleTextInput.value.trim();
    if (!text) {
        return;
    }
    const rule = await createRuleEntry(text, projectRuleCategoryInput.value.trim() || null);
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
    const entry = await createGlossaryEntry(source, target, projectGlossaryNoteInput.value.trim() || null);
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
        aiConfiguration: readProjectAIConfiguration(),
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
    void loadChapterAIAnalysisConnections();
    persistCurrentProjectPosition();
}

function renderChapterText(chapter, chapterIndex) {
    const displayTitle = chapter.title || `Chapter ${chapterIndex}`;
    chapterTitle.textContent = `Вибраний розділ: ${displayTitle}`;
    chapterNumber.textContent = `Розділ ${chapterIndex} з ${loadedChapters.length}`;
    chapterName.textContent = `Назва: ${displayTitle}`;
    chapterWordCount.textContent = `Слів: ${formatNumber(chapter.wordCount)}`;
    chapterParagraphCount.textContent = `Абзаців: ${chapter.elements.filter((element) => element.type === 'paragraph').length}`;
    translateChapterButton.disabled = !chapter.chapterId;
    const state = getTranslationState(chapterIndex - 1, chapter);
    translationRows.replaceChildren();
    renderChapterTitleTranslation(chapter, state);
    renderChapterAIAnalysis(chapter);
    chapterText.hidden = false;

    let paragraphIndex = 0;
    chapter.elements.forEach((element) => {
        if (element.type === 'image') {
            const imageElement = document.createElement('figure');
            imageElement.className = 'inline-image-element';
            const image = document.createElement('img');
            image.src = WorkbenchApi.inlineImageUrl(element.imageId);
            image.alt = 'Зображення з книги';
            image.loading = 'lazy';
            imageElement.append(image);
            translationRows.append(imageElement);
            return;
        }
        const paragraph = element;
        const currentParagraphIndex = paragraphIndex;
        const draft = state.draft[currentParagraphIndex];
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
            syncParagraphPairHeight(original, translation);
        });
        const translationControl = document.createElement('div');
        translationControl.className = 'translation-control';
        const translateButton = document.createElement('button');
        translateButton.type = 'button';
        translateButton.className = 'secondary-btn translate-paragraph-button';
        translateButton.textContent = 'Перекласти DeepL';
        translateButton.disabled = !paragraph.paragraphId;
        translateButton.addEventListener('click', async () => {
            const previousText = translateButton.textContent;
            translateButton.disabled = true;
            translateButton.textContent = 'Перекладаємо…';
            try {
                const translated = await WorkbenchApi.translateParagraph(paragraph.paragraphId);
                state.undo.push(cloneParagraphDrafts(state.draft));
                translation.value = translated.translationText || '';
                syncParagraphPairHeight(original, translation);
                checkbox.checked = false;
                state.draft = readTranslationDraft();
                state.saved[currentParagraphIndex] = { ...state.draft[currentParagraphIndex] };
                state.redo = [];
                updateParagraphVisualStates(state.draft);
                updateTranslationButtons();
            } catch (error) {
                window.alert(error.message);
            } finally {
                translateButton.disabled = false;
                translateButton.textContent = previousText;
            }
        });
        translationControl.append(translation, translateButton);
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
        row.append(original, translationControl, review, status);
        translationRows.append(row);
        updateParagraphVisualState(row, draft);
        syncParagraphPairHeight(original, translation);
        paragraphIndex += 1;
    });
    restoreCurrentParagraphRow();
    updateTranslationButtons();
}

function syncParagraphPairHeight(original, translation) {
    original.style.height = 'auto';
    translation.style.height = 'auto';
    const height = `${Math.max(original.scrollHeight, translation.scrollHeight)}px`;
    original.style.height = height;
    translation.style.height = height;
}

function renderChapterTitleTranslation(chapter, state) {
    chapterTitleTranslation.replaceChildren();
    if (!chapter.title) {
        chapterTitleTranslation.hidden = true;
        return;
    }
    chapterTitleTranslation.hidden = false;
    const label = document.createElement('p');
    label.className = 'chapter-title-label';
    label.textContent = 'Назва розділу';
    const original = document.createElement('div');
    original.className = 'original-paragraph';
    original.textContent = chapter.title;
    const translation = document.createElement('textarea');
    translation.className = 'translation-paragraph chapter-title-input';
    translation.rows = 2;
    translation.value = state.titleDraft.translationTitle;
    translation.placeholder = 'Введіть переклад назви розділу...';
    translation.addEventListener('input', () => {
        state.titleDraft.translationTitle = translation.value;
        updateTranslationButtons();
    });
    const review = document.createElement('label');
    review.className = 'paragraph-review';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'chapter-title-reviewed';
    checkbox.checked = state.titleDraft.reviewed;
    checkbox.addEventListener('change', () => {
        state.titleDraft.reviewed = checkbox.checked;
        updateTranslationButtons();
    });
    const text = document.createElement('span');
    text.textContent = 'Перевірено';
    review.append(checkbox, text);
    chapterTitleTranslation.append(label, original, translation, review);
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
        const initialDraft = chapter.elements.filter((element) => element.type === 'paragraph').map(createParagraphDraft);
        translationStates.set(chapterIndex, {
            saved: cloneParagraphDrafts(initialDraft),
            draft: cloneParagraphDrafts(initialDraft),
            titleSaved: { translationTitle: chapter.translationTitle || '', reviewed: Boolean(chapter.titleReviewed) },
            titleDraft: { translationTitle: chapter.translationTitle || '', reviewed: Boolean(chapter.titleReviewed) },
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
    return state && (
        state.draft.some((draft, index) => !paragraphDraftsEqual(draft, state.saved[index]))
        || state.titleDraft.translationTitle !== state.titleSaved.translationTitle
        || state.titleDraft.reviewed !== state.titleSaved.reviewed
    );
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
    if (loadedChapters[selectedChapterIndex].title) {
        state.titleDraft = {
            translationTitle: chapterTitleTranslation.querySelector('.chapter-title-input').value,
            reviewed: chapterTitleTranslation.querySelector('.chapter-title-reviewed').checked,
        };
    }
    const dirtyIndexes = state.draft
        .map((draft, index) => (paragraphDraftsEqual(draft, state.saved[index]) ? -1 : index))
        .filter((index) => index !== -1);
    const persistableIndexes = dirtyIndexes.filter((index) => state.draft[index].paragraphId);
    const unpersistableIndexes = dirtyIndexes.filter((index) => !state.draft[index].paragraphId);
    if (unpersistableIndexes.length > 0) {
        console.warn(`Абзаци без paragraphId не будуть збережені (індекси: ${unpersistableIndexes.join(', ')}).`);
    }
    try {
        if (loadedChapters[selectedChapterIndex].title && (state.titleDraft.translationTitle !== state.titleSaved.translationTitle || state.titleDraft.reviewed !== state.titleSaved.reviewed)) {
            const title = await WorkbenchApi.updateChapterTitle(loadedChapters[selectedChapterIndex].chapterId, state.titleDraft);
            state.titleSaved = { translationTitle: title.translationTitle || '', reviewed: title.titleReviewed };
            loadedChapters[selectedChapterIndex].translationTitle = state.titleSaved.translationTitle;
            loadedChapters[selectedChapterIndex].titleReviewed = state.titleSaved.reviewed;
        }
        await Promise.all(persistableIndexes.map((index) => {
            const draft = state.draft[index];
            return WorkbenchApi.updateParagraph(draft.paragraphId, {
                translationText: draft.translationText || null,
                reviewed: draft.reviewed,
            });
        }));
        persistableIndexes.forEach((index) => {
            state.saved[index] = { ...state.draft[index] };
        });
        state.undo = [];
        state.redo = [];
        updateParagraphVisualStates(state.draft);
        updateTranslationButtons();
        if (unpersistableIndexes.length > 0) {
            window.alert('Деякі абзаци не мають paragraphId і не були збережені.');
            return false;
        }
        return true;
    } catch (error) {
        updateTranslationButtons();
        window.alert(`Не вдалося зберегти розділ: ${error.message}`);
        return false;
    }
}

async function translateCurrentChapter() {
    if (!currentProject || selectedChapterIndex === null) {
        return;
    }
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId) {
        return;
    }
    const state = translationStates.get(selectedChapterIndex);
    const previousText = translateChapterButton.textContent;
    translateChapterButton.disabled = true;
    translateChapterButton.textContent = 'Перекладаємо розділ…';
    try {
        const result = await WorkbenchApi.translateChapter(currentProject.projectId, chapter.chapterId);
        state.undo.push(cloneParagraphDrafts(state.draft));
        state.redo = [];
        const translationByParagraphId = new Map(
            (result.paragraphs || []).map((paragraph) => [paragraph.paragraphId, paragraph])
        );
        state.draft.forEach((draft, index) => {
            const translated = draft.paragraphId ? translationByParagraphId.get(draft.paragraphId) : null;
            if (!translated) {
                return;
            }
            state.draft[index] = {
                paragraphId: draft.paragraphId,
                translationText: translated.translationText || '',
                reviewed: Boolean(translated.reviewed),
            };
            state.saved[index] = { ...state.draft[index] };
        });
        renderTranslationFields(state.draft);
    } catch (error) {
        window.alert(error.message);
    } finally {
        translateChapterButton.disabled = false;
        translateChapterButton.textContent = previousText;
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
        const translation = row.querySelector('.translation-paragraph');
        translation.value = values[index].translationText;
        row.querySelector('.paragraph-review input').checked = values[index].reviewed;
        updateParagraphVisualState(row, values[index]);
        syncParagraphPairHeight(row.querySelector('.original-paragraph'), translation);
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
