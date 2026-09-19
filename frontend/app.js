const fileInput = document.querySelector('#file-input');
const uploadButton = document.querySelector('#upload-button');
const downloadProjectArchiveButton = document.querySelector('#download-project-archive');
const exportBilingualDocxButton = document.querySelector('#export-bilingual-docx');
const exportTranslationDocxButton = document.querySelector('#export-translation-docx');
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
const chapterExportCheckbox = document.querySelector('#chapter-export-checkbox');
const chapterAIAnalysisCategories = document.querySelector('#chapter-ai-analysis-categories');
const chapterAIAnalysisPrompt = document.querySelector('#chapter-ai-analysis-prompt');
const chapterAIAnalysisConnections = document.querySelector('#chapter-ai-analysis-connections');
const chapterAIAnalysisToggle = document.querySelector('#chapter-ai-analysis-toggle');
const chapterAIAnalysisToggleIcon = document.querySelector('#chapter-ai-analysis-toggle-icon');
const chapterAIAnalysisBody = document.querySelector('#chapter-ai-analysis-body');
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
const translationGlossaryEditorToggle = document.querySelector('#translation-glossary-editor-toggle');
const translationGlossaryEditorToggleIcon = document.querySelector('#translation-glossary-editor-toggle-icon');
const translationGlossaryEditorBody = document.querySelector('#translation-glossary-editor-body');
const translationGlossarySourceLanguage = document.querySelector('#translation-glossary-source-language');
const translationGlossaryTargetLanguage = document.querySelector('#translation-glossary-target-language');
const translationGlossaryEntries = document.querySelector('#translation-glossary-entries');
const addTranslationGlossaryEntryButton = document.querySelector('#add-translation-glossary-entry');
const openGlossaryCatalogDialogButton = document.querySelector('#open-glossary-catalog-dialog');
const glossaryCatalogDialog = document.querySelector('#glossary-catalog-dialog');
const closeGlossaryCatalogDialogButton = document.querySelector('#close-glossary-catalog-dialog');
const glossaryCatalogGroupsContainer = document.querySelector('#glossary-catalog-groups');
const saveTranslationGlossaryButton = document.querySelector('#save-translation-glossary');
const cancelTranslationGlossaryButton = document.querySelector('#cancel-translation-glossary');
const translationGlossaryStatus = document.querySelector('#translation-glossary-status');
const saveTranslationButton = document.querySelector('#save-translation');
const undoTranslationButton = document.querySelector('#undo-translation');
const redoTranslationButton = document.querySelector('#redo-translation');
const aiQaCountersSticky = document.querySelector('#ai-qa-counters-sticky');
const addFootnoteButton = document.querySelector('#add-footnote');
const footnoteDialog = document.querySelector('#footnote-dialog');
const closeFootnoteDialogButton = document.querySelector('#close-footnote-dialog');
const footnoteTextInput = document.querySelector('#footnote-text-input');
const saveFootnoteButton = document.querySelector('#save-footnote');
const deleteFootnoteButton = document.querySelector('#delete-footnote');
const bookReplacementDialog = document.querySelector('#book-replacement-dialog');
const archiveAndUploadButton = document.querySelector('#archive-and-upload');
const replaceWithoutArchiveButton = document.querySelector('#replace-without-archive');
const cancelBookReplacementButton = document.querySelector('#cancel-book-replacement');
const mainScreenView = document.querySelector('#main-screen-view');
const settingsView = document.querySelector('#settings-view');
const settingsBackToMainButton = document.querySelector('#settings-back-to-main');
const projectWorkspaceView = document.querySelector('#project-workspace-view');
const projectPageTitle = document.querySelector('#project-page-title');
const projectPageSummary = document.querySelector('#project-page-summary');
const quickActionsProjectTitle = document.querySelector('#quick-actions-project-title');
const openSearchButton = document.querySelector('#open-search');
const searchDialog = document.querySelector('#search-dialog');
const closeSearchDialogButton = document.querySelector('#close-search-dialog');
const searchInput = document.querySelector('#search-input');
const searchScopeToggle = document.querySelector('#search-scope-toggle');
const searchMatchToggle = document.querySelector('#search-match-toggle');
const deepLUsageBadge = document.querySelector('#deepl-usage-badge');
const deepLQuotaDialog = document.querySelector('#deepl-quota-dialog');
const closeDeepLQuotaDialogButton = document.querySelector('#close-deepl-quota-dialog');
const deepLQuotaDialogMessage = document.querySelector('#deepl-quota-dialog-message');
const deepLQuotaConnectionList = document.querySelector('#deepl-quota-connection-list');
const searchResultsContainer = document.querySelector('#search-results');
const searchNavBar = document.querySelector('#search-nav-bar');
const searchNavQueryLabel = document.querySelector('#search-nav-query');
const searchNavPositionLabel = document.querySelector('#search-nav-position');
const searchNavPrevButton = document.querySelector('#search-nav-prev');
const searchNavNextButton = document.querySelector('#search-nav-next');
const searchNavReturnButton = document.querySelector('#search-nav-return');
const searchNavExitButton = document.querySelector('#search-nav-exit');
const aiQaNavBar = document.querySelector('#ai-qa-nav-bar');
const aiQaNavPositionLabel = document.querySelector('#ai-qa-nav-position');
const aiQaNavContent = document.querySelector('#ai-qa-nav-content');
const aiQaNavPrevButton = document.querySelector('#ai-qa-nav-prev');
const aiQaNavNextButton = document.querySelector('#ai-qa-nav-next');
const aiQaNavExitButton = document.querySelector('#ai-qa-nav-exit');
const bookInfoModeButton = document.querySelector('[data-project-mode="book-info"]');
const analysisModeButton = document.querySelector('[data-project-mode="analysis"]');
const translationModeButton = document.querySelector('[data-project-mode="translation"]');
const bookInfoWorkspace = document.querySelector('#book-info-workspace');
const projectSubmodeNavigation = document.querySelector('#project-submode-navigation');
const translationInformationContent = document.querySelector('#translation-information-content');
const projectSubmodeButtons = document.querySelectorAll('.project-submode-navigation-button');
const translationRulesContent = document.querySelector('#translation-rules-content');
const translationStructuredRulesContent = document.querySelector('#translation-structured-rules-content');
const translationGlossaryContent = document.querySelector('#translation-glossary-content');
const translationQaContent = document.querySelector('#translation-qa-content');
const projectInformationCard = document.querySelector('.project-information-card');
const projectFileCard = document.querySelector('#project-file-card');
const projectBriefCard = document.querySelector('#project-brief-card');
const projectReferencesCard = document.querySelector('#project-references-card');
const analysisWorkspaceCard = document.querySelector('#analysis-workspace-card');
const translationWorkspaceCard = document.querySelector('#translation-workspace-card');
const draftRecoveryBanner = document.querySelector('#draft-recovery-banner');
const draftRecoveryText = document.querySelector('#draft-recovery-text');
const draftRecoveryRestoreButton = document.querySelector('#draft-recovery-restore');
const draftRecoveryDiscardButton = document.querySelector('#draft-recovery-discard');
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
const { genderSelect: referencesGlossaryGenderSelect, indeclinableCheckbox: referencesGlossaryIndeclinableCheckbox, speechRegisterInput: referencesGlossarySpeechRegisterInput } = attachGlossaryExtraFields(referencesGlossaryNoteInput, 'references-glossary');
const referencesCancelGlossaryButton = document.querySelector('#references-cancel-glossary');
const referencesAddGlossaryButton = document.querySelector('#references-add-glossary');
const projectList = document.querySelector('.project-list');
const newProjectButton = document.querySelector('#new-project-button');
const settingsButton = document.querySelector('#settings-button');
const serverLogButton = document.querySelector('#server-log-button');
const serverLogDialog = document.querySelector('#server-log-dialog');
const closeServerLogDialogButton = document.querySelector('#close-server-log-dialog');
const refreshServerLogButton = document.querySelector('#refresh-server-log');
const serverLogOutput = document.querySelector('#server-log-output');
const serverLogError = document.querySelector('#server-log-error');
const serverLogFilterText = document.querySelector('#server-log-filter-text');
const serverLogFilterLevel = document.querySelector('#server-log-filter-level');
const serverLogFilterCount = document.querySelector('#server-log-filter-count');
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
const projectNarratorGenderSelect = document.querySelector('#project-narrator-gender-select');
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
const { genderSelect: projectGlossaryGenderSelect, indeclinableCheckbox: projectGlossaryIndeclinableCheckbox, speechRegisterInput: projectGlossarySpeechRegisterInput } = attachGlossaryExtraFields(projectGlossaryNoteInput, 'project-glossary');
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
const projectChatPanel = document.querySelector('#project-chat-panel');
const projectChatToggle = document.querySelector('#project-chat-toggle');
const projectChatToggleIcon = document.querySelector('#project-chat-toggle-icon');
const projectChatClearButton = document.querySelector('#project-chat-clear');
const projectChatBody = document.querySelector('#project-chat-body');
const projectChatMessagesContainer = document.querySelector('#project-chat-messages');
const projectChatStatus = document.querySelector('#project-chat-status');
const projectChatForm = document.querySelector('#project-chat-form');
const projectChatInput = document.querySelector('#project-chat-input');
const projectChatSendButton = document.querySelector('#project-chat-send');
const chaptersPerPage = 25;
const projectPositionStoragePrefix = 'translation-workbench:project-position:';
const paragraphDraftStoragePrefix = 'translation-workbench:paragraph-draft:';
const paragraphDraftDebounceTimers = new Map();
let pendingDraftRecovery = [];
let loadedChapters = [];
let selectedChapterIndex = null;
let currentChapterPage = 1;
let currentParagraphId = null;
let translationStates = new Map();
let pendingNavigation = null;
let newProjectDraft = null;
let currentProject = null;
let currentSearchScope = 'chapter';
let currentSearchMatchMode = 'partial';
let activeDeepLConnectionId = null;
let pendingQuotaRetry = null;
let searchDebounceTimer = null;
let searchRequestToken = 0;
let lastSearchQuery = '';
let lastSearchResults = [];
let lastSearchScope = 'chapter';
let preSearchPosition = null;
let searchNavResults = [];
let searchNavIndex = -1;
let editingProjectId = null;
let pendingUploadFile = null;
let currentBriefEntries = [];
let referencesDraft = null;
let integrationProviders = [];
let integrationConnections = [];
let credentialStorageAvailable = false;
let projectTranslationGlossaries = [];
let projectChatMessages = [];
let projectChatLoadToken = 0;
let projectChatSending = false;
let editingTranslationGlossaryId = null;
let translationGlossaryDraft = [];
let translationGlossaryCatalog = [];
let editingTranslationGlossaryDraftId = null;
let editingTranslationGlossaryDraftIsNew = false;
let editingTranslationGlossaryDraftSnapshot = null;
let paragraphHeightSyncFrame = null;

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
exportBilingualDocxButton.addEventListener('click', () => downloadProjectDocx('bilingual', exportBilingualDocxButton));
exportTranslationDocxButton.addEventListener('click', () => downloadProjectDocx('translation_only', exportTranslationDocxButton));
saveTranslationButton.addEventListener('click', saveCurrentTranslation);
undoTranslationButton.addEventListener('click', undoTranslation);
redoTranslationButton.addEventListener('click', redoTranslation);
draftRecoveryRestoreButton.addEventListener('click', () => {
    const state = translationStates.get(selectedChapterIndex);
    if (state) {
        pendingDraftRecovery.forEach((entry) => {
            if (state.draft[entry.index]) {
                state.draft[entry.index] = { ...state.draft[entry.index], translationText: entry.translationText };
            }
        });
        renderTranslationFields(state.draft);
    }
    pendingDraftRecovery = [];
    draftRecoveryBanner.hidden = true;
});
draftRecoveryDiscardButton.addEventListener('click', () => {
    pendingDraftRecovery.forEach((entry) => clearParagraphDraftFromStorage(entry.paragraphId));
    pendingDraftRecovery = [];
    draftRecoveryBanner.hidden = true;
});

let lastTranslationCaret = null;
let footnoteDialogContext = null;

document.addEventListener('selectionchange', () => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
        return;
    }
    const range = selection.getRangeAt(0);
    const container = range.startContainer.nodeType === Node.TEXT_NODE
        ? range.startContainer.parentElement
        : range.startContainer;
    const translationElement = container && container.closest ? container.closest('.translation-paragraph') : null;
    if (!translationElement) {
        return;
    }
    lastTranslationCaret = {
        element: translationElement,
        paragraphId: translationElement.dataset.paragraphId,
        chapterIndex: Number(translationElement.dataset.chapterIndex),
        paragraphIndex: Number(translationElement.dataset.paragraphIndex),
        offset: getPlainTextOffset(translationElement, range.startContainer, range.startOffset),
    };
});

addFootnoteButton.addEventListener('click', () => {
    if (!lastTranslationCaret || !lastTranslationCaret.paragraphId) {
        window.alert('Постав курсор у місце в перекладі, де потрібна зноска.');
        return;
    }
    footnoteDialogContext = { mode: 'create', ...lastTranslationCaret };
    footnoteTextInput.value = '';
    deleteFootnoteButton.hidden = true;
    footnoteDialog.hidden = false;
    footnoteTextInput.focus();
});

translationRows.addEventListener('click', (event) => {
    const marker = event.target.closest('.footnote-marker');
    if (!marker) {
        return;
    }
    event.preventDefault();
    const translationElement = marker.closest('.translation-paragraph');
    if (!translationElement) {
        return;
    }
    const chapterIndex = Number(translationElement.dataset.chapterIndex);
    const paragraphIndex = Number(translationElement.dataset.paragraphIndex);
    const footnoteId = marker.dataset.footnoteId;
    const paragraphElement = getParagraphElementByIndex(chapterIndex, paragraphIndex);
    const existing = (paragraphElement?.footnotes || []).find((footnote) => footnote.footnoteId === footnoteId);
    footnoteDialogContext = {
        mode: 'edit',
        footnoteId,
        paragraphId: translationElement.dataset.paragraphId,
        chapterIndex,
        paragraphIndex,
        markerElement: marker,
    };
    footnoteTextInput.value = existing?.noteText || '';
    deleteFootnoteButton.hidden = false;
    footnoteDialog.hidden = false;
    footnoteTextInput.focus();
});

closeFootnoteDialogButton.addEventListener('click', closeFootnoteDialog);

function closeFootnoteDialog() {
    footnoteDialog.hidden = true;
    footnoteDialogContext = null;
}

function insertFootnoteMarker(translationElement, offset, footnoteId) {
    selectEditableText(translationElement, offset, offset);
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
        return;
    }
    const range = selection.getRangeAt(0);
    const marker = document.createElement('sup');
    marker.className = 'footnote-marker';
    marker.contentEditable = 'false';
    marker.dataset.footnoteId = footnoteId;
    marker.textContent = '•';
    range.insertNode(marker);
    range.setStartAfter(marker);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    const row = translationElement.closest('.translation-row');
    const original = row ? row.querySelector('.original-paragraph') : null;
    if (original) {
        syncParagraphPairHeight(original, translationElement);
    }
}

saveFootnoteButton.addEventListener('click', async () => {
    if (!footnoteDialogContext) {
        return;
    }
    const noteText = footnoteTextInput.value.trim();
    if (!noteText) {
        window.alert('Введіть текст зноски.');
        return;
    }
    saveFootnoteButton.disabled = true;
    try {
        if (footnoteDialogContext.mode === 'create') {
            const footnote = await WorkbenchApi.createParagraphFootnote(footnoteDialogContext.paragraphId, { noteText });
            insertFootnoteMarker(footnoteDialogContext.element, footnoteDialogContext.offset, footnote.footnoteId);
            const paragraphElement = getParagraphElementByIndex(footnoteDialogContext.chapterIndex, footnoteDialogContext.paragraphIndex);
            if (paragraphElement) {
                if (!Array.isArray(paragraphElement.footnotes)) {
                    paragraphElement.footnotes = [];
                }
                paragraphElement.footnotes.push({ footnoteId: footnote.footnoteId, noteText: footnote.noteText, number: null });
            }
        } else {
            await WorkbenchApi.updateParagraphFootnote(footnoteDialogContext.paragraphId, footnoteDialogContext.footnoteId, { noteText });
            const paragraphElement = getParagraphElementByIndex(footnoteDialogContext.chapterIndex, footnoteDialogContext.paragraphIndex);
            const existing = paragraphElement?.footnotes?.find((footnote) => footnote.footnoteId === footnoteDialogContext.footnoteId);
            if (existing) {
                existing.noteText = noteText;
            }
        }
        const state = translationStates.get(footnoteDialogContext.chapterIndex);
        if (state) {
            updateDraftFromControls(state);
        }
        closeFootnoteDialog();
    } catch (error) {
        window.alert(error.message);
    } finally {
        saveFootnoteButton.disabled = false;
    }
});

deleteFootnoteButton.addEventListener('click', async () => {
    if (!footnoteDialogContext || footnoteDialogContext.mode !== 'edit') {
        return;
    }
    if (!window.confirm('Видалити зноску?')) {
        return;
    }
    deleteFootnoteButton.disabled = true;
    try {
        await WorkbenchApi.deleteParagraphFootnote(footnoteDialogContext.paragraphId, footnoteDialogContext.footnoteId);
        footnoteDialogContext.markerElement?.remove();
        const state = translationStates.get(footnoteDialogContext.chapterIndex);
        if (state) {
            updateDraftFromControls(state);
        }
        closeFootnoteDialog();
    } catch (error) {
        window.alert(error.message);
    } finally {
        deleteFootnoteButton.disabled = false;
    }
});
openSearchButton.addEventListener('click', openSearchPanel);
closeSearchDialogButton.addEventListener('click', closeSearchPanel);
searchInput.addEventListener('input', () => {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => { void runSearch(); }, 300);
});
searchScopeToggle.addEventListener('click', (event) => {
    const button = event.target.closest('.search-scope-button');
    if (button && !button.disabled) {
        setSearchScope(button.dataset.scope);
    }
});
searchMatchToggle.addEventListener('click', (event) => {
    const button = event.target.closest('.search-scope-button');
    if (button && !button.disabled) {
        setSearchMatchMode(button.dataset.matchMode);
    }
});
closeDeepLQuotaDialogButton.addEventListener('click', () => closeDeepLQuotaDialog());
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !searchDialog.hidden) {
        closeSearchPanel();
    }
    if (event.key === 'Escape' && !footnoteDialog.hidden) {
        closeFootnoteDialog();
    }
    if (event.key === 'Escape' && !deepLQuotaDialog.hidden) {
        closeDeepLQuotaDialog();
    }
});
searchNavPrevButton.addEventListener('click', () => {
    if (searchNavIndex > 0) {
        void navigateToSearchResult(searchNavResults[searchNavIndex - 1]);
    }
});
searchNavNextButton.addEventListener('click', () => {
    if (searchNavIndex < searchNavResults.length - 1) {
        void navigateToSearchResult(searchNavResults[searchNavIndex + 1]);
    }
});
searchNavReturnButton.addEventListener('click', () => { void returnToPreSearchPosition(); });
searchNavExitButton.addEventListener('click', exitSearchNavigation);
aiQaNavPrevButton.addEventListener('click', () => stepAiQaFilter(-1));
aiQaNavNextButton.addEventListener('click', () => stepAiQaFilter(1));
aiQaNavExitButton.addEventListener('click', exitAiQaFilter);

function openSearchPanel() {
    searchDialog.hidden = false;
    updateSearchScopeAvailability();
    searchInput.value = '';
    renderSearchPlaceholder('Введіть текст для пошуку.');
    searchInput.focus();
}

function closeSearchPanel() {
    searchDialog.hidden = true;
    clearTimeout(searchDebounceTimer);
}

function renderSearchPlaceholder(text) {
    const placeholder = document.createElement('p');
    placeholder.className = 'muted';
    placeholder.textContent = text;
    searchResultsContainer.replaceChildren(placeholder);
}

function updateSearchScopeAvailability() {
    const chapterButton = searchScopeToggle.querySelector('[data-scope="chapter"]');
    const projectButton = searchScopeToggle.querySelector('[data-scope="project"]');
    if (chapterButton) {
        chapterButton.disabled = selectedChapterIndex === null;
    }
    if (projectButton) {
        projectButton.disabled = !currentProject;
    }
    if (
        (currentSearchScope === 'chapter' && selectedChapterIndex === null)
        || (currentSearchScope === 'project' && !currentProject)
    ) {
        setSearchScope('all');
    } else {
        setSearchScope(currentSearchScope, { rerun: false });
    }
}

function setSearchScope(scope, { rerun = true } = {}) {
    currentSearchScope = scope;
    searchScopeToggle.querySelectorAll('.search-scope-button').forEach((button) => {
        button.classList.toggle('active', button.dataset.scope === scope);
    });
    if (rerun && searchInput.value.trim()) {
        void runSearch();
    }
}

function setSearchMatchMode(matchMode, { rerun = true } = {}) {
    currentSearchMatchMode = matchMode;
    searchMatchToggle.querySelectorAll('.search-scope-button').forEach((button) => {
        button.classList.toggle('active', button.dataset.matchMode === matchMode);
    });
    if (rerun && searchInput.value.trim()) {
        void runSearch();
    }
}

async function runSearch() {
    const query = searchInput.value.trim();
    if (!query) {
        renderSearchPlaceholder('Введіть текст для пошуку.');
        return;
    }
    const requestToken = ++searchRequestToken;
    renderSearchPlaceholder('Шукаю…');
    try {
        const params = { scope: currentSearchScope, matchMode: currentSearchMatchMode };
        if (currentSearchScope === 'chapter' && selectedChapterIndex !== null) {
            params.chapterId = loadedChapters[selectedChapterIndex]?.chapterId;
        }
        if (currentSearchScope === 'project' && currentProject) {
            params.projectId = currentProject.projectId;
        }
        const result = await WorkbenchApi.search(query, params);
        if (requestToken !== searchRequestToken) {
            return;
        }
        lastSearchQuery = query;
        lastSearchResults = result?.results || [];
        lastSearchScope = currentSearchScope;
        renderSearchResults(result);
    } catch (error) {
        if (requestToken !== searchRequestToken) {
            return;
        }
        renderSearchPlaceholder(error.message);
    }
}

function highlightSnippet(snippet) {
    const escaped = escapeRichText(String(snippet ?? ''));
    return escaped.replaceAll('⟦', '<mark>').replaceAll('⟧', '</mark>');
}

function renderSearchResults(result) {
    const results = result?.results || [];
    if (results.length === 0) {
        renderSearchPlaceholder('Нічого не знайдено.');
        return;
    }
    searchResultsContainer.replaceChildren();
    results.forEach((item) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'search-result-item';

        const meta = document.createElement('div');
        meta.className = 'search-result-meta';
        meta.textContent = `${item.projectTitle} · ${String(item.chapterIndex + 1).padStart(2, '0')} · ${item.chapterTitle} · ${item.positionPercent}%`;

        const snippet = document.createElement('div');
        snippet.className = 'search-result-snippet';
        snippet.innerHTML = highlightSnippet(item.snippet);

        button.append(meta, snippet);
        button.addEventListener('click', () => { void navigateToSearchResult(item); });
        searchResultsContainer.append(button);
    });
}

async function navigateToSearchResult(result) {
    const isFirstJump = !preSearchPosition;
    if (isFirstJump) {
        preSearchPosition = {
            projectId: currentProject?.projectId ?? null,
            chapterIndex: selectedChapterIndex,
            paragraphId: currentParagraphId,
        };
    }
    const isDifferentProject = !currentProject || currentProject.projectId !== result.projectId;
    if (isDifferentProject) {
        try {
            const projectPromise = loadProjectDetail(result.projectId);
            const structurePromise = WorkbenchApi.getProjectBookStructure(result.projectId);
            const project = await projectPromise;
            showProjectWorkspace(project, structurePromise);
            const structure = await structurePromise;
            renderFileDetails(structure);
        } catch (error) {
            window.alert(error.message);
            return;
        }
    }
    const chapterIndex = loadedChapters.findIndex((chapter) => chapter.chapterId === result.chapterId);
    if (chapterIndex === -1) {
        return;
    }
    if (selectedChapterIndex !== chapterIndex) {
        selectChapter(chapterIndex);
    }
    showTranslationMode();
    searchNavResults = lastSearchResults;
    searchNavIndex = searchNavResults.indexOf(result);
    showSearchNavBar();
    closeSearchPanel();
    highlightSearchResultParagraph(result);
}

function highlightQueryInElement(element, query) {
    if (!element || !query) {
        return null;
    }
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    let fullText = '';
    let node;
    while ((node = walker.nextNode())) {
        textNodes.push({ node, start: fullText.length });
        fullText += node.nodeValue;
    }
    const matchIndex = fullText.toLocaleLowerCase().indexOf(query.toLocaleLowerCase());
    if (matchIndex === -1) {
        return null;
    }
    const matchEnd = matchIndex + query.length;
    let startPoint = null;
    let endPoint = null;
    for (const { node: textNode, start } of textNodes) {
        const end = start + textNode.nodeValue.length;
        if (!startPoint && matchIndex < end) {
            startPoint = [textNode, Math.max(0, matchIndex - start)];
        }
        if (endPoint === null && matchEnd <= end) {
            endPoint = [textNode, matchEnd - start];
            break;
        }
    }
    if (!startPoint || !endPoint) {
        return null;
    }
    try {
        const range = document.createRange();
        range.setStart(...startPoint);
        range.setEnd(...endPoint);
        const mark = document.createElement('mark');
        mark.className = 'search-word-highlight';
        range.surroundContents(mark);
        return mark;
    } catch (error) {
        return null;
    }
}

function clearSearchWordHighlight() {
    document.querySelectorAll('.search-word-highlight').forEach((mark) => {
        const parent = mark.parentNode;
        if (!parent) {
            return;
        }
        while (mark.firstChild) {
            parent.insertBefore(mark.firstChild, mark);
        }
        parent.removeChild(mark);
        parent.normalize();
    });
}

function highlightSearchResultParagraph(result) {
    clearSearchWordHighlight();
    const row = translationRows.querySelector(`.translation-row[data-paragraph-id="${CSS.escape(result.paragraphId)}"]`);
    if (!row) {
        return;
    }
    const targetSelector = result.field === 'translation_text' ? '.translation-paragraph' : '.original-paragraph';
    const target = row.querySelector(targetSelector);
    const mark = target ? highlightQueryInElement(target, lastSearchQuery) : null;
    (mark || row).scrollIntoView({ behavior: 'smooth', block: 'center' });
    if (!mark) {
        row.classList.add('search-result-highlight');
        setTimeout(() => row.classList.remove('search-result-highlight'), 6000);
    }
}

function showSearchNavBar() {
    searchNavBar.hidden = false;
    searchNavQueryLabel.textContent = lastSearchQuery;
    projectWorkspaceView.classList.add('search-nav-active');
    updateSearchNavBar();
}

function hideSearchNavBar() {
    searchNavBar.hidden = true;
    projectWorkspaceView.classList.remove('search-nav-active');
}

function updateSearchNavBar() {
    const hasCycling = searchNavResults.length > 0;
    searchNavPrevButton.hidden = !hasCycling;
    searchNavNextButton.hidden = !hasCycling;
    if (hasCycling) {
        const current = searchNavResults[searchNavIndex];
        const chapterInfo = current ? ` · ${String(current.chapterIndex + 1).padStart(2, '0')} · ${current.chapterTitle} · ${current.positionPercent}%` : '';
        searchNavPositionLabel.textContent = `${searchNavIndex + 1} з ${searchNavResults.length}${chapterInfo}`;
    } else {
        searchNavPositionLabel.textContent = '';
    }
    searchNavPrevButton.disabled = !hasCycling || searchNavIndex <= 0;
    searchNavNextButton.disabled = !hasCycling || searchNavIndex >= searchNavResults.length - 1;
}

function exitSearchNavigation() {
    preSearchPosition = null;
    searchNavResults = [];
    searchNavIndex = -1;
    clearSearchWordHighlight();
    hideSearchNavBar();
}

async function returnToPreSearchPosition() {
    const target = preSearchPosition;
    exitSearchNavigation();
    if (!target) {
        return;
    }
    if (target.projectId && (!currentProject || currentProject.projectId !== target.projectId)) {
        try {
            const projectPromise = loadProjectDetail(target.projectId);
            const structurePromise = WorkbenchApi.getProjectBookStructure(target.projectId);
            const project = await projectPromise;
            showProjectWorkspace(project, structurePromise);
            const structure = await structurePromise;
            renderFileDetails(structure);
        } catch (error) {
            window.alert(error.message);
            return;
        }
    }
    if (target.chapterIndex !== null && target.chapterIndex !== undefined) {
        selectChapter(target.chapterIndex);
    }
    if (target.paragraphId) {
        const row = translationRows.querySelector(`.translation-row[data-paragraph-id="${CSS.escape(target.paragraphId)}"]`);
        row?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}
bookInfoModeButton.addEventListener('click', showBookInfoMode);
analysisModeButton.addEventListener('click', showAnalysisMode);
translationModeButton.addEventListener('click', showTranslationMode);
projectSubmodeButtons.forEach((button) => {
    button.addEventListener('click', () => {
        showTranslationSubmode(button.textContent.trim());
    });
});
translateChapterButton.addEventListener('click', translateCurrentChapter);

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
checkGenderAgreementButton.insertAdjacentElement('afterend', genderAgreementStatus);

const aiQaConnections = document.createElement('div');
aiQaConnections.className = 'ai-qa-connections';
aiQaConnections.id = 'ai-qa-connections';
translationQaContent.append(aiQaConnections);

const AI_QA_PROVIDER_LABELS = { claude: 'Claude', gemini: 'Gemini', openai: 'GPT', grok: 'Grok' };
const AI_QA_CATEGORY_OPTIONS = [
    { value: 'critical', label: 'Критично' },
    { value: 'stylistic', label: 'Стилістично' },
    { value: 'typo', label: 'Одруківка' },
];

const aiQaCategories = document.createElement('div');
aiQaCategories.className = 'ai-qa-categories';
aiQaCategories.id = 'ai-qa-categories';
AI_QA_CATEGORY_OPTIONS.forEach(({ value, label }) => {
    const optionLabel = document.createElement('label');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = value;
    checkbox.checked = true;
    optionLabel.append(checkbox, document.createTextNode(` ${label}`));
    aiQaCategories.append(optionLabel);
});
aiQaConnections.insertAdjacentElement('afterend', aiQaCategories);

function getSelectedAiQaCategories() {
    return [...aiQaCategories.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
}

const checkAiQaButton = document.createElement('button');
checkAiQaButton.type = 'button';
checkAiQaButton.className = 'secondary-btn';
checkAiQaButton.id = 'check-ai-qa-button';
checkAiQaButton.textContent = 'AI QA (сенс/стиль)';
aiQaConnections.insertAdjacentElement('afterend', checkAiQaButton);
checkAiQaButton.addEventListener('click', () => checkCurrentChapterAiQa());

const aiQaStatus = document.createElement('span');
aiQaStatus.className = 'ai-qa-status';
aiQaStatus.id = 'ai-qa-status';
checkAiQaButton.insertAdjacentElement('afterend', aiQaStatus);

const clearAiQaButton = document.createElement('button');
clearAiQaButton.type = 'button';
clearAiQaButton.className = 'text-btn';
clearAiQaButton.id = 'clear-ai-qa-button';
clearAiQaButton.textContent = 'Скинути AI QA';
aiQaStatus.insertAdjacentElement('afterend', clearAiQaButton);
clearAiQaButton.addEventListener('click', clearAiQaIssues);

const aiQaCounters = document.createElement('div');
aiQaCounters.className = 'ai-qa-counters';
aiQaCounters.id = 'ai-qa-counters';
aiQaStatus.insertAdjacentElement('afterend', aiQaCounters);

const runSelectedQaButton = document.createElement('button');
runSelectedQaButton.type = 'button';
runSelectedQaButton.className = 'secondary-btn';
runSelectedQaButton.id = 'run-selected-qa-button';
runSelectedQaButton.textContent = 'Прогнати вибрані';
aiQaCounters.insertAdjacentElement('afterend', runSelectedQaButton);
runSelectedQaButton.addEventListener('click', () => checkSelectedParagraphsAiQa());

const aiQaStepControls = document.createElement('div');
aiQaStepControls.className = 'ai-qa-step-controls';
aiQaStepControls.id = 'ai-qa-step-controls';
aiQaStepControls.hidden = true;
runSelectedQaButton.insertAdjacentElement('afterend', aiQaStepControls);

const aiQaStepStatus = document.createElement('span');
aiQaStepStatus.className = 'ai-qa-step-status muted';
aiQaStepStatus.id = 'ai-qa-step-status';

const aiQaNextBatchButton = document.createElement('button');
aiQaNextBatchButton.type = 'button';
aiQaNextBatchButton.className = 'secondary-btn';
aiQaNextBatchButton.id = 'ai-qa-next-batch-button';
aiQaNextBatchButton.textContent = 'Наступний батч';
aiQaNextBatchButton.addEventListener('click', () => advanceAiQaBatch());

const aiQaRepeatBatchButton = document.createElement('button');
aiQaRepeatBatchButton.type = 'button';
aiQaRepeatBatchButton.className = 'secondary-btn';
aiQaRepeatBatchButton.id = 'ai-qa-repeat-batch-button';
aiQaRepeatBatchButton.textContent = 'Повторити батч';
aiQaRepeatBatchButton.addEventListener('click', () => { void runAiQaBatch(); });

const aiQaCancelBatchButton = document.createElement('button');
aiQaCancelBatchButton.type = 'button';
aiQaCancelBatchButton.className = 'text-btn';
aiQaCancelBatchButton.id = 'ai-qa-cancel-batch-button';
aiQaCancelBatchButton.textContent = 'Скасувати';
aiQaCancelBatchButton.addEventListener('click', () => exitAiQaActiveRun());

aiQaStepControls.append(aiQaStepStatus, aiQaNextBatchButton, aiQaRepeatBatchButton, aiQaCancelBatchButton);
translationQaContent.append(checkAiQaButton, aiQaConnections, aiQaCategories, aiQaStatus, aiQaCounters, runSelectedQaButton, aiQaStepControls, clearAiQaButton);
chapterExportCheckbox.addEventListener('change', toggleCurrentChapterExport);
chapterAIAnalysisToggle.addEventListener('click', () => toggleChapterAIAnalysis());
window.addEventListener('resize', scheduleParagraphHeightsSync);
if (chapterList) {
    chapterList.addEventListener('wheel', (event) => {
        if (event.deltaY !== 0) {
            chapterList.scrollLeft += event.deltaY;
            event.preventDefault();
        }
    }, { passive: false });
}
const chapterListSentinel = document.querySelector('#chapter-list-sentinel');
const chapterListPlaceholder = document.querySelector('#chapter-list-placeholder');

function syncStuckChapterListBounds() {
    if (!chapterBrowser) {
        return;
    }
    const rect = chapterBrowser.getBoundingClientRect();
    chapterList.style.left = `${rect.left}px`;
    chapterList.style.width = `${rect.width}px`;
}

function setChapterListStuck(stuck) {
    const isStuck = chapterList.classList.contains('chapters-strip--stuck');
    if (stuck === isStuck) {
        return;
    }
    if (stuck) {
        if (chapterListPlaceholder) {
            chapterListPlaceholder.style.height = `${chapterList.getBoundingClientRect().height}px`;
            chapterListPlaceholder.hidden = false;
            chapterListPlaceholder.classList.add('chapters-strip--stuck');
        }
        chapterList.classList.add('chapters-strip--stuck');
        syncStuckChapterListBounds();
    } else {
        chapterList.classList.remove('chapters-strip--stuck');
        chapterList.style.left = '';
        chapterList.style.width = '';
        if (chapterListPlaceholder) {
            chapterListPlaceholder.hidden = true;
            chapterListPlaceholder.classList.remove('chapters-strip--stuck');
        }
    }
}

if (chapterList && chapterListSentinel && 'IntersectionObserver' in window) {
    // The sentinel sits just above the chapter strip. Once it scrolls out of
    // view, the strip would normally scroll away under the quick-actions-bar —
    // that's the cue to pin it there instead, in its compact "stuck" appearance.
    //
    // This can't be plain `position: sticky`: the app-wide `overflow-x: hidden`
    // on html/body forces their overflow-y to compute to "auto" too (a CSS
    // overflow-spec side effect), which makes body — which never actually
    // scrolls itself, since real scrolling happens on the documentElement —
    // the "nearest scrolling ancestor" sticky resolves against, so it never
    // engages. A scroll-driven class + position: fixed sidesteps that.
    const chapterListStickyObserver = new IntersectionObserver(
        ([entry]) => setChapterListStuck(!entry.isIntersecting),
        // Shrinks the effective viewport by the quick-actions-bar's height (48px)
        // so "not intersecting" fires exactly when the strip should pin under
        // it, not only once the sentinel scrolls past the true viewport edge.
        { threshold: 0, rootMargin: '-48px 0px 0px 0px' },
    );
    chapterListStickyObserver.observe(chapterListSentinel);
    window.addEventListener('resize', () => {
        if (chapterList.classList.contains('chapters-strip--stuck')) {
            syncStuckChapterListBounds();
        }
    });
}
selectAllChapterAICategoriesButton.addEventListener('click', () => setChapterAICategories(true));
clearChapterAICategoriesButton.addEventListener('click', () => setChapterAICategories(false));
runChapterAIAnalysisButton.addEventListener('click', runChapterAIAnalysis);
saveTranslationRulesButton.addEventListener('click', saveTranslationRules);
addTranslationGlossaryButton.addEventListener('click', () => openTranslationGlossaryEditor());
translationGlossaryEditorToggle.addEventListener('click', () => toggleTranslationGlossaryEditor());
addTranslationGlossaryEntryButton.addEventListener('click', () => addTranslationGlossaryEntry());
openGlossaryCatalogDialogButton.addEventListener('click', openGlossaryCatalogDialog);
closeGlossaryCatalogDialogButton.addEventListener('click', closeGlossaryCatalogDialog);
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
settingsBackToMainButton.addEventListener('click', showMainScreen);
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
            exitSearchNavigation();
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
projectChatToggle.addEventListener('click', () => toggleProjectChatPanel());
projectChatClearButton.addEventListener('click', clearProjectChatHistory);
projectChatForm.addEventListener('submit', submitProjectChatMessage);
serverLogButton.addEventListener('click', openServerLogDialog);
closeServerLogDialogButton.addEventListener('click', closeServerLogDialog);
refreshServerLogButton.addEventListener('click', loadServerLog);
serverLogFilterText.addEventListener('input', applyServerLogFilters);
serverLogFilterLevel.addEventListener('change', applyServerLogFilters);

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
                reviewed: draft?.reviewed ?? Boolean(paragraph.reviewed),
                isService: draft?.isService ?? Boolean(paragraph.isService),
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

async function downloadProjectDocx(format, button) {
    if (!currentProject) return;
    button.disabled = true;
    try {
        const download = await WorkbenchApi.downloadProjectDocx(currentProject.projectId, format);
        downloadBlob(download.blob, download.filename);
    } catch (error) {
        window.alert(error.message);
    } finally {
        button.disabled = false;
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
    exportBilingualDocxButton.hidden = false;
    exportTranslationDocxButton.hidden = false;
    workspaceContent.replaceChildren();
    translationInformationContent.replaceChildren();
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
        translationInformationContent.append(details);
        workspaceContent.append(structureButton, chapterBrowser);
        const restoredPosition = renderChapters(data.chapters);
        chapterBrowser.hidden = !restoredPosition;
        structureButton.hidden = restoredPosition;
    } else {
        chapterBrowser.hidden = true;
        translationInformationContent.append(details);
    }
}

function normalizeBookStructure(data) {
    if (!Array.isArray(data?.chapters)) {
        return data;
    }

    return {
        ...data,
        chapters: data.chapters.map((chapter) => {
            const normalizedChapter = chapter && typeof chapter === 'object' ? chapter : {};
            const rawElements = Array.isArray(normalizedChapter.elements)
                ? normalizedChapter.elements
                : (Array.isArray(normalizedChapter.paragraphs) ? normalizedChapter.paragraphs.map((paragraph) => ({
                    type: 'paragraph',
                    ...(typeof paragraph === 'string' ? { originalText: paragraph } : (paragraph || {})),
                })) : []);
            return {
                ...normalizedChapter,
                elements: rawElements.map((rawElement) => {
                if (rawElement && rawElement.type === 'image') {
                    return rawElement;
                }
                const rawParagraph = rawElement || {};
                if (typeof rawParagraph !== 'string') {
                    return {
                        type: 'paragraph',
                        paragraphId: rawParagraph.paragraphId || null,
                        originalText: rawParagraph.originalText || '',
                        translationText: rawParagraph.translationText || null,
                        reviewed: Boolean(rawParagraph.reviewed),
                        isService: Boolean(rawParagraph.isService),
                        queuedForQa: Boolean(rawParagraph.queuedForQa),
                        narratorChange: rawParagraph.narratorChange || null,
                        footnotes: Array.isArray(rawParagraph.footnotes) ? rawParagraph.footnotes : [],
                    };
                }
                return {
                    type: 'paragraph',
                    paragraphId: null,
                    originalText: rawParagraph,
                    translationText: null,
                    reviewed: false,
                    isService: false,
                    narratorChange: null,
                    footnotes: [],
                };
                }),
            };
        }),
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

function getChapterReviewStatus(chapter, chapterIndex) {
    const paragraphs = (Array.isArray(chapter?.elements) ? chapter.elements : [])
        .filter((element) => element && element.type === 'paragraph');
    if (paragraphs.length === 0) {
        return 'none';
    }

    const state = translationStates.get(chapterIndex);
    let reviewedCount = 0;

    paragraphs.forEach((paragraph, paragraphIndex) => {
        const draft = state?.draft[paragraphIndex];
        const isReviewed = draft ? Boolean(draft.reviewed) : Boolean(paragraph.reviewed);
        if (isReviewed) {
            reviewedCount += 1;
        }
    });

    if (reviewedCount === paragraphs.length) {
        return 'all';
    }
    if (reviewedCount > 0) {
        return 'partial';
    }
    return 'none';
}

function updateChapterButtonReviewStates() {
    if (!chapterList) return;
    const buttons = chapterList.querySelectorAll('.chapter-button');
    buttons.forEach((button, chapterIndex) => {
        const chapter = loadedChapters[chapterIndex];
        if (!chapter) return;
        const status = getChapterReviewStatus(chapter, chapterIndex);
        button.classList.toggle('reviewed-all', status === 'all');
        button.classList.toggle('reviewed-partial', status === 'partial');
        button.classList.toggle('excluded-from-export', Boolean(chapter.excludeFromExport));
    });
}

const chapterQaRunCounts = new Map();

function formatChapterQaRunCounts(counts) {
    return ['claude', 'gemini', 'openai', 'grok']
        .filter((provider) => (counts?.[provider] || 0) > 0)
        .map((provider) => `${AI_QA_PROVIDER_LABELS[provider]} ${counts[provider]}×`)
        .join(' · ');
}

function updateChapterQaRunBadge(chapterId) {
    const chapterIndex = loadedChapters.findIndex((chapter) => chapter?.chapterId === chapterId);
    if (chapterIndex < 0 || !chapterList) {
        return;
    }
    const button = chapterList.querySelector(`.chapter-button[data-chapter-index="${chapterIndex}"]`);
    if (!button) {
        return;
    }
    let badge = button.querySelector('.chapter-qa-runs-badge');
    const text = formatChapterQaRunCounts(chapterQaRunCounts.get(chapterId));
    if (!text) {
        badge?.remove();
        return;
    }
    if (!badge) {
        badge = document.createElement('span');
        badge.className = 'chapter-qa-runs-badge';
        button.append(badge);
    }
    badge.textContent = text;
}

async function loadChapterQaRunCounts(chapterId) {
    try {
        const counts = await WorkbenchApi.listChapterQaRuns(chapterId);
        chapterQaRunCounts.set(chapterId, counts || {});
        updateChapterQaRunBadge(chapterId);
    } catch (error) {
        // The badge is supplemental; findings/progress should still render if this fails.
    }
}

function scrollActiveChapterIntoView() {
    if (!chapterList) {
        return;
    }
    const activeButton = chapterList.querySelector('.chapter-button.active');
    if (!activeButton) {
        return;
    }
    // Deferred a frame: this can run while the chapter strip's ancestor tab is
    // still hidden (e.g. right after opening a project, before the Переклад
    // tab is shown), and scrollIntoView is a no-op on a hidden element.
    requestAnimationFrame(() => {
        activeButton.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    });
}

function renderChapterPage() {
    chapterList.replaceChildren();
    if (chapterPagination) {
        chapterPagination.replaceChildren();
    }

    loadedChapters.forEach((chapter, chapterIndex) => {
        const chapterButton = document.createElement('button');
        chapterButton.type = 'button';
        chapterButton.className = 'chapter-button';
        const reviewStatus = getChapterReviewStatus(chapter, chapterIndex);
        if (reviewStatus === 'all') {
            chapterButton.classList.add('reviewed-all');
        } else if (reviewStatus === 'partial') {
            chapterButton.classList.add('reviewed-partial');
        }
        chapterButton.classList.toggle('excluded-from-export', Boolean(chapter.excludeFromExport));
        chapterButton.dataset.chapterIndex = String(chapterIndex);
        const chapterLabel = document.createElement('span');
        chapterLabel.className = 'chapter-button-label';
        chapterLabel.textContent = `${String(chapterIndex + 1).padStart(2, '0')} · ${chapter.title || `Chapter ${chapterIndex + 1}`}`;
        chapterButton.append(chapterLabel);
        const qaRunCountText = formatChapterQaRunCounts(chapterQaRunCounts.get(chapter.chapterId));
        if (qaRunCountText) {
            const qaRunBadge = document.createElement('span');
            qaRunBadge.className = 'chapter-qa-runs-badge';
            qaRunBadge.textContent = qaRunCountText;
            chapterButton.append(qaRunBadge);
        }
        if (chapterIndex === selectedChapterIndex) {
            chapterButton.classList.add('active');
        }
        chapterButton.addEventListener('click', () => {
            requestNavigation(() => selectChapter(chapterIndex));
        });
        chapterList.append(chapterButton);
    });
    scrollActiveChapterIntoView();
}

function clearChapterText() {
    chapterTitle.textContent = '';
    chapterNumber.textContent = '';
    chapterName.textContent = '';
    chapterWordCount.textContent = '';
    chapterParagraphCount.textContent = '';
    chapterExportCheckbox.checked = false;
    chapterExportCheckbox.disabled = true;
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
        renderAiQaConnections();
    } catch (error) {
        chapterAIAnalysisStatus.textContent = error.message;
    }
}

function renderAiQaConnections() {
    aiQaConnections.replaceChildren();
    const configuredIds = new Set(
        (currentProject?.aiConfiguration?.qaConnectionIds || [])
            .filter((connectionId) => typeof connectionId === 'string' && connectionId),
    );
    integrationConnections
        .filter((connection) => (
            configuredIds.has(connection.connectionId)
            && connection.enabled
            && (connection.statusCode === 'ok' || connection.status === 'connected')
            && Object.hasOwn(AI_QA_PROVIDER_LABELS, connection.providerId)
        ))
        .forEach((connection) => {
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = connection.connectionId;
            checkbox.checked = true;
            label.append(checkbox, document.createTextNode(`${AI_QA_PROVIDER_LABELS[connection.providerId]} (${connection.displayName})`));
            aiQaConnections.append(label);
        });
    const chapter = loadedChapters[selectedChapterIndex];
    checkAiQaButton.disabled = !chapter?.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
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
    integrationConnections
        .filter((connection) => (
            configuredIds.has(connection.connectionId)
            && connection.enabled
            && connection.statusCode === 'ok'
            && Object.hasOwn(AI_QA_PROVIDER_LABELS, connection.providerId)
        ))
        .forEach((connection) => {
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = connection.connectionId;
            checkbox.checked = true;
            label.append(checkbox, document.createTextNode(`${AI_QA_PROVIDER_LABELS[connection.providerId]} (${connection.displayName})`));
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
    Object.entries(results || {}).forEach(([resultKey, result]) => {
        const providerId = result?.providerId || resultKey;
        if (!selectedProviderIds.has(providerId) || !Object.hasOwn(AI_QA_PROVIDER_LABELS, providerId) || !result || typeof result !== 'object') {
            return;
        }
        const section = document.createElement('section');
        section.className = 'chapter-ai-analysis-result';
        section.dataset.providerId = providerId;
        const heading = document.createElement('h5');
        heading.textContent = AI_QA_PROVIDER_LABELS[providerId];
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
    exportBilingualDocxButton.hidden = true;
    exportTranslationDocxButton.hidden = true;
    renderProjectInformation(currentProject);
    mainScreenView.hidden = true;
    settingsView.hidden = true;
    projectWorkspaceView.hidden = false;
    backToProjectsButton.hidden = false;
    showBookInfoMode();
    void restoreProjectBook(project, structurePromise);
    void initProjectChat(currentProject.projectId);
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

function showTranslationSubmode(submode) {
    translationInformationContent.hidden = submode !== 'Інформація';
    translationRulesContent.hidden = submode !== 'Правила';
    translationStructuredRulesContent.hidden = submode !== 'Структуровані правила';
    translationGlossaryContent.hidden = submode !== 'Глосарій';
    translationGlossaryEditor.hidden = submode !== 'Глосарій';
    translationQaContent.hidden = submode !== 'QA AI';
    if (submode === 'QA AI') {
        if (integrationConnections.length === 0) {
            void loadChapterAIAnalysisConnections();
        } else {
            renderAiQaConnections();
        }
    }
    updateAiQaCountersStickyVisibility();
}

function toggleTranslationGlossaryEditor(expand = translationGlossaryEditorBody.hidden) {
    translationGlossaryEditorBody.hidden = !expand;
    translationGlossaryEditorToggle.setAttribute('aria-expanded', String(expand));
    translationGlossaryEditorToggleIcon.textContent = expand ? '▲' : '▼';
}

function toggleChapterAIAnalysis(expand = chapterAIAnalysisBody.hidden) {
    chapterAIAnalysisBody.hidden = !expand;
    chapterAIAnalysisToggle.setAttribute('aria-expanded', String(expand));
    chapterAIAnalysisToggleIcon.textContent = expand ? '▲' : '▼';
}

async function openTranslationGlossaryEditor(glossary = null) {
    showTranslationSubmode('Глосарій');
    editingTranslationGlossaryId = glossary?.glossaryRuleId || null;
    translationGlossarySourceLanguage.value = glossary?.sourceLanguage || 'EN';
    translationGlossaryTargetLanguage.value = glossary?.targetLanguage || 'UK';
    translationGlossaryStatus.textContent = '';
    translationGlossaryEditor.hidden = false;
    toggleTranslationGlossaryEditor(false);
    translationGlossaryEntries.replaceChildren();
    translationGlossaryDraft = [];
    editingTranslationGlossaryDraftId = null;
    editingTranslationGlossaryDraftIsNew = false;
    editingTranslationGlossaryDraftSnapshot = null;

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
                characterGender: entry.characterGender || '',
                speechRegister: entry.speechRegister || '',
                indeclinable: Boolean(entry.indeclinable),
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
    editingTranslationGlossaryDraftId = null;
    editingTranslationGlossaryDraftIsNew = false;
    editingTranslationGlossaryDraftSnapshot = null;
    translationGlossaryEntries.replaceChildren();
    translationGlossaryStatus.textContent = '';
    translationGlossaryEditor.hidden = true;
    closeGlossaryCatalogDialog();
}

const TRANSLATION_GLOSSARY_GENDER_LABELS = { femn: 'Жіночий', masc: 'Чоловічий', plur: 'На «ви» / небінарний' };

function renderTranslationGlossaryDraft() {
    translationGlossaryEntries.replaceChildren();
    translationGlossaryDraft.forEach((draftItem) => {
        const card = draftItem.draftId === editingTranslationGlossaryDraftId
            ? buildTranslationGlossaryCardForm(draftItem)
            : buildTranslationGlossaryCardView(draftItem);
        translationGlossaryEntries.append(card);
    });
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
}

// Groups the user has expanded in the currently-open catalog dialog. Reset
// each time the dialog opens fresh; "З цієї серії"/"Від цієї авторки" starts
// expanded, everything else (including "Без прив'язки") starts collapsed.
let glossaryCatalogExpandedGroupKeys = new Set();

function openGlossaryCatalogDialog() {
    glossaryCatalogExpandedGroupKeys = new Set(['__current__']);
    renderGlossaryCatalogGroups();
    glossaryCatalogDialog.hidden = false;
}

function closeGlossaryCatalogDialog() {
    glossaryCatalogDialog.hidden = true;
}

function renderGlossaryCatalogGroups() {
    glossaryCatalogGroupsContainer.replaceChildren();
    const selectedIds = new Set(
        translationGlossaryDraft
            .map((item) => item.glossaryEntryId)
            .filter(Boolean),
    );
    const available = translationGlossaryCatalog.filter((entry) => !selectedIds.has(entry.glossaryEntryId));
    const groups = groupGlossaryCatalogEntries(available);

    if (groups.length === 0) {
        const empty = document.createElement('p');
        empty.className = 'muted';
        empty.textContent = 'Усі терміни довідника вже додані до цього глосарію.';
        glossaryCatalogGroupsContainer.append(empty);
        return;
    }

    groups.forEach((group) => glossaryCatalogGroupsContainer.append(buildGlossaryCatalogGroup(group)));
}

function buildGlossaryCatalogGroup(group) {
    const expanded = glossaryCatalogExpandedGroupKeys.has(group.key);

    const wrapper = document.createElement('div');
    wrapper.className = 'glossary-catalog-group' + (group.key === '__current__' ? ' glossary-catalog-group-current' : '');

    const header = document.createElement('button');
    header.type = 'button';
    header.className = 'glossary-catalog-group-header';
    header.setAttribute('aria-expanded', String(expanded));

    const icon = document.createElement('span');
    icon.className = 'glossary-catalog-group-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = expanded ? '▾' : '▸';

    const label = document.createElement('span');
    label.className = 'glossary-catalog-group-label';
    label.textContent = group.label;

    const count = document.createElement('span');
    count.className = 'glossary-catalog-group-count';
    count.textContent = String(group.entries.length);

    header.append(icon, label, count);

    const body = document.createElement('div');
    body.className = 'glossary-catalog-group-body';
    body.hidden = !expanded;
    group.entries.forEach((entry) => body.append(buildGlossaryCatalogTermButton(entry)));

    header.addEventListener('click', () => {
        const willExpand = body.hidden;
        body.hidden = !willExpand;
        icon.textContent = willExpand ? '▾' : '▸';
        header.setAttribute('aria-expanded', String(willExpand));
        if (willExpand) {
            glossaryCatalogExpandedGroupKeys.add(group.key);
        } else {
            glossaryCatalogExpandedGroupKeys.delete(group.key);
        }
    });

    wrapper.append(header, body);
    return wrapper;
}

function buildGlossaryCatalogTermButton(entry) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'glossary-catalog-term';

    const label = document.createElement('span');
    label.className = 'glossary-catalog-term-label';
    label.textContent = `${formatGlossaryEntryLabel(entry)}${entry.note ? ` (${entry.note})` : ''}`;
    button.append(label);

    const provenance = formatGlossaryEntryProvenance(entry);
    if (provenance) {
        const provenanceLabel = document.createElement('span');
        provenanceLabel.className = 'glossary-catalog-term-provenance';
        provenanceLabel.textContent = provenance;
        button.append(provenanceLabel);
    }

    button.addEventListener('click', () => {
        addExistingTranslationGlossaryEntryToDraft(entry.glossaryEntryId);
        renderGlossaryCatalogGroups();
    });
    return button;
}

function addExistingTranslationGlossaryEntryToDraft(glossaryEntryId) {
    if (!glossaryEntryId) return;
    const entry = translationGlossaryCatalog.find((item) => item.glossaryEntryId === glossaryEntryId);
    if (!entry) return;
    translationGlossaryDraft.push({
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
}

async function syncGlossaryEntryFactsIfNeeded(catalogEntry, characterGender, indeclinable, speechRegister) {
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
        const characterGender = item.characterGender || null;
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
    projectSubmodeNavigation.hidden = true;
    bookInfoModeButton.classList.add('active');
    bookInfoModeButton.setAttribute('aria-current', 'page');
    translationModeButton.classList.remove('active');
    translationModeButton.removeAttribute('aria-current');
    analysisModeButton.classList.remove('active');
    analysisModeButton.removeAttribute('aria-current');
    updateAiQaCountersStickyVisibility();
}

function showAnalysisMode() {
    bookInfoWorkspace.hidden = true;
    projectInformationCard.hidden = true;
    projectFileCard.hidden = true;
    projectBriefCard.hidden = false;
    projectReferencesCard.hidden = false;
    analysisWorkspaceCard.hidden = false;
    translationWorkspaceCard.hidden = true;
    projectSubmodeNavigation.hidden = true;
    analysisModeButton.classList.add('active');
    analysisModeButton.setAttribute('aria-current', 'page');
    bookInfoModeButton.classList.remove('active');
    bookInfoModeButton.removeAttribute('aria-current');
    translationModeButton.classList.remove('active');
    translationModeButton.removeAttribute('aria-current');
    updateAiQaCountersStickyVisibility();
}

function showTranslationMode() {
    bookInfoWorkspace.hidden = true;
    projectInformationCard.hidden = true;
    projectFileCard.hidden = true;
    projectBriefCard.hidden = true;
    projectReferencesCard.hidden = true;
    analysisWorkspaceCard.hidden = true;
    translationWorkspaceCard.hidden = false;
    projectSubmodeNavigation.hidden = false;
    showTranslationSubmode('Інформація');
    translationModeButton.classList.add('active');
    translationModeButton.setAttribute('aria-current', 'page');
    bookInfoModeButton.classList.remove('active');
    bookInfoModeButton.removeAttribute('aria-current');
    analysisModeButton.classList.remove('active');
    analysisModeButton.removeAttribute('aria-current');
    scheduleParagraphHeightsSync();
    scrollActiveChapterIntoView();
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
    exitSearchNavigation();
    projectWorkspaceView.hidden = true;
    settingsView.hidden = true;
    mainScreenView.hidden = false;
    backToProjectsButton.hidden = true;
    closeBriefDialog();
    resetProjectChat();
}

function showSettingsView() {
    mainScreenView.hidden = true;
    projectWorkspaceView.hidden = true;
    settingsView.hidden = false;
    backToProjectsButton.hidden = false;
    renderAuthorCatalog();
    renderSeriesCatalog();
    resetProjectChat();
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
        const providerConnections = integrationConnections.filter((item) => item.providerId === provider.providerId);
        const rows = providerConnections.length > 0 ? providerConnections : [null];
        rows.forEach((connection) => {
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
        if (providerConnections.length > 0) {
            const addMore = createConnectionButton(
                `＋ Додати ще одне підключення ${provider.displayName}`,
                'configure',
                provider.providerId,
                undefined,
                !credentialStorageAvailable
            );
            addMore.className = 'text-btn add-connection-button';
            connectionsList.append(addMore);
        }
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

const DEEPL_USAGE_THRESHOLDS = [99, 95, 90, 80];

async function refreshDeepLUsageBadge() {
    if (!activeDeepLConnectionId) {
        deepLUsageBadge.hidden = true;
        return;
    }
    try {
        const connection = await WorkbenchApi.testConnection(activeDeepLConnectionId);
        const limit = connection.providerMetadata?.characterLimit;
        const count = connection.providerMetadata?.characterCount;
        if (!limit) {
            deepLUsageBadge.hidden = true;
            return;
        }
        const percent = Math.floor((count / limit) * 100);
        const threshold = DEEPL_USAGE_THRESHOLDS.find((value) => percent >= value);
        if (!threshold) {
            deepLUsageBadge.hidden = true;
            return;
        }
        deepLUsageBadge.hidden = false;
        deepLUsageBadge.textContent = `⚠️ DeepL «${connection.displayName}»: ${percent}% ліміту`;
        deepLUsageBadge.className = `deepl-usage-badge ${threshold >= 95 ? 'deepl-usage-badge-critical' : 'deepl-usage-badge-warning'}`;
    } catch {
        // Best-effort reminder — a failed usage check shouldn't interrupt translation.
    }
}

async function showDeepLQuotaDialog(error, retryFn) {
    pendingQuotaRetry = retryFn;
    try {
        integrationConnections = await WorkbenchApi.listConnections();
    } catch {
        // Fall back to whatever connections list is already cached.
    }
    const exhaustedConnectionId = error.connectionId;
    const alternatives = integrationConnections.filter((item) => (
        item.providerId === 'deepl'
        && item.connectionId !== exhaustedConnectionId
        && item.enabled
        && item.status === 'connected'
    ));
    deepLQuotaDialogMessage.textContent = error.message || 'DeepL вичерпав ліміт символів для цього підключення.';
    deepLQuotaConnectionList.replaceChildren();
    if (alternatives.length === 0) {
        const empty = document.createElement('p');
        empty.className = 'muted';
        empty.textContent = 'Немає інших активних підключень DeepL. Додайте нове в Налаштування → Connections.';
        deepLQuotaConnectionList.append(empty);
    } else {
        alternatives.forEach((connection) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'secondary-btn deepl-quota-connection-button';
            button.textContent = connection.displayName;
            button.addEventListener('click', () => {
                activeDeepLConnectionId = connection.connectionId;
                const retry = pendingQuotaRetry;
                closeDeepLQuotaDialog();
                if (retry) void retry();
            });
            deepLQuotaConnectionList.append(button);
        });
    }
    deepLQuotaDialog.hidden = false;
}

function closeDeepLQuotaDialog() {
    deepLQuotaDialog.hidden = true;
    pendingQuotaRetry = null;
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

let serverLogRefreshTimer = null;
let serverLogRawLines = [];

async function openServerLogDialog() {
    serverLogDialog.hidden = false;
    await loadServerLog();
    serverLogRefreshTimer = window.setInterval(loadServerLog, 5000);
}

function closeServerLogDialog() {
    serverLogDialog.hidden = true;
    if (serverLogRefreshTimer) {
        window.clearInterval(serverLogRefreshTimer);
        serverLogRefreshTimer = null;
    }
}

async function loadServerLog() {
    serverLogError.hidden = true;
    try {
        const { lines } = await WorkbenchApi.getServerLogs();
        serverLogRawLines = lines;
        applyServerLogFilters();
    } catch (error) {
        serverLogError.textContent = error.message;
        serverLogError.hidden = false;
    }
}

function applyServerLogFilters() {
    const keyword = serverLogFilterText.value.trim().toLowerCase();
    const level = serverLogFilterLevel.value;
    const filtered = serverLogRawLines.filter((line) => {
        if (level && !line.includes(`[${level}]`)) {
            return false;
        }
        if (keyword && !line.toLowerCase().includes(keyword)) {
            return false;
        }
        return true;
    });
    serverLogOutput.textContent = filtered.join('\n');
    serverLogOutput.scrollTop = serverLogOutput.scrollHeight;
    serverLogFilterCount.textContent = (keyword || level)
        ? `Показано ${filtered.length} з ${serverLogRawLines.length} рядків`
        : `${serverLogRawLines.length} рядків`;
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

function toggleProjectChatPanel(expand = projectChatBody.hidden) {
    projectChatBody.hidden = !expand;
    projectChatToggle.setAttribute('aria-expanded', String(expand));
    projectChatToggleIcon.textContent = expand ? '▼' : '▲';
    if (expand) {
        projectChatMessagesContainer.scrollTop = projectChatMessagesContainer.scrollHeight;
    }
}

function resetProjectChat() {
    projectChatLoadToken += 1;
    projectChatMessages = [];
    projectChatSending = false;
    projectChatStatus.textContent = '';
    projectChatInput.value = '';
    projectChatMessagesContainer.replaceChildren();
    toggleProjectChatPanel(false);
}

async function initProjectChat(projectId) {
    resetProjectChat();
    const loadToken = projectChatLoadToken;
    try {
        const { messages } = await WorkbenchApi.getProjectChatMessages(projectId);
        if (loadToken !== projectChatLoadToken) return;
        projectChatMessages = messages;
        renderProjectChatMessages();
    } catch (error) {
        if (loadToken !== projectChatLoadToken) return;
        projectChatStatus.textContent = error.message;
    }
}

const projectChatProviderNames = { claude: 'Claude', gemini: 'Gemini', openai: 'OpenAI', grok: 'Grok' };

async function clearProjectChatHistory() {
    if (!currentProject || projectChatSending) return;
    if (!window.confirm('Очистити всю історію чату?')) return;
    projectChatStatus.textContent = '';
    projectChatClearButton.disabled = true;
    try {
        await WorkbenchApi.clearProjectChatMessages(currentProject.projectId);
        projectChatMessages = [];
        renderProjectChatMessages();
    } catch (error) {
        projectChatStatus.textContent = error.message;
    } finally {
        projectChatClearButton.disabled = false;
    }
}

function renderProjectChatMessages(showTyping = false) {
    projectChatMessagesContainer.replaceChildren();
    if (projectChatMessages.length === 0 && !showTyping) {
        const empty = document.createElement('p');
        empty.className = 'muted';
        empty.textContent = 'Повідомлень поки немає.';
        projectChatMessagesContainer.append(empty);
    } else {
        projectChatMessages.forEach((message) => {
            const item = document.createElement('div');
            item.className = `project-chat-message project-chat-message-${message.role}`;
            const meta = document.createElement('div');
            meta.className = 'project-chat-message-meta';
            meta.textContent = message.role === 'assistant'
                ? projectChatProviderNames[message.providerId] || 'Асистент'
                : 'Ви';
            const text = document.createElement('p');
            text.textContent = message.content;
            item.append(meta, text);
            projectChatMessagesContainer.append(item);
        });
    }
    if (showTyping) {
        const typing = document.createElement('div');
        typing.className = 'project-chat-message project-chat-message-assistant project-chat-message-typing';
        typing.textContent = 'Асистент друкує…';
        projectChatMessagesContainer.append(typing);
    }
    projectChatMessagesContainer.scrollTop = projectChatMessagesContainer.scrollHeight;
}

async function submitProjectChatMessage(event) {
    event.preventDefault();
    if (!currentProject || projectChatSending) return;
    const text = projectChatInput.value.trim();
    if (!text) return;
    const providerId = projectChatForm.querySelector('input[name="project-chat-provider"]:checked')?.value;
    projectChatSending = true;
    projectChatSendButton.disabled = true;
    projectChatStatus.textContent = '';
    projectChatInput.value = '';
    projectChatMessages.push({ role: 'user', content: text, providerId: null, createdAt: new Date().toISOString() });
    renderProjectChatMessages(true);
    try {
        const response = await WorkbenchApi.sendProjectChatMessage(currentProject.projectId, { message: text, providerId });
        projectChatMessages[projectChatMessages.length - 1] = response.userMessage;
        projectChatMessages.push(response.assistantMessage);
        renderProjectChatMessages();
    } catch (error) {
        // The backend persists the user message before contacting the provider, so keep it visible on failure.
        renderProjectChatMessages();
        projectChatStatus.textContent = error.code === 'connection_required'
            ? 'Підключіть цього провайдера в розділі Connections.'
            : error.message;
    } finally {
        projectChatSending = false;
        projectChatSendButton.disabled = false;
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

const narratorGenderLabels = { femn: 'Жінка', masc: 'Чоловік', third: 'Третя особа' };

function renderProjectInformation(project) {
    if (!project) {
        return;
    }
    const author = mockAuthors.find((item) => item.authorId === project.authorId);
    const series = mockSeries.find((item) => item.seriesId === project.seriesId);
    const bookNumber = project.bookNumber ? `книга №${project.bookNumber}` : 'номер книги не вказано';
    projectPageTitle.textContent = project.title;
    projectPageSummary.textContent = `${author?.name || 'Авторку не вказано'} · ${series?.name || 'Серію не вказано'} · ${bookNumber}`;
    quickActionsProjectTitle.textContent = project.title;
    projectInformation.replaceChildren(
        createProjectMetadata('Назва', project.title),
        createProjectMetadata('Авторка', author ? author.name : 'Не вказано'),
        createProjectMetadata('Серія', series ? series.name : 'Не вказано'),
        createProjectMetadata('Номер книги', project.bookNumber || 'Не вказано'),
        createProjectMetadata('Статус', projectStatusLabels[project.status] || project.status),
        createProjectMetadata('Оповідач (за замовчуванням)', narratorGenderLabels[project.narratorGender]),
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
        text.textContent = formatGlossaryEntryLabel(entry);
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
        text.textContent = formatGlossaryEntryLabel(entry);
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
        const entry = await createGlossaryEntry(
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
        aiConfiguration: project?.aiConfiguration || {},
        // Tracks whether the user actually touched rules/glossary in this dialog session.
        // A save must only resend projectRuleIds/projectGlossaryEntryIds/inheritedRules/
        // inheritedGlossary when this is true — otherwise an edit to an unrelated field
        // (e.g. narratorGender) would resubmit these arrays anyway and, combined with any
        // staleness in how they got rebuilt on dialog open, risk wiping project_rules/
        // project_glossary rows that were never meant to be touched.
        referencesModified: false,
    };
    newProjectForm.reset();
    projectTitleInput.value = project?.title || '';
    projectBookNumberInput.value = project?.bookNumber || '';
    projectStatusSelect.value = project?.status || 'new';
    projectNarratorGenderSelect.value = project?.narratorGender || '';
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
        ['deepl', 'openai', 'gemini', 'claude', 'grok'].includes(connection.providerId)
        && (connection.status === 'connected' || selectedIds.has(connection.connectionId))
    ));
    const analysisConnections = connections.filter((connection) => (
        ['openai', 'gemini', 'claude', 'grok'].includes(connection.providerId)
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
        label.append(checkbox, document.createTextNode(`${AI_QA_PROVIDER_LABELS[connection.providerId] || connection.providerId} (${connection.displayName})`));
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
        newProjectDraft.referencesModified = true;
        inheritedContent.hidden = true;
    }
    renderSeriesSelect();
    renderNewSeriesAuthorSelect();
    updateCreateProjectButton();
}

async function handleSeriesSelection() {
    newProjectDraft.seriesId = projectSeriesSelect.value || null;
    const context = await ensureSeriesAuthorContext(newProjectDraft.seriesId, newProjectDraft.authorId);
    const isSameContext = newProjectDraft.inheritedContextSeriesId === newProjectDraft.seriesId
        && newProjectDraft.inheritedContextAuthorId === newProjectDraft.authorId;
    // Only rebuild the project's inherited rules/glossary when the series or author actually
    // changed. This function also runs on every dialog open (to populate the picker) even
    // when nothing changed — rebuilding there too would replace the project's real,
    // already-loaded inherited set with a fresh (possibly empty, e.g. on a first-time context
    // fetch) one, and that gets silently wiped from project_rules/project_glossary on save.
    if (!isSameContext) {
        newProjectDraft.inheritedRules = context
            ? context.ruleIds.map((ruleId) => ({ ruleId, confirmed: false, confirmedAt: null }))
            : [];
        newProjectDraft.inheritedGlossary = context
            ? context.glossaryEntryIds.map((glossaryEntryId) => ({ glossaryEntryId, confirmed: false, confirmedAt: null }))
            : [];
        newProjectDraft.inheritedContextSeriesId = context ? newProjectDraft.seriesId : null;
        newProjectDraft.inheritedContextAuthorId = context ? newProjectDraft.authorId : '';
        newProjectDraft.referencesModified = true;
    }
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
            newProjectDraft.referencesModified = true;
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
            newProjectDraft.referencesModified = true;
        });
        const text = document.createElement('span');
        text.textContent = formatGlossaryEntryLabel(entry);
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
                formatGlossaryEntryLabel(entry),
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

function formatGlossaryEntryLabel(entry) {
    let label = `${entry.source} → ${entry.target}`;
    const badges = [];
    if (entry.characterGender === 'femn') badges.push('ж');
    else if (entry.characterGender === 'masc') badges.push('ч');
    else if (entry.characterGender === 'plur') badges.push('на «ви»');
    if (entry.indeclinable) badges.push('незмінюване');
    if (badges.length > 0) {
        label += ` · ${badges.join(', ')}`;
    }
    return label;
}

function formatGlossaryEntryProvenance(entry) {
    const usedIn = entry.usedIn || [];
    if (usedIn.length === 0) {
        return '';
    }
    const labels = usedIn.map((context) => (
        context.seriesName ? `${context.seriesName} / ${context.projectTitle}` : context.projectTitle
    ));
    const unique = [...new Set(labels)];
    return unique.length > 2 ? `${unique.slice(0, 2).join(', ')} +${unique.length - 2}` : unique.join(', ');
}

// Groups catalog entries for the "Додати з довідника" picker: entries already
// linked (via project_glossary) to the current project's series/author come
// first in their own group, the rest are grouped by whichever series/author
// they're linked to elsewhere, and entries with no project link at all land
// in a trailing "Без прив'язки" group. There's no stored "origin" for a
// catalog entry — a term can legitimately belong to several projects — so
// this grouping is derived from live usedIn data on every render, not from
// a fixed ownership field.
function groupGlossaryCatalogEntries(entries) {
    const currentSeriesId = currentProject?.seriesId || null;
    const currentAuthorId = currentProject?.authorId || null;
    const currentGroupLabel = currentSeriesId ? 'З цієї серії' : (currentAuthorId ? 'Від цієї авторки' : null);

    const groups = new Map();
    entries.forEach((entry) => {
        const usedIn = entry.usedIn || [];
        const matchesCurrent = currentGroupLabel && usedIn.some((context) => (
            (currentSeriesId && context.seriesId === currentSeriesId)
            || (!currentSeriesId && currentAuthorId && context.authorId === currentAuthorId)
        ));
        let key;
        let label;
        if (matchesCurrent) {
            key = '__current__';
            label = currentGroupLabel;
        } else if (usedIn.length === 0) {
            key = '__orphan__';
            label = 'Без прив’язки';
        } else {
            const primary = usedIn[0];
            if (primary.seriesId) {
                key = `series:${primary.seriesId}`;
                label = primary.seriesName || 'Серія без назви';
            } else if (primary.authorId) {
                key = `author:${primary.authorId}`;
                label = primary.authorName || 'Авторка без імені';
            } else {
                key = '__orphan__';
                label = 'Без прив’язки';
            }
        }
        if (!groups.has(key)) {
            groups.set(key, { key, label, entries: [] });
        }
        groups.get(key).entries.push(entry);
    });

    return [...groups.values()]
        .sort((groupA, groupB) => {
            if (groupA.key === '__current__') return -1;
            if (groupB.key === '__current__') return 1;
            if (groupA.key === '__orphan__') return 1;
            if (groupB.key === '__orphan__') return -1;
            return groupA.label.localeCompare(groupB.label, 'uk');
        });
}

function populateGenderSelectOptions(select) {
    [
        ['', 'Рід: —'],
        ['femn', 'Жіночий'],
        ['masc', 'Чоловічий'],
        ['plur', 'На «ви» / небінарний'],
    ].forEach(([value, text]) => {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        select.append(option);
    });
}

function attachGlossaryExtraFields(noteInput, idPrefix) {
    const genderLabel = document.createElement('label');
    genderLabel.className = 'field-label';
    genderLabel.textContent = 'Рід персонажа (для перевірки узгодження)';
    const genderSelect = document.createElement('select');
    genderSelect.id = `${idPrefix}-character-gender`;
    populateGenderSelectOptions(genderSelect);
    genderLabel.append(genderSelect);

    const indeclinableLabel = document.createElement('label');
    indeclinableLabel.className = 'checkbox-item';
    const indeclinableCheckbox = document.createElement('input');
    indeclinableCheckbox.type = 'checkbox';
    indeclinableCheckbox.id = `${idPrefix}-indeclinable`;
    const indeclinableText = document.createElement('span');
    indeclinableText.textContent = 'Незмінюваний термін (не відмінюється)';
    indeclinableLabel.append(indeclinableCheckbox, indeclinableText);

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

async function createGlossaryEntry(source, target, note, characterGender, indeclinable, speechRegister) {
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
}

async function createProjectRule() {
    const text = projectRuleTextInput.value.trim();
    if (!text) {
        return;
    }
    const rule = await createRuleEntry(text, projectRuleCategoryInput.value.trim() || null);
    newProjectDraft.projectRuleIds.push(rule.ruleId);
    newProjectDraft.referencesModified = true;
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
        newProjectDraft.referencesModified = true;
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
    const entry = await createGlossaryEntry(
        source,
        target,
        projectGlossaryNoteInput.value.trim() || null,
        projectGlossaryGenderSelect.value || null,
        projectGlossaryIndeclinableCheckbox.checked,
        projectGlossarySpeechRegisterInput.value.trim() || null
    );
    newProjectDraft.projectGlossaryEntryIds.push(entry.glossaryEntryId);
    newProjectDraft.referencesModified = true;
    renderProjectGlossary();
    projectGlossarySourceInput.value = '';
    projectGlossaryTargetInput.value = '';
    projectGlossaryNoteInput.value = '';
    projectGlossaryGenderSelect.value = '';
    projectGlossaryIndeclinableCheckbox.checked = false;
    projectGlossarySpeechRegisterInput.value = '';
    toggleInlineForm(projectGlossaryForm, false);
}

async function editGlossaryEntry(entry) {
    const source = window.prompt('Оригінал:', entry.source)?.trim();
    const target = window.prompt('Переклад:', entry.target)?.trim();
    if (!source || !target) {
        return;
    }
    const note = window.prompt('Примітка:', entry.note || '')?.trim() || null;
    const genderInput = window.prompt('Рід персонажа (femn/masc/plur, порожньо — немає):', entry.characterGender || '')?.trim() || '';
    if (genderInput && !['femn', 'masc', 'plur'].includes(genderInput)) {
        window.alert('Рід має бути femn, masc, plur або порожнім. Зміни не збережено.');
        return;
    }
    const indeclinable = window.confirm('Це незмінюваний термін? OK — так, Скасувати — ні.');
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
        });
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
        newProjectDraft.referencesModified = true;
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
        narratorGender: projectNarratorGenderSelect.value || null,
        progress: {
            progress: 0,
            analysisProgress: 0,
            translationProgress: 0,
            auditProgress: 0
        },
        aiConfiguration: readProjectAIConfiguration(),
    };
    // Only resend projectRuleIds/projectGlossaryEntryIds/inheritedRules/inheritedGlossary when
    // this dialog session actually touched them (or this is a brand-new project). Editing an
    // unrelated field (title/status/narratorGender/AI connections) must never re-derive and
    // resubmit these arrays — the backend deletes+reinserts project_rules/project_glossary
    // whenever these keys are present, so any staleness here would be written straight to the
    // database even though the user never touched references at all.
    if (!editingProjectId || newProjectDraft.referencesModified) {
        projectData.inheritedRules = newProjectDraft.inheritedRules.map((reference) => ({ ...reference }));
        projectData.inheritedGlossary = newProjectDraft.inheritedGlossary.map((reference) => ({ ...reference }));
        projectData.projectRuleIds = [...newProjectDraft.projectRuleIds];
        projectData.projectGlossaryEntryIds = [...newProjectDraft.projectGlossaryEntryIds];
    }
    if (!editingProjectId) {
        projectData.chapterCount = 0;
        projectData.fileName = null;
        projectData.fileFormat = null;
        projectData.fileSize = null;
        projectData.analysisResult = null;
    }
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

const RICH_TEXT_TAGS = new Set(['b', 'i', 's', 'strong', 'em', 'del', 'strike']);
const RICH_TEXT_TAG_ALIASES = { strong: 'b', em: 'i', del: 's', strike: 's' };

// Footnote position marker embedded directly inside translation_text, mirrors
// backend FOOTNOTE_TOKEN_RE (storage.py): \uE000<footnoteId>\uE000.
const FOOTNOTE_TOKEN_PATTERN = /\uE000([0-9a-zA-Z_-]+)\uE000/g;

function renderFootnoteMarkers(html, footnotes) {
    const numberById = new Map((footnotes || []).map((footnote) => [footnote.footnoteId, footnote.number]));
    return (html || '').replace(FOOTNOTE_TOKEN_PATTERN, (match, footnoteId) => {
        const number = numberById.has(footnoteId) ? numberById.get(footnoteId) : '•';
        return `<sup class="footnote-marker" contenteditable="false" data-footnote-id="${footnoteId}">${number}</sup>`;
    });
}

function getParagraphElementByIndex(chapterIndex, paragraphIndex) {
    const chapter = loadedChapters[chapterIndex];
    if (!chapter) {
        return null;
    }
    const paragraphElements = chapter.elements.filter((element) => element.type === 'paragraph');
    return paragraphElements[paragraphIndex] || null;
}

function getPlainTextOffset(root, node, offset) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let total = 0;
    let current;
    while ((current = walker.nextNode())) {
        if (current === node) {
            return total + offset;
        }
        total += current.nodeValue.length;
    }
    return total;
}

function escapeRichText(text) {
    return text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

function sanitizeRichText(text) {
    const parsed = new DOMParser().parseFromString(text || '', 'text/html');

    function serialize(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return escapeRichText(node.nodeValue || '');
        }
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return '';
        }
        if (node.tagName === 'BR') {
            return '\n';
        }
        const content = Array.from(node.childNodes, serialize).join('');
        const tag = node.tagName.toLowerCase();
        if (!RICH_TEXT_TAGS.has(tag)) {
            return content;
        }
        const canonicalTag = RICH_TEXT_TAG_ALIASES[tag] || tag;
        return `<${canonicalTag}>${content}</${canonicalTag}>`;
    }

    return Array.from(parsed.body.childNodes, serialize).join('');
}

function serializeRichText(element) {
    function serialize(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node.nodeValue || '';
        }
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return '';
        }
        if (node.tagName === 'BR') {
            return '\n';
        }
        if (node.classList && node.classList.contains('footnote-marker')) {
            return `\uE000${node.dataset.footnoteId}\uE000`;
        }
        const content = Array.from(node.childNodes, serialize).join('');
        const tag = node.tagName.toLowerCase();
        if (!RICH_TEXT_TAGS.has(tag)) {
            return content;
        }
        const canonicalTag = RICH_TEXT_TAG_ALIASES[tag] || tag;
        return `<${canonicalTag}>${content}</${canonicalTag}>`;
    }

    return Array.from(element.childNodes, serialize).join('');
}

function selectEditableText(element, start, end) {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    let currentNode;
    let offset = 0;
    let startPoint;
    let endPoint;
    while ((currentNode = walker.nextNode())) {
        const nodeEnd = offset + currentNode.nodeValue.length;
        if (!startPoint && start <= nodeEnd) {
            startPoint = [currentNode, Math.max(0, start - offset)];
        }
        if (end <= nodeEnd) {
            endPoint = [currentNode, Math.max(0, end - offset)];
            break;
        }
        offset = nodeEnd;
    }
    if (!startPoint || !endPoint) {
        return;
    }
    const range = document.createRange();
    range.setStart(...startPoint);
    range.setEnd(...endPoint);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
}

function renderChapterText(chapter, chapterIndex) {
    const displayTitle = chapter.title || `Chapter ${chapterIndex}`;
    chapterTitle.textContent = `Вибраний розділ: ${displayTitle}`;
    chapterNumber.textContent = `Розділ ${chapterIndex} з ${loadedChapters.length}`;
    chapterName.textContent = `Назва: ${displayTitle}`;
    chapterWordCount.textContent = `Слів: ${formatNumber(chapter.wordCount)}`;
    chapterParagraphCount.textContent = `Абзаців: ${chapter.elements.filter((element) => element.type === 'paragraph').length}`;
    translateChapterButton.disabled = !chapter.chapterId;
    checkGenderAgreementButton.disabled = !chapter.chapterId;
    genderAgreementStatus.textContent = '';
    checkAiQaButton.disabled = !chapter.chapterId || aiQaConnections.querySelectorAll('input').length === 0;
    aiQaStatus.textContent = '';
    exitAiQaFilter();
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    if (chapter.chapterId && currentProject?.projectId) {
        void loadChapterAiQaFindings(chapter.chapterId);
        void loadChapterQaRunCounts(chapter.chapterId);
    }
    aiQaActiveRun = null;
    aiQaStepControls.hidden = true;
    aiQaStepStatus.textContent = '';
    aiQaNextBatchButton.hidden = false;
    setAiQaConnectionsDisabled(false);
    checkAiQaButton.hidden = false;
    updateAiQaResumeLabel();
    chapterExportCheckbox.checked = Boolean(chapter.excludeFromExport);
    chapterExportCheckbox.disabled = !chapter.chapterId;
    chapterExportCheckbox.setAttribute('aria-label', `Не експортувати: ${displayTitle}`);
    const state = getTranslationState(chapterIndex - 1, chapter);
    translationRows.replaceChildren();
    renderChapterTitleTranslation(chapter, state);
    renderChapterAIAnalysis(chapter);
    chapterText.hidden = false;

    let paragraphIndex = 0;
    const leftoverDrafts = [];
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
        if (paragraph.paragraphId) {
            const storedDraft = readParagraphDraftFromStorage(paragraph.paragraphId);
            if (storedDraft && storedDraft.translationText !== (paragraph.translationText || '')) {
                leftoverDrafts.push({
                    index: currentParagraphIndex,
                    paragraphId: paragraph.paragraphId,
                    translationText: storedDraft.translationText,
                    timestamp: storedDraft.timestamp,
                });
            } else if (storedDraft) {
                clearParagraphDraftFromStorage(paragraph.paragraphId);
            }
        }
        const row = document.createElement('div');
        row.className = 'translation-row';
        row.dataset.chapterIndex = String(chapterIndex - 1);
        row.dataset.paragraphIndex = String(paragraphIndex);
        row.dataset.paragraphId = paragraph.paragraphId || '';
        const original = document.createElement('div');
        original.className = 'original-paragraph';
        original.dataset.chapterIndex = String(chapterIndex - 1);
        original.dataset.paragraphIndex = String(paragraphIndex);
        original.innerHTML = sanitizeRichText(paragraph.originalText);
        const translation = document.createElement('div');
        translation.className = 'translation-paragraph';
        translation.contentEditable = 'true';
        translation.setAttribute('role', 'textbox');
        translation.setAttribute('aria-multiline', 'true');
        translation.dataset.chapterIndex = String(chapterIndex - 1);
        translation.dataset.paragraphIndex = String(paragraphIndex);
        translation.dataset.paragraphId = paragraph.paragraphId || '';
        translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(draft.translationText), paragraph.footnotes);
        translation.dataset.placeholder = 'Введіть переклад абзацу...';
        translation.addEventListener('focus', () => setCurrentParagraph(paragraph.paragraphId));
        translation.addEventListener('input', () => {
            updateDraftFromControls(state);
            syncParagraphPairHeight(original, translation);
            scheduleParagraphDraftPersist(paragraph.paragraphId, () => serializeRichText(translation));
        });
        const translationControl = document.createElement('div');
        translationControl.className = 'translation-control';
        translationControl.addEventListener('click', () => setCurrentParagraph(paragraph.paragraphId));
        const translateButton = document.createElement('button');
        translateButton.type = 'button';
        translateButton.className = 'secondary-btn translate-paragraph-button';
        translateButton.textContent = 'Перекласти DeepL';
        translateButton.disabled = !paragraph.paragraphId;
        const runTranslateParagraph = async () => {
            const previousText = translateButton.textContent;
            translateButton.disabled = true;
            translateButton.textContent = 'Перекладаємо…';
            try {
                const translated = await WorkbenchApi.translateParagraph(paragraph.paragraphId, activeDeepLConnectionId);
                activeDeepLConnectionId = translated.connectionId || activeDeepLConnectionId;
                void refreshDeepLUsageBadge();
                state.undo.push(cloneParagraphDrafts(state.draft));
                translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(translated.translationText || ''), paragraph.footnotes);
                scheduleParagraphHeightsSync();
                reviewCheckbox.checked = false;
                state.draft = readTranslationDraft();
                state.saved[currentParagraphIndex] = { ...state.draft[currentParagraphIndex] };
                clearParagraphDraftFromStorage(paragraph.paragraphId);
                state.redo = [];
                updateParagraphVisualStates(state.draft);
                updateTranslationButtons();
            } catch (error) {
                if (error.code === 'quota_exceeded') {
                    void showDeepLQuotaDialog(error, runTranslateParagraph);
                } else {
                    window.alert(error.message);
                }
            } finally {
                translateButton.disabled = false;
                translateButton.textContent = previousText;
            }
        };
        translateButton.addEventListener('click', () => { void runTranslateParagraph(); });
        translationControl.append(translation, translateButton);
        const review = document.createElement('label');
        review.className = 'paragraph-review';
        const reviewCheckbox = document.createElement('input');
        reviewCheckbox.type = 'checkbox';
        reviewCheckbox.dataset.paragraphId = paragraph.paragraphId || '';
        reviewCheckbox.checked = draft.reviewed;
        reviewCheckbox.addEventListener('focus', () => setCurrentParagraph(paragraph.paragraphId));
        reviewCheckbox.addEventListener('change', () => {
            updateDraftFromControls(state);
        });
        const reviewText = document.createElement('span');
        reviewText.textContent = 'Перевірено';
        review.append(reviewCheckbox, reviewText);
        const service = document.createElement('label');
        service.className = 'paragraph-review paragraph-service';
        const serviceCheckbox = document.createElement('input');
        serviceCheckbox.type = 'checkbox';
        serviceCheckbox.dataset.paragraphId = paragraph.paragraphId || '';
        serviceCheckbox.checked = draft.isService;
        serviceCheckbox.addEventListener('focus', () => setCurrentParagraph(paragraph.paragraphId));
        serviceCheckbox.addEventListener('change', async () => {
            const nextIsService = serviceCheckbox.checked;
            const previousIsService = !nextIsService;
            updateDraftFromControls(state);
            if (!paragraph.paragraphId) {
                return;
            }
            serviceCheckbox.disabled = true;
            try {
                const saved = await WorkbenchApi.updateParagraph(paragraph.paragraphId, {
                    translationText: state.draft[currentParagraphIndex].translationText || null,
                    reviewed: state.draft[currentParagraphIndex].reviewed,
                    isService: nextIsService,
                });
                state.draft[currentParagraphIndex].isService = Boolean(saved.isService);
                state.saved[currentParagraphIndex] = { ...state.draft[currentParagraphIndex] };
                clearParagraphDraftFromStorage(paragraph.paragraphId);
                paragraph.isService = Boolean(saved.isService);
                serviceCheckbox.checked = Boolean(saved.isService);
                updateTranslationButtons();
            } catch (error) {
                serviceCheckbox.checked = previousIsService;
                state.draft = readTranslationDraft();
                updateTranslationButtons();
                window.alert(`Не вдалося зберегти службовий статус: ${error.message}`);
            } finally {
                serviceCheckbox.disabled = false;
            }
        });
        const serviceText = document.createElement('span');
        serviceText.textContent = 'Службовий текст';
        service.append(serviceCheckbox, serviceText);
        const qaQueue = document.createElement('label');
        qaQueue.className = 'paragraph-review paragraph-qa-queue';
        const qaQueueCheckbox = document.createElement('input');
        qaQueueCheckbox.type = 'checkbox';
        qaQueueCheckbox.className = 'qa-queue-checkbox';
        qaQueueCheckbox.dataset.paragraphId = paragraph.paragraphId || '';
        qaQueueCheckbox.checked = Boolean(paragraph.queuedForQa);
        qaQueueCheckbox.disabled = !paragraph.paragraphId;
        qaQueueCheckbox.addEventListener('focus', () => setCurrentParagraph(paragraph.paragraphId));
        qaQueueCheckbox.addEventListener('change', async () => {
            const nextQueued = qaQueueCheckbox.checked;
            if (!paragraph.paragraphId) {
                return;
            }
            qaQueueCheckbox.disabled = true;
            try {
                const currentDraft = state.draft[currentParagraphIndex];
                const saved = await WorkbenchApi.updateParagraph(paragraph.paragraphId, {
                    translationText: currentDraft?.translationText || null,
                    reviewed: currentDraft?.reviewed ?? Boolean(paragraph.reviewed),
                    isService: currentDraft?.isService ?? Boolean(paragraph.isService),
                    queuedForQa: nextQueued,
                });
                paragraph.queuedForQa = Boolean(saved.queuedForQa);
                qaQueueCheckbox.checked = Boolean(saved.queuedForQa);
                clearParagraphDraftFromStorage(paragraph.paragraphId);
            } catch (error) {
                qaQueueCheckbox.checked = !nextQueued;
                window.alert(`Не вдалося зберегти позначку QA: ${error.message}`);
            } finally {
                qaQueueCheckbox.disabled = false;
            }
        });
        const qaQueueText = document.createElement('span');
        qaQueueText.textContent = 'У черзі на QA';
        qaQueue.append(qaQueueCheckbox, qaQueueText);
        const narratorChange = document.createElement('label');
        narratorChange.className = 'paragraph-review paragraph-narrator-change';
        const narratorChangeText = document.createElement('span');
        narratorChangeText.textContent = 'Оповідач з цього абзаца:';
        const narratorChangeSelect = document.createElement('select');
        narratorChangeSelect.className = 'narrator-change-select';
        narratorChangeSelect.dataset.paragraphId = paragraph.paragraphId || '';
        narratorChangeSelect.disabled = !paragraph.paragraphId;
        [
            ['', 'без позначки'],
            ['femn', 'жінка'],
            ['masc', 'чоловік'],
            ['third', 'третя особа'],
        ].forEach(([value, label]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            narratorChangeSelect.append(option);
        });
        narratorChangeSelect.value = paragraph.narratorChange || '';
        narratorChangeSelect.addEventListener('focus', () => setCurrentParagraph(paragraph.paragraphId));
        narratorChangeSelect.addEventListener('change', async () => {
            const nextValue = narratorChangeSelect.value || null;
            const previousValue = paragraph.narratorChange || '';
            if (!paragraph.paragraphId) {
                return;
            }
            narratorChangeSelect.disabled = true;
            try {
                const saved = await WorkbenchApi.updateParagraphNarratorChange(paragraph.paragraphId, nextValue);
                paragraph.narratorChange = saved.narratorChange || null;
                narratorChangeSelect.value = saved.narratorChange || '';
            } catch (error) {
                narratorChangeSelect.value = previousValue;
                window.alert(`Не вдалося зберегти позначку оповідача: ${error.message}`);
            } finally {
                narratorChangeSelect.disabled = false;
            }
        });
        narratorChange.append(narratorChangeText, narratorChangeSelect);
        const status = document.createElement('span');
        status.className = 'paragraph-status';
        const saveStatus = document.createElement('span');
        saveStatus.className = 'paragraph-save-status';
        saveStatus.hidden = true;
        const actions = document.createElement('div');
        actions.className = 'paragraph-actions';
        actions.append(translateButton, review, service, qaQueue, narratorChange);
        translationControl.append(translation, saveStatus, actions);
        row.addEventListener('click', () => setCurrentParagraph(paragraph.paragraphId));
        row.append(original, translationControl, status);
        translationRows.append(row);
        updateParagraphVisualState(row, draft);
        paragraphIndex += 1;
    });
    showDraftRecoveryBanner(leftoverDrafts);
    restoreCurrentParagraphRow();
    updateTranslationButtons();
    scheduleParagraphHeightsSync();
}

function showDraftRecoveryBanner(leftoverDrafts) {
    pendingDraftRecovery = leftoverDrafts;
    if (leftoverDrafts.length === 0) {
        draftRecoveryBanner.hidden = true;
        return;
    }
    const latestTimestamp = Math.max(...leftoverDrafts.map((entry) => entry.timestamp || 0));
    const when = latestTimestamp ? new Date(latestTimestamp).toLocaleString('uk-UA') : 'невідомого часу';
    draftRecoveryText.textContent = leftoverDrafts.length === 1
        ? `Знайдено незбережені зміни перекладу в одному абзаці від ${when}.`
        : `Знайдено незбережені зміни перекладу у ${leftoverDrafts.length} абзацах, останні — від ${when}.`;
    draftRecoveryBanner.hidden = false;
}

async function toggleCurrentChapterExport() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject) return;

    const previousValue = Boolean(chapter.excludeFromExport);
    const nextValue = chapterExportCheckbox.checked;
    chapterExportCheckbox.disabled = true;
    try {
        await WorkbenchApi.setChapterExportFlag(currentProject.projectId, chapter.chapterId, nextValue);
        chapter.excludeFromExport = nextValue;
        renderChapterPage();
    } catch (error) {
        chapterExportCheckbox.checked = previousValue;
        window.alert(error.message);
    } finally {
        chapterExportCheckbox.disabled = false;
    }
}

function syncParagraphPairHeight(original, translation) {
    original.style.height = 'auto';
    translation.style.height = 'auto';
    const height = `${Math.max(original.scrollHeight, translation.scrollHeight)}px`;
    original.style.height = height;
    translation.style.height = height;
}

function scheduleParagraphHeightsSync() {
    if (paragraphHeightSyncFrame !== null) {
        cancelAnimationFrame(paragraphHeightSyncFrame);
    }
    paragraphHeightSyncFrame = requestAnimationFrame(() => {
        paragraphHeightSyncFrame = null;
        translationRows.querySelectorAll('.translation-row').forEach((row) => {
            syncParagraphPairHeight(
                row.querySelector('.original-paragraph'),
                row.querySelector('.translation-paragraph')
            );
        });
    });
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
        isService: Boolean(paragraph.isService),
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
            redo: [],
            saving: false,
            saveError: false,
        });
    }
    return translationStates.get(chapterIndex);
}

function paragraphDraftStorageKey(paragraphId) {
    return `${paragraphDraftStoragePrefix}${currentProject?.projectId}:${paragraphId}`;
}

function saveParagraphDraftToStorage(paragraphId, translationText) {
    if (!currentProject?.projectId || !paragraphId) {
        return;
    }
    try {
        window.localStorage.setItem(paragraphDraftStorageKey(paragraphId), JSON.stringify({
            translationText,
            timestamp: Date.now(),
        }));
    } catch {
        // localStorage can be unavailable (private mode, quota) — buffering is best-effort only.
    }
}

function readParagraphDraftFromStorage(paragraphId) {
    if (!currentProject?.projectId || !paragraphId) {
        return null;
    }
    try {
        const raw = window.localStorage.getItem(paragraphDraftStorageKey(paragraphId));
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function clearParagraphDraftFromStorage(paragraphId) {
    if (!currentProject?.projectId || !paragraphId) {
        return;
    }
    try {
        window.localStorage.removeItem(paragraphDraftStorageKey(paragraphId));
    } catch {
        // ignore
    }
}

function scheduleParagraphDraftPersist(paragraphId, getText) {
    if (!paragraphId) {
        return;
    }
    if (paragraphDraftDebounceTimers.has(paragraphId)) {
        clearTimeout(paragraphDraftDebounceTimers.get(paragraphId));
    }
    const timer = setTimeout(() => {
        paragraphDraftDebounceTimers.delete(paragraphId);
        saveParagraphDraftToStorage(paragraphId, getText());
    }, 500);
    paragraphDraftDebounceTimers.set(paragraphId, timer);
}

function isParagraphUnsaved(paragraphId) {
    if (selectedChapterIndex === null || !paragraphId) {
        return false;
    }
    const state = translationStates.get(selectedChapterIndex);
    if (!state) {
        return false;
    }
    const index = state.draft.findIndex((draft) => draft.paragraphId === paragraphId);
    if (index === -1) {
        return false;
    }
    return state.saving || !paragraphDraftsEqual(state.draft[index], state.saved[index]);
}

function updateParagraphSaveIndicators(state) {
    if (!state) {
        translationRows.querySelectorAll('.paragraph-save-status').forEach((el) => { el.hidden = true; });
        return;
    }
    translationRows.querySelectorAll('.translation-row').forEach((row, index) => {
        const indicator = row.querySelector('.paragraph-save-status');
        if (!indicator) {
            return;
        }
        const draft = state.draft[index];
        const saved = state.saved[index];
        const dirty = Boolean(draft) && Boolean(saved) && !paragraphDraftsEqual(draft, saved);
        if (state.saving) {
            indicator.hidden = !dirty;
            indicator.textContent = 'Зберігається…';
            indicator.className = 'paragraph-save-status paragraph-save-status-saving';
        } else if (dirty && state.saveError) {
            indicator.hidden = false;
            indicator.textContent = 'Помилка збереження — натисніть «Зберегти» ще раз';
            indicator.className = 'paragraph-save-status paragraph-save-status-error';
        } else if (dirty) {
            indicator.hidden = false;
            indicator.textContent = 'Незбережені зміни';
            indicator.className = 'paragraph-save-status paragraph-save-status-dirty';
        } else {
            indicator.hidden = true;
            indicator.textContent = '';
            indicator.className = 'paragraph-save-status';
        }
    });
}

function readTranslationDraft() {
    return Array.from(translationRows.querySelectorAll('.translation-row'), (row) => ({
        paragraphId: row.dataset.paragraphId || null,
        translationText: serializeRichText(row.querySelector('.translation-paragraph')),
        reviewed: row.querySelector('.paragraph-review input').checked,
        isService: row.querySelector('.paragraph-service input').checked,
    }));
}

function paragraphDraftsEqual(left, right) {
    return left.paragraphId === right.paragraphId
        && left.translationText === right.translationText
        && left.reviewed === right.reviewed
        && left.isService === right.isService;
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
    updateChapterButtonReviewStates();
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
    state.saving = true;
    state.saveError = false;
    updateTranslationButtons();
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
                isService: draft.isService,
            });
        }));
        persistableIndexes.forEach((index) => {
            state.saved[index] = { ...state.draft[index] };
            clearParagraphDraftFromStorage(state.draft[index].paragraphId);
        });
        state.undo = [];
        state.redo = [];
        state.saving = false;
        updateParagraphVisualStates(state.draft);
        updateTranslationButtons();
        updateChapterButtonReviewStates();
        if (unpersistableIndexes.length > 0) {
            window.alert('Деякі абзаци не мають paragraphId і не були збережені.');
            return false;
        }
        return true;
    } catch (error) {
        state.saving = false;
        state.saveError = true;
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
        const result = await WorkbenchApi.translateChapter(currentProject.projectId, chapter.chapterId, activeDeepLConnectionId);
        activeDeepLConnectionId = result.connectionId || activeDeepLConnectionId;
        void refreshDeepLUsageBadge();
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
                isService: draft.isService,
            };
            state.saved[index] = { ...state.draft[index] };
        });
        renderTranslationFields(state.draft);
    } catch (error) {
        if (error.code === 'quota_exceeded') {
            void showDeepLQuotaDialog(error, translateCurrentChapter);
        } else {
            window.alert(error.message);
        }
    } finally {
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
                selectEditableText(textarea, issue.wordStart, issue.wordEnd);
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

const AI_QA_CATEGORY_LABELS = { critical: 'Критично', stylistic: 'Стилістично', typo: 'Одруківка' };
let aiQaFlatFindings = [];
let aiQaFilterCategory = null;
let aiQaFilterIndex = 0;
let aiQaActiveRun = null; // { connectionIds, batchIndex, totalBatches } | null

const AI_QA_PROGRESS_STORAGE_PREFIX = 'workbench:qaBatchProgress:';

function aiQaProgressKey(projectId, chapterId) {
    return `${AI_QA_PROGRESS_STORAGE_PREFIX}${projectId}:${chapterId}`;
}

function loadAiQaProgress(projectId, chapterId) {
    try {
        const raw = window.localStorage.getItem(aiQaProgressKey(projectId, chapterId));
        if (!raw) {
            return null;
        }
        const parsed = JSON.parse(raw);
        if (typeof parsed?.batchIndex === 'number' && Array.isArray(parsed?.connectionIds) && Array.isArray(parsed?.categories)) {
            return parsed;
        }
    } catch (error) {
        // Corrupt or outdated entry — treat as no saved progress.
    }
    return null;
}

function saveAiQaProgress(projectId, chapterId, batchIndex, connectionIds, categories) {
    try {
        window.localStorage.setItem(aiQaProgressKey(projectId, chapterId), JSON.stringify({ batchIndex, connectionIds, categories }));
    } catch (error) {
        // Best-effort only; a failed save just means no resume offer next time.
    }
}

function clearAiQaProgress(projectId, chapterId) {
    try {
        window.localStorage.removeItem(aiQaProgressKey(projectId, chapterId));
    } catch (error) {
        // ignore
    }
}

function sameConnectionSet(a, b) {
    if (a.length !== b.length) {
        return false;
    }
    const sortedA = [...a].sort();
    const sortedB = [...b].sort();
    return sortedA.every((value, index) => value === sortedB[index]);
}

function setAiQaConnectionsDisabled(disabled) {
    aiQaConnections.querySelectorAll('input').forEach((checkbox) => {
        checkbox.disabled = disabled;
    });
    aiQaCategories.querySelectorAll('input').forEach((checkbox) => {
        checkbox.disabled = disabled;
    });
}

function setAiQaStepButtonsDisabled(disabled) {
    aiQaNextBatchButton.disabled = disabled;
    aiQaRepeatBatchButton.disabled = disabled;
    aiQaCancelBatchButton.disabled = disabled;
}

function updateAiQaResumeLabel() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId) {
        checkAiQaButton.textContent = 'AI QA (сенс/стиль)';
        return;
    }
    const saved = loadAiQaProgress(currentProject.projectId, chapter.chapterId);
    checkAiQaButton.textContent = saved ? `Продовжити AI QA (з батчу ${saved.batchIndex + 1})` : 'AI QA (сенс/стиль)';
}

function exitAiQaActiveRun() {
    aiQaActiveRun = null;
    aiQaStepControls.hidden = true;
    aiQaStepStatus.textContent = '';
    aiQaNextBatchButton.hidden = false;
    setAiQaConnectionsDisabled(false);
    checkAiQaButton.hidden = false;
    updateAiQaResumeLabel();
}

async function runAiQaBatch() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId || !aiQaActiveRun) {
        return;
    }
    const { connectionIds, categories, batchIndex } = aiQaActiveRun;
    setAiQaStepButtonsDisabled(true);
    aiQaStepStatus.textContent = `Перевіряємо батч ${batchIndex + 1}…`;
    let hadError = false;
    let totalBatches = aiQaActiveRun.totalBatches;
    try {
        for (const connectionId of connectionIds) {
            const result = await WorkbenchApi.checkChapterTranslationQuality(
                currentProject.projectId,
                chapter.chapterId,
                [connectionId],
                batchIndex,
                { categories },
            );
            renderAiQaResults(result);
            totalBatches = result.totalBatches;
            if (Object.keys(result.errors || {}).length > 0) {
                hadError = true;
            }
        }
        aiQaActiveRun.totalBatches = totalBatches;
        saveAiQaProgress(currentProject.projectId, chapter.chapterId, batchIndex, connectionIds, categories);
        const isLastBatch = batchIndex + 1 >= totalBatches;
        aiQaStepStatus.textContent = hadError
            ? `Батч ${batchIndex + 1} з ${totalBatches} — з помилками (див. статус вище).`
            : `Батч ${batchIndex + 1} з ${totalBatches} перевірено.`;
        aiQaNextBatchButton.hidden = isLastBatch;
        if (isLastBatch) {
            clearAiQaProgress(currentProject.projectId, chapter.chapterId);
        }
    } catch (error) {
        aiQaStepStatus.textContent = `Помилка перевірки: ${error.message}`;
    } finally {
        setAiQaStepButtonsDisabled(false);
    }
}

async function advanceAiQaBatch() {
    if (!aiQaActiveRun) {
        return;
    }
    aiQaActiveRun.batchIndex += 1;
    await runAiQaBatch();
}

async function checkCurrentChapterAiQa() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId) {
        return;
    }
    const connectionIds = [...aiQaConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (connectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б одну QA-модель.';
        return;
    }
    const categories = getSelectedAiQaCategories();
    if (categories.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б один напрям перевірки.';
        return;
    }
    const saved = loadAiQaProgress(currentProject.projectId, chapter.chapterId);
    const resumable = saved
        && sameConnectionSet(saved.connectionIds, connectionIds)
        && sameConnectionSet(saved.categories, categories);
    const startBatchIndex = resumable ? saved.batchIndex : 0;
    aiQaActiveRun = { connectionIds, categories, batchIndex: startBatchIndex, totalBatches: startBatchIndex + 1 };
    aiQaStatus.textContent = '';
    setAiQaConnectionsDisabled(true);
    checkAiQaButton.hidden = true;
    aiQaStepControls.hidden = false;
    await runAiQaBatch();
}

async function checkSelectedParagraphsAiQa() {
    const chapter = loadedChapters[selectedChapterIndex];
    if (!chapter?.chapterId || !currentProject?.projectId) {
        return;
    }
    const paragraphIds = [...translationRows.querySelectorAll('.qa-queue-checkbox:checked')]
        .map((checkbox) => checkbox.dataset.paragraphId)
        .filter(Boolean);
    if (paragraphIds.length === 0) {
        aiQaStatus.textContent = 'Познач абзаци чекбоксом «У черзі на QA».';
        return;
    }
    const connectionIds = [...aiQaConnections.querySelectorAll('input:checked')].map((checkbox) => checkbox.value);
    if (connectionIds.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б одну QA-модель.';
        return;
    }
    const categories = getSelectedAiQaCategories();
    if (categories.length === 0) {
        aiQaStatus.textContent = 'Оберіть хоча б один напрям перевірки.';
        return;
    }
    const previousText = runSelectedQaButton.textContent;
    runSelectedQaButton.disabled = true;
    aiQaStatus.textContent = '';
    let hadErrors = false;
    try {
        for (const connectionId of connectionIds) {
            let batchIndex = 0;
            let totalBatches = 1;
            while (batchIndex < totalBatches) {
                const progress = totalBatches > 1 ? ` (${batchIndex + 1} з ${totalBatches})` : '';
                runSelectedQaButton.textContent = `Перевіряємо вибрані${progress}…`;
                const result = await WorkbenchApi.checkChapterTranslationQuality(
                    currentProject.projectId,
                    chapter.chapterId,
                    [connectionId],
                    batchIndex,
                    { paragraphIds, categories },
                );
                renderAiQaResults(result);
                if (Object.keys(result.errors || {}).length > 0) {
                    hadErrors = true;
                }
                totalBatches = result.totalBatches;
                batchIndex += 1;
            }
        }
        if (!hadErrors) {
            // Mirrors the backend auto-clearing queued_for_qa once every
            // requested connection has checked this set without error.
            translationRows.querySelectorAll('.qa-queue-checkbox').forEach((checkbox) => {
                if (paragraphIds.includes(checkbox.dataset.paragraphId)) {
                    checkbox.checked = false;
                }
            });
            chapter.elements.forEach((element) => {
                if (element.type === 'paragraph' && paragraphIds.includes(element.paragraphId)) {
                    element.queuedForQa = false;
                }
            });
        }
    } catch (error) {
        aiQaStatus.textContent = `Помилка перевірки вибраних: ${error.message}`;
    } finally {
        runSelectedQaButton.disabled = false;
        runSelectedQaButton.textContent = previousText;
    }
}

async function loadChapterAiQaFindings(chapterId) {
    try {
        const result = await WorkbenchApi.listChapterQaFindings(currentProject.projectId, chapterId);
        renderAiQaResults(result);
    } catch (error) {
        aiQaStatus.textContent = `Не вдалося завантажити AI QA: ${error.message}`;
    }
}

async function clearAiQaIssues() {
    exitAiQaFilter();
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaCounters.replaceChildren();
    aiQaFlatFindings = [];
    const chapter = loadedChapters[selectedChapterIndex];
    if (chapter?.chapterId && currentProject?.projectId) {
        clearAiQaProgress(currentProject.projectId, chapter.chapterId);
    }
    exitAiQaActiveRun();
    await clearAiQaQueueInCurrentChapter();
}

async function clearAiQaQueueInCurrentChapter() {
    const checkboxes = [...translationRows.querySelectorAll('.qa-queue-checkbox:checked')];
    if (checkboxes.length === 0) {
        return;
    }
    await Promise.all(checkboxes.map(async (checkbox) => {
        const paragraphId = checkbox.dataset.paragraphId;
        if (!paragraphId) {
            return;
        }
        const row = checkbox.closest('.translation-row');
        const translationText = row ? serializeRichText(row.querySelector('.translation-paragraph')) : null;
        const reviewed = row ? Boolean(row.querySelector('.paragraph-review input')?.checked) : false;
        const isService = row ? Boolean(row.querySelector('.paragraph-service input')?.checked) : false;
        checkbox.disabled = true;
        try {
            const saved = await WorkbenchApi.updateParagraph(paragraphId, {
                translationText,
                reviewed,
                isService,
                queuedForQa: false,
            });
            checkbox.checked = Boolean(saved.queuedForQa);
            const chapter = loadedChapters[selectedChapterIndex];
            const element = chapter?.elements.find((item) => item.type === 'paragraph' && item.paragraphId === paragraphId);
            if (element) {
                element.queuedForQa = Boolean(saved.queuedForQa);
            }
        } catch (error) {
            // Leave it checked — clearing the queue here is a convenience,
            // not something that should silently drop a paragraph the user
            // deliberately queued if the save fails.
        } finally {
            checkbox.disabled = false;
        }
    }));
}

function findOrCreateAiQaPanel(row) {
    let panel = row.querySelector('.ai-qa-issues');
    if (panel) {
        return panel;
    }
    panel = document.createElement('div');
    panel.className = 'ai-qa-issues';
    const translationControl = row.querySelector('.translation-control');
    if (translationControl) {
        translationControl.insertAdjacentElement('afterend', panel);
    } else {
        row.append(panel);
    }
    return panel;
}

function refreshAiQaCounters() {
    aiQaCounters.replaceChildren();
    aiQaCountersSticky.replaceChildren();
    const counts = { critical: 0, stylistic: 0, typo: 0 };
    aiQaFlatFindings.forEach((entry) => {
        if (Object.hasOwn(counts, entry.finding.category)) {
            counts[entry.finding.category] += 1;
        }
    });
    ['critical', 'stylistic', 'typo'].forEach((category) => {
        [aiQaCounters, aiQaCountersSticky].forEach((container) => {
            const badge = document.createElement('button');
            badge.type = 'button';
            badge.className = `ai-qa-counter ai-qa-counter-${category}`;
            badge.textContent = `${AI_QA_CATEGORY_LABELS[category]}: ${counts[category]}`;
            badge.disabled = !counts[category];
            badge.addEventListener('click', () => startAiQaFilter(category));
            container.append(badge);
        });
    });
    updateAiQaCountersStickyVisibility();
}

function updateAiQaCountersStickyVisibility() {
    const qaSubmodeActive = !translationWorkspaceCard.hidden && !translationQaContent.hidden;
    aiQaCountersSticky.hidden = !qaSubmodeActive || aiQaFlatFindings.length === 0;
}

function renderAiQaResults(result) {
    // The backend always returns the complete current pending set, so this
    // is a full replace, not a merge.
    if (result.chapterId) {
        void loadChapterQaRunCounts(result.chapterId);
    }
    exitAiQaFilter();
    translationRows.querySelectorAll('.ai-qa-issues').forEach((panel) => panel.remove());
    aiQaFlatFindings = [];

    const errorMessages = Object.values(result.errors || {});
    aiQaStatus.textContent = errorMessages.length > 0 ? errorMessages.join(' ') : '';

    const paragraphResults = result.paragraphResults || [];
    paragraphResults.forEach((paragraphResult) => {
        const row = translationRows.querySelector(`.translation-row[data-paragraph-id="${CSS.escape(paragraphResult.paragraphId)}"]`);
        if (!row) {
            return;
        }
        const panel = findOrCreateAiQaPanel(row);
        paragraphResult.findings.forEach((finding) => {
            const findingId = finding.findingId;
            finding.paragraphId = paragraphResult.paragraphId;

            const item = document.createElement('div');
            item.className = `ai-qa-finding ai-qa-finding-${finding.category}`;
            item.dataset.findingId = findingId;

            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'ai-qa-finding-chip';
            chip.textContent = `${AI_QA_CATEGORY_LABELS[finding.category] || finding.category} · «${finding.quote}» (${finding.sourceModel})`;

            const details = document.createElement('div');
            details.className = 'ai-qa-finding-details';
            details.hidden = true;
            const explanation = document.createElement('p');
            explanation.textContent = finding.explanation || '';
            details.append(explanation);
            if (finding.suggestion) {
                const suggestion = document.createElement('p');
                suggestion.className = 'ai-qa-finding-suggestion';
                suggestion.textContent = `Варіант: ${finding.suggestion}`;
                details.append(suggestion);
            }

            chip.addEventListener('click', () => {
                details.hidden = !details.hidden;
            });

            item.append(chip, details);
            panel.append(item);
            aiQaFlatFindings.push({ findingId, paragraphId: paragraphResult.paragraphId, finding, row });
        });
        if (panel.children.length === 0) {
            panel.remove();
        }
    });

    refreshAiQaCounters();
}

function startAiQaFilter(category) {
    const list = aiQaFlatFindings.filter((entry) => entry.finding.category === category);
    if (list.length === 0) {
        return;
    }
    aiQaFilterCategory = category;
    aiQaFilterIndex = 0;
    projectWorkspaceView.classList.add('ai-qa-nav-active');
    aiQaNavBar.hidden = false;
    showAiQaFilterItem();
}

function currentAiQaFilterList() {
    return aiQaFlatFindings.filter((entry) => entry.finding.category === aiQaFilterCategory);
}

function stepAiQaFilter(direction) {
    const list = currentAiQaFilterList();
    const nextIndex = aiQaFilterIndex + direction;
    if (nextIndex < 0 || nextIndex >= list.length) {
        return;
    }
    aiQaFilterIndex = nextIndex;
    showAiQaFilterItem();
}

function showAiQaFilterItem() {
    const list = currentAiQaFilterList();
    document.querySelectorAll('.ai-qa-finding-current').forEach((el) => el.classList.remove('ai-qa-finding-current'));
    if (list.length === 0) {
        exitAiQaFilter();
        return;
    }
    if (aiQaFilterIndex >= list.length) {
        aiQaFilterIndex = list.length - 1;
    }
    const entry = list[aiQaFilterIndex];
    const itemEl = translationRows.querySelector(`.ai-qa-finding[data-finding-id="${CSS.escape(entry.findingId)}"]`);
    if (itemEl) {
        itemEl.classList.add('ai-qa-finding-current');
    }
    entry.row.scrollIntoView({ behavior: 'smooth', block: 'center' });

    aiQaNavPositionLabel.textContent = `${aiQaFilterIndex + 1} з ${list.length}`;
    aiQaNavPrevButton.disabled = aiQaFilterIndex <= 0;
    aiQaNavNextButton.disabled = aiQaFilterIndex >= list.length - 1;

    aiQaNavContent.replaceChildren();

    const text = document.createElement('div');
    text.className = 'ai-qa-nav-text';
    const quote = document.createElement('span');
    quote.className = 'ai-qa-nav-quote';
    quote.textContent = `«${entry.finding.quote}»`;
    const explanation = document.createElement('span');
    explanation.className = 'ai-qa-nav-explanation';
    explanation.textContent = entry.finding.explanation || '';
    text.append(quote, explanation);
    if (entry.finding.suggestion) {
        const suggestion = document.createElement('span');
        suggestion.className = 'ai-qa-nav-suggestion';
        suggestion.textContent = `→ ${entry.finding.suggestion}`;
        text.append(suggestion);
    }
    aiQaNavContent.append(text);

    const actions = document.createElement('div');
    actions.className = 'ai-qa-nav-actions';
    const accept = document.createElement('button');
    accept.type = 'button';
    accept.className = 'icon-btn';
    accept.setAttribute('aria-label', 'Погодитись зі знахідкою');
    accept.textContent = '✔️';
    accept.addEventListener('click', () => void markAiQaFinding(entry));
    const dismiss = document.createElement('button');
    dismiss.type = 'button';
    dismiss.className = 'icon-btn';
    dismiss.setAttribute('aria-label', 'Відхилити знахідку');
    dismiss.textContent = '✖️';
    dismiss.addEventListener('click', () => void markAiQaFinding(entry));
    actions.append(accept, dismiss);
    aiQaNavContent.append(actions);
}

async function markAiQaFinding(entry) {
    if (isParagraphUnsaved(entry.paragraphId)) {
        const proceed = window.confirm(
            'У цьому абзаці є незбережені зміни перекладу (ще не підтверджені сервером). '
            + 'Закрити знахідку попри це? Виправлення, яке мало її закрити, може так і не зберегтися.'
        );
        if (!proceed) {
            return;
        }
    }
    const actionButtons = [...aiQaNavContent.querySelectorAll('.ai-qa-nav-actions button')];
    actionButtons.forEach((button) => { button.disabled = true; });
    try {
        await WorkbenchApi.resolveQaFinding(entry.findingId);
    } catch (error) {
        actionButtons.forEach((button) => { button.disabled = false; });
        aiQaStatus.textContent = `Не вдалося зберегти позначку: ${error.message}`;
        return;
    }
    aiQaStatus.textContent = '';
    aiQaFlatFindings = aiQaFlatFindings.filter((item) => item.findingId !== entry.findingId);
    const itemEl = translationRows.querySelector(`.ai-qa-finding[data-finding-id="${CSS.escape(entry.findingId)}"]`);
    if (itemEl) {
        const panel = itemEl.closest('.ai-qa-issues');
        itemEl.remove();
        if (panel && panel.children.length === 0) {
            panel.remove();
        }
    }
    refreshAiQaCounters();
    showAiQaFilterItem();
}

function exitAiQaFilter() {
    aiQaFilterCategory = null;
    aiQaFilterIndex = 0;
    aiQaNavBar.hidden = true;
    projectWorkspaceView.classList.remove('ai-qa-nav-active');
    document.querySelectorAll('.ai-qa-finding-current').forEach((el) => el.classList.remove('ai-qa-finding-current'));
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
        const chapterIndex = Number(row.dataset.chapterIndex);
        const paragraphElement = getParagraphElementByIndex(chapterIndex, index);
        translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(values[index].translationText), paragraphElement?.footnotes);
        row.querySelector('.paragraph-review input').checked = values[index].reviewed;
        updateParagraphVisualState(row, values[index]);
    });
    updateTranslationButtons();
    updateChapterButtonReviewStates();
    scheduleParagraphHeightsSync();
}

function updateTranslationButtons() {
    const state = translationStates.get(selectedChapterIndex);
    saveTranslationButton.disabled = !state || state.saving || !isTranslationDirty(selectedChapterIndex);
    undoTranslationButton.disabled = !state || state.undo.length === 0;
    redoTranslationButton.disabled = !state || state.redo.length === 0;
    updateParagraphSaveIndicators(state);
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
