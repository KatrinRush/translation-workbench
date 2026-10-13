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
const translationProviderToggle = document.querySelector('#translation-provider-toggle');
const translationProviderHint = document.querySelector('#translation-provider-hint');
const translationProviderHintText = document.querySelector('#translation-provider-hint-text');
const translationProviderOpenConnections = document.querySelector('#translation-provider-open-connections');
const translationEngineModel = document.querySelector('#translation-engine-model');
const translationSettingsButton = document.querySelector('#translation-settings-button');
const translationSettingsDialog = document.querySelector('#translation-settings-dialog');
const translationSettingsForm = document.querySelector('#translation-settings-form');
const translationEngineSections = document.querySelector('#translation-engine-sections');
const translationSettingsError = document.querySelector('#translation-settings-error');
const translationBatchChars = document.querySelector('#translation-batch-chars');
const translationBatchParagraphs = document.querySelector('#translation-batch-paragraphs');
const modelPricesTable = document.querySelector('#model-prices-table');
const translationRunSummary = document.querySelector('#translation-run-summary');
const projectCostDialog = document.querySelector('#project-cost-dialog');
const saveTranslationSettingsButton = document.querySelector('#save-translation-settings');
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
const projectTranslationModelInput = document.querySelector('#project-translation-model');
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
const activeDeepLConnectionStorageKey = 'translation-workbench:active-deepl-connection-id';

function readStoredActiveDeepLConnectionId() {
    try {
        return window.localStorage.getItem(activeDeepLConnectionStorageKey) || null;
    } catch {
        return null;
    }
}

function setActiveDeepLConnectionId(connectionId) {
    activeDeepLConnectionId = connectionId || null;
    try {
        if (activeDeepLConnectionId) {
            window.localStorage.setItem(activeDeepLConnectionStorageKey, activeDeepLConnectionId);
        } else {
            window.localStorage.removeItem(activeDeepLConnectionStorageKey);
        }
    } catch {
        // Best-effort persistence — a blocked/unavailable localStorage shouldn't break translation.
    }
}
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
let activeDeepLConnectionId = readStoredActiveDeepLConnectionId();
let pendingQuotaRetry = null;
let searchDebounceTimer = null;
let searchRequestToken = 0;
let lastSearchQuery = '';
let lastSearchResults = [];
let lastSearchScope = 'chapter';
let preSearchPosition = null;
let searchNavResults = [];
let searchNavIndex = -1;
let searchUserNavigated = false;
let searchCollapsed = readSearchCollapsed();
let searchResultsPending = false;
// «Усі рушії»: the editor plus two read-only panels (A, B) per paragraph; the choices are remembered in localStorage.
let compareMode = readCompareFlag('workbench.compareEngines.mode');
let compareDiffOn = readCompareFlag('workbench.compareEngines.diff');
let compareEngines = readCompareEngines();
let replaceModeOn = false;
let replaceMatches = [];
let replaceIndex = -1;
let replaceMeta = null;
let replaceFindToken = 0;
let replaceBusy = false;
let replacePending = null;
let editingProjectId = null;
let pendingUploadFile = null;
let currentBriefEntries = [];
let referencesDraft = null;
let integrationProviders = [];
let integrationConnections = [];
const TRANSLATION_PROVIDER_LABELS = { deepl: 'DeepL', claude: 'Claude', openai: 'GPT', gemini: 'Gemini' };
const LLM_TRANSLATION_ENGINES = ['claude', 'openai', 'gemini'];
// Default model per provider, read from /api/integration-providers (never hardcoded here).
let translationDefaultModels = {};
let translationConnectionsLoaded = false;
let translationProviderSaving = false;
// One-off notice (e.g. "no Claude connection to switch to"), cleared on the next switch.
let translationProviderMessage = '';

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
document.querySelector('#collapse-search-panel').addEventListener('click', () => setSearchCollapsed(true));
document.querySelector('#search-collapsed-tab').addEventListener('click', () => { setSearchCollapsed(false); searchInput.focus(); });
searchInput.addEventListener('input', () => {
    captureSearchStartPosition();
    clearTimeout(searchDebounceTimer);
    searchResultsPending = true;
    searchDebounceTimer = setTimeout(() => { searchResultsPending = false; void runSearch(); }, 300);
});
// Enter: next match, Shift+Enter: previous (a search still waiting for its debounce runs first).
searchInput.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' || event.isComposing) return;
    event.preventDefault();
    void (async () => {
        if (searchResultsPending) {
            clearTimeout(searchDebounceTimer);
            searchResultsPending = false;
            await runSearch();
        }
        stepSearch(event.shiftKey ? -1 : 1);
    })();
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
    if (event.key === 'Escape' && !projectCostDialog.hidden) {
        projectCostDialog.hidden = true;
        return;
    }
    if (event.key === 'Escape' && !enginePromptDialog.hidden) {
        closeEnginePrompt();
        return;
    }
    if (event.key === 'Escape' && !translationSettingsDialog.hidden) {
        closeTranslationSettingsDialog();
    }
    if (event.key === 'Escape' && !searchDialog.hidden && !searchEffectiveCollapsed()) {
        event.preventDefault(); // a type=search input would otherwise clear its text on Esc
        handleSearchEscape();
    }
    if (event.key === 'Escape' && !footnoteDialog.hidden) {
        closeFootnoteDialog();
    }
    if (event.key === 'Escape' && !deepLQuotaDialog.hidden) {
        closeDeepLQuotaDialog();
    }
});
document.querySelector('#search-prev').addEventListener('click', () => stepSearch(-1));
document.querySelector('#search-next').addEventListener('click', () => stepSearch(1));
document.querySelector('#search-return').addEventListener('click', () => { void returnToPreSearchPosition(); });
aiQaNavPrevButton.addEventListener('click', () => stepAiQaFilter(-1));
aiQaNavNextButton.addEventListener('click', () => stepAiQaFilter(1));
aiQaNavExitButton.addEventListener('click', exitAiQaFilter);

// --- The search panel: docked on the right (a bottom sheet on a tablet), the same panel for «Знайти й замінити» ---
// It stays open while you move through the matches. Its query and results are kept when it is closed, collapsed or
// hidden by the dictionary (only one docked panel at a time). Matches in the open chapter are painted with the CSS
// Custom Highlight API (soft for all, strong for the current one); the paragraph DOM is never changed.

function readSearchCollapsed() {
    try {
        return window.localStorage.getItem('workbench.searchPanelCollapsed') === '1';
    } catch (error) {
        return false;
    }
}

function searchSideLayout() {
    return window.matchMedia('(min-width: 1100px) and (pointer: fine)').matches;
}

// Collapsing is a computer feature: on a tablet the panel is a sheet and ✕ closes it.
function searchEffectiveCollapsed() {
    return searchCollapsed && searchSideLayout();
}

function applySearchPanelLayout() {
    const open = !searchDialog.hidden;
    const collapsed = open && searchEffectiveCollapsed();
    const changed = document.body.classList.contains('search-panel-open') !== (open && !collapsed)
        || document.body.classList.contains('search-panel-collapsed') !== collapsed;
    searchDialog.classList.toggle('search-collapsed', collapsed);
    document.querySelector('#search-collapsed-tab').hidden = !collapsed;
    document.body.classList.toggle('search-panel-open', open && !collapsed);
    document.body.classList.toggle('search-panel-collapsed', collapsed);
    if (changed) {
        scheduleParagraphHeightsSync(); // the columns got a new width
        syncPinnedRows();
    }
}

const SEARCH_COLLAPSED_KEY = 'workbench.searchPanelCollapsed';

function setSearchCollapsed(collapsed) {
    searchCollapsed = Boolean(collapsed);
    try {
        window.localStorage.setItem(SEARCH_COLLAPSED_KEY, searchCollapsed ? '1' : '0');
    } catch (error) {
        // the choice still applies to this page
    }
    applySearchPanelLayout();
    updateSearchStatus();
    window.setTimeout(refreshSearchHighlights, 60);
}

function openSearchPanel() {
    const wasHidden = searchDialog.hidden;
    parkDictionarySheet(); // one docked panel at a time: the dictionary keeps its last answer
    searchDialog.hidden = false;
    if (searchCollapsed) {
        searchCollapsed = false;
        try { window.localStorage.setItem(SEARCH_COLLAPSED_KEY, '0'); } catch (error) { /* private mode */ }
    }
    updateSearchScopeAvailability();
    applySearchPanelLayout();
    updateReplaceStatus();
    searchInput.focus();
    searchInput.select();
    if (wasHidden && searchInput.value.trim()) void runSearch({ keepIndex: true });
    else refreshSearchHighlights();
}

function closeSearchPanel() {
    searchDialog.hidden = true;
    clearTimeout(searchDebounceTimer);
    searchResultsPending = false;
    hideReplaceConfirm();
    clearSearchHighlights();
    applySearchPanelLayout();
}

// Esc: the confirmation and an open menu first (the menu closes itself), then the panel.
function handleSearchEscape() {
    if (openDropdown) return;
    if (!document.querySelector('#replace-confirm').hidden) {
        hideReplaceConfirm();
        return;
    }
    closeSearchPanel();
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

async function runSearch(options = {}) {
    if (replaceModeOn) {
        await runReplaceFind(options);
        return;
    }
    await runPlainSearch(options);
}

// «← Повернутися» goes back to where the search was started: the position is taken when a NEW search starts
// (the first edit of the query after a navigation), not at every click on a match.
function captureSearchStartPosition() {
    if (preSearchPosition && !searchUserNavigated) return;
    preSearchPosition = {
        projectId: currentProject?.projectId ?? null,
        chapterIndex: selectedChapterIndex,
        paragraphId: currentParagraphId,
    };
    searchUserNavigated = false;
}

async function runPlainSearch({ keepIndex = false } = {}) {
    const query = searchInput.value.trim();
    if (!query) {
        searchNavResults = [];
        searchNavIndex = -1;
        lastSearchResults = [];
        renderSearchPlaceholder('Введіть текст для пошуку.');
        updateSearchStatus();
        refreshSearchHighlights();
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
        const keptParagraph = keepIndex ? searchNavResults[searchNavIndex]?.paragraphId : null;
        lastSearchQuery = query;
        lastSearchResults = result?.results || [];
        lastSearchScope = currentSearchScope;
        searchNavResults = lastSearchResults;
        searchNavIndex = keptParagraph ? lastSearchResults.findIndex((item) => item.paragraphId === keptParagraph) : -1;
        renderSearchResults(result);
        updateSearchStatus();
        refreshSearchHighlights();
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

// The list of matches: a clickable snippet for each, with the chapter, the position in it and the highlighted match;
// grouped by chapter (with a count) when the scope is a project or every project.
function renderSearchResults(result) {
    const results = result?.results || [];
    if (results.length === 0) {
        renderSearchPlaceholder('Нічого не знайдено.');
        return;
    }
    const grouped = lastSearchScope !== 'chapter';
    const counts = new Map();
    results.forEach((item) => {
        const key = `${item.projectId}|${item.chapterId}`;
        counts.set(key, (counts.get(key) || 0) + 1);
    });
    const fragment = document.createDocumentFragment();
    let groupKey = null;
    results.forEach((item, index) => {
        const key = `${item.projectId}|${item.chapterId}`;
        if (grouped && key !== groupKey) {
            groupKey = key;
            const title = document.createElement('div');
            title.className = 'search-group-title';
            title.setAttribute('role', 'heading');
            title.setAttribute('aria-level', '4');
            const project = lastSearchScope === 'all' ? `${item.projectTitle} · ` : '';
            title.textContent = `${project}${String(item.chapterIndex + 1).padStart(2, '0')} · ${item.chapterTitle} — ${counts.get(key)}`;
            fragment.append(title);
        }
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'search-result-item';
        button.dataset.index = String(index);

        const meta = document.createElement('div');
        meta.className = 'search-result-meta';
        const project = lastSearchScope === 'all' ? `${item.projectTitle} · ` : '';
        meta.textContent = `${project}${String(item.chapterIndex + 1).padStart(2, '0')} · ${item.chapterTitle} · ${item.positionPercent}%`;

        const snippet = document.createElement('div');
        snippet.className = 'search-result-snippet';
        snippet.innerHTML = highlightSnippet(item.snippet);

        button.append(meta, snippet);
        button.addEventListener('click', () => { void navigateToSearchResult(item); });
        fragment.append(button);
    });
    searchResultsContainer.replaceChildren(fragment);
    markCurrentSearchItem(false);
}

function markCurrentSearchItem(scroll) {
    searchResultsContainer.querySelectorAll('.search-result-item').forEach((button) => {
        const current = Number(button.dataset.index) === searchNavIndex;
        button.classList.toggle('search-result-current', current);
        if (current) {
            button.setAttribute('aria-current', 'true');
            if (scroll) button.scrollIntoView({ block: 'nearest' });
        } else {
            button.removeAttribute('aria-current');
        }
    });
}

function stepSearch(delta) {
    if (!searchNavResults.length) return;
    let index = searchNavIndex;
    if (index < 0) index = delta > 0 ? 0 : searchNavResults.length - 1;
    else index += delta;
    const target = searchNavResults[index];
    if (target) void navigateToSearchResult(target);
}

async function navigateToSearchResult(result) {
    searchUserNavigated = true;
    if (!preSearchPosition) {
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
    if (replaceModeOn) replaceIndex = searchNavIndex;
    markCurrentSearchItem(true);
    updateSearchStatus();
    refreshSearchHighlights();
    showCurrentSearchMatch(result);
}

// --- highlights of the matches in the open chapter ---------------------------------------------------

const searchHl = { token: 0, byRow: new Map(), current: null, near: new Set(), observer: null, frame: null, timer: null };

function searchHighlightApi() {
    return typeof CSS !== 'undefined' && CSS.highlights && typeof Highlight === 'function' ? CSS.highlights : null;
}

function searchQueryField(query) {
    return /[Ѐ-ӿ]/.test(query) ? 'translation_text' : 'original_text';
}

function searchTextNodes(target) {
    const walker = document.createTreeWalker(target, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) => (node.parentElement?.closest('.footnote-marker') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
    });
    const nodes = [];
    let text = '';
    let node;
    while ((node = walker.nextNode())) {
        nodes.push({ node, start: text.length });
        text += node.nodeValue;
    }
    return { nodes, text };
}

function searchRangeFromOffsets(nodes, start, end) {
    let startPoint = null;
    let endPoint = null;
    for (const { node, start: nodeStart } of nodes) {
        const nodeEnd = nodeStart + node.nodeValue.length;
        if (!startPoint && start < nodeEnd) startPoint = [node, start - nodeStart];
        if (startPoint && end <= nodeEnd) {
            endPoint = [node, end - nodeStart];
            break;
        }
    }
    if (!startPoint || !endPoint) return null;
    const range = document.createRange();
    range.setStart(...startPoint);
    range.setEnd(...endPoint);
    return range;
}

// The matches of the plain query inside one element (case-insensitive; «exact» = whole words), as Ranges.
function plainSearchRanges(target) {
    const ranges = [];
    if (!lastSearchQuery) return ranges;
    const { nodes, text } = searchTextNodes(target);
    const haystack = text.toLowerCase();
    const needle = lastSearchQuery.toLowerCase();
    const word = /[\p{L}\p{N}_]/u;
    if (haystack.length !== text.length || !needle) return ranges;
    let from = 0;
    let index;
    while ((index = haystack.indexOf(needle, from)) >= 0) {
        const end = index + needle.length;
        const whole = currentSearchMatchMode !== 'exact'
            || (!(index > 0 && word.test(haystack[index - 1])) && !(end < haystack.length && word.test(haystack[end])));
        if (whole) {
            const range = searchRangeFromOffsets(nodes, index, end);
            if (range) ranges.push(range);
        }
        from = end;
    }
    return ranges;
}

// The ranges of one paragraph, cached for the open chapter. Plain search: found here in the text on screen with the
// rules of the server's search (a substring ignoring case, or whole words). Replace mode: the offsets of the server.
function searchRangesForRow(row) {
    if (searchHl.byRow.has(row)) return searchHl.byRow.get(row);
    let ranges = [];
    const paragraphId = row.dataset.paragraphId;
    if (replaceModeOn && replaceAvailable()) {
        const target = row.querySelector('.translation-paragraph');
        ranges = target ? replaceMatches.filter((match) => match.paragraphId === paragraphId)
            .map((match) => replaceRangeFor(target, match.visibleStart, match.visibleEnd, match.matchedText)) : [];
    } else if (lastSearchQuery) {
        const target = row.querySelector(searchQueryField(lastSearchQuery) === 'translation_text' ? '.translation-paragraph' : '.original-paragraph');
        if (target) ranges = plainSearchRanges(target);
    }
    searchHl.byRow.set(row, ranges);
    return ranges;
}

function clearCurrentSearchHighlight() {
    const api = searchHighlightApi();
    if (api) api.delete('search-current');
    searchHl.current = null;
    document.querySelectorAll('.search-result-highlight').forEach((row) => row.classList.remove('search-result-highlight'));
    scheduleSearchRects();
}

function clearSearchHighlights() {
    searchHl.token += 1;
    window.clearTimeout(searchHl.timer);
    const api = searchHighlightApi();
    if (api) {
        api.delete('search-all');
        api.delete('search-current');
    }
    searchHl.byRow = new Map();
    searchHl.current = null;
    searchHl.near.clear();
    searchHl.observer?.disconnect();
    searchHl.observer = null;
    document.querySelector('#search-highlight-layer')?.replaceChildren();
    document.querySelectorAll('.search-result-highlight').forEach((row) => row.classList.remove('search-result-highlight'));
}

// Paint all matches of the open chapter softly, in slices of work so a long chapter does not block the page.
function refreshSearchHighlights() {
    window.clearTimeout(searchHl.timer);
    const keep = searchHl.current;
    clearSearchHighlights();
    if (searchDialog.hidden || searchEffectiveCollapsed() || !lastSearchQuery || selectedChapterIndex === null) return;
    if (!searchInput.value.trim()) return;
    const rows = Array.from(translationRows.querySelectorAll('.translation-row'));
    const token = searchHl.token;
    const api = searchHighlightApi();
    const all = api ? new Highlight() : null;
    if (api) api.set('search-all', all);
    else observeSearchRows(rows);
    let index = 0;
    const slice = () => {
        if (token !== searchHl.token) return;
        const stop = Math.min(rows.length, index + 40);
        for (; index < stop; index += 1) {
            searchRangesForRow(rows[index]).forEach((range) => { if (range && all) all.add(range); });
            if (all) paintSearchInPanels(rows[index], all);
        }
        if (!api) scheduleSearchRects();
        if (index < rows.length) searchHl.timer = window.setTimeout(slice, 16);
    };
    slice();
    if (keep) showCurrentSearchMatch(keep.result, { scroll: false });
}

function showCurrentSearchMatch(result, { scroll = true } = {}) {
    clearCurrentSearchHighlight();
    const row = translationRows.querySelector(`.translation-row[data-paragraph-id="${CSS.escape(result.paragraphId)}"]`);
    if (!row) return;
    const ranges = searchRangesForRow(row);
    const range = (Number.isInteger(result.occurrence) ? ranges[result.occurrence] : null) || ranges.find(Boolean) || null;
    if (scroll) {
        const sheet = !searchSideLayout() && !searchDialog.hidden ? searchDialog.querySelector('.search-dialog-content').offsetHeight : 0;
        const anchor = range ? { getBoundingClientRect: () => range.getBoundingClientRect() } : row;
        scrollIntoWorkspaceView(anchor, { behavior: 'auto', bottomReserve: sheet });
    }
    const api = searchHighlightApi();
    if (range && api) {
        const current = new Highlight(range);
        current.priority = 10;
        api.set('search-current', current);
        searchHl.current = { result, range };
    } else if (range) {
        searchHl.current = { result, range };
        scheduleSearchRects();
    } else {
        row.classList.add('search-result-highlight'); // the text on screen is not the searched one: mark the paragraph
        searchHl.current = { result, range: null };
    }
}

// Without the Custom Highlight API: rectangles over the matches of the paragraphs near the screen.
function observeSearchRows(rows) {
    if (!('IntersectionObserver' in window)) return;
    searchHl.observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => (entry.isIntersecting ? searchHl.near.add(entry.target) : searchHl.near.delete(entry.target)));
        scheduleSearchRects();
    }, { rootMargin: '100% 0px' });
    rows.forEach((row) => searchHl.observer.observe(row));
}

function scheduleSearchRects() {
    if (searchHighlightApi() || searchHl.frame) return;
    searchHl.frame = requestAnimationFrame(drawSearchRects);
}

function drawSearchRects() {
    searchHl.frame = null;
    let layer = document.querySelector('#search-highlight-layer');
    if (!layer) {
        layer = document.createElement('div');
        layer.id = 'search-highlight-layer';
        layer.className = 'dictionary-highlight-layer';
        layer.setAttribute('aria-hidden', 'true');
        document.body.append(layer);
    }
    const boxes = [];
    const add = (range, current) => {
        if (!range?.startContainer.isConnected) return;
        Array.from(range.getClientRects()).filter((rect) => rect.width > 0).forEach((rect) => {
            const box = document.createElement('div');
            box.className = `search-highlight-rect${current ? ' search-highlight-rect-current' : ''}`;
            box.style.cssText = `left:${rect.left - 1}px;top:${rect.top}px;width:${rect.width + 2}px;height:${rect.height}px`;
            boxes.push(box);
        });
    };
    let count = 0;
    searchHl.near.forEach((row) => {
        (searchHl.byRow.get(row) || []).forEach((range) => { if (count < 300) { add(range, false); count += 1; } });
    });
    if (searchHl.current?.range) add(searchHl.current.range, true);
    layer.replaceChildren(...boxes);
}

window.addEventListener('scroll', scheduleSearchRects, { capture: true, passive: true });
window.addEventListener('resize', () => {
    scheduleSearchRects();
    if (!searchDialog.hidden) applySearchPanelLayout();
});

// The status line, ‹ ›, «← Повернутися» and the collapsed strip's «Пошук 7/50»: one place for both search and replace.
function updateSearchStatus() {
    updateReplaceStatus();
}

function exitSearchNavigation() {
    preSearchPosition = null;
    searchUserNavigated = false;
    searchNavResults = [];
    searchNavIndex = -1;
    lastSearchResults = [];
    replaceMatches = [];
    replaceMeta = null;
    replaceIndex = -1;
    renderSearchPlaceholder('Введіть текст для пошуку.');
    closeSearchPanel(); // a project is opened or left: its results do not apply any more (the query text is kept)
    updateReplaceStatus();
}

async function returnToPreSearchPosition() {
    const target = preSearchPosition;
    preSearchPosition = null;
    searchUserNavigated = false;
    searchNavIndex = -1;
    replaceIndex = -1;
    clearCurrentSearchHighlight();
    markCurrentSearchItem(false);
    updateSearchStatus();
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
        scrollIntoWorkspaceView(row);
    }
    refreshSearchHighlights();
}
bookInfoModeButton.addEventListener('click', showBookInfoMode);
analysisModeButton.addEventListener('click', showAnalysisMode);
translationModeButton.addEventListener('click', showTranslationMode);
// The actions row is pinned only while the chapter text is on screen.
[bookInfoModeButton, analysisModeButton, translationModeButton].forEach((button) => {
    button.addEventListener('click', scheduleChapterActionsSticky);
});
projectSubmodeButtons.forEach((button) => {
    button.addEventListener('click', () => {
        showTranslationSubmode(button.textContent.trim());
    });
});
translateChapterButton.addEventListener('click', translateCurrentChapter);
translationProviderToggle.addEventListener('change', (event) => {
    if (event.target.name === 'translation-provider') {
        void changeTranslationProvider(event.target.value);
    }
});
translationProviderOpenConnections.addEventListener('click', showSettingsView);
translationSettingsButton.addEventListener('click', () => { void openTranslationSettingsDialog(); });
translationSettingsForm.addEventListener('submit', (event) => { void saveTranslationSettings(event); });
document.querySelector('#add-model-price').addEventListener('click', () => {
    addModelPriceRow('', {}, { editableName: true }).querySelector('.model-price-name').focus();
});
document.querySelector('#project-cost-button').addEventListener('click', () => { void openProjectCostDialog(); });
document.querySelector('#close-project-cost').addEventListener('click', () => { projectCostDialog.hidden = true; });
document.querySelector('#project-cost-done').addEventListener('click', () => { projectCostDialog.hidden = true; });
document.querySelector('#project-cost-prices').addEventListener('click', () => {
    projectCostDialog.hidden = true;
    void openTranslationSettingsDialog();
});
document.querySelector('#close-translation-settings').addEventListener('click', closeTranslationSettingsDialog);
document.querySelector('#cancel-translation-settings').addEventListener('click', closeTranslationSettingsDialog);

const checkGenderAgreementButton = document.createElement('button');
checkGenderAgreementButton.type = 'button';
checkGenderAgreementButton.className = 'secondary-btn';
checkGenderAgreementButton.id = 'check-gender-agreement-button';
checkGenderAgreementButton.textContent = 'Перевірити узгодження';
// after the engine switch and the model label, so the translate button and the switch stay first in the pinned row
document.querySelector('#translation-engine-model').insertAdjacentElement('afterend', checkGenderAgreementButton);
checkGenderAgreementButton.addEventListener('click', checkCurrentChapterGenderAgreement);

const selectAllParagraphsReviewedCheckbox = document.createElement('input');
selectAllParagraphsReviewedCheckbox.type = 'checkbox';
selectAllParagraphsReviewedCheckbox.id = 'select-all-paragraphs-reviewed';

const selectAllParagraphsReviewedLabel = document.createElement('label');
selectAllParagraphsReviewedLabel.className = 'chapter-actions-select-all';
selectAllParagraphsReviewedLabel.append(selectAllParagraphsReviewedCheckbox, document.createTextNode('Всі абзаци'));
document.querySelector('#chapter-actions-checkboxes').prepend(selectAllParagraphsReviewedLabel);
selectAllParagraphsReviewedCheckbox.addEventListener('change', () => {
    if (selectedChapterIndex === null) return;
    const state = translationStates.get(selectedChapterIndex);
    if (!state) return;
    const reviewed = selectAllParagraphsReviewedCheckbox.checked;
    translationRows.querySelectorAll('.translation-row').forEach((row) => {
        const checkbox = row.querySelector('.paragraph-review input');
        if (checkbox) checkbox.checked = reviewed;
    });
    updateDraftFromControls(state);
});

const genderAgreementStatus = document.createElement('span');
genderAgreementStatus.className = 'paragraph-status';
genderAgreementStatus.id = 'gender-agreement-status';
// Kept out of the pinned actions row: the status text can be long and belongs to the flow.
document.querySelector('#chapter-actions-status').append(genderAgreementStatus);

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

// Horizontal bounds for a pinned row: the chapter browser's, clamped to the viewport
// (on phones the browser box is wider than the screen and starts off its left edge).
function pinnedRowBounds() {
    const rect = (chapterBrowser || chapterText).getBoundingClientRect();
    const left = Math.max(rect.left, 0);
    const right = Math.min(rect.right, document.documentElement.clientWidth);
    return { left, width: Math.max(right - left, 0) };
}

function syncStuckChapterListBounds() {
    if (!chapterBrowser) {
        return;
    }
    const { left, width } = pinnedRowBounds();
    chapterList.style.left = `${left}px`;
    chapterList.style.width = `${width}px`;
}

// Pinning the strip changes the chips' size and the strip's width, which moves every chip
// under a fixed scrollLeft. Remember the chip nearest the strip's centre and put it back
// there afterwards, so a centred active chapter stays centred.
function chapterStripCenterAnchor() {
    if (chapterList.clientWidth === 0) {
        return null;
    }
    const stripRect = chapterList.getBoundingClientRect();
    const center = stripRect.left + chapterList.clientWidth / 2;
    let anchor = null;
    for (const chip of chapterList.children) {
        const chipRect = chip.getBoundingClientRect();
        const offset = chipRect.left + chipRect.width / 2 - center;
        if (!anchor || Math.abs(offset) < Math.abs(anchor.offset)) {
            anchor = { chip, offset };
        }
    }
    return anchor;
}

function restoreChapterStripCenterAnchor(anchor) {
    if (!anchor || chapterList.clientWidth === 0) {
        return;
    }
    const stripRect = chapterList.getBoundingClientRect();
    const chipRect = anchor.chip.getBoundingClientRect();
    const center = stripRect.left + chapterList.clientWidth / 2;
    chapterList.scrollLeft += (chipRect.left + chipRect.width / 2 - center) - anchor.offset;
}

function setChapterListStuck(stuck) {
    const isStuck = chapterList.classList.contains('chapters-strip--stuck');
    if (stuck === isStuck) {
        return;
    }
    const anchor = chapterStripCenterAnchor();
    try {
        applyChapterListStuck(stuck);
    } finally {
        restoreChapterStripCenterAnchor(anchor);
        flushChapterStripCenter();
    }
}

function applyChapterListStuck(stuck) {
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
        ([entry]) => {
            // Pinned only once the sentinel has scrolled UP past the pin line. A sentinel that is out of the
            // viewport below it (a long page above the chapters) or not laid out at all (tab hidden) must not pin.
            const scrolledPast = entry.boundingClientRect.top < QUICK_ACTIONS_BAR_HEIGHT;
            chapterListWantsStuck = !entry.isIntersecting && scrolledPast && chapterListSentinel.offsetParent !== null;
            setChapterListStuck(chapterListWantsStuck && !stickyPanelsCollapsed);
            updateChapterActionsSticky();
        },
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
        updateChapterActionsSticky();
    });
}

// --- Pinned chapter actions row -----------------------------------------------------
//
// Same technique as the chapter strip (position: sticky can't engage here, see above):
// once the actions row would scroll under the pinned strip, it is fixed right below it
// and a placeholder keeps its place in the flow. The whole pinned stack (quick-actions
// bar + strip + actions) can be collapsed; the choice is remembered per browser.
const chapterActionsRow = document.querySelector('#chapter-actions-row');
const chapterActionsPlaceholder = document.querySelector('#chapter-actions-placeholder');
const toggleStickyPanelsButton = document.querySelector('#toggle-sticky-panels');
// Bottom edge of the top bar (project title and icons), measured: it follows the density and the zoom.
// 48px is only the fallback while the bar is not laid out (the project view is hidden). Exposed to CSS as
// --topbar-h: the docked panels start right below the bar, the pinned rows right below them.
const QUICK_ACTIONS_BAR_FALLBACK = 48;
let QUICK_ACTIONS_BAR_HEIGHT = QUICK_ACTIONS_BAR_FALLBACK;
let pinnedGeometryReady = false;

function syncTopbarHeight() {
    const bar = document.querySelector('#quick-actions-bar');
    const measured = bar ? Math.round(bar.getBoundingClientRect().bottom * 100) / 100 : 0;
    const height = measured > 0 ? measured : QUICK_ACTIONS_BAR_FALLBACK;
    if (height === QUICK_ACTIONS_BAR_HEIGHT && document.documentElement.style.getPropertyValue('--topbar-h')) return;
    QUICK_ACTIONS_BAR_HEIGHT = height;
    document.documentElement.style.setProperty('--topbar-h', `${height}px`);
    if (!pinnedGeometryReady) return; // the pinned-row state is declared further down
    updateChapterActionsSticky();
    updateStickyStackHeight();
}

// The pinned rows (chapters, actions) have exactly the left and right edge of the work area; it changes when a
// side panel opens, collapses or closes, so they follow it (a ResizeObserver on the area, plus the events).
function syncPinnedRows() {
    if (chapterList?.classList.contains('chapters-strip--stuck')) syncStuckChapterListBounds();
    if (chapterActionsRow?.classList.contains('chapter-actions--stuck')) {
        const bounds = pinnedRowBounds();
        chapterActionsRow.style.left = `${bounds.left}px`;
        chapterActionsRow.style.width = `${bounds.width}px`;
    }
}

(function observePinnedGeometry() {
    const bar = document.querySelector('#quick-actions-bar');
    if ('ResizeObserver' in window) {
        if (bar) new ResizeObserver(syncTopbarHeight).observe(bar);
        if (chapterBrowser) new ResizeObserver(syncPinnedRows).observe(chapterBrowser);
        new ResizeObserver(syncPinnedRows).observe(document.documentElement);
    }
    window.addEventListener('resize', () => { syncTopbarHeight(); syncPinnedRows(); });
    syncTopbarHeight();
    window.addEventListener('DOMContentLoaded', () => { pinnedGeometryReady = true; syncTopbarHeight(); });
    if (document.readyState !== 'loading') pinnedGeometryReady = true;
})();
const STICKY_PANELS_STORAGE_KEY = 'workbench.stickyPanelsCollapsed';
let chapterListWantsStuck = false;
let stickyPanelsCollapsed = readStickyPanelsCollapsed();
let chapterActionsStickyFrame = null;

function readStickyPanelsCollapsed() {
    try {
        return window.localStorage.getItem(STICKY_PANELS_STORAGE_KEY) === 'true';
    } catch {
        return false;  // storage blocked (private mode, policy): just start expanded
    }
}

function writeStickyPanelsCollapsed(collapsed) {
    try {
        window.localStorage.setItem(STICKY_PANELS_STORAGE_KEY, collapsed ? 'true' : 'false');
    } catch {
        // Remembering the choice is a convenience; the toggle still works for this page.
    }
}

function renderStickyPanelsToggle() {
    const label = stickyPanelsCollapsed ? 'Розгорнути закріплені рядки' : 'Згорнути закріплені рядки';
    toggleStickyPanelsButton.textContent = stickyPanelsCollapsed ? '▾' : '▴';
    toggleStickyPanelsButton.setAttribute('aria-expanded', stickyPanelsCollapsed ? 'false' : 'true');
    toggleStickyPanelsButton.setAttribute('aria-label', label);
    toggleStickyPanelsButton.title = label;
    projectWorkspaceView.classList.toggle('sticky-panels-collapsed', stickyPanelsCollapsed);
}

function setStickyPanelsCollapsed(collapsed) {
    stickyPanelsCollapsed = collapsed;
    writeStickyPanelsCollapsed(collapsed);
    renderStickyPanelsToggle();
    setChapterListStuck(chapterListWantsStuck && !collapsed);
    updateChapterActionsSticky();
}

function isChapterActionsRowShown() {
    return Boolean(chapterActionsRow) && !chapterText.hidden && chapterText.offsetParent !== null;
}

function chapterActionsStickyTop() {
    const listStuck = chapterList?.classList.contains('chapters-strip--stuck');
    return QUICK_ACTIONS_BAR_HEIGHT + (listStuck ? chapterList.getBoundingClientRect().height : 0);
}

function setChapterActionsStuck(stuck) {
    const isStuck = chapterActionsRow.classList.contains('chapter-actions--stuck');
    if (stuck) {
        if (!isStuck) {
            chapterActionsPlaceholder.style.height = `${chapterActionsRow.getBoundingClientRect().height}px`;
            chapterActionsPlaceholder.hidden = false;
            chapterActionsRow.classList.add('chapter-actions--stuck');
        }
        const bounds = pinnedRowBounds();
        chapterActionsRow.style.top = `${chapterActionsStickyTop()}px`;
        chapterActionsRow.style.left = `${bounds.left}px`;
        chapterActionsRow.style.width = `${bounds.width}px`;
    } else if (isStuck) {
        chapterActionsRow.classList.remove('chapter-actions--stuck');
        chapterActionsRow.style.top = '';
        chapterActionsRow.style.left = '';
        chapterActionsRow.style.width = '';
        chapterActionsPlaceholder.hidden = true;
    }
    updateStickyStackHeight();
}

function updateChapterActionsSticky() {
    if (!chapterActionsRow || !chapterActionsPlaceholder) {
        return;
    }
    if (stickyPanelsCollapsed || !isChapterActionsRowShown()) {
        setChapterActionsStuck(false);
        return;
    }
    const anchor = chapterActionsRow.classList.contains('chapter-actions--stuck') ? chapterActionsPlaceholder : chapterActionsRow;
    setChapterActionsStuck(anchor.getBoundingClientRect().top < chapterActionsStickyTop());
}

function scheduleChapterActionsSticky() {
    if (chapterActionsStickyFrame !== null) {
        return;
    }
    chapterActionsStickyFrame = requestAnimationFrame(() => {
        chapterActionsStickyFrame = null;
        updateChapterActionsSticky();
    });
}

// Height actually covered at the top of the viewport right now (exposed to CSS as
// --sticky-stack-height for scroll-margin-top).
function updateStickyStackHeight() {
    let bottom = QUICK_ACTIONS_BAR_HEIGHT;
    [chapterList, chapterActionsRow].forEach((element) => {
        if (element && (element.classList.contains('chapters-strip--stuck') || element.classList.contains('chapter-actions--stuck'))) {
            bottom = Math.max(bottom, element.getBoundingClientRect().bottom);
        }
    });
    document.documentElement.style.setProperty('--sticky-stack-height', `${Math.round(bottom)}px`);
    return bottom;
}

// What will be covered once the page has scrolled down into the chapter: the strip and
// the actions row are pinned then (unless the pinned block is collapsed).
function expectedStickyStackHeight() {
    if (stickyPanelsCollapsed || !isChapterActionsRowShown()) {
        return QUICK_ACTIONS_BAR_HEIGHT;
    }
    const listHeight = chapterList.classList.contains('chapters-strip--stuck')
        ? chapterList.getBoundingClientRect().height
        : STUCK_ROW_FALLBACK_HEIGHT;
    const actionsHeight = chapterActionsRow.classList.contains('chapter-actions--stuck')
        ? chapterActionsRow.getBoundingClientRect().height
        : STUCK_ROW_FALLBACK_HEIGHT;
    return QUICK_ACTIONS_BAR_HEIGHT + listHeight + actionsHeight;
}
const STUCK_ROW_FALLBACK_HEIGHT = 45;

// Fixed bars at the bottom (search ‹ ›, AI QA navigation, the chat dock) also hide content.
function bottomOverlayHeight() {
    let covered = 0;
    [aiQaNavBar, document.querySelector('#project-chat-panel')].forEach((element) => {
        if (element && !element.hidden && element.offsetParent !== null) {
            covered = Math.max(covered, window.innerHeight - element.getBoundingClientRect().top);
        }
    });
    return Math.max(0, covered);
}

// Scroll so `element` sits in the part of the viewport no pinned bar covers: centred
// when it fits, otherwise with its top just below the pinned block.
function scrollIntoWorkspaceView(element, { behavior = 'smooth', bottomReserve = 0 } = {}) {
    if (!element) {
        return;
    }
    const topInset = expectedStickyStackHeight() + 8;
    const visibleBottom = window.innerHeight - Math.max(bottomOverlayHeight(), bottomReserve) - 8;
    const available = Math.max(visibleBottom - topInset, 40);
    const rect = element.getBoundingClientRect();
    const targetTop = rect.height <= available ? topInset + (available - rect.height) / 2 : topInset;
    window.scrollTo({ top: Math.max(0, window.scrollY + rect.top - targetTop), behavior });
}

if (chapterActionsRow) {
    window.addEventListener('scroll', scheduleChapterActionsSticky, { passive: true });
    // Swipe/scrollbar scroll the row sideways; a vertical wheel does too, but only when
    // the row actually overflows, so it never blocks scrolling the page.
    chapterActionsRow.addEventListener('wheel', (event) => {
        if (event.deltaY !== 0 && chapterActionsRow.scrollWidth > chapterActionsRow.clientWidth) {
            chapterActionsRow.scrollLeft += event.deltaY;
            event.preventDefault();
        }
    }, { passive: false });
}
toggleStickyPanelsButton.addEventListener('click', () => setStickyPanelsCollapsed(!stickyPanelsCollapsed));
renderStickyPanelsToggle();
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
                        selectedVariantId: rawParagraph.selectedVariantId || null,
                        translationVariants: Array.isArray(rawParagraph.translationVariants) ? rawParagraph.translationVariants : [],
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

// Centres the active chapter's chip by scrolling the strip itself (never the page).
// Instant and computed from the geometry as it is right now: a smooth scrollIntoView is
// planned against the layout it starts in and was cut short when the strip got pinned a
// moment later (chips shrink to <= 170px, the row turns position: fixed) or when the page
// scrolled to the remembered paragraph. Returns false while the strip is not laid out
// (its tab is still hidden), so the caller can try again once it is shown.
let chapterStripCenterPending = false;

function centerActiveChapterChip() {
    const chip = chapterList.querySelector('.chapter-button.active');
    if (!chip || chapterList.clientWidth === 0) {
        return false;
    }
    const stripRect = chapterList.getBoundingClientRect();
    const chipRect = chip.getBoundingClientRect();
    chapterList.scrollLeft += (chipRect.left + chipRect.width / 2) - (stripRect.left + chapterList.clientWidth / 2);
    return true;
}

function flushChapterStripCenter() {
    if (chapterStripCenterPending && centerActiveChapterChip()) {
        chapterStripCenterPending = false;
    }
}

function scrollActiveChapterIntoView() {
    if (!chapterList) {
        return;
    }
    chapterStripCenterPending = true;
    flushChapterStripCenter();
    // Again after the layout of this frame (e.g. right after a tab was un-hidden).
    requestAnimationFrame(flushChapterStripCenter);
}

if (chapterList && 'ResizeObserver' in window) {
    // The strip gets its size when its tab is shown; that is the moment a pending centring can run.
    new ResizeObserver(flushChapterStripCenter).observe(chapterList);
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
        // The pinned strip shows a one-line, truncated label: the tooltip keeps the full text.
        chapterButton.title = [chapterLabel.textContent, qaRunCountText].filter(Boolean).join(' · ');
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
    scheduleChapterActionsSticky();
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
    void loadLatestQueue();
    translationProviderMessage = '';
    renderTranslationProviderToggle();
    // Re-read connections on every workspace open: one may have been added in Connections meanwhile.
    translationConnectionsLoaded = false;
    void ensureTranslationConnections();
}

async function loadProjectTranslationGlossaries() {
    if (!currentProject) return;
    try {
        projectTranslationGlossaries = await WorkbenchApi.listProjectTranslationGlossaries(currentProject.projectId, activeDeepLConnectionId);
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
            connectionId: activeDeepLConnectionId,
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
    void initUsageSettings();
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
                setActiveDeepLConnectionId(connection.connectionId);
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
    // Only follow new lines to the bottom if the reader was already there — otherwise the
    // 5s auto-refresh yanks them away from an error they scrolled up to read.
    const wasAtBottom = serverLogOutput.scrollTop + serverLogOutput.clientHeight >= serverLogOutput.scrollHeight - 24;
    serverLogOutput.textContent = filtered.join('\n');
    if (wasAtBottom) {
        serverLogOutput.scrollTop = serverLogOutput.scrollHeight;
    }
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
    // Translation runs only on DeepL or Claude; the empty choice is the DeepL default.
    [...projectTranslationConnectionSelect.options].forEach((option) => {
        if (!option.value) {
            option.textContent = 'DeepL (за замовчуванням)';
            return;
        }
        const connection = connections.find((item) => item.connectionId === option.value);
        if (!['deepl', ...LLM_TRANSLATION_ENGINES].includes(connection?.providerId)) {
            option.remove();
        }
    });
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
    projectTranslationModelInput.value = configuration.translationModels?.claude || configuration.translationModel || '';
    projectOrchestrationConnectionSelect.value = configuration.orchestrationConnectionId || '';
    [...projectQaConnectionsSelect.options].forEach((option) => {
        option.selected = (configuration.qaConnectionIds || []).includes(option.value);
    });
}

function readProjectAIConfiguration() {
    // Keep the GPT/Gemini models set in the ⚙ translation settings; this dialog edits only Claude's.
    const existingModels = newProjectDraft?.aiConfiguration?.translationModels || {};
    return {
        translationConnectionId: projectTranslationConnectionSelect.value || null,
        translationModels: { ...existingModels, claude: projectTranslationModelInput.value.trim() || null },
        translationModel: null,
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
                translationProviderMessage = '';
                renderTranslationProviderToggle();
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
    selectAllParagraphsReviewedCheckbox.checked = false;
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
    variantContexts.clear();
    manualVariantPristine.clear();
    renderChapterTitleTranslation(chapter, state);
    renderChapterAIAnalysis(chapter);
    chapterText.hidden = false;
    scheduleChapterActionsSticky();

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
            // The first real keystroke turns a shown-but-untouched manual variant into an edit.
            manualVariantPristine.delete(paragraph.paragraphId);
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
        translateButton.textContent = translateParagraphButtonLabel();
        translateButton.disabled = !paragraph.paragraphId;
        const runTranslateParagraph = async () => {
            translateButton.disabled = true;
            translateButton.textContent = 'Перекладаємо…';
            try {
                const translated = await WorkbenchApi.translateParagraph(paragraph.paragraphId, activeDeepLConnectionId);
                if (translated.providerId === 'deepl') {
                    setActiveDeepLConnectionId(translated.connectionId || activeDeepLConnectionId);
                    void refreshDeepLUsageBadge();
                }
                // The engine writes its own variant; the chosen text only changes when the
                // paragraph had no chosen variant yet.
                if ((translated.translationText || '') !== (state.draft[currentParagraphIndex].translationText || '')) {
                    state.undo.push(cloneParagraphDrafts(state.draft));
                    state.redo = [];
                }
                const paragraphUsage = createRunUsage();
                addRunUsage(paragraphUsage, translated);
                showRunSummary(paragraphUsage, '1 абзац');
                openLatestEngineVariant(paragraph.paragraphId, translated, translated.providerId);
                applyParagraphFromServer(paragraph, translated);
                clearParagraphDraftFromStorage(paragraph.paragraphId);
                updateParagraphVisualStates(state.draft);
                updateTranslationButtons();
            } catch (error) {
                if (error.code === 'quota_exceeded') {
                    void showDeepLQuotaDialog(error, runTranslateParagraph);
                } else if ((error.code === 'connection_required' || error.code === 'connection_not_ready') && activeDeepLConnectionId) {
                    // The remembered connection is gone or disabled (e.g. deleted after a key
                    // rotation) — fall back to the default DeepL connection instead of getting
                    // stuck asking to reconnect on every reload.
                    setActiveDeepLConnectionId(null);
                    void runTranslateParagraph();
                } else {
                    window.alert(error.message);
                }
            } finally {
                translateButton.disabled = false;
                translateButton.textContent = translateParagraphButtonLabel();
            }
        };
        translateButton.addEventListener('click', () => { void runTranslateParagraph(); });
        const variantPreview = document.createElement('div');
        variantPreview.className = 'variant-preview';
        variantPreview.hidden = true;
        const variantBar = document.createElement('div');
        variantBar.className = 'variant-bar';
        const variantContext = { paragraph, state, index: currentParagraphIndex, row, translation, variantPreview, variantBar };
        if (paragraph.paragraphId) {
            variantContexts.set(paragraph.paragraphId, variantContext);
        }
        renderVariantBar(variantContext, initialVariantTab(paragraph, state.draft[currentParagraphIndex]));
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
                syncParagraphVariants(paragraph.paragraphId, saved);
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
                syncParagraphVariants(paragraph.paragraphId, saved);
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
        // One compact service line UNDER the text: variant tabs, versions, «У файл», the paragraph's translate
        // button, the muted «рушій · модель · дата», «Перевірено» and the «⋯» menu. It wraps onto a second
        // line when the column is narrow; the less important items come last.
        const paraBar = document.createElement('div');
        paraBar.className = 'para-bar';
        paraBar.append(variantBar, translateButton, review, createParagraphMenu(paragraph.paragraphId, [service, qaQueue, narratorChange]));
        translationControl.append(translation, variantPreview, saveStatus, paraBar);
        row.addEventListener('click', () => setCurrentParagraph(paragraph.paragraphId));
        row.append(original, translationControl, status);
        if (compareMode) attachComparePanels(row, variantContext);
        translationRows.append(row);
        updateParagraphVisualState(row, draft);
        paragraphIndex += 1;
    });
    showDraftRecoveryBanner(leftoverDrafts);
    restoreCurrentParagraphRow();
    document.querySelector('#chapter-bulk-status').hidden = true;
    reapplyChapterViewMode();
    updateTranslationButtons();
    scheduleParagraphHeightsSync();
    if (!searchDialog.hidden) window.setTimeout(refreshSearchHighlights, 0); // the rows are new: paint the matches again
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
    scrollIntoWorkspaceView(currentRow, { behavior: 'auto' });
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

// --- Translation variants (per-paragraph tabs) ------------------------------------------

const VARIANT_ENGINE_ORDER = ['current', 'deepl', 'claude', 'openai', 'gemini'];
const VARIANT_LABELS = { current: 'Поточний', deepl: 'DeepL', claude: 'Claude', openai: 'GPT', gemini: 'Gemini', manual: 'Вручну' };
// paragraphId -> { paragraph, state, index, row, translation, variantPreview, variantBar, activeKey }
const variantContexts = new Map();
// paragraphId -> the chosen text, while the editor only *shows* the older manual variant.
// readTranslationDraft reports this value, so merely opening «Вручну» changes nothing.
const manualVariantPristine = new Map();
// paragraphId -> the tab to open (a variantId or 'manual'): set when an engine run has just
// produced a variant, kept up to date while the user switches tabs, so that re-rendering the
// chapter (every batch re-renders it) does not fall back to the default tab. UI state only:
// nothing is stored, a reloaded page opens the default tabs.
const variantTabOverrides = new Map();

// The newest variant of an engine in a paragraph payload (variants arrive oldest first).
function latestVariantOfEngine(variants, engine) {
    const matching = (variants || []).filter((variant) => variant.engine === engine);
    return matching[matching.length - 1] || null;
}

// After an engine run: open that engine's newest variant in the paragraph. Neither the chosen
// variant nor translation_text is touched — only which tab is on screen.
function openLatestEngineVariant(paragraphId, data, engine) {
    const variant = paragraphId ? latestVariantOfEngine(data?.translationVariants, engine) : null;
    if (!variant) {
        return;
    }
    variantTabOverrides.set(paragraphId, variant.variantId);
    const context = variantContexts.get(paragraphId);
    if (context) {
        context.activeKey = variant.variantId;
    }
}

function initialVariantTab(paragraph, draft) {
    const wanted = variantTabOverrides.get(paragraph.paragraphId);
    if (wanted === 'manual' || (wanted && (paragraph.translationVariants || []).some((variant) => variant.variantId === wanted))) {
        return wanted;
    }
    return defaultVariantTab(paragraph, draft);
}

function formatVariantDate(value) {
    if (!value) {
        return '';
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('uk-UA', { dateStyle: 'short', timeStyle: 'short' });
}

// One tab per engine. The tab shows one version of that engine's variant: the one that is
// open, else the one in the file, else the newest. Versions arrive oldest first.
function variantTabs(paragraph, activeKey = null) {
    const variants = Array.isArray(paragraph.translationVariants) ? paragraph.translationVariants : [];
    const tabs = [];
    VARIANT_ENGINE_ORDER.forEach((engine) => {
        const versions = variants.filter((variant) => variant.engine === engine);
        if (versions.length === 0) {
            return;
        }
        const shown = versions.find((variant) => variant.variantId === activeKey)
            || versions.find((variant) => variant.variantId === paragraph.selectedVariantId)
            || versions[versions.length - 1];
        const inFile = versions.some((variant) => variant.variantId === paragraph.selectedVariantId);
        tabs.push({ key: shown.variantId, engine, label: VARIANT_LABELS[engine], variant: shown, versions, inFile });
    });
    tabs.push({ key: 'manual', engine: 'manual', label: VARIANT_LABELS.manual, variant: variants.find((variant) => variant.engine === 'manual') || null, versions: [], inFile: false });
    return tabs;
}

function defaultVariantTab(paragraph, draft) {
    const selected = (paragraph.translationVariants || []).find((variant) => variant.variantId === paragraph.selectedVariantId);
    const manual = (paragraph.translationVariants || []).find((variant) => variant.engine === 'manual');
    // An engine variant is in the file but an older manual edit differs from it: show the
    // engine tab, so the editor never presents the stale manual text as what is in the file.
    if (selected && selected.engine !== 'manual' && manual && manual.text !== (draft?.translationText || '')) {
        return selected.variantId;
    }
    return 'manual';
}

// ‹ 3/5 › — steps through the versions of the engine's variant (1 = oldest). «У файл» acts on
// the version on screen; the version that is in the file is marked ✓.
function createVersionSwitcher(context, active) {
    const { paragraph } = context;
    const position = active.versions.findIndex((variant) => variant.variantId === active.variant.variantId);
    const switcher = document.createElement('span');
    switcher.className = 'variant-versions';
    switcher.setAttribute('role', 'group');
    switcher.setAttribute('aria-label', 'Версії варіанта');
    const step = (offset, symbol, label) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'variant-version-step';
        button.textContent = symbol;
        button.setAttribute('aria-label', label);
        const target = active.versions[position + offset];
        button.disabled = !target;
        if (target) {
            button.addEventListener('click', () => {
                setCurrentParagraph(paragraph.paragraphId);
                showVariantTab(context, target.variantId);
            });
        }
        return button;
    };
    const counter = document.createElement('span');
    counter.className = 'variant-version-counter';
    const inFile = active.variant.variantId === paragraph.selectedVariantId;
    counter.textContent = `${position + 1}/${active.versions.length}${inFile ? ' ✓' : ''}`;
    counter.title = inFile ? 'Ця версія у файлі' : 'Версія не у файлі';
    switcher.append(step(-1, '‹', 'Попередня версія'), counter, step(1, '›', 'Наступна версія'));
    return switcher;
}

function variantTooltip(tab) {
    if (!tab.variant) {
        return 'Ручне редагування тексту для файлу';
    }
    // Only the LLM engines have instructions; an older version (no hash) and one made without them both read «—».
    const hash = tab.variant.promptHash && tab.variant.promptHash !== '—' ? `#${tab.variant.promptHash}` : '—';
    const instructions = ENGINE_INSTRUCTION_LABELS[tab.engine] ? `інструкції ${hash}` : '';
    return [VARIANT_LABELS[tab.engine], tab.variant.model, formatVariantDate(tab.variant.updatedAt || tab.variant.createdAt), instructions].filter(Boolean).join(' · ');
}

function renderVariantBar(context, activeKey = context.activeKey) {
    const { paragraph, variantBar, translation, variantPreview } = context;
    if (compareMode) activeKey = 'manual'; // the tabs are replaced by the panels: the editor is always the field
    const tabs = variantTabs(paragraph, activeKey);
    const hasVariants = tabs.some((tab) => tab.variant);
    variantBar.replaceChildren();
    variantBar.hidden = !hasVariants;
    if (!hasVariants) {
        context.activeKey = 'manual';
        translation.hidden = false;
        variantPreview.hidden = true;
        renderComparePanels(context);
        return;
    }
    const active = tabs.find((tab) => tab.key === activeKey) || tabs[tabs.length - 1];
    context.activeKey = active.key;
    if (variantTabOverrides.has(paragraph.paragraphId)) {
        variantTabOverrides.set(paragraph.paragraphId, active.key);
    }

    const tabList = document.createElement('div');
    tabList.className = 'variant-tabs';
    tabList.setAttribute('role', 'tablist');
    tabList.setAttribute('aria-label', 'Варіанти перекладу');
    tabs.forEach((tab) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'variant-tab';
        button.setAttribute('role', 'tab');
        button.dataset.engine = tab.engine;
        button.setAttribute('aria-selected', tab.key === active.key ? 'true' : 'false');
        const inFile = tab.engine === 'manual'
            ? Boolean(tab.variant && tab.variant.variantId === paragraph.selectedVariantId)
            : tab.inFile;
        button.dataset.inFile = inFile ? 'true' : 'false';
        button.textContent = inFile ? `✓ ${tab.label}` : tab.label;
        button.title = variantTooltip(tab);
        button.addEventListener('click', () => {
            setCurrentParagraph(paragraph.paragraphId);
            showVariantTab(context, tab.key);
        });
        tabList.append(button);
    });

    const header = document.createElement('div');
    header.className = 'variant-panel-header';
    const toFile = document.createElement('button');
    toFile.type = 'button';
    toFile.className = 'variant-to-file';
    const inFile = Boolean(active.variant && active.variant.variantId === paragraph.selectedVariantId);
    toFile.setAttribute('aria-pressed', inFile ? 'true' : 'false');
    // the state is part of the button: «✓ у файлі» (nothing to do) or «≠ У файл» (not in the file; press to choose it)
    toFile.textContent = inFile ? '✓ у файлі' : (active.variant ? '≠ У файл' : 'У файл');
    toFile.disabled = inFile || !active.variant || !paragraph.paragraphId;
    toFile.title = inFile ? 'Ця версія в файлі' : 'Не в файлі. Натисніть, щоб обрати для файлу';
    if (!active.variant) {
        toFile.title = 'Почніть редагувати текст, щоб створити варіант «Вручну»';
    }
    toFile.addEventListener('click', () => { void chooseVariantForFile(context, active.variant); });
    const meta = document.createElement('span');
    meta.className = 'variant-meta muted';
    if (active.engine === 'manual') {
        const selected = (paragraph.translationVariants || []).find((variant) => variant.variantId === paragraph.selectedVariantId);
        if (selected && selected.engine !== 'manual' && !manualVariantPristine.has(paragraph.paragraphId)) {
            // The long sentence is a tooltip; only the open paragraph shows it in full (see .variant-meta-long).
            const longText = `Редагування тексту для файлу (зараз: ${VARIANT_LABELS[selected.engine]}). Зміни збережуться як «Вручну».`;
            meta.append(dictNode('span', 'variant-meta-short', '✎ Вручну'), dictNode('span', 'variant-meta-long', ` — ${longText}`));
            meta.title = longText;
        } else {
            meta.textContent = active.variant ? `Вручну · ${formatVariantDate(active.variant.updatedAt)}` : 'Зміни збережуться як «Вручну».';
        }
    } else {
        meta.textContent = variantTooltip(active);
    }
    if (!meta.title) meta.title = meta.textContent;
    header.append(toFile);
    if (active.versions.length > 1) {
        header.append(createVersionSwitcher(context, active));
    }
    header.append(meta);
    // «Показувати весь розділ у варіанті X»: mark a paragraph whose shown version is not the one in the file.
    const differs = Boolean(context.state?.viewEngine) && active.engine === context.state.viewEngine
        && Boolean(active.variant) && active.variant.variantId !== paragraph.selectedVariantId;
    context.row?.classList.toggle('translation-row--shows-other', differs);
    if (differs) {
        const badge = document.createElement('span');
        badge.className = 'variant-differs';
        badge.setAttribute('role', 'note');
        badge.textContent = '≠ у файлі інша версія';
        header.append(badge);
    }
    variantBar.append(tabList, header);
    // Checks the engine output failed (glossary terms not used) — for the variant on screen,
    // or, in «Вручну», for the variant currently in the file.
    const inFileVariant = (paragraph.translationVariants || []).find((variant) => variant.variantId === paragraph.selectedVariantId);
    const warningVariant = active.engine === 'manual' ? inFileVariant : active.variant;
    const missingTerms = (warningVariant?.warnings || []).filter((warning) => warning.type === 'glossary_missing');
    if (missingTerms.length) {
        const warning = document.createElement('p');
        warning.className = 'variant-warning';
        warning.setAttribute('role', 'note');
        warning.textContent = `⚠ ${VARIANT_LABELS[warningVariant.engine]} не використав термін глосарію: `
            + missingTerms.map((item) => `${item.source} → ${item.target}`).join('; ');
        warning.title = warning.textContent;
        variantBar.append(warning);
    }
    applyVariantView(context, active);
    renderComparePanels(context);
}

function applyVariantView(context, tab) {
    const { paragraph, state, index, translation, variantPreview } = context;
    if (tab.engine === 'manual') {
        const selected = (paragraph.translationVariants || []).find((variant) => variant.variantId === paragraph.selectedVariantId);
        const draftText = state.draft[index]?.translationText || '';
        const showStoredManual = !compareMode && tab.variant && selected?.engine !== 'manual' && tab.variant.text !== draftText;
        if (showStoredManual && !manualVariantPristine.has(paragraph.paragraphId)) {
            manualVariantPristine.set(paragraph.paragraphId, draftText);
            translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(tab.variant.text), paragraph.footnotes);
        }
        translation.hidden = false;
        variantPreview.hidden = true;
    } else {
        restoreChosenTextInEditor(context);
        variantPreview.innerHTML = renderFootnoteMarkers(sanitizeRichText(tab.variant.text), paragraph.footnotes);
        translation.hidden = true;
        variantPreview.hidden = false;
    }
    scheduleParagraphHeightsSync();
}

function restoreChosenTextInEditor(context) {
    const { paragraph, translation } = context;
    if (manualVariantPristine.has(paragraph.paragraphId)) {
        translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(manualVariantPristine.get(paragraph.paragraphId)), paragraph.footnotes);
        manualVariantPristine.delete(paragraph.paragraphId);
    }
}

function showVariantTab(context, key) {
    if (key !== 'manual') {
        restoreChosenTextInEditor(context);
    }
    renderVariantBar(context, key);
}

// Take the server's view of one paragraph (after translate / select / undo / save).
function applyParagraphFromServer(paragraph, data) {
    if (!data) {
        return;
    }
    paragraph.translationText = data.translationText || '';
    paragraph.reviewed = Boolean(data.reviewed);
    if ('translationVariants' in data) {
        paragraph.translationVariants = data.translationVariants || [];
        paragraph.selectedVariantId = data.selectedVariantId || null;
    }
    const context = variantContexts.get(paragraph.paragraphId);
    if (!context) {
        return;
    }
    const { state, index, row, translation } = context;
    context.paragraph = paragraph;
    if (state.draft[index]) {
        state.draft[index] = { ...state.draft[index], translationText: paragraph.translationText, reviewed: paragraph.reviewed };
        state.saved[index] = { ...state.draft[index] };
    }
    manualVariantPristine.delete(paragraph.paragraphId);
    translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(paragraph.translationText), paragraph.footnotes);
    const reviewCheckbox = row.querySelector('.paragraph-review input');
    if (reviewCheckbox) {
        reviewCheckbox.checked = paragraph.reviewed;
    }
    renderVariantBar(context, context.activeKey === 'manual' || !paragraph.translationVariants?.some((variant) => variant.variantId === context.activeKey)
        ? defaultVariantTab(paragraph, state.draft[index])
        : context.activeKey);
    updateParagraphVisualStates(state.draft);
    updateTranslationButtons();
    updateChapterButtonReviewStates();
}

// Variants/selection may change on any save of the paragraph (a real edit becomes «Вручну»).
function syncParagraphVariants(paragraphId, data) {
    const context = variantContexts.get(paragraphId);
    if (!context || !data || !('translationVariants' in data)) {
        return;
    }
    context.paragraph.translationVariants = data.translationVariants || [];
    context.paragraph.selectedVariantId = data.selectedVariantId || null;
    context.paragraph.translationText = data.translationText || '';
    renderVariantBar(context, context.activeKey);
}

async function chooseVariantForFile(context, variant) {
    const { paragraph, state, index } = context;
    if (!variant || !paragraph.paragraphId) {
        return;
    }
    if (state.draft[index]?.reviewed && !window.confirm('Абзац позначено як перевірений. Обрати цей варіант для файлу? Позначку «Перевірено» буде знято.')) {
        return;
    }
    try {
        state.serverActionRunning = true;
        // Unsaved edits of this paragraph are kept as «Вручну» before the choice replaces them.
        if (!paragraphDraftsEqual(state.draft[index], state.saved[index]) && !manualVariantPristine.has(paragraph.paragraphId)) {
            const saved = await WorkbenchApi.updateParagraph(paragraph.paragraphId, {
                translationText: state.draft[index].translationText || null,
                reviewed: state.draft[index].reviewed,
                isService: state.draft[index].isService,
            });
            state.saved[index] = { ...state.draft[index] };
            clearParagraphDraftFromStorage(paragraph.paragraphId);
            applyParagraphFromServer(paragraph, saved);
            variant = (paragraph.translationVariants || []).find((item) => item.variantId === variant.variantId) || variant;
        }
        const before = cloneParagraphDrafts(state.draft);
        const result = await WorkbenchApi.selectTranslationVariant(paragraph.paragraphId, variant.variantId);
        before.serverAction = { paragraphId: paragraph.paragraphId, previous: result.previous, variantId: variant.variantId };
        state.undo.push(before);
        state.redo = [];
        context.activeKey = variant.engine === 'manual' ? 'manual' : variant.variantId;
        applyParagraphFromServer(paragraph, result);
        if (result.movedFootnoteIds?.length) {
            window.alert('Маркери виносок перенесено в кінець абзацу — перемістіть їх на потрібне місце у вкладці «Вручну».');
        }
    } catch (error) {
        window.alert(`Не вдалося обрати варіант: ${error.message}`);
    } finally {
        state.serverActionRunning = false;
        updateTranslationButtons();
    }
}

// Undo/redo of «У файл» goes through the server: it restores the selected variant, text,
// reviewed flag and footnote markers exactly, without recording a manual edit.
async function runServerUndoRedo(state, direction) {
    const from = direction === 'undo' ? state.undo : state.redo;
    const to = direction === 'undo' ? state.redo : state.undo;
    const entry = from[from.length - 1];
    const { paragraphId } = entry.serverAction;
    const context = variantContexts.get(paragraphId);
    state.serverActionRunning = true;
    undoTranslationButton.disabled = true;
    redoTranslationButton.disabled = true;
    try {
        const snapshot = cloneParagraphDrafts(state.draft);
        let data;
        if (direction === 'undo') {
            data = await WorkbenchApi.restoreTranslationSelection(paragraphId, entry.serverAction.previous);
            snapshot.serverAction = { ...entry.serverAction };
        } else {
            data = await WorkbenchApi.selectTranslationVariant(paragraphId, entry.serverAction.variantId);
            snapshot.serverAction = { ...entry.serverAction, previous: data.previous };
        }
        from.pop();
        to.push(snapshot);
        state.draft = cloneParagraphDrafts(entry).map((draft, index) => (
            context && index === context.index ? { ...draft, translationText: data.translationText || '', reviewed: Boolean(data.reviewed) } : draft
        ));
        if (context) {
            context.paragraph.translationText = data.translationText || '';
            context.paragraph.reviewed = Boolean(data.reviewed);
            context.paragraph.translationVariants = data.translationVariants || [];
            context.paragraph.selectedVariantId = data.selectedVariantId || null;
            state.saved[context.index] = { ...state.draft[context.index] };
        }
        renderTranslationFields(state.draft);
    } catch (error) {
        window.alert(`Не вдалося ${direction === 'undo' ? 'скасувати' : 'повторити'} вибір варіанта: ${error.message}`);
    } finally {
        state.serverActionRunning = false;
        updateTranslationButtons();
    }
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
        translationText: manualVariantPristine.has(row.dataset.paragraphId)
            ? manualVariantPristine.get(row.dataset.paragraphId)
            : serializeRichText(row.querySelector('.translation-paragraph')),
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
        const savedParagraphs = await Promise.all(persistableIndexes.map((index) => {
            const draft = state.draft[index];
            return WorkbenchApi.updateParagraph(draft.paragraphId, {
                translationText: draft.translationText || null,
                reviewed: draft.reviewed,
                isService: draft.isService,
            });
        }));
        savedParagraphs.forEach((saved) => syncParagraphVariants(saved?.paragraphId, saved));
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

// --- Cost of a run and the «Вартість» dialog --------------------------------------------------

function formatUsd(value) {
    if (value === null || value === undefined) return null;
    if (value === 0) return '$0.00';
    return value >= 0.01 ? `$${value.toFixed(2)}` : `$${value.toFixed(4)}`;
}

function formatTokenCount(count) {
    return (count || 0).toLocaleString('uk-UA');
}

// "$0.08", "$0.08 (оцінка)", "$0.05 + ціну не задано для частини" or "ціну не задано".
function describeCost(group) {
    const usd = formatUsd(group.costUsd);
    if (usd === null) return 'ціну не задано';
    if (group.unpriced) return `≈ ${usd} + ціну не задано для частини`;
    return group.estimated ? `≈ ${usd} (оцінка)` : `≈ ${usd}`;
}

function pluralize(count, one, few, many) {
    const mod10 = count % 10;
    const mod100 = count % 100;
    if (mod10 === 1 && mod100 !== 11) return one;
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
    return many;
}

// Sums the usageSummary of every batch response of one run.
function createRunUsage() {
    return { batches: 0, tokens: 0, costUsd: 0, unpriced: false, estimated: false, fellBack: null };
}

function addRunUsage(run, response) {
    run.batches += 1;
    const summary = response?.usageSummary;
    if (summary) {
        run.tokens += summary.tokens || 0;
        run.costUsd += summary.costUsd || 0;
        run.unpriced = run.unpriced || summary.unpriced;
        run.estimated = run.estimated || summary.estimated;
    }
    if (response?.reasoning?.fellBack && !run.fellBack) {
        run.fellBack = response.reasoning;
    }
}

function showRunSummary(run, unitLabel = null) {
    if (run.batches === 0) {
        translationRunSummary.textContent = '';
        return;
    }
    const cost = describeCost({ costUsd: run.unpriced && run.costUsd === 0 ? null : run.costUsd, unpriced: run.unpriced, estimated: run.estimated });
    const units = unitLabel || `${run.batches} ${pluralize(run.batches, 'батч', 'батчі', 'батчів')}`;
    let text = `${cost} · ${units} · ${formatTokenCount(run.tokens)} токенів`;
    if (run.fellBack) {
        text += ` · ⚠ модель відхилила рівень роздумів «${run.fellBack.requested}», використано «${run.fellBack.used}»`;
    }
    translationRunSummary.textContent = text;
}

const USAGE_KIND_LABELS = { translate: 'Переклад', retry: 'Повтори', qa: 'AI QA', analysis: 'Аналіз розділу', chat: 'Чат', dictionary: 'Словник' };

function costTable(headers, rows) {
    const table = document.createElement('table');
    table.className = 'project-cost-table';
    const head = document.createElement('thead');
    const headRow = document.createElement('tr');
    headers.forEach((text) => {
        const cell = document.createElement('th');
        cell.scope = 'col';
        cell.textContent = text;
        headRow.append(cell);
    });
    head.append(headRow);
    const body = document.createElement('tbody');
    rows.forEach((cells) => {
        const row = document.createElement('tr');
        cells.forEach((text, index) => {
            const cell = document.createElement('td');
            cell.textContent = text;
            if (index > 0) cell.className = 'num';
            row.append(cell);
        });
        body.append(row);
    });
    table.append(head, body);
    const wrapper = document.createElement('div');
    wrapper.className = 'project-cost-table-wrap';
    wrapper.append(table);
    return wrapper;
}

function renderProjectCostReport(report) {
    const body = document.querySelector('#project-cost-body');
    body.replaceChildren();
    const section = (title, content) => {
        const heading = document.createElement('h3');
        heading.textContent = title;
        body.append(heading, content);
    };
    section('Рушій і модель', costTable(
        ['Рушій / модель', 'Виклики', 'Вхід', 'Вихід', 'Кеш (читання)', 'Вартість'],
        report.byModel.map((item) => [`${item.engine} / ${item.model}`, item.calls, formatTokenCount(item.inputTokens),
            formatTokenCount(item.outputTokens), formatTokenCount(item.cacheReadTokens), describeCost(item)]),
    ));
    section('За розділами', costTable(
        ['Розділ', 'Виклики', 'Токени', 'Вартість'],
        report.byChapter.map((item) => [
            item.chapterId === null ? 'Без розділу (чат)' : (item.removed ? '(видалений розділ)' : `${String(item.chapterIndex).padStart(2, '0')} · ${item.title || `Chapter ${item.chapterIndex}`}`),
            item.calls, formatTokenCount(item.tokens), describeCost(item)]),
    ));
    section('За типом викликів', costTable(
        ['Тип', 'Виклики', 'Токени', 'Вартість'],
        report.byKind.map((item) => [USAGE_KIND_LABELS[item.kind] || item.kind, item.calls, formatTokenCount(item.tokens), describeCost(item)]),
    ));
    const total = document.createElement('p');
    total.className = 'project-cost-total';
    total.textContent = `Разом по проєкту: ${describeCost(report.total)} · ${report.total.calls} ${pluralize(report.total.calls, 'виклик', 'виклики', 'викликів')} · ${formatTokenCount(report.total.tokens)} токенів`;
    body.append(total);
    if (report.unpricedModels.length) {
        const note = document.createElement('p');
        note.className = 'muted';
        note.textContent = `Ціну не задано для: ${report.unpricedModels.join(', ')}. Додайте її в ⚙ → «Ціни моделей».`;
        body.append(note);
    }
}

async function openProjectCostDialog() {
    if (!currentProject) return;
    if (projectCostDaysView) {
        projectCostDaysPanel.replaceChildren();
        projectCostDaysView = null;  // a view belongs to one project
    }
    selectProjectCostTab('total');
    const status = document.querySelector('#project-cost-status');
    const body = document.querySelector('#project-cost-body');
    body.replaceChildren();
    status.textContent = 'Завантажуємо…';
    projectCostDialog.hidden = false;
    try {
        const report = await WorkbenchApi.getProjectUsage(currentProject.projectId);
        if (report.total.calls === 0) {
            status.textContent = 'У цьому проєкті ще немає записаних викликів LLM. Облік іде з моменту його появи; DeepL не рахується.';
            return;
        }
        status.textContent = 'Токени записані в момент кожного виклику; вартість — за поточною таблицею цін. Без тексту книги.';
        renderProjectCostReport(report);
    } catch (error) {
        status.textContent = `Не вдалося завантажити вартість: ${error.message}`;
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
    const chapterIndex = selectedChapterIndex;
    const state = translationStates.get(chapterIndex);
    const previousText = translateChapterButton.textContent;
    translateChapterButton.disabled = true;
    translateChapterButton.textContent = 'Перекладаємо розділ…';
    // DeepL answers the whole chapter in one response. Claude answers one batch per
    // request (totalBatches > 1) so no single request runs into Cloudflare's 524;
    // every finished batch is already saved on the server.
    let batchIndex = 0;
    let totalBatches = 1;
    let undoPushed = false;
    let translatedCount = 0;
    let skippedReviewedCount = 0;
    const runUsage = createRunUsage();
    translationRunSummary.textContent = '';
    try {
        do {
            const result = await WorkbenchApi.translateChapter(currentProject.projectId, chapter.chapterId, activeDeepLConnectionId, batchIndex);
            if ((result.paragraphs || []).length > 0) addRunUsage(runUsage, result);
            if (result.providerId === 'deepl') {
                setActiveDeepLConnectionId(result.connectionId || activeDeepLConnectionId);
                void refreshDeepLUsageBadge();
            }
            if (!undoPushed && (result.paragraphs || []).length > 0) {
                state.undo.push(cloneParagraphDrafts(state.draft));
                state.redo = [];
                undoPushed = true;
            }
            const translationByParagraphId = new Map(
                (result.paragraphs || []).map((paragraph) => [paragraph.paragraphId, paragraph])
            );
            state.draft.forEach((draft, index) => {
                const translated = draft.paragraphId ? translationByParagraphId.get(draft.paragraphId) : null;
                if (!translated) {
                    return;
                }
                const element = getParagraphElementByIndex(chapterIndex, index);
                if (element) {
                    element.translationText = translated.translationText || '';
                    element.reviewed = Boolean(translated.reviewed);
                    if ('translationVariants' in translated) {
                        element.translationVariants = translated.translationVariants || [];
                        element.selectedVariantId = translated.selectedVariantId || null;
                    }
                }
                openLatestEngineVariant(draft.paragraphId, translated, result.providerId);
                state.draft[index] = {
                    paragraphId: draft.paragraphId,
                    translationText: translated.translationText || '',
                    reviewed: Boolean(translated.reviewed),
                    isService: draft.isService,
                };
                state.saved[index] = { ...state.draft[index] };
            });
            if (selectedChapterIndex === chapterIndex) {
                renderTranslationFields(state.draft);
            }
            translatedCount += (result.paragraphs || []).length;
            skippedReviewedCount = (result.skippedReviewedParagraphIds || []).length;
            totalBatches = result.totalBatches || 1;
            batchIndex += 1;
            if (batchIndex < totalBatches) {
                translateChapterButton.textContent = `Перекладаємо… батч ${batchIndex + 1} з ${totalBatches}`;
            }
        } while (batchIndex < totalBatches);
        if (translatedCount === 0 && skippedReviewedCount > 0) {
            window.alert('Усі абзаци розділу позначені як перевірені — переклад розділу їх не змінює. Окремий абзац можна перекласти його кнопкою.');
        }
    } catch (error) {
        if (error.code === 'quota_exceeded') {
            void showDeepLQuotaDialog(error, translateCurrentChapter);
        } else if ((error.code === 'connection_required' || error.code === 'connection_not_ready') && activeDeepLConnectionId) {
            setActiveDeepLConnectionId(null);
            void translateCurrentChapter();
        } else if (batchIndex > 0) {
            window.alert(`Перекладено й збережено батчів: ${batchIndex} з ${totalBatches}. Батч ${batchIndex + 1} не перекладено: ${error.message}`);
        } else {
            window.alert(error.message);
        }
    } finally {
        translateChapterButton.disabled = false;
        translateChapterButton.textContent = previousText;
        showRunSummary(runUsage);
    }
}

function isReadyConnection(connection) {
    return Boolean(connection?.enabled) && connection.status === 'connected';
}

// Mirrors the backend rule: only a project translation connection that is a Claude, OpenAI
// or Gemini connection switches translation away from DeepL; anything else stays on DeepL.
function projectTranslationProvider(project = currentProject) {
    const configuredId = project?.aiConfiguration?.translationConnectionId;
    const configured = configuredId ? integrationConnections.find((item) => item.connectionId === configuredId) : null;
    return LLM_TRANSLATION_ENGINES.includes(configured?.providerId) ? configured.providerId : 'deepl';
}

function translateParagraphButtonLabel() {
    return `Перекласти ${TRANSLATION_PROVIDER_LABELS[projectTranslationProvider()]}`;
}

function configuredTranslationModel(providerId, project = currentProject) {
    const configuration = project?.aiConfiguration || {};
    const model = configuration.translationModels?.[providerId] || (providerId === 'claude' ? configuration.translationModel : null);
    return typeof model === 'string' && model.trim() ? model.trim() : null;
}

// The connection a translation (or a model list) for this engine goes through: the
// project's chosen one if it belongs to the engine, else the first ready one.
function translationConnectionFor(providerId, project = currentProject) {
    const configuredId = project?.aiConfiguration?.translationConnectionId;
    const configured = integrationConnections.find((item) => item.connectionId === configuredId && item.providerId === providerId);
    const candidates = integrationConnections.filter((item) => item.providerId === providerId);
    return (configured && isReadyConnection(configured) ? configured : null)
        || candidates.find(isReadyConnection)
        || configured
        || candidates[0]
        || null;
}

async function ensureTranslationConnections() {
    if (!translationConnectionsLoaded) {
        try {
            const [connections, providers] = await Promise.all([
                WorkbenchApi.listConnections(),
                WorkbenchApi.listIntegrationProviders().catch(() => null),
            ]);
            integrationConnections = connections;
            (providers?.providers || []).forEach((provider) => {
                translationDefaultModels[provider.providerId] = provider.defaultTranslationModel || null;
            });
            translationConnectionsLoaded = true;
        } catch (error) {
            translationProviderMessage = `Не вдалося завантажити підключення: ${error.message}`;
        }
    }
    renderTranslationProviderToggle();
}

function renderTranslationProviderToggle() {
    const provider = projectTranslationProvider();
    translationProviderToggle.querySelectorAll('input[name="translation-provider"]').forEach((input) => {
        input.checked = input.value === provider;
        input.disabled = !currentProject || translationProviderSaving;
    });
    const label = TRANSLATION_PROVIDER_LABELS[provider];
    let missing = '';
    if (translationConnectionsLoaded && currentProject) {
        if (provider !== 'deepl') {
            const configured = integrationConnections.find((item) => item.connectionId === currentProject.aiConfiguration?.translationConnectionId);
            if (!isReadyConnection(configured)) {
                missing = `Підключення ${label} неактивне або не перевірене. Перевірте його в Connections.`;
            }
        } else if (!integrationConnections.some((item) => item.providerId === 'deepl' && isReadyConnection(item))) {
            missing = 'Немає активного підключення DeepL. Додайте DeepL API key у Connections.';
        }
    }
    const message = translationProviderMessage || missing;
    translationProviderHintText.textContent = message;
    translationProviderHint.hidden = !message;
    translationProviderToggle.dataset.missing = message ? 'true' : 'false';
    if (provider === 'deepl') {
        translationEngineModel.textContent = 'Модель: quality_optimized';
    } else {
        const model = configuredTranslationModel(provider);
        const fallback = translationDefaultModels[provider];
        translationEngineModel.textContent = model
            ? `Модель: ${model}`
            : (fallback ? `Модель: ${fallback} (за замовчуванням)` : 'Модель: за замовчуванням');
    }
    // The label is a compact, truncated caption in the pinned row; the full name is also
    // in the tooltips of the caption and of ⚙.
    translationEngineModel.title = translationEngineModel.textContent;
    translationSettingsButton.title = `Налаштування перекладу · ${translationEngineModel.textContent}`;
    document.querySelectorAll('.translate-paragraph-button').forEach((button) => {
        if (!button.disabled) {
            button.textContent = translateParagraphButtonLabel();
        }
    });
}

function applyUpdatedProject(updated) {
    currentProject = updated;
    const index = mockProjects.findIndex((item) => item.projectId === updated.projectId);
    if (index >= 0) {
        mockProjects[index] = updated;
    }
}

async function changeTranslationProvider(providerId) {
    if (!currentProject) {
        return;
    }
    translationProviderMessage = '';
    if (!translationConnectionsLoaded) {
        await ensureTranslationConnections();
    }
    const configuration = currentProject.aiConfiguration || {};
    const configured = integrationConnections.find((item) => item.connectionId === configuration.translationConnectionId);
    let nextConnectionId;
    if (LLM_TRANSLATION_ENGINES.includes(providerId)) {
        const candidate = translationConnectionFor(providerId);
        if (!candidate) {
            const label = TRANSLATION_PROVIDER_LABELS[providerId];
            translationProviderMessage = `Немає підключення ${label}. Додайте ${label} API key у розділі Connections.`;
            renderTranslationProviderToggle();
            return;
        }
        nextConnectionId = candidate.connectionId;
    } else {
        // Keep an explicitly chosen DeepL connection; otherwise fall back to the default DeepL resolution.
        nextConnectionId = configured?.providerId === 'deepl' ? configured.connectionId : null;
    }
    if (nextConnectionId === (configuration.translationConnectionId || null)) {
        renderTranslationProviderToggle();
        return;
    }
    translationProviderSaving = true;
    renderTranslationProviderToggle();
    try {
        applyUpdatedProject(await WorkbenchApi.updateProject(currentProject.projectId, {
            aiConfiguration: { ...configuration, translationConnectionId: nextConnectionId },
        }));
    } catch (error) {
        translationProviderMessage = `Не вдалося зберегти вибір провайдера: ${error.message}`;
    } finally {
        translationProviderSaving = false;
        renderTranslationProviderToggle();
    }
}

// --- Translation settings dialog (⚙) -------------------------------------------------

const translationSettingsState = {};
const REASONING_ENGINES = ['openai', 'gemini'];
const REASONING_LEVEL_LABELS = [['minimal', 'Мінімальний'], ['low', 'Низький'], ['medium', 'Середній']];
const BATCH_DEFAULTS = { maxChars: 1500, maxParagraphs: 8 };

function configuredReasoningLevel(providerId, project = currentProject) {
    const level = project?.aiConfiguration?.translationReasoning?.[providerId];
    return REASONING_LEVEL_LABELS.some(([value]) => value === level) ? level : 'low';
}

async function openTranslationSettingsDialog() {
    if (!currentProject) {
        return;
    }
    translationConnectionsLoaded = false;
    await ensureTranslationConnections();
    translationSettingsError.hidden = true;
    translationEngineSections.replaceChildren();
    LLM_TRANSLATION_ENGINES.forEach((providerId) => {
        translationEngineSections.append(renderTranslationEngineSettings(providerId));
    });
    const batch = currentProject.aiConfiguration?.translationBatch || {};
    translationBatchChars.value = Number.isInteger(batch.maxChars) ? String(batch.maxChars) : '';
    translationBatchParagraphs.value = Number.isInteger(batch.maxParagraphs) ? String(batch.maxParagraphs) : '';
    translationSettingsDialog.hidden = false;
    translationSettingsDialog.querySelector('select, input, button')?.focus();
    LLM_TRANSLATION_ENGINES.forEach((providerId) => { void loadTranslationModels(providerId); });
    setupDictionarySettings();
    void openEngineInstructions();
    void loadModelPriceRows();
}

// --- Own instructions per LLM engine (⚙ → «Інструкції рушіїв») ----------------------------------------
// Two scopes per engine: global (all projects) and an addition for this project. The drafts of every
// (engine, scope) pair stay in memory while the dialog is open; «Зберегти інструкції» saves the changed ones.

const engineInstructions = { engine: 'claude', scope: 'global', limit: 4000, saved: new Map(), drafts: new Map() };
const engineInstructionsText = document.querySelector('#engine-instructions-text');
const engineInstructionsCounter = document.querySelector('#engine-instructions-counter');
const engineInstructionsStatus = document.querySelector('#engine-instructions-status');
const engineInstructionsTabs = document.querySelector('#engine-instructions-tabs');
const engineInstructionsScope = document.querySelector('#engine-instructions-scope');
const engineInstructionsSaveButton = document.querySelector('#save-engine-instructions');
const engineInstructionsShowButton = document.querySelector('#show-engine-prompt');
const enginePromptDialog = document.querySelector('#engine-prompt-dialog');
const ENGINE_INSTRUCTION_LABELS = { claude: 'Claude', openai: 'GPT', gemini: 'Gemini' };

function engineInstructionKey(engine = engineInstructions.engine, scope = engineInstructions.scope) {
    return `${engine}:${scope}`;
}

// Cyrillic runs at about 3 characters per token for these models: a rough figure, as the prompt preview says.
function approxTokens(text) {
    return Math.round((text || '').length / 3);
}

function engineInstructionDraft(key) {
    return engineInstructions.drafts.has(key) ? engineInstructions.drafts.get(key) : (engineInstructions.saved.get(key) ?? '');
}

function engineInstructionsDirtyKeys() {
    return [...engineInstructions.drafts.keys()].filter((key) => engineInstructions.drafts.get(key) !== (engineInstructions.saved.get(key) ?? ''));
}

function renderEngineInstructionsCounter() {
    const text = engineInstructionsText.value;
    const over = text.length > engineInstructions.limit;
    engineInstructionsCounter.textContent = `${text.length} / ${engineInstructions.limit} символів · ≈ ${approxTokens(text)} токенів`;
    engineInstructionsCounter.classList.toggle('over-limit', over);
    const dirty = engineInstructionsDirtyKeys().length > 0;
    engineInstructionsSaveButton.disabled = !dirty || [...engineInstructions.drafts.values()].some((value) => value.length > engineInstructions.limit);
    if (over) {
        engineInstructionsStatus.textContent = `Занадто довго: ліміт — ${engineInstructions.limit} символів.`;
    } else if (dirty) {
        engineInstructionsStatus.textContent = 'Є незбережені зміни.';
    }
}

async function loadEngineInstructions(engine, scope) {
    const key = engineInstructionKey(engine, scope);
    if (engineInstructions.saved.has(key)) return;
    const projectId = scope === 'project' ? currentProject?.projectId : null;
    const result = await WorkbenchApi.getEngineInstructions(engine, projectId);
    engineInstructions.limit = result.limit || engineInstructions.limit;
    engineInstructions.saved.set(key, result.text || '');
}

async function showEngineInstructions() {
    const { engine, scope } = engineInstructions;
    const key = engineInstructionKey();
    engineInstructionsText.disabled = true;
    try {
        await loadEngineInstructions(engine, scope);
        if (engine !== engineInstructions.engine || scope !== engineInstructions.scope) return; // the user already moved on
        engineInstructionsText.value = engineInstructionDraft(key);
        engineInstructionsStatus.textContent = '';
    } catch (error) {
        engineInstructionsStatus.textContent = error.message || 'Не вдалося завантажити інструкції.';
    } finally {
        engineInstructionsText.disabled = false;
    }
    engineInstructionsTabs.querySelectorAll('[data-engine]').forEach((button) => {
        const active = button.dataset.engine === engine;
        button.classList.toggle('active', active);
        button.setAttribute('aria-selected', String(active));
    });
    engineInstructionsScope.querySelectorAll('[data-scope]').forEach((button) => {
        const active = button.dataset.scope === scope;
        button.classList.toggle('active', active);
        button.setAttribute('aria-checked', String(active));
    });
    renderEngineInstructionsCounter();
}

async function openEngineInstructions() {
    engineInstructions.saved.clear();
    engineInstructions.drafts.clear();
    engineInstructionsStatus.textContent = '';
    await showEngineInstructions();
}

async function saveEngineInstructions() {
    const keys = engineInstructionsDirtyKeys();
    if (!keys.length) return;
    engineInstructionsSaveButton.disabled = true;
    try {
        for (const key of keys) {
            const [engine, scope] = key.split(':');
            const result = await WorkbenchApi.saveEngineInstructions(
                engine, engineInstructions.drafts.get(key), scope === 'project' ? currentProject?.projectId : null,
            );
            engineInstructions.saved.set(key, result.text || '');
            engineInstructions.drafts.delete(key);
        }
        engineInstructionsText.value = engineInstructionDraft(engineInstructionKey());
        engineInstructionsStatus.textContent = 'Збережено. Нові запити перекладу вже використовують ці інструкції.';
        renderEngineInstructionsCounter();
    } catch (error) {
        engineInstructionsStatus.textContent = error.message || 'Не вдалося зберегти інструкції.';
        engineInstructionsSaveButton.disabled = false;
    }
}

// The prompt shows the saved texts, or, when this engine has unsaved changes in the field, those drafts:
// the server builds it from them without writing anything, and the window says it is a draft.
async function showEnginePrompt() {
    const engine = engineInstructions.engine;
    const draft = {};
    engineInstructionsDirtyKeys().forEach((key) => {
        const [keyEngine, scope] = key.split(':');
        if (keyEngine === engine) draft[scope] = engineInstructions.drafts.get(key);
    });
    const isDraft = Object.keys(draft).length > 0;
    engineInstructionsShowButton.disabled = true;
    try {
        const result = isDraft
            ? await WorkbenchApi.previewEnginePrompt(currentProject.projectId, engine, draft)
            : await WorkbenchApi.getEnginePrompt(currentProject.projectId, engine);
        document.querySelector('#engine-prompt-engine').textContent = `${ENGINE_INSTRUCTION_LABELS[engine]} · ${currentProject.title || 'проєкт'}`;
        document.querySelector('#engine-prompt-draft').hidden = !isDraft;
        document.querySelector('#engine-prompt-text').value = result.prompt;
        document.querySelector('#engine-prompt-summary').textContent =
            `≈ ${result.approxTokens} токенів (${result.chars} символів) · інструкції ${result.promptHash === '—' ? '—' : `#${result.promptHash}`}${isDraft ? ' (чернетка)' : ''}`;
        enginePromptDialog.hidden = false;
        document.querySelector('#close-engine-prompt').focus();
    } catch (error) {
        engineInstructionsStatus.textContent = error.message || 'Не вдалося зібрати промпт.';
    } finally {
        engineInstructionsShowButton.disabled = false;
    }
}

function closeEnginePrompt() {
    enginePromptDialog.hidden = true;
    engineInstructionsShowButton.focus();
}

engineInstructionsTabs.addEventListener('click', (event) => {
    const button = event.target.closest('[data-engine]');
    if (!button || button.dataset.engine === engineInstructions.engine) return;
    engineInstructions.engine = button.dataset.engine;
    void showEngineInstructions();
});
engineInstructionsScope.addEventListener('click', (event) => {
    const button = event.target.closest('[data-scope]');
    if (!button || button.dataset.scope === engineInstructions.scope) return;
    engineInstructions.scope = button.dataset.scope;
    void showEngineInstructions();
});
engineInstructionsText.addEventListener('input', () => {
    engineInstructions.drafts.set(engineInstructionKey(), engineInstructionsText.value);
    renderEngineInstructionsCounter();
});
engineInstructionsSaveButton.addEventListener('click', () => { void saveEngineInstructions(); });
engineInstructionsShowButton.addEventListener('click', () => { void showEnginePrompt(); });
document.querySelector('#close-engine-prompt').addEventListener('click', closeEnginePrompt);
enginePromptDialog.addEventListener('click', (event) => {
    if (event.target === enginePromptDialog) closeEnginePrompt();
});

// --- Model prices (global table, edited in ⚙) -----------------------------------------------

const PRICE_FIELDS = [
    ['inputPerMTok', 'Вхід'],
    ['outputPerMTok', 'Вихід'],
    ['cacheReadPerMTok', 'Читання кешу'],
    ['cacheWritePerMTok', 'Запис кешу'],
];
let loadedModelPriceModels = new Set();
const PRICE_SOURCE_LABELS = { seed: 'початкова', manual: 'вручну', list: 'зі списку' };

function formatLocalDate(isoString) {
    const date = new Date(isoString);
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString('uk-UA');
}

function formatLocalDateTime(isoString) {
    const date = new Date(isoString);
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('uk-UA', { dateStyle: 'short', timeStyle: 'short' });
}

function addModelPriceRow(model, prices = {}, { editableName = false } = {}) {
    const row = document.createElement('div');
    row.className = 'model-price-row';
    row.setAttribute('role', 'group');
    const name = document.createElement('input');
    name.type = 'text';
    name.className = 'model-price-name';
    name.maxLength = 100;
    name.autocomplete = 'off';
    name.spellcheck = false;
    name.value = model;
    name.readOnly = !editableName;
    name.placeholder = 'ID моделі';
    name.setAttribute('aria-label', 'Модель');
    row.setAttribute('aria-label', model || 'Нова модель');
    row.append(name);
    if (prices.source) {
        const origin = document.createElement('span');
        origin.className = 'model-price-origin muted';
        origin.textContent = `${PRICE_SOURCE_LABELS[prices.source] || prices.source}${prices.updatedAt ? ` · ${formatLocalDate(prices.updatedAt)}` : ''}`;
        row.dataset.source = prices.source;
        row.append(origin);
    }
    PRICE_FIELDS.forEach(([key, label]) => {
        const field = document.createElement('label');
        field.className = 'model-price-field';
        const caption = document.createElement('span');
        caption.textContent = label;
        const input = document.createElement('input');
        input.type = 'number';
        input.inputMode = 'decimal';
        input.min = '0';
        input.step = 'any';
        input.dataset.key = key;
        input.placeholder = 'не задано';
        input.value = prices[key] === null || prices[key] === undefined ? '' : String(prices[key]);
        input.setAttribute('aria-label', `${label} · ${model || 'нова модель'}`);
        field.append(caption, input);
        row.append(field);
    });
    modelPricesTable.append(row);
    return row;
}

async function loadModelPriceRows() {
    modelPricesTable.replaceChildren();
    loadedModelPriceModels = new Set();
    try {
        const [payload, usage] = await Promise.all([
            WorkbenchApi.getModelPrices(),
            currentProject ? WorkbenchApi.getProjectUsage(currentProject.projectId).catch(() => null) : Promise.resolve(null),
        ]);
        const { prices } = payload;
        showModelPricesStatus(payload);
        prices.forEach((price) => {
            loadedModelPriceModels.add(price.model);
            addModelPriceRow(price.model, price);
        });
        // Models this project has used or is configured with, but that have no price yet.
        const wanted = new Set((usage?.byModel || []).map((item) => item.model));
        LLM_TRANSLATION_ENGINES.forEach((providerId) => {
            const model = configuredTranslationModel(providerId) || translationDefaultModels[providerId];
            if (model) wanted.add(model);
        });
        [...wanted].filter((model) => model && !loadedModelPriceModels.has(model)).forEach((model) => addModelPriceRow(model, {}));
    } catch (error) {
        const message = document.createElement('p');
        message.className = 'form-error';
        message.textContent = `Не вдалося завантажити ціни: ${error.message}`;
        modelPricesTable.append(message);
    }
}

// The rows to send: named rows that have a price or already exist on the server. A loaded row
// whose four prices were all cleared is a deletion (the server removes it); `deletions` lists them
// so the user can be asked first.
function collectModelPrices() {
    const prices = [];
    const deletions = [];
    for (const row of modelPricesTable.querySelectorAll('.model-price-row')) {
        const model = row.querySelector('.model-price-name').value.trim();
        const entry = { model };
        let any = false;
        for (const [key, label] of PRICE_FIELDS) {
            const raw = row.querySelector(`input[data-key="${key}"]`).value.trim();
            if (raw === '') {
                entry[key] = null;
                continue;
            }
            const value = Number(raw);
            if (!Number.isFinite(value) || value < 0) {
                throw new Error(`Ціна «${label}» для ${model || 'нової моделі'} має бути числом від 0.`);
            }
            entry[key] = value;
            any = true;
        }
        if (!model) {
            if (any) throw new Error('Вкажіть ID моделі для рядка з ціною.');
            continue;
        }
        if (!any && loadedModelPriceModels.has(model)) deletions.push(model);
        if (any || loadedModelPriceModels.has(model)) prices.push(entry);
    }
    return { prices, deletions };
}

function closeTranslationSettingsDialog() {
    translationSettingsDialog.hidden = true;
}

function renderTranslationEngineSettings(providerId) {
    const label = TRANSLATION_PROVIDER_LABELS[providerId];
    const connection = translationConnectionFor(providerId);
    const current = configuredTranslationModel(providerId);
    const section = document.createElement('section');
    section.className = 'translation-engine-settings';
    section.dataset.engine = providerId;

    const heading = document.createElement('h3');
    heading.textContent = label;
    const status = document.createElement('p');
    status.className = 'translation-engine-status';
    const statusText = document.createElement('span');
    statusText.textContent = connection
        ? (isReadyConnection(connection) ? `Підключено: ${connection.displayName}` : `Підключення ${connection.displayName} неактивне або не перевірене`)
        : 'Немає підключення';
    status.dataset.ready = isReadyConnection(connection) ? 'true' : 'false';
    const openConnections = document.createElement('button');
    openConnections.type = 'button';
    openConnections.className = 'text-btn';
    openConnections.textContent = 'Відкрити Connections';
    openConnections.addEventListener('click', () => {
        closeTranslationSettingsDialog();
        showSettingsView();
    });
    status.append(statusText, openConnections);

    const listLabel = document.createElement('label');
    listLabel.textContent = 'Модель зі списку';
    const search = document.createElement('input');
    search.type = 'search';
    search.className = 'search-input translation-model-search';
    search.placeholder = 'Пошук моделі…';
    search.setAttribute('aria-label', `Пошук моделі ${label}`);
    const select = document.createElement('select');
    select.className = 'translation-model-select';
    select.setAttribute('aria-label', `Модель ${label}`);
    const listStatus = document.createElement('p');
    listStatus.className = 'translation-model-list-status muted';
    listStatus.setAttribute('role', 'status');
    listLabel.append(search, select);

    const manualLabel = document.createElement('label');
    manualLabel.textContent = 'Інша модель';
    const manual = document.createElement('input');
    manual.type = 'text';
    manual.className = 'translation-model-manual';
    manual.maxLength = 100;
    manual.autocomplete = 'off';
    manual.spellcheck = false;
    manual.placeholder = 'ID моделі, якщо її немає в списку';
    manualLabel.append(manual);

    translationSettingsState[providerId] = { section, select, search, manual, listStatus, models: [], current };
    fillTranslationModelSelect(providerId);
    search.addEventListener('input', () => fillTranslationModelSelect(providerId));
    select.addEventListener('change', () => {
        if (select.value) {
            manual.value = '';
        }
    });
    section.append(heading, status, listLabel, listStatus, manualLabel);
    if (REASONING_ENGINES.includes(providerId)) {
        const reasoningLabel = document.createElement('label');
        reasoningLabel.textContent = 'Рівень роздумів';
        const reasoning = document.createElement('select');
        reasoning.className = 'translation-reasoning-select';
        reasoning.setAttribute('aria-label', `Рівень роздумів ${label}`);
        REASONING_LEVEL_LABELS.forEach(([value, text]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = text;
            reasoning.append(option);
        });
        reasoning.value = configuredReasoningLevel(providerId);
        const hint = document.createElement('p');
        hint.className = 'muted';
        hint.textContent = providerId === 'gemini'
            ? 'Токени роздумів оплачуються як вихідні й дають основну витрату. Діє для Gemini 3.x; для 2.5 не застосовується. Якщо модель відхилить рівень, один раз повторимо з «Низький».'
            : 'Токени роздумів оплачуються як вихідні й дають основну витрату. Якщо модель відхилить рівень, один раз повторимо з «Низький».';
        reasoningLabel.append(reasoning);
        section.append(reasoningLabel, hint);
        translationSettingsState[providerId].reasoning = reasoning;
    }
    return section;
}

function fillTranslationModelSelect(providerId) {
    const entry = translationSettingsState[providerId];
    if (!entry) {
        return;
    }
    const needle = entry.search.value.trim().toLocaleLowerCase();
    const chosen = entry.select.value || entry.current || '';
    entry.select.replaceChildren();
    const fallback = translationDefaultModels[providerId];
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = fallback ? `За замовчуванням (${fallback})` : 'За замовчуванням';
    entry.select.append(defaultOption);
    const listed = entry.models.filter((model) => !needle
        || model.id.toLocaleLowerCase().includes(needle)
        || (model.displayName || '').toLocaleLowerCase().includes(needle));
    listed.forEach((model) => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.displayName && model.displayName !== model.id ? `${model.displayName} (${model.id})` : model.id;
        entry.select.append(option);
    });
    const known = entry.models.some((model) => model.id === chosen);
    if (chosen && known) {
        entry.select.value = chosen;
    } else if (chosen && !entry.manual.value && chosen === entry.current) {
        // The saved model is not in the list (custom or retired ID): keep it in "Інша модель".
        entry.manual.value = chosen;
    }
}

async function loadTranslationModels(providerId) {
    const entry = translationSettingsState[providerId];
    const connection = translationConnectionFor(providerId);
    if (!entry) {
        return;
    }
    if (!connection) {
        entry.listStatus.textContent = 'Список моделей недоступний без підключення. Можна ввести ID моделі вручну.';
        entry.select.disabled = true;
        entry.search.disabled = true;
        fillTranslationModelSelect(providerId);
        return;
    }
    entry.listStatus.textContent = 'Завантажуємо список моделей…';
    try {
        const result = await WorkbenchApi.listConnectionModels(connection.connectionId);
        entry.models = result.models || [];
        entry.listStatus.textContent = entry.models.length
            ? `Моделей у списку: ${entry.models.length}.`
            : 'Провайдер не повернув жодної текстової моделі. Можна ввести ID вручну.';
    } catch (error) {
        entry.models = [];
        entry.select.disabled = true;
        entry.search.disabled = true;
        entry.listStatus.textContent = `Не вдалося отримати список моделей: ${error.message} Можна ввести ID моделі вручну.`;
    }
    fillTranslationModelSelect(providerId);
}

async function saveTranslationSettings(event) {
    event.preventDefault();
    if (!currentProject) {
        return;
    }
    const translationModels = {};
    LLM_TRANSLATION_ENGINES.forEach((providerId) => {
        const entry = translationSettingsState[providerId];
        const manualValue = entry?.manual.value.trim();
        translationModels[providerId] = manualValue || entry?.select.value || null;
    });
    const configuration = currentProject.aiConfiguration || {};
    const translationReasoning = {};
    REASONING_ENGINES.forEach((providerId) => {
        translationReasoning[providerId] = translationSettingsState[providerId]?.reasoning?.value || 'low';
    });
    const translationBatch = {};
    try {
        [[translationBatchChars, 'maxChars', 500, 6000, 'символів'], [translationBatchParagraphs, 'maxParagraphs', 1, 20, 'абзаців']].forEach(([input, key, min, max, unit]) => {
            const raw = input.value.trim();
            if (raw === '') return; // empty: the default (1500 characters, 8 paragraphs)
            const value = Number(raw);
            if (!Number.isInteger(value) || value < min || value > max) {
                throw new Error(`Макс. ${unit} у батчі — ціле число від ${min} до ${max}.`);
            }
            translationBatch[key] = value;
        });
    } catch (error) {
        translationSettingsError.textContent = error.message;
        translationSettingsError.hidden = false;
        return;
    }
    let prices;
    try {
        const collected = collectModelPrices();
        prices = collected.prices;
        const declined = collected.deletions.find((model) => !window.confirm(`Видалити ціну моделі ${model}?`));
        if (declined) {
            throw new Error(`Збереження скасовано: ціну моделі ${declined} не видалено. Введіть ціну або підтвердіть видалення.`);
        }
    } catch (error) {
        translationSettingsError.textContent = error.message;
        translationSettingsError.hidden = false;
        return;
    }
    saveTranslationSettingsButton.disabled = true;
    try {
        if (prices.length) {
            await WorkbenchApi.saveModelPrices(prices);
        }
        applyUpdatedProject(await WorkbenchApi.updateProject(currentProject.projectId, {
            // translationModel is the older Claude-only field; translationModels.claude replaces it.
            aiConfiguration: { ...configuration, translationModels, translationModel: null, translationReasoning, translationBatch, dictionary: collectDictionarySettings() },
        }));
        renderTranslationProviderToggle();
        closeTranslationSettingsDialog();
    } catch (error) {
        translationSettingsError.textContent = `Не вдалося зберегти налаштування: ${error.message}`;
        translationSettingsError.hidden = false;
    } finally {
        saveTranslationSettingsButton.disabled = false;
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
                scrollIntoWorkspaceView(row);
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
    scrollIntoWorkspaceView(entry.row);

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

async function undoTranslation() {
    const state = translationStates.get(selectedChapterIndex);
    if (!state || state.undo.length === 0 || state.serverActionRunning) {
        return;
    }
    if (state.undo[state.undo.length - 1].bulkAction) {
        await runBulkUndoRedo(state, 'undo');
        return;
    }
    if (state.undo[state.undo.length - 1].serverAction) {
        await runServerUndoRedo(state, 'undo');
        return;
    }
    state.redo.push(cloneParagraphDrafts(state.draft));
    state.draft = cloneParagraphDrafts(state.undo.pop());
    renderTranslationFields(state.draft);
}

async function redoTranslation() {
    const state = translationStates.get(selectedChapterIndex);
    if (!state || state.redo.length === 0 || state.serverActionRunning) {
        return;
    }
    if (state.redo[state.redo.length - 1].bulkAction) {
        await runBulkUndoRedo(state, 'redo');
        return;
    }
    if (state.redo[state.redo.length - 1].serverAction) {
        await runServerUndoRedo(state, 'redo');
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
        manualVariantPristine.delete(row.dataset.paragraphId);
        translation.innerHTML = renderFootnoteMarkers(sanitizeRichText(values[index].translationText), paragraphElement?.footnotes);
        row.querySelector('.paragraph-review input').checked = values[index].reviewed;
        updateParagraphVisualState(row, values[index]);
        const context = variantContexts.get(row.dataset.paragraphId);
        if (context && paragraphElement) {
            context.paragraph = paragraphElement;
            renderVariantBar(context, initialVariantTab(paragraphElement, values[index]));
        }
    });
    updateTranslationButtons();
    updateChapterButtonReviewStates();
    scheduleParagraphHeightsSync();
}

function updateTranslationButtons() {
    refreshChapterViewControls();
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

// --- Model prices: status, refresh from the public list, restore ------------------------------

const modelPricesStatus = document.querySelector('#model-prices-status');
const priceRefreshPanel = document.querySelector('#price-refresh-panel');
const refreshModelPricesButton = document.querySelector('#refresh-model-prices');
const restoreModelPricesButton = document.querySelector('#restore-model-prices');

function showModelPricesStatus(payload, extra = '') {
    const parts = [];
    if (payload?.updatedAt) {
        parts.push(`Ціни оновлено ${formatLocalDateTime(payload.updatedAt)}${payload.source?.name ? ` · джерело: ${payload.source.name}` : ''}`);
    } else {
        parts.push('Ціни зі списку ще не оновлювались: початкові значення та ваші правки.');
    }
    if (extra) parts.push(extra);
    modelPricesStatus.textContent = parts.join(' · ');
}

function formatPrice(value) {
    return value === null || value === undefined ? '—' : String(value);
}

const PRICE_FIELD_SHORT = [['inputPerMTok', 'вхід'], ['outputPerMTok', 'вихід'], ['cacheReadPerMTok', 'кеш чит.'], ['cacheWritePerMTok', 'кеш зап.']];

function describePriceChange(item) {
    return PRICE_FIELD_SHORT.map(([key, label]) => {
        const before = item.current ? item.current[key] : null;
        const after = item.proposed ? item.proposed[key] : null;
        return before === after || (before === null && after === null)
            ? `${label} ${formatPrice(after)}`
            : `${label} ${formatPrice(before)} → ${formatPrice(after)}`;
    }).join(' · ');
}

function renderPriceComparison(preview) {
    priceRefreshPanel.replaceChildren();
    priceRefreshPanel.hidden = false;
    const heading = document.createElement('h4');
    heading.textContent = 'Порівняння цін';
    const source = document.createElement('p');
    source.className = 'muted';
    source.textContent = `Джерело: ${preview.source.name}${preview.source.fallback ? ' (запасне: основне недоступне)' : ''} · отримано ${formatLocalDateTime(preview.source.fetchedAt)} · ${preview.source.url}. `
        + 'Нічого не змінено, доки ви не підтвердите. Порівняння діє 10 хвилин.';
    priceRefreshPanel.append(heading, source);

    const list = document.createElement('div');
    list.className = 'price-comparison-list';
    const selectable = [];
    preview.items.forEach((item) => {
        const row = document.createElement('div');
        row.className = 'price-comparison-row';
        row.dataset.model = item.model;
        row.dataset.status = item.status;
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'price-comparison-select';
        checkbox.setAttribute('aria-label', `Оновити ${item.model}`);
        const changeable = item.status === 'changed' || item.status === 'new';
        checkbox.disabled = !changeable;
        checkbox.checked = Boolean(item.defaultSelected);
        const body = document.createElement('div');
        body.className = 'price-comparison-body';
        const title = document.createElement('strong');
        title.textContent = item.model;
        const detail = document.createElement('span');
        detail.className = 'price-comparison-detail';
        if (item.status === 'not_found') {
            detail.textContent = 'немає в списку (збігається лише точна назва або з префіксом провайдера)';
        } else if (item.status === 'same') {
            detail.textContent = `без змін · ${describePriceChange(item)} · збіг: ${item.matchedKey}`;
        } else {
            detail.textContent = `${item.status === 'new' ? 'нова ціна' : 'було → стане'}: ${describePriceChange(item)} · збіг: ${item.matchedKey}`;
        }
        body.append(title, detail);
        if (item.current) {
            const origin = document.createElement('span');
            origin.className = 'muted';
            origin.textContent = `зараз: ${PRICE_SOURCE_LABELS[item.current.source] || item.current.source}`;
            body.append(origin);
        }
        if (item.suspicious) {
            const warning = document.createElement('span');
            warning.className = 'price-comparison-warning';
            warning.textContent = '⚠ нова ціна відрізняється більш ніж удвічі — перевірте зіставлення; за замовчуванням не вибрано';
            body.append(warning);
        }
        if (item.protectedManual && changeable) {
            const manual = document.createElement('span');
            manual.className = 'price-comparison-warning';
            manual.textContent = '✎ ручна правка: буде пропущено без галочки «Перезаписати й ручні»';
            body.append(manual);
        }
        row.append(checkbox, body);
        list.append(row);
        if (changeable) selectable.push(checkbox);
    });
    if (!preview.items.length) {
        const empty = document.createElement('p');
        empty.className = 'muted';
        empty.textContent = 'У таблиці немає моделей для порівняння.';
        list.append(empty);
    }
    priceRefreshPanel.append(list);

    const overwriteLabel = document.createElement('label');
    overwriteLabel.className = 'price-overwrite-manual';
    const overwrite = document.createElement('input');
    overwrite.type = 'checkbox';
    overwrite.id = 'price-overwrite-manual';
    overwriteLabel.append(overwrite, document.createTextNode(' Перезаписати й ручні'));
    const message = document.createElement('p');
    message.className = 'muted';
    message.setAttribute('role', 'status');
    const actions = document.createElement('div');
    actions.className = 'model-prices-actions';
    const apply = document.createElement('button');
    apply.type = 'button';
    apply.className = 'primary-btn';
    apply.id = 'apply-price-comparison';
    apply.textContent = 'Застосувати вибране';
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.className = 'secondary-btn';
    cancel.textContent = 'Скасувати';
    const updateApply = () => { apply.disabled = !selectable.some((box) => box.checked); };
    selectable.forEach((box) => box.addEventListener('change', updateApply));
    updateApply();
    cancel.addEventListener('click', () => { priceRefreshPanel.hidden = true; priceRefreshPanel.replaceChildren(); });
    apply.addEventListener('click', async () => {
        const models = [...list.querySelectorAll('.price-comparison-row')]
            .filter((row) => row.querySelector('.price-comparison-select').checked)
            .map((row) => row.dataset.model);
        apply.disabled = true;
        try {
            const result = await WorkbenchApi.applyModelPrices(preview.previewId, models, overwrite.checked);
            priceRefreshPanel.hidden = true;
            priceRefreshPanel.replaceChildren();
            await loadModelPriceRows();
            showModelPricesStatus(result, `застосовано: ${result.applied.length}${result.skippedManual.length ? `, пропущено ручних: ${result.skippedManual.length}` : ''}`);
        } catch (error) {
            message.textContent = `Не вдалося застосувати: ${error.message}`;
            updateApply();
        }
    });
    actions.append(apply, cancel);
    priceRefreshPanel.append(overwriteLabel, message, actions);
}

refreshModelPricesButton.addEventListener('click', async () => {
    refreshModelPricesButton.disabled = true;
    const previous = refreshModelPricesButton.textContent;
    refreshModelPricesButton.textContent = 'Отримуємо список…';
    try {
        renderPriceComparison(await WorkbenchApi.refreshModelPrices());
    } catch (error) {
        priceRefreshPanel.hidden = false;
        priceRefreshPanel.replaceChildren();
        const failure = document.createElement('p');
        failure.className = 'form-error';
        failure.setAttribute('role', 'alert');
        failure.textContent = `Не вдалося оновити ціни: ${error.message}`;
        priceRefreshPanel.append(failure);
    } finally {
        refreshModelPricesButton.disabled = false;
        refreshModelPricesButton.textContent = previous;
    }
});

restoreModelPricesButton.addEventListener('click', async () => {
    restoreModelPricesButton.disabled = true;
    try {
        const result = await WorkbenchApi.restoreDefaultModelPrices();
        await loadModelPriceRows();
        showModelPricesStatus(result, result.restored.length ? `відновлено: ${result.restored.join(', ')}` : 'нічого відновлювати: усі стартові моделі на місці');
    } catch (error) {
        modelPricesStatus.textContent = `Не вдалося відновити: ${error.message}`;
    } finally {
        restoreModelPricesButton.disabled = false;
    }
});

// --- Usage by day ("По днях" and Settings → "Витрати") ---------------------------------------------

const USAGE_DAY_RANGES = [7, 30, 90];

function describeDailyCost(group) {
    if (!group.calls) return '—';
    const usd = formatUsd(group.costUsd);
    if (usd === null) return `ціну не задано (${group.unpricedCalls} ${pluralize(group.unpricedCalls, 'виклик', 'виклики', 'викликів')})`;
    if (group.unpricedCalls > 0) {
        return `≥ ${usd} + ${group.unpricedCalls} ${pluralize(group.unpricedCalls, 'виклик', 'виклики', 'викликів')} без ціни`;
    }
    return group.estimated ? `≈ ${usd} (оцінка)` : `≈ ${usd}`;
}

function describeBreakdown(items, labelOf) {
    return items.map((item) => `${labelOf(item)}: ${item.calls} · ${describeDailyCost(item)}`).join('; ');
}

function svgElement(name, attributes = {}) {
    const element = document.createElementNS('http://www.w3.org/2000/svg', name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
}

// Bars of ≈$ per day. A day with calls that could not be priced fully is drawn hatched, a day
// with no price at all as a small marker. The table below carries the same numbers.
function renderDailyChart(container, report) {
    container.replaceChildren();
    const rows = report.rows;
    const maxCost = Math.max(0, ...rows.map((row) => row.costUsd || 0));
    const width = 640;
    const height = 170;
    const left = 44;
    const bottom = 24;
    const top = 12;
    const plotHeight = height - bottom - top;
    const step = (width - left - 8) / rows.length;
    const barWidth = Math.max(2, step * 0.7);
    const svg = svgElement('svg', { viewBox: `0 0 ${width} ${height}`, class: 'daily-chart-svg', role: 'img', preserveAspectRatio: 'xMidYMid meet' });
    svg.setAttribute('aria-label', `Витрати за днями, ${report.from} — ${report.to}. Найбільше за день: ${maxCost > 0 ? formatUsd(maxCost) : 'немає даних із цінами'}. Ті самі числа в таблиці нижче.`);
    svg.append(svgElement('line', { x1: left, y1: top + plotHeight, x2: width - 4, y2: top + plotHeight, class: 'daily-chart-axis' }));
    const maxLabel = svgElement('text', { x: left - 6, y: top + 8, class: 'daily-chart-label', 'text-anchor': 'end' });
    maxLabel.textContent = maxCost > 0 ? formatUsd(maxCost) : '';
    const zeroLabel = svgElement('text', { x: left - 6, y: top + plotHeight, class: 'daily-chart-label', 'text-anchor': 'end' });
    zeroLabel.textContent = '$0';
    svg.append(maxLabel, zeroLabel);
    rows.forEach((row, index) => {
        const x = left + index * step + (step - barWidth) / 2;
        const title = svgElement('title');
        title.textContent = `${row.date}: ${describeDailyCost(row)} · ${row.calls} ${pluralize(row.calls, 'виклик', 'виклики', 'викликів')}`;
        let bar;
        if (row.costUsd === null && row.calls > 0) {
            bar = svgElement('rect', { x, y: top + plotHeight - 6, width: barWidth, height: 6, class: 'daily-bar daily-bar-unpriced' });
        } else if (row.costUsd > 0 && maxCost > 0) {
            const barHeight = Math.max(2, (row.costUsd / maxCost) * plotHeight);
            bar = svgElement('rect', { x, y: top + plotHeight - barHeight, width: barWidth, height: barHeight,
                class: `daily-bar${row.incomplete ? ' daily-bar-incomplete' : ''}` });
        } else {
            return;
        }
        bar.dataset.date = row.date;
        bar.append(title);
        svg.append(bar);
    });
    [0, Math.floor((rows.length - 1) / 2), rows.length - 1].forEach((index, position) => {
        const label = svgElement('text', { x: left + index * step + step / 2, y: height - 6, class: 'daily-chart-label',
            'text-anchor': position === 0 ? 'start' : (position === 2 ? 'end' : 'middle') });
        label.textContent = rows[index].date.slice(5);
        svg.append(label);
    });
    container.append(svg);
    if (maxCost === 0) {
        const note = document.createElement('p');
        note.className = 'muted';
        note.textContent = 'У цьому діапазоні немає викликів із цінами: графік порожній.';
        container.append(note);
    }
}

function renderDailyTable(container, report) {
    container.replaceChildren();
    const active = report.rows.filter((row) => row.calls > 0).reverse();
    if (!active.length) {
        const empty = document.createElement('p');
        empty.className = 'muted';
        empty.textContent = 'У цьому діапазоні немає записаних викликів.';
        container.append(empty);
        return;
    }
    const wrapper = document.createElement('div');
    wrapper.className = 'project-cost-table-wrap';
    const table = document.createElement('table');
    table.className = 'project-cost-table daily-usage-table';
    const head = document.createElement('thead');
    const headRow = document.createElement('tr');
    ['Дата', '≈ $', 'Вхід', 'Вихід', 'Кеш', 'Виклики'].forEach((text) => {
        const cell = document.createElement('th');
        cell.scope = 'col';
        cell.textContent = text;
        headRow.append(cell);
    });
    head.append(headRow);
    const body = document.createElement('tbody');
    active.forEach((row) => {
        const tr = document.createElement('tr');
        tr.dataset.date = row.date;
        if (row.incomplete) tr.classList.add('daily-incomplete');
        const dateCell = document.createElement('td');
        const toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'text-btn daily-toggle';
        toggle.setAttribute('aria-expanded', 'false');
        toggle.textContent = row.date;
        dateCell.append(toggle);
        const values = [describeDailyCost(row), formatTokenCount(row.inputTokens), formatTokenCount(row.outputTokens),
            formatTokenCount(row.cacheReadTokens + row.cacheWriteTokens), row.calls];
        tr.append(dateCell);
        values.forEach((text, index) => {
            const cell = document.createElement('td');
            cell.textContent = String(text);
            cell.className = index === 0 ? 'daily-cost' : 'num';
            tr.append(cell);
        });
        const detail = document.createElement('tr');
        detail.className = 'daily-detail';
        detail.hidden = true;
        const detailCell = document.createElement('td');
        detailCell.colSpan = 6;
        detailCell.textContent = `Рушії — ${describeBreakdown(row.byEngine, (item) => item.engine)}. Типи — ${describeBreakdown(row.byKind, (item) => USAGE_KIND_LABELS[item.kind] || item.kind)}.`;
        detail.append(detailCell);
        toggle.addEventListener('click', () => {
            detail.hidden = !detail.hidden;
            toggle.setAttribute('aria-expanded', detail.hidden ? 'false' : 'true');
        });
        body.append(tr, detail);
    });
    table.append(head, body);
    wrapper.append(table);
    container.append(wrapper);
}

// One reusable view: range 7/30/90, summary, chart, table, breakdowns and the CSV link.
function createDailyUsageView({ withProjectSelect = false, projectId = null } = {}) {
    const root = document.createElement('div');
    root.className = 'daily-usage';
    const state = { days: 7, projectId };

    const controls = document.createElement('div');
    controls.className = 'daily-usage-controls';
    const range = document.createElement('div');
    range.className = 'daily-usage-range';
    range.setAttribute('role', 'group');
    range.setAttribute('aria-label', 'Діапазон');
    const buttons = USAGE_DAY_RANGES.map((days) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'daily-range-button';
        button.dataset.days = String(days);
        button.textContent = `${days} днів`;
        button.addEventListener('click', () => { state.days = days; void view.load(); });
        range.append(button);
        return button;
    });
    const exportLink = document.createElement('a');
    exportLink.className = 'secondary-btn daily-export';
    exportLink.textContent = 'Експорт CSV';
    exportLink.setAttribute('download', '');
    controls.append(range, exportLink);

    const note = document.createElement('p');
    note.className = 'muted daily-usage-note';
    const summary = document.createElement('p');
    summary.className = 'daily-usage-summary';
    summary.setAttribute('role', 'status');
    const chart = document.createElement('div');
    chart.className = 'daily-chart';
    const table = document.createElement('div');
    const breakdown = document.createElement('div');
    breakdown.className = 'daily-breakdown';
    root.append(controls, note, summary, chart, table, breakdown);

    const view = {
        root,
        setProject(id) { state.projectId = id || null; },
        async load() {
            buttons.forEach((button) => button.setAttribute('aria-pressed', button.dataset.days === String(state.days) ? 'true' : 'false'));
            exportLink.href = WorkbenchApi.usageExportUrl(state.days, state.projectId);
            summary.textContent = 'Завантажуємо…';
            try {
                const report = await WorkbenchApi.getDailyUsage(state.days, state.projectId);
                note.textContent = `Дні рахуються за часовим поясом ${report.timezone}; у базі час зберігається в UTC. ${report.from} — ${report.to}.`;
                const total = report.total;
                let text = `Разом: ${describeDailyCost(total.calls ? total : { ...total, calls: 1, costUsd: 0 })} · ${total.calls} ${pluralize(total.calls, 'виклик', 'виклики', 'викликів')} · ${formatTokenCount(total.tokens)} токенів`;
                if (total.incomplete) {
                    text += ` · ⚠ ${total.unpricedCalls} ${pluralize(total.unpricedCalls, 'виклик', 'виклики', 'викликів')} без ціни — сума неповна (${report.unpricedModels.join(', ')})`;
                }
                summary.textContent = total.calls ? text : 'У цьому діапазоні немає записаних викликів.';
                summary.classList.toggle('daily-usage-incomplete', Boolean(total.incomplete));
                renderDailyChart(chart, report);
                renderDailyTable(table, report);
                breakdown.replaceChildren();
                if (total.calls) {
                    [['За рушіями', report.byEngine, (item) => item.engine], ['За типом викликів', report.byKind, (item) => USAGE_KIND_LABELS[item.kind] || item.kind]].forEach(([title, items, labelOf]) => {
                        const heading = document.createElement('h3');
                        heading.textContent = title;
                        breakdown.append(heading, costTable(
                            [title.replace('За ', ''), 'Виклики', 'Токени', 'Вартість'],
                            items.map((item) => [labelOf(item), item.calls, formatTokenCount(item.tokens), describeDailyCost(item)]),
                        ));
                    });
                }
            } catch (error) {
                summary.textContent = `Не вдалося завантажити витрати: ${error.message}`;
                chart.replaceChildren();
                table.replaceChildren();
                breakdown.replaceChildren();
            }
        },
    };
    return view;
}

// --- «Вартість» tabs --------------------------------------------------------------------------

const projectCostTabTotal = document.querySelector('#project-cost-tab-total');
const projectCostTabDays = document.querySelector('#project-cost-tab-days');
const projectCostDaysPanel = document.querySelector('#project-cost-days');
const projectCostTotalPanel = document.querySelector('#project-cost-total-panel');
let projectCostDaysView = null;

function selectProjectCostTab(which) {
    const days = which === 'days';
    projectCostTabTotal.setAttribute('aria-selected', days ? 'false' : 'true');
    projectCostTabDays.setAttribute('aria-selected', days ? 'true' : 'false');
    projectCostTotalPanel.hidden = days;
    projectCostDaysPanel.hidden = !days;
    if (days && currentProject) {
        if (!projectCostDaysView) {
            projectCostDaysView = createDailyUsageView({ projectId: currentProject.projectId });
            projectCostDaysPanel.append(projectCostDaysView.root);
        }
        projectCostDaysView.setProject(currentProject.projectId);
        void projectCostDaysView.load();
    }
}

projectCostTabTotal.addEventListener('click', () => selectProjectCostTab('total'));
projectCostTabDays.addEventListener('click', () => selectProjectCostTab('days'));

// --- Settings → «Витрати» ---------------------------------------------------------------------

const usageSettingsProject = document.querySelector('#usage-settings-project');
const usageSettingsTimezone = document.querySelector('#usage-settings-timezone');
const usageSettingsStatus = document.querySelector('#usage-settings-status');
let usageSettingsView = null;

async function initUsageSettings() {
    if (!usageSettingsView) {
        usageSettingsView = createDailyUsageView({ withProjectSelect: true });
        document.querySelector('#usage-settings-view').append(usageSettingsView.root);
    }
    const chosen = usageSettingsProject.value;
    usageSettingsProject.replaceChildren(new Option('Усі проєкти', ''));
    mockProjects.forEach((project) => usageSettingsProject.append(new Option(project.title, project.projectId)));
    usageSettingsProject.value = mockProjects.some((project) => project.projectId === chosen) ? chosen : '';
    usageSettingsView.setProject(usageSettingsProject.value);
    try {
        usageSettingsTimezone.value = (await WorkbenchApi.getAppSettings()).timezone;
    } catch (error) {
        usageSettingsStatus.textContent = `Не вдалося прочитати часовий пояс: ${error.message}`;
    }
    await usageSettingsView.load();
}

usageSettingsProject.addEventListener('change', () => {
    usageSettingsView?.setProject(usageSettingsProject.value);
    void usageSettingsView?.load();
});

document.querySelector('#usage-settings-save-timezone').addEventListener('click', async () => {
    usageSettingsStatus.textContent = '';
    try {
        const saved = await WorkbenchApi.saveAppSettings({ timezone: usageSettingsTimezone.value.trim() });
        usageSettingsTimezone.value = saved.timezone;
        usageSettingsStatus.textContent = `Часовий пояс збережено: ${saved.timezone}. Дні перераховано, дані не змінено.`;
        await usageSettingsView?.load();
        if (projectCostDaysView && !projectCostDaysPanel.hidden) await projectCostDaysView.load();
    } catch (error) {
        usageSettingsStatus.textContent = error.message;
    }
});

// --- Whole-chapter choice: «Обрати для файлу весь розділ з…» --------------------------------------
//
// DOM lookups happen inside the functions (not in top-level consts) because updateTranslationButtons()
// calls refreshChapterViewControls() and may run before this block has been evaluated.

const BULK_ENGINES = [['claude', 'Claude'], ['openai', 'GPT'], ['gemini', 'Gemini'], ['deepl', 'DeepL'], ['current', 'Поточний']];
const bulkEl = (selector) => document.querySelector(selector);

function currentChapterParagraphs() {
    const chapter = loadedChapters[selectedChapterIndex];
    return (chapter?.elements || []).filter((element) => element.type === 'paragraph' && element.paragraphId);
}

// engine -> how many paragraphs of the open chapter have a variant of it
function chapterEngineCounts() {
    const counts = {};
    currentChapterParagraphs().forEach((paragraph) => {
        new Set((paragraph.translationVariants || []).map((variant) => variant.engine)).forEach((engine) => {
            counts[engine] = (counts[engine] || 0) + 1;
        });
    });
    return counts;
}

function bulkSummaryText(summary) {
    let text = `Змінено ${summary.changed}, без варіанта ${summary.withoutVariant}, пропущено вичитаних ${summary.skippedReviewed}`;
    if (summary.alreadySelected > 0) text += `, вже обрано ${summary.alreadySelected}`;
    return text;
}

function showBulkStatus(text, summary = null) {
    const status = bulkEl('#chapter-bulk-status');
    let full = text;
    if (summary?.movedFootnotes > 0) {
        full += `. Маркери виносок перенесено в кінець у ${summary.movedFootnotes} ${pluralize(summary.movedFootnotes, 'абзаці', 'абзацах', 'абзацах')} — перемістіть їх у «Вручну»`;
    }
    status.textContent = full;
    status.hidden = !full;
}

// Saving first is offered whenever the chapter has unsaved edits: the bulk action replaces the
// chosen text, so unsaved edits would be lost. Declining cancels the action.
async function ensureChapterSavedBefore(what) {
    if (!isTranslationDirty(selectedChapterIndex)) return true;
    if (!window.confirm(`У розділі є незбережені зміни. Зберегти розділ перед тим, як ${what}?`)) return false;
    return saveCurrentTranslation();
}

// Take the server's view of every paragraph the bulk action touched. Each paragraph then shows the
// variant that is in the file now (its ✓ tab), like after a single «У файл» or its undo.
function applyBulkParagraphs(paragraphs) {
    (paragraphs || []).forEach((payload) => {
        const context = variantContexts.get(payload.paragraphId);
        if (!context) return;
        const chosen = (payload.translationVariants || []).find((variant) => variant.variantId === payload.selectedVariantId);
        if (chosen && chosen.engine !== 'manual') context.activeKey = chosen.variantId;
        applyParagraphFromServer(context.paragraph, payload);
    });
}

let bulkPreviewToken = 0;
let bulkLastPreview = null;

function selectedBulkEngine() {
    return bulkEl('#bulk-select-engines input[name="bulk-engine"]:checked')?.value || null;
}

function renderBulkPreview(result) {
    const preview = bulkEl('#bulk-select-preview');
    preview.replaceChildren();
    const { summary } = result;
    const line = document.createElement('p');
    line.className = 'bulk-select-summary';
    line.textContent = `Буде: ${bulkSummaryText(summary).replace('Змінено', 'змінено')}.`;
    preview.append(line);
    if (summary.reviewedUnmarked > 0) {
        const warning = document.createElement('p');
        warning.className = 'bulk-select-warning';
        warning.textContent = `⚠ З ${summary.reviewedUnmarked} ${pluralize(summary.reviewedUnmarked, 'вичитаного абзацу', 'вичитаних абзаців', 'вичитаних абзаців')} буде знято «Перевірено» (текст зміниться). Перед виконанням буде одне підтвердження.`;
        preview.append(warning);
    }
    if (result.examples.length) {
        const heading = document.createElement('p');
        heading.className = 'muted';
        heading.textContent = `Приклади (${result.examples.length} з ${summary.changed}):`;
        const list = document.createElement('ul');
        list.className = 'bulk-select-examples';
        result.examples.forEach((example) => {
            const item = document.createElement('li');
            const number = document.createElement('strong');
            number.textContent = `№${example.number}${example.reviewed ? ' ✓' : ''}: `;
            const before = document.createElement('span');
            before.className = 'bulk-example-before';
            before.textContent = example.before || '(порожньо)';
            const arrow = document.createTextNode(' → ');
            const after = document.createElement('span');
            after.className = 'bulk-example-after';
            after.textContent = example.after;
            item.append(number, before, arrow, after);
            list.append(item);
        });
        preview.append(heading, list);
    } else {
        const none = document.createElement('p');
        none.className = 'muted';
        none.textContent = 'Нічого міняти: усе вже обране, пропущене або без такого варіанта.';
        preview.append(none);
    }
}

async function refreshBulkPreview() {
    const applyButton = bulkEl('#apply-bulk-select');
    const error = bulkEl('#bulk-select-error');
    const engine = selectedBulkEngine();
    error.hidden = true;
    bulkLastPreview = null;
    applyButton.disabled = true;
    if (!engine) return;
    const token = ++bulkPreviewToken;
    const chapterId = loadedChapters[selectedChapterIndex]?.chapterId;
    bulkEl('#bulk-select-preview').textContent = 'Рахуємо…';
    try {
        const result = await WorkbenchApi.selectChapterVariants(chapterId, engine, bulkEl('#bulk-select-reviewed').checked, true);
        if (token !== bulkPreviewToken) return; // a newer choice is already being counted
        bulkLastPreview = result;
        renderBulkPreview(result);
        applyButton.disabled = result.summary.changed === 0;
    } catch (failure) {
        if (token !== bulkPreviewToken) return;
        bulkEl('#bulk-select-preview').textContent = '';
        error.textContent = `Не вдалося порахувати: ${failure.message}`;
        error.hidden = false;
    }
}

async function openBulkSelectDialog() {
    if (selectedChapterIndex === null || !loadedChapters[selectedChapterIndex]?.chapterId) return;
    const counts = chapterEngineCounts();
    const engines = BULK_ENGINES.filter(([engine]) => counts[engine] > 0);
    if (!engines.length) {
        window.alert('У цьому розділі ще немає варіантів перекладу, з яких можна обрати.');
        return;
    }
    if (!(await ensureChapterSavedBefore('обирати варіанти для всього розділу'))) return;
    const container = bulkEl('#bulk-select-engines');
    container.replaceChildren();
    const preferred = engines.find(([engine]) => engine === projectTranslationProvider())?.[0] || engines[0][0];
    engines.forEach(([engine, label]) => {
        const row = document.createElement('label');
        row.className = 'bulk-select-engine';
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'bulk-engine';
        radio.value = engine;
        radio.checked = engine === preferred;
        radio.addEventListener('change', () => { void refreshBulkPreview(); });
        const text = document.createElement('span');
        text.textContent = `${label} · ${counts[engine]} ${pluralize(counts[engine], 'абзац', 'абзаци', 'абзаців')} з варіантом`;
        row.append(radio, text);
        container.append(row);
    });
    bulkEl('#bulk-select-reviewed').checked = false;
    bulkEl('#bulk-select-error').hidden = true;
    bulkEl('#bulk-select-dialog').hidden = false;
    bulkEl('#bulk-select-engines input:checked')?.focus();
    void refreshBulkPreview();
}

function closeBulkSelectDialog() {
    bulkEl('#bulk-select-dialog').hidden = true;
    bulkPreviewToken += 1;
}

async function applyBulkSelection(event) {
    event.preventDefault();
    const engine = selectedBulkEngine();
    const state = translationStates.get(selectedChapterIndex);
    const chapterId = loadedChapters[selectedChapterIndex]?.chapterId;
    if (!engine || !state || !chapterId || !bulkLastPreview || bulkLastPreview.summary.changed === 0) return;
    const includeReviewed = bulkEl('#bulk-select-reviewed').checked;
    if (includeReviewed && bulkLastPreview.summary.reviewedUnmarked > 0
        && !window.confirm(`З ${bulkLastPreview.summary.reviewedUnmarked} ${pluralize(bulkLastPreview.summary.reviewedUnmarked, 'вичитаного абзацу', 'вичитаних абзаців', 'вичитаних абзаців')} буде знято «Перевірено». Продовжити?`)) {
        return;
    }
    const applyButton = bulkEl('#apply-bulk-select');
    applyButton.disabled = true;
    state.serverActionRunning = true;
    try {
        const before = cloneParagraphDrafts(state.draft);
        const result = await WorkbenchApi.selectChapterVariants(chapterId, engine, includeReviewed, false);
        applyBulkParagraphs(result.paragraphs);
        if (result.undo.items.length) {
            // One step for the whole action: undo restores every changed paragraph from the server.
            before.bulkAction = { chapterId, engine, items: result.undo.items };
            state.undo.push(before);
            state.redo = [];
        }
        showBulkStatus(`${bulkSummaryText(result.summary)}.`, result.summary);
        closeBulkSelectDialog();
    } catch (failure) {
        bulkEl('#bulk-select-error').textContent = `Не вдалося обрати варіанти: ${failure.message}`;
        bulkEl('#bulk-select-error').hidden = false;
        applyButton.disabled = false;
    } finally {
        state.serverActionRunning = false;
        updateTranslationButtons();
    }
}

// Undo / redo of the whole action in one step (the server restores or re-applies every paragraph).
async function runBulkUndoRedo(state, direction) {
    const entry = (direction === 'undo' ? state.undo : state.redo)[(direction === 'undo' ? state.undo : state.redo).length - 1];
    const bulk = entry.bulkAction;
    if (isTranslationDirty(selectedChapterIndex)) {
        const verb = direction === 'undo' ? 'скасувати масовий вибір' : 'повторити масовий вибір';
        if (!window.confirm(`У розділі є незбережені зміни. Зберегти розділ перед тим, як ${verb}?`)) return;
        if (!(await saveCurrentTranslation())) return;
        // saving empties the undo/redo stacks: put the bulk step back so it can still be taken
        (direction === 'undo' ? state.undo : state.redo).push(entry);
    }
    state.serverActionRunning = true;
    undoTranslationButton.disabled = true;
    redoTranslationButton.disabled = true;
    try {
        const isReplace = bulk.kind === 'replace';
        let data;
        if (isReplace) {
            data = direction === 'undo'
                ? await WorkbenchApi.restoreReplacement(bulk.projectId, { chapterId: bulk.chapterId, items: bulk.items.map(({ paragraphId, previous }) => ({ paragraphId, previous })) })
                : await WorkbenchApi.applyReplacement(bulk.projectId, { chapterId: bulk.chapterId, items: bulk.items.map(({ paragraphId, text, variants }) => ({ paragraphId, text, variants })) });
        } else {
            data = direction === 'undo'
                ? await WorkbenchApi.restoreChapterSelection(bulk.chapterId, bulk.items.map(({ paragraphId, previous }) => ({ paragraphId, previous })))
                : await WorkbenchApi.applyChapterSelection(bulk.chapterId, bulk.items.map(({ paragraphId, variantId }) => ({ paragraphId, variantId })));
        }
        const snapshot = cloneParagraphDrafts(state.draft);
        snapshot.bulkAction = direction === 'undo' ? { ...bulk } : { ...bulk, items: data.undo.items };
        (direction === 'undo' ? state.undo : state.redo).pop();
        (direction === 'undo' ? state.redo : state.undo).push(snapshot);
        applyBulkParagraphs(data.paragraphs);
        if (bulk.kind === 'replace') {
            await refreshChaptersByIds(data.chapterIds || []);
            if (replaceModeOn && !searchDialog.hidden) void runReplaceFind({ keepIndex: true });
        }
        const what = bulk.kind === 'replace' ? 'Заміну' : 'Масовий вибір';
        showBulkStatus(direction === 'undo'
            ? `${what} скасовано: відновлено ${data.restored} ${pluralize(data.restored, 'абзац', 'абзаци', 'абзаців')}.`
            : `${what} повторено: ${data.applied} ${pluralize(data.applied, 'абзац', 'абзаци', 'абзаців')}.`);
    } catch (error) {
        window.alert(`Не вдалося ${direction === 'undo' ? 'скасувати' : 'повторити'} масовий вибір: ${error.message}`);
    } finally {
        state.serverActionRunning = false;
        updateTranslationButtons();
    }
}

// --- «Показувати весь розділ у варіанті X» (view only) -----------------------------------------------

let chapterViewSignature = '';

function chapterViewLabel(engine) {
    return BULK_ENGINES.find(([id]) => id === engine)?.[1] || engine;
}

function refreshChapterViewControls(force = false) {
    const select = bulkEl('#chapter-view-select');
    const bulkButton = bulkEl('#bulk-select-button');
    if (!select || !bulkButton) return;
    const counts = selectedChapterIndex === null ? {} : chapterEngineCounts();
    const state = translationStates.get(selectedChapterIndex);
    const viewEngine = state?.viewEngine || '';
    const signature = `${selectedChapterIndex}|${BULK_ENGINES.map(([engine]) => counts[engine] || 0).join(',')}|${viewEngine}`;
    bulkButton.disabled = !BULK_ENGINES.some(([engine]) => counts[engine] > 0);
    if (signature === chapterViewSignature && !force) return;
    chapterViewSignature = signature;
    select.replaceChildren(new Option('Як обрано для файлу', ''));
    BULK_ENGINES.filter(([engine]) => counts[engine] > 0).forEach(([engine, label]) => {
        select.append(new Option(`${label} — найновіша версія ${label}`, engine));
    });
    select.value = viewEngine && counts[viewEngine] > 0 ? viewEngine : '';
    select.disabled = compareMode; // «Усі рушії» shows every engine in the panels
    bulkEl('#chapter-view-hint').textContent = select.value
        ? `Показано найновішу версію ${chapterViewLabel(select.value)}; у файлі нічого не змінено. Абзаци без такого варіанта показують обране; позначка «≠» — у файлі інша версія.`
        : '';
}

function applyChapterViewMode(engine) {
    const state = translationStates.get(selectedChapterIndex);
    if (!state) return;
    state.viewEngine = engine || null;
    currentChapterParagraphs().forEach((paragraph) => {
        const context = variantContexts.get(paragraph.paragraphId);
        if (!context) return;
        const latest = engine ? latestVariantOfEngine(context.paragraph.translationVariants, engine) : null;
        if (latest) {
            variantTabOverrides.set(paragraph.paragraphId, latest.variantId);
            renderVariantBar(context, latest.variantId);
        } else {
            variantTabOverrides.delete(paragraph.paragraphId);
            renderVariantBar(context, defaultVariantTab(context.paragraph, state.draft[context.index]));
        }
    });
    refreshChapterViewControls(true);
    scheduleParagraphHeightsSync();
}

// After a chapter has been drawn (rows are new): show it in the mode remembered for this chapter.
function reapplyChapterViewMode() {
    const state = translationStates.get(selectedChapterIndex);
    if (state?.viewEngine && !compareMode) applyChapterViewMode(state.viewEngine);
    refreshChapterViewControls(true);
}

bulkEl('#bulk-select-button').addEventListener('click', () => { void openBulkSelectDialog(); });
bulkEl('#close-bulk-select').addEventListener('click', closeBulkSelectDialog);
bulkEl('#cancel-bulk-select').addEventListener('click', closeBulkSelectDialog);
bulkEl('#bulk-select-reviewed').addEventListener('change', () => { void refreshBulkPreview(); });
bulkEl('#bulk-select-form').addEventListener('submit', (event) => { void applyBulkSelection(event); });
bulkEl('#chapter-view-select').addEventListener('change', (event) => applyChapterViewMode(event.target.value));
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !bulkEl('#bulk-select-dialog').hidden) closeBulkSelectDialog();
});

// --- Translation queue: several chapters in the background (server-side job) --------------------------

const QUEUE_STATUS_LABELS = {
    running: 'Іде переклад', paused: 'На паузі', completed: 'Завершено', stopped: 'Зупинено',
    budget_reached: 'Зупинено: досягнуто межі', failed: 'Помилка черги',
};
const QUEUE_POLL_MS = 2000;
let queueState = null;
let queuePollTimer = null;
let queueEstimateToken = 0;
let queueLastEstimate = null;
let queueSyncedBatches = -1;
let queueSyncing = false;

function queueEl(selector) {
    return document.querySelector(selector);
}

function queueSelection() {
    const mode = queueEl('input[name="queue-mode"]:checked')?.value || 'untranslated';
    const selection = { mode, includeTranslated: queueEl('#queue-include-translated').checked };
    if (mode === 'range') {
        selection.fromChapter = Number(queueEl('#queue-from').value);
        selection.toChapter = Number(queueEl('#queue-to').value);
    }
    return selection;
}

function queueDurationText(seconds) {
    const total = Math.round(seconds || 0);
    const minutes = Math.floor(total / 60);
    return minutes ? `${minutes} хв ${total % 60} с` : `${total} с`;
}

function queueEstimateMethodText(method) {
    return {
        history: 'за середньою вартістю символа цього рушія з обліку',
        history_legacy: 'за середньою вартістю символа з обліку (старі записи, приблизно)',
        tokens: 'за кількістю токенів і цінами моделі (історії ще нема)',
    }[method] || '';
}

function renderQueueEstimate(estimate) {
    const box = queueEl('#queue-estimate');
    const skipped = estimate.skipped || {};
    const lines = [];
    const head = document.createElement('p');
    head.className = 'bulk-select-summary';
    head.textContent = `Буде перекладено: ${estimate.totals.chapters} ${pluralize(estimate.totals.chapters, 'розділ', 'розділи', 'розділів')}, `
        + `${estimate.totals.paragraphs} ${pluralize(estimate.totals.paragraphs, 'абзац', 'абзаци', 'абзаців')}, `
        + `${estimate.totals.chars.toLocaleString('uk-UA')} символів, ${estimate.totals.batches} ${pluralize(estimate.totals.batches, 'батч', 'батчі', 'батчів')}.`;
    lines.push(head);
    const cost = document.createElement('p');
    if (!estimate.priced) {
        cost.textContent = `Для моделі ${estimate.model} не задано ціну: вартість не оцінити.`;
    } else if (estimate.estimate.usd === null) {
        cost.textContent = 'Оцінка вартості недоступна.';
    } else {
        cost.textContent = `Оцінка вартості: ≈ ${formatUsd(estimate.estimate.usd)} — ${queueEstimateMethodText(estimate.estimate.method)}.`;
    }
    lines.push(cost);
    const skips = [];
    if (skipped.excludedChapters) skips.push(`розділів «Не експортувати»: ${skipped.excludedChapters}`);
    if (skipped.reviewedParagraphs) skips.push(`вичитаних абзаців: ${skipped.reviewedParagraphs}`);
    if (skipped.translatedParagraphs) skips.push(`абзаців з перекладом: ${skipped.translatedParagraphs}`);
    if (skips.length) {
        const skipLine = document.createElement('p');
        skipLine.className = 'muted';
        skipLine.textContent = `Пропущено: ${skips.join('; ')}.`;
        lines.push(skipLine);
    }
    box.replaceChildren(...lines);
    const warning = queueEl('#queue-warning');
    const over = estimate.priced && estimate.estimate.usd !== null && estimate.estimate.usd > estimate.estimate.warnOver;
    warning.textContent = over ? `Увага: оцінка перевищує $${estimate.estimate.warnOver}. Перевір баланс і задай «Максимум $».` : '';
    warning.hidden = !over;
    queueEl('#queue-unpriced-row').hidden = estimate.priced;
    queueEl('#queue-budget').disabled = !estimate.priced;
    if (!estimate.priced) queueEl('#queue-budget').value = '';
}

function refreshQueueStartButton() {
    const estimate = queueLastEstimate;
    const unpricedOk = !estimate || estimate.priced || queueEl('#queue-confirm-unpriced').checked;
    queueEl('#start-queue').disabled = !(estimate && estimate.totals.paragraphs > 0 && unpricedOk);
}

async function refreshQueueEstimate() {
    const token = ++queueEstimateToken;
    queueLastEstimate = null;
    refreshQueueStartButton();
    queueEl('#queue-error').hidden = true;
    queueEl('#queue-estimate').textContent = 'Рахуємо…';
    queueEl('#queue-from').disabled = queueEl('#queue-to').disabled = queueSelection().mode !== 'range';
    try {
        const estimate = await WorkbenchApi.estimateTranslationQueue(currentProject.projectId, queueSelection());
        if (token !== queueEstimateToken) return;
        queueLastEstimate = estimate;
        renderQueueEstimate(estimate);
        if (!estimate.totals.paragraphs) queueEl('#queue-estimate').append(Object.assign(document.createElement('p'), { textContent: 'За цими умовами нема що перекладати.' }));
    } catch (error) {
        if (token !== queueEstimateToken) return;
        queueEl('#queue-estimate').textContent = '';
        queueEl('#queue-error').textContent = error.message;
        queueEl('#queue-error').hidden = false;
    }
    refreshQueueStartButton();
}

async function openQueueDialog() {
    if (!currentProject) return;
    if (projectTranslationProvider() === 'deepl') {
        window.alert('Черга працює лише для Claude, GPT і Gemini. DeepL перекладає по одному розділу кнопкою «Перекласти розділ». Щоб скористатися чергою, обери LLM-рушій у ⚙ налаштуваннях перекладу.');
        return;
    }
    if (queueState?.active) {
        window.alert('У проєкті вже є активна черга перекладу — дочекайся її завершення або зупини.');
        return;
    }
    const chapters = loadedChapters.map((chapter, index) => ({ number: index + 1, title: chapter.title || chapter.name || '' }));
    for (const select of [queueEl('#queue-from'), queueEl('#queue-to')]) {
        select.replaceChildren(...chapters.map(({ number, title }) => Object.assign(document.createElement('option'), {
            value: String(number), textContent: `${String(number).padStart(2, '0')} · ${title}`.slice(0, 80),
        })));
    }
    queueEl('#queue-to').value = String(chapters.length);
    queueEl('#queue-engine-line').textContent = `Рушій і модель беруться з поточного вибору проєкту: ${TRANSLATION_PROVIDER_LABELS[projectTranslationProvider()]}.`;
    queueEl('input[name="queue-mode"][value="untranslated"]').checked = true;
    queueEl('#queue-include-translated').checked = false;
    queueEl('#queue-budget').value = '';
    queueEl('#queue-confirm-unpriced').checked = false;
    queueEl('#queue-dialog').hidden = false;
    queueEl('input[name="queue-mode"]:checked').focus();
    void refreshQueueEstimate();
}

function closeQueueDialog() {
    queueEl('#queue-dialog').hidden = true;
    queueEstimateToken += 1;
}

async function startQueue(event) {
    event.preventDefault();
    if (!queueLastEstimate || queueEl('#start-queue').disabled) return;
    const data = queueSelection();
    const budgetText = queueEl('#queue-budget').value.trim();
    if (budgetText) data.budgetUsd = Number(budgetText);
    if (!queueLastEstimate.priced) data.confirmUnpriced = queueEl('#queue-confirm-unpriced').checked;
    const button = queueEl('#start-queue');
    button.disabled = true;
    try {
        queueSyncedBatches = -1;
        showQueueState(await WorkbenchApi.createTranslationQueue(currentProject.projectId, data));
        closeQueueDialog();
    } catch (error) {
        queueEl('#queue-error').textContent = error.message;
        queueEl('#queue-error').hidden = false;
        button.disabled = false;
    }
}

function showQueueState(state) {
    queueState = state;
    const panel = queueEl('#queue-panel');
    if (!state) {
        panel.hidden = true;
        window.clearTimeout(queuePollTimer);
        return;
    }
    panel.hidden = false;
    const progress = state.progress;
    const summary = state.summary;
    const cost = `≈ ${formatUsd(state.spentUsd) || '$0.00'}${state.costIncomplete ? ' + ціну не задано для частини' : ''}`;
    const budget = state.budgetUsd ? ` / межа ${formatUsd(state.budgetUsd)}` : '';
    queueEl('#queue-panel-title').textContent = `Черга перекладу · ${QUEUE_STATUS_LABELS[state.status] || state.status}`;
    queueEl('#queue-progress-fill').style.width = `${progress.batchesAll ? Math.round(100 * progress.batchesDone / progress.batchesAll) : 100}%`;
    if (state.active) {
        queueEl('#queue-panel-line').textContent = `розділ ${Math.min(progress.chapterPosition + 1, progress.chaptersTotal)}/${progress.chaptersTotal}`
            + ` · батч ${progress.batch ?? '–'}/${progress.batchesTotal ?? '–'} · ${cost}${budget}`
            + (progress.chapterTitle ? ` · ${progress.chapterTitle}` : '');
    } else {
        queueEl('#queue-panel-line').textContent = `${cost}${budget} · ${queueDurationText(summary.seconds)}`;
    }
    const chapters = summary.chapters;
    const finishedText = state.active ? '' : `Розділів: перекладено ${chapters.done}, частково ${chapters.partial}, з помилкою ${chapters.error}, пропущено ${chapters.skipped}. `
        + `Абзаців: ${summary.paragraphs}. Вартість: ${cost}. Час: ${queueDurationText(summary.seconds)}.`
        + (state.undoneAt ? ' Перекладене чергою скасовано.' : '');
    queueEl('#queue-panel-summary').textContent = finishedText;
    const errors = queueEl('#queue-panel-errors');
    errors.replaceChildren(...(state.active ? [] : state.errors).map((item) => Object.assign(document.createElement('li'), {
        textContent: `Розділ ${item.chapterNumber} «${item.title || ''}»: ${item.error || 'помилка'}`,
    })));
    queueEl('#queue-pause-button').hidden = state.status !== 'running';
    queueEl('#queue-resume-button').hidden = state.status !== 'paused';
    queueEl('#queue-stop-button').hidden = !state.active;
    queueEl('#queue-undo-button').hidden = state.active || Boolean(state.undoneAt) || !summary.variantsCreated;
    queueEl('#queue-dismiss-button').hidden = state.active;
    window.clearTimeout(queuePollTimer);
    if (state.active) queuePollTimer = window.setTimeout(() => { void pollQueue(); }, QUEUE_POLL_MS);
    if (state.progress.batchesDone !== queueSyncedBatches) void syncQueueResults(state);
}

async function pollQueue() {
    if (!queueState) return;
    try {
        showQueueState(await WorkbenchApi.getTranslationQueue(queueState.queueId));
    } catch (error) {
        queueEl('#queue-panel-error').textContent = `Немає зв'язку з сервером: ${error.message}`;
        queueEl('#queue-panel-error').hidden = false;
        queuePollTimer = window.setTimeout(() => { void pollQueue(); }, QUEUE_POLL_MS * 2);
        return;
    }
    queueEl('#queue-panel-error').hidden = true;
}

// Chapters the queue translated are read again from the server. Chapters with unsaved edits are left alone.
async function syncQueueResults(state) {
    if (queueSyncing || !currentProject || currentProject.projectId !== state.projectId) return;
    queueSyncing = true;
    const batches = state.progress.batchesDone;
    try {
        const fresh = normalizeBookStructure(await WorkbenchApi.getProjectBookStructure(currentProject.projectId));
        const touched = new Set(state.items.filter((item) => item.paragraphsDone > 0).map((item) => item.chapterId));
        fresh.chapters.forEach((chapter) => {
            if (!touched.has(chapter.chapterId)) return;
            const index = loadedChapters.findIndex((loaded) => loaded.chapterId === chapter.chapterId);
            if (index < 0 || isTranslationDirty(index)) return;
            if (index === selectedChapterIndex) {
                chapter.elements.forEach((element) => {
                    const context = element.paragraphId ? variantContexts.get(element.paragraphId) : null;
                    if (context) applyParagraphFromServer(context.paragraph, element);
                });
            } else {
                loadedChapters[index].elements = chapter.elements;
                translationStates.delete(index);
            }
        });
        queueSyncedBatches = batches;
    } catch (error) {
        // the next poll tries again
    } finally {
        queueSyncing = false;
    }
}

async function queueControl(action) {
    if (!queueState) return;
    try {
        showQueueState(await WorkbenchApi.controlTranslationQueue(queueState.queueId, action));
        queueEl('#queue-panel-error').hidden = true;
    } catch (error) {
        queueEl('#queue-panel-error').textContent = error.message;
        queueEl('#queue-panel-error').hidden = false;
    }
}

async function undoQueueResults() {
    if (!queueState) return;
    try {
        const dry = await WorkbenchApi.controlTranslationQueue(queueState.queueId, 'undo', { dryRun: true });
        const message = `Буде видалено варіантів, створених чергою: ${dry.removedVariants}; скасовано автоматичний вибір: ${dry.revertedSelections}.`
            + (dry.keptChosen ? ` Лишаться без змін (обрані, відредаговані чи вичитані): ${dry.keptChosen}.` : '')
            + '\nПродовжити? Витрачені гроші це не повертає.';
        if (!dry.removedVariants && !dry.revertedSelections) {
            window.alert('Нема чого скасовувати: усе перекладене чергою вже змінено вручну або видалено.');
            return;
        }
        if (!window.confirm(message)) return;
        await WorkbenchApi.controlTranslationQueue(queueState.queueId, 'undo', {});
        queueSyncedBatches = -1;
        const fresh = await WorkbenchApi.getTranslationQueue(queueState.queueId);
        showQueueState(fresh);
    } catch (error) {
        queueEl('#queue-panel-error').textContent = `Не вдалося скасувати: ${error.message}`;
        queueEl('#queue-panel-error').hidden = false;
    }
}

// Called when a project is opened: shows the latest queue (a running one keeps going on the server).
async function loadLatestQueue() {
    window.clearTimeout(queuePollTimer);
    queueState = null;
    queueSyncedBatches = -1;
    queueEl('#queue-panel').hidden = true;
    if (!currentProject) return;
    const projectId = currentProject.projectId;
    try {
        const result = await WorkbenchApi.getLatestTranslationQueue(projectId);
        if (currentProject?.projectId !== projectId || !result.queue) return;
        // a finished queue is shown until the user closes it; only keep ones from the last day
        const age = Date.now() - Date.parse(result.queue.finishedAt || result.queue.createdAt);
        if (result.queue.active || (age < 24 * 3600 * 1000 && !localStorageSafeGet(`queue-dismissed:${result.queue.queueId}`))) showQueueState(result.queue);
    } catch (error) {
        // the panel simply stays hidden
    }
}

function localStorageSafeGet(key) {
    try { return window.localStorage.getItem(key); } catch (error) { return null; }
}

function localStorageSafeSet(key, value) {
    try { window.localStorage.setItem(key, value); } catch (error) { /* private mode */ }
}

queueEl('#queue-open-button').addEventListener('click', () => { void openQueueDialog(); });
queueEl('#close-queue').addEventListener('click', closeQueueDialog);
queueEl('#cancel-queue').addEventListener('click', closeQueueDialog);
queueEl('#queue-form').addEventListener('submit', (event) => { void startQueue(event); });
document.querySelectorAll('input[name="queue-mode"]').forEach((radio) => radio.addEventListener('change', () => { void refreshQueueEstimate(); }));
['#queue-from', '#queue-to', '#queue-include-translated'].forEach((selector) => queueEl(selector).addEventListener('change', () => { void refreshQueueEstimate(); }));
queueEl('#queue-confirm-unpriced').addEventListener('change', refreshQueueStartButton);
queueEl('#queue-pause-button').addEventListener('click', () => { void queueControl('pause'); });
queueEl('#queue-resume-button').addEventListener('click', () => { void queueControl('resume'); });
queueEl('#queue-stop-button').addEventListener('click', () => {
    if (window.confirm('Зупинити чергу? Уже перекладені батчі лишаться, розділ у роботі буде позначено «частково».')) void queueControl('stop');
});
queueEl('#queue-undo-button').addEventListener('click', () => { void undoQueueResults(); });
queueEl('#queue-dismiss-button').addEventListener('click', () => {
    if (queueState) localStorageSafeSet(`queue-dismissed:${queueState.queueId}`, '1');
    showQueueState(null);
    queueState = null;
});
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !queueEl('#queue-dialog').hidden) closeQueueDialog();
});

// --- Dictionary: a word or phrase of the original column, in its sentence ----------------------------
// Tap a word (mode «📖 Словник») or select several words; Alt+click opens it without the mode on a
// computer. Words are found from the touch point with caret APIs and a Range, never by wrapping
// every word in a tag.

const DICTIONARY_MODE_KEY = 'dictionary-mode';
const DICTIONARY_WORD_RE = /[\p{L}\p{M}]+(?:['’‘ʼ‐‑-][\p{L}\p{M}]+)*/gu;
const DICTIONARY_SELECTION_DELAY_MS = 450;
const DICTIONARY_TYPE_LABELS = { word: 'слово', phrase: 'фраза', idiom: 'ідіома', phrasal_verb: 'фразове дієслово' };
let dictionaryMode = false;
let dictionaryBusy = false;
let dictionaryPointerDown = false;
let dictionarySelectionTimer = null;
let dictionaryLastKey = '';
let dictionaryState = null;

function dictEl(selector) {
    return document.querySelector(selector);
}

function dictReadMode() {
    try { return window.localStorage.getItem(DICTIONARY_MODE_KEY) === '1'; } catch (error) { return false; }
}

function dictWriteMode(on) {
    try { window.localStorage.setItem(DICTIONARY_MODE_KEY, on ? '1' : '0'); } catch (error) { /* private mode */ }
}

function setDictionaryMode(on, persist = true) {
    dictionaryMode = Boolean(on);
    if (persist) dictWriteMode(dictionaryMode);
    const button = dictEl('#dictionary-toggle-button');
    button.setAttribute('aria-pressed', String(dictionaryMode));
    button.classList.toggle('dictionary-toggle-active', dictionaryMode);
    dictEl('#dictionary-mode-bar').hidden = !dictionaryMode;
    document.body.classList.toggle('dictionary-mode', dictionaryMode);
    if (!dictionaryMode) {
        window.clearTimeout(dictionarySelectionTimer);
        closeDictionarySheet();
        dictionaryParked = null;
    }
    updateDictionaryParkedHint();
}

function dictTextNodeOffset(root, node, offset) {
    return getPlainTextOffset(root, node, offset);
}

// The word around `offset` in a text node, as a Range; null when the offset is not on a letter.
function dictWordRangeAt(node, offset) {
    const data = node.nodeValue || '';
    DICTIONARY_WORD_RE.lastIndex = 0;
    let match;
    while ((match = DICTIONARY_WORD_RE.exec(data))) {
        const start = match.index;
        const end = start + match[0].length;
        if (offset >= start && offset <= end) {
            const range = document.createRange();
            range.setStart(node, start);
            range.setEnd(node, end);
            return range;
        }
        if (start > offset) break;
    }
    return null;
}

function dictCaretFromPoint(x, y) {
    if (document.caretPositionFromPoint) {
        const position = document.caretPositionFromPoint(x, y);
        if (position) return { node: position.offsetNode, offset: position.offset };
    }
    if (document.caretRangeFromPoint) {
        const range = document.caretRangeFromPoint(x, y);
        if (range) return { node: range.startContainer, offset: range.startOffset };
    }
    return null;
}

function dictRangeIsAt(range, x, y) {
    return Array.from(range.getClientRects()).some((rect) => (
        x >= rect.left - 8 && x <= rect.right + 8 && y >= rect.top - 10 && y <= rect.bottom + 10
    ));
}

function dictSelectionFromRange(original, range) {
    const row = original.closest('.translation-row');
    const paragraphId = row?.dataset.paragraphId;
    if (!paragraphId) return null;
    const start = dictTextNodeOffset(original, range.startContainer, range.startOffset);
    const end = dictTextNodeOffset(original, range.endContainer, range.endOffset);
    const text = range.toString();
    if (end <= start || !text.trim()) return null;
    const rect = range.getBoundingClientRect();
    return { paragraphId, start, end, text, rect: { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom } };
}

function dictOriginalOf(node) {
    const element = node?.nodeType === Node.TEXT_NODE ? node.parentElement : node;
    return element?.closest ? element.closest('.original-paragraph') : null;
}

function handleDictionaryClick(event) {
    const original = event.target.closest ? event.target.closest('.original-paragraph') : null;
    if (!original) return;
    const viaAlt = event.altKey && !dictionaryMode;
    if (!dictionaryMode && !viaAlt) return;
    const selection = window.getSelection();
    if (selection && !selection.isCollapsed) return; // a selection is handled when it is finished
    const picked = dictWordAtPoint(original, event.clientX, event.clientY);
    if (!picked) {
        closeDictionarySheet(); // a tap on the original that is not on a word: outside the window
        return;
    }
    if (viaAlt) event.preventDefault();
    void openDictionary(picked, 'word');
}

function dictWordAtPoint(original, x, y) {
    const caret = dictCaretFromPoint(x, y);
    if (!caret || caret.node?.nodeType !== Node.TEXT_NODE || dictOriginalOf(caret.node) !== original) return null;
    const range = dictWordRangeAt(caret.node, caret.offset);
    if (!range || !dictRangeIsAt(range, x, y)) return null;
    return dictSelectionFromRange(original, range);
}

function handleDictionarySelectionChange() {
    window.clearTimeout(dictionarySelectionTimer);
    if (!dictionaryMode) return;
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) return;
    dictionarySelectionTimer = window.setTimeout(finishDictionarySelection, DICTIONARY_SELECTION_DELAY_MS);
}

function finishDictionarySelection() {
    if (!dictionaryMode || dictionaryPointerDown || dictionaryBusy) return;
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) return;
    const range = selection.getRangeAt(0);
    const original = dictOriginalOf(range.startContainer);
    if (!original || dictOriginalOf(range.endContainer) !== original) return;
    // trim the range to its first and last letters, so a stray space or quote is not part of the phrase
    const text = range.toString();
    const leading = text.length - text.trimStart().length;
    const picked = dictSelectionFromRange(original, range);
    if (!picked) return;
    picked.start += leading;
    picked.text = text.trim();
    picked.end = picked.start + picked.text.length;
    const wordCount = (picked.text.match(DICTIONARY_WORD_RE) || []).length;
    if (wordCount === 0) return;
    if (wordCount > 8 || picked.text.length > 80) {
        showDictionarySheetMessage(picked, 'Виділіть коротшу фразу (до 8 слів).');
        return;
    }
    void openDictionary(picked, wordCount > 1 ? 'phrase' : 'word');
}

function dictSelectionKey(selection) {
    return `${selection.paragraphId}:${selection.start}:${selection.end}`;
}

// Desktop: a fixed panel on the right, the page gets a right padding while it is open (nothing is
// covered). Tablet / narrow screen / touch: a bottom sheet of at most 42vh.
function dictionarySideLayout() {
    return window.matchMedia('(min-width: 1100px) and (pointer: fine)').matches;
}

function positionDictionarySheet() {
    const sheet = dictEl('#dictionary-sheet');
    const side = dictionarySideLayout();
    sheet.classList.toggle('dictionary-sheet-side', side);
    sheet.classList.toggle('dictionary-sheet-bottom', !side);
    const open = !sheet.hidden && side;
    if (document.body.classList.contains('dictionary-panel-open') !== open) {
        document.body.classList.toggle('dictionary-panel-open', open);
        scheduleParagraphHeightsSync(); // the columns got a new width
        syncPinnedRows();
    }
}

// --- the highlight of the word being looked up -------------------------------------------------------
// CSS Custom Highlight API when the browser has it (the text DOM is never touched); otherwise
// fixed rectangles from Range.getClientRects(), kept in place on scroll and resize.

let dictionaryHighlightRange = null;
let dictionaryRectFrame = null;
let dictionaryFlashTimers = [];

function dictionaryHighlightApi() {
    return typeof CSS !== 'undefined' && CSS.highlights && typeof Highlight === 'function' ? CSS.highlights : null;
}

function dictBuildRange(paragraphId, start, end) {
    const row = Array.from(translationRows.querySelectorAll('.translation-row')).find((item) => item.dataset.paragraphId === paragraphId);
    const original = row?.querySelector('.original-paragraph');
    if (!original) return null;
    const walker = document.createTreeWalker(original, NodeFilter.SHOW_TEXT);
    let offset = 0;
    let node;
    let startNode = null;
    let startOffset = 0;
    const range = document.createRange();
    while ((node = walker.nextNode())) {
        const length = node.nodeValue.length;
        if (!startNode && start < offset + length) {
            startNode = node;
            startOffset = start - offset;
            range.setStart(node, startOffset);
        }
        if (startNode && end <= offset + length) {
            range.setEnd(node, end - offset);
            return range;
        }
        offset += length;
    }
    return null;
}

function dictionaryRectLayer() {
    let layer = document.querySelector('#dictionary-highlight-layer');
    if (!layer) {
        layer = document.createElement('div');
        layer.id = 'dictionary-highlight-layer';
        layer.className = 'dictionary-highlight-layer';
        layer.setAttribute('aria-hidden', 'true');
        document.body.append(layer);
    }
    return layer;
}

function renderDictionaryRects() {
    dictionaryRectFrame = null;
    const layer = document.querySelector('#dictionary-highlight-layer');
    if (!dictionaryHighlightRange || dictionaryHighlightApi()) {
        layer?.replaceChildren();
        return;
    }
    if (!dictionaryHighlightRange.startContainer.isConnected) {
        clearDictionaryHighlight();
        return;
    }
    const target = dictionaryRectLayer();
    target.replaceChildren(...Array.from(dictionaryHighlightRange.getClientRects()).filter((rect) => rect.width > 0).map((rect) => {
        const box = document.createElement('div');
        box.className = 'dictionary-highlight-rect';
        box.style.left = `${rect.left - 2}px`;
        box.style.top = `${rect.top - 1}px`;
        box.style.width = `${rect.width + 4}px`;
        box.style.height = `${rect.height + 2}px`;
        return box;
    }));
}

function scheduleDictionaryRects() {
    if (!dictionaryHighlightRange || dictionaryHighlightApi() || dictionaryRectFrame) return;
    dictionaryRectFrame = requestAnimationFrame(renderDictionaryRects);
}

function setDictionaryHighlight(range) {
    clearDictionaryHighlight();
    if (!range) return;
    dictionaryHighlightRange = range;
    const api = dictionaryHighlightApi();
    if (api) api.set('dictionary-term', new Highlight(range));
    else renderDictionaryRects();
}

function clearDictionaryHighlight() {
    dictionaryFlashTimers.forEach((timer) => window.clearTimeout(timer));
    dictionaryFlashTimers = [];
    dictionaryHighlightRange = null;
    const api = dictionaryHighlightApi();
    if (api) {
        api.delete('dictionary-term');
        api.delete('dictionary-flash');
    }
    document.querySelector('#dictionary-highlight-layer')?.replaceChildren();
}

// A short blink so the eye finds the word again after the page was scrolled.
function flashDictionaryHighlight() {
    if (!dictionaryHighlightRange) return;
    const api = dictionaryHighlightApi();
    const layer = document.querySelector('#dictionary-highlight-layer');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const set = (on) => {
        if (api) {
            if (on && dictionaryHighlightRange) api.set('dictionary-flash', new Highlight(dictionaryHighlightRange));
            else api.delete('dictionary-flash');
        }
        layer?.classList.toggle('dictionary-flash-on', on);
    };
    dictionaryFlashTimers.forEach((timer) => window.clearTimeout(timer));
    dictionaryFlashTimers = [];
    const steps = reduced ? [true, false] : [true, false, true, false, true, false];
    steps.forEach((on, index) => {
        dictionaryFlashTimers.push(window.setTimeout(() => set(on), index * (reduced ? 900 : 220)));
    });
}

// The word must not sit behind the pinned block, the bottom bars or the bottom sheet.
function ensureDictionaryWordVisible() {
    if (!dictionaryHighlightRange || !dictionaryHighlightRange.startContainer.isConnected) return;
    const sheet = dictEl('#dictionary-sheet');
    const reserve = !sheet.hidden && !dictionarySideLayout() ? sheet.offsetHeight : 0;
    const rect = dictionaryHighlightRange.getBoundingClientRect();
    const topInset = expectedStickyStackHeight() + 8;
    const bottomInset = window.innerHeight - Math.max(bottomOverlayHeight(), reserve) - 8;
    if (rect.top >= topInset && rect.bottom <= bottomInset) return;
    scrollIntoWorkspaceView({ getBoundingClientRect: () => dictionaryHighlightRange.getBoundingClientRect() }, { behavior: 'auto', bottomReserve: reserve });
    scheduleDictionaryRects();
}

function refreshDictionaryLayout() {
    positionDictionarySheet();
    requestAnimationFrame(() => requestAnimationFrame(() => {
        scheduleDictionaryRects();
        ensureDictionaryWordVisible();
    }));
}

function showDictionaryInText() {
    const selection = dictionaryState?.selection;
    if (!selection) return;
    const range = dictBuildRange(selection.paragraphId, selection.start, selection.end);
    if (!range) return;
    if (!dictionaryHighlightRange?.startContainer.isConnected) setDictionaryHighlight(range);
    const sheet = dictEl('#dictionary-sheet');
    const reserve = !dictionarySideLayout() ? sheet.offsetHeight : 0;
    const row = range.startContainer.parentElement?.closest('.translation-row');
    scrollIntoWorkspaceView(row?.querySelector('.original-paragraph') || row, { behavior: 'auto', bottomReserve: reserve });
    scheduleDictionaryRects();
    flashDictionaryHighlight();
}

window.addEventListener('scroll', scheduleDictionaryRects, { capture: true, passive: true });
window.addEventListener('resize', () => { if (!dictEl('#dictionary-sheet').hidden) refreshDictionaryLayout(); });
if ('ResizeObserver' in window) new ResizeObserver(scheduleDictionaryRects).observe(translationRows);

function showDictionarySheetMessage(selection, message) {
    if (!searchDialog.hidden) closeSearchPanel();
    dictionaryState = { selection, response: null, extras: [] };
    const sheet = dictEl('#dictionary-sheet');
    dictEl('#dictionary-term').textContent = selection.text;
    dictEl('#dictionary-subtitle').textContent = '';
    dictEl('#dictionary-body').replaceChildren();
    dictEl('#dictionary-glossary-form').hidden = true;
    dictEl('#dictionary-actions').hidden = true;
    dictEl('#dictionary-status').textContent = message;
    dictEl('#dictionary-status').dataset.state = 'error';
    dictEl('#dictionary-context').hidden = true;
    sheet.hidden = false;
    setDictionaryHighlight(dictBuildRange(selection.paragraphId, selection.start, selection.end));
    refreshDictionaryLayout();
}

async function openDictionary(selection, mode, { keepOpen = false } = {}) {
    if (dictionaryBusy || !currentProject) return;
    const key = dictSelectionKey(selection);
    if (!keepOpen && key === dictionaryLastKey && !dictEl('#dictionary-sheet').hidden) return; // the same tap again
    if (mode !== 'more' && dictionaryParked && dictionaryParked.key === key) {
        restoreDictionarySheet(); // the word of the hidden answer: no new request
        return;
    }
    if (mode !== 'more') {
        dictionaryParked = null;
        updateDictionaryParkedHint();
        if (!searchDialog.hidden) closeSearchPanel();
    }
    dictionaryBusy = true;
    dictionaryLastKey = key;
    const sheet = dictEl('#dictionary-sheet');
    if (mode !== 'more') {
        dictionaryState = { selection, response: null, extras: [] };
        dictEl('#dictionary-term').textContent = selection.text;
        dictEl('#dictionary-subtitle').textContent = '';
        dictEl('#dictionary-body').replaceChildren();
        dictEl('#dictionary-glossary-form').hidden = true;
        dictEl('#dictionary-actions').hidden = true;
        dictEl('#dictionary-context').hidden = true;
        sheet.hidden = false;
        setDictionaryHighlight(dictBuildRange(selection.paragraphId, selection.start, selection.end));
        refreshDictionaryLayout();
    }
    const status = dictEl('#dictionary-status');
    status.dataset.state = 'loading';
    status.textContent = mode === 'more' ? 'Шукаємо інші значення…' : 'Шукаємо…';
    dictEl('#dictionary-more').disabled = true;
    try {
        const response = await WorkbenchApi.dictionaryLookup({
            projectId: currentProject.projectId, paragraphId: selection.paragraphId, text: selection.text,
            offsetStart: selection.start, offsetEnd: selection.end, mode,
        });
        if (mode === 'more') {
            dictionaryState.extras.push(response);
            dictionaryState.moreRemaining = response.moreRemaining;
        } else {
            dictionaryState.response = response;
            dictionaryState.moreRemaining = response.moreRemaining;
        }
        status.dataset.state = '';
        status.textContent = '';
        renderDictionary();
    } catch (error) {
        status.dataset.state = 'error';
        status.textContent = dictionaryErrorText(error);
        dictEl('#dictionary-actions').hidden = !dictionaryState?.response;
        if (dictionaryState?.response) renderDictionary(true);
    } finally {
        dictionaryBusy = false;
        refreshDictionaryLayout();
    }
}

function dictionaryErrorText(error) {
    const code = error?.code;
    if (code === 'dictionary_no_connection') return 'Немає підключення до Claude, GPT чи Gemini. Додай його в Connections.';
    if (code === 'dictionary_connection_unavailable') return 'Підключення моделі словника недоступне. Обери інше в ⚙ → «Модель словника» або перевір його в Connections.';
    if (code === 'dictionary_model_error') return error.message;
    if (code === 'dictionary_invalid_response') return 'Модель відповіла у неправильному форматі. Спробуй ще раз.';
    if (code === 'dictionary_stale') return 'Абзац змінився. Торкнись слова ще раз.';
    if (code === 'dictionary_more_limit') return 'Більше значень немає: ліміт — 3 додаткові запити на слово.';
    return error?.message || 'Не вдалося отримати відповідь словника.';
}

function dictNode(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

function dictSection(title) {
    const section = dictNode('section', 'dictionary-section');
    section.append(dictNode('h4', 'dictionary-section-title', title));
    return section;
}

function dictAllTranslations() {
    const seen = new Set();
    const list = [];
    [dictionaryState.response, ...dictionaryState.extras].forEach((response) => {
        (response?.result?.translations || []).forEach((item) => {
            const key = item.text.toLocaleLowerCase();
            if (!seen.has(key)) { seen.add(key); list.push(item); }
        });
    });
    return list;
}

function renderDictionary(keepStatus = false) {
    const { response, extras, selection } = dictionaryState;
    if (!response) return;
    const result = response.result;
    const first = result || extras.find((item) => item.result)?.result || null;
    dictEl('#dictionary-term').textContent = first?.term || response.term;
    const subtitle = [first?.lemma && first.lemma.toLocaleLowerCase() !== (first.term || '').toLocaleLowerCase() ? first.lemma : null,
        first?.pos, first ? DICTIONARY_TYPE_LABELS[first.termType] : null].filter(Boolean).join(' · ');
    dictEl('#dictionary-subtitle').textContent = subtitle;
    const body = dictEl('#dictionary-body');
    const parts = [];
    if (response.priceWarning) parts.push(dictNode('p', 'dictionary-warning', response.priceWarning));
    if (response.glossary?.length) {
        const section = dictSection('У глосарії');
        const list = dictNode('ul', 'dictionary-list');
        response.glossary.forEach((entry) => {
            list.append(dictNode('li', '', `${entry.source} → ${entry.target}${entry.note ? ` (${entry.note})` : ''}`));
        });
        section.append(list);
        parts.push(section);
    }
    if (first) {
        const meaning = dictSection('Значення в цьому реченні');
        meaning.append(dictNode('p', '', first.meaningInContext));
        if (response.expanded) {
            const expand = dictNode('button', 'text-btn dictionary-expand', `Це частина фрази «${response.expanded.text}» — шукати фразу`);
            expand.type = 'button';
            expand.addEventListener('click', () => {
                void openDictionary({ ...selection, start: response.expanded.start, end: response.expanded.end, text: response.expanded.text }, 'phrase');
            });
            meaning.append(expand);
        }
        parts.push(meaning);
        const here = dictSection('Як перекладено тут');
        here.append(dictNode('p', first.inThisTranslation ? '' : 'muted', first.inThisTranslation || 'У поточному перекладі абзацу не знайдено.'));
        if (first.inThisTranslation) here.lastChild.className = 'dictionary-here';
        parts.push(here);
        const others = dictSection('Інші значення');
        const list = dictNode('ul', 'dictionary-list');
        dictAllTranslations().forEach((item) => {
            const li = dictNode('li', '', item.text);
            if (item.register) li.append(' ', dictNode('span', 'dictionary-badge', item.register));
            list.append(li);
        });
        others.append(list);
        const notes = [first, ...extras.map((item) => item.result)].filter((item) => item?.registerNote).map((item) => item.registerNote);
        if (notes.length) others.append(dictNode('p', 'muted', `Регістр: ${[...new Set(notes)].join(', ')}`));
        parts.push(others);
        const examples = [first, ...extras.map((item) => item.result)].flatMap((item) => item?.examples || []);
        if (examples.length) {
            const section = dictSection('Приклади');
            const exampleList = dictNode('ul', 'dictionary-list');
            examples.forEach((example) => {
                const li = dictNode('li', '');
                li.append(dictNode('span', 'dictionary-example-en', example.en), dictNode('br'), dictNode('span', 'muted', example.uk));
                exampleList.append(li);
            });
            section.append(exampleList);
            parts.push(section);
        }
    } else {
        parts.push(dictNode('p', 'muted', 'Для цього терміна є запис у глосарії. Натисни «Ще значення», щоб запитати модель.'));
    }
    body.replaceChildren(...parts);
    dictEl('#dictionary-actions').hidden = false;
    const more = dictEl('#dictionary-more');
    more.disabled = (dictionaryState.moreRemaining ?? 3) <= 0;
    more.textContent = more.disabled ? 'Більше значень немає' : 'Ще значення';
    const term = first?.term || response.term;
    const lemma = first?.lemma || term;
    dictEl('#dictionary-reverso').href = `https://context.reverso.net/translation/english-ukrainian/${encodeURIComponent(term)}`;
    const wiktionaryTerm = (response.mode === 'phrase' || /\s/.test(term) ? term : lemma).replace(/\s+/g, '_');
    dictEl('#dictionary-wiktionary').href = `https://en.wiktionary.org/wiki/${encodeURIComponent(wiktionaryTerm)}`;
    if (!keepStatus) dictEl('#dictionary-status').textContent = '';
    renderDictionaryContext(response);
    refreshDictionaryLayout();
}

// «У реченні: …» — the sentence with the looked-up word or phrase in bold.
function renderDictionaryContext(response) {
    const line = dictEl('#dictionary-context');
    if (typeof response.sentence !== 'string' || !Number.isInteger(response.termStart) || !Number.isInteger(response.termEnd)) {
        line.hidden = true;
        return;
    }
    line.replaceChildren(
        dictNode('span', 'dictionary-context-label', 'У реченні: '),
        document.createTextNode(response.sentence.slice(0, response.termStart)),
        dictNode('strong', '', response.sentence.slice(response.termStart, response.termEnd)),
        document.createTextNode(response.sentence.slice(response.termEnd)),
    );
    line.hidden = false;
}

// One docked panel at a time: when the search opens, the dictionary hides but keeps its last answer. It comes back
// when the same word is tapped again or with «Остання відповідь» in the dictionary bar, never by itself.
let dictionaryParked = null;

function parkDictionarySheet() {
    const sheet = dictEl('#dictionary-sheet');
    if (sheet.hidden || !dictionaryState?.response) return;
    dictionaryParked = { state: dictionaryState, key: dictionaryLastKey };
    sheet.hidden = true;
    dictEl('#dictionary-glossary-form').hidden = true;
    dictionaryLastKey = '';
    dictionaryState = null;
    clearDictionaryHighlight();
    positionDictionarySheet();
    updateDictionaryParkedHint();
}

function restoreDictionarySheet() {
    if (!dictionaryParked) return;
    const { state, key } = dictionaryParked;
    dictionaryParked = null;
    if (!searchDialog.hidden) closeSearchPanel();
    dictionaryState = state;
    dictionaryLastKey = key;
    dictEl('#dictionary-term').textContent = state.selection.text;
    dictEl('#dictionary-sheet').hidden = false;
    dictEl('#dictionary-status').textContent = '';
    setDictionaryHighlight(dictBuildRange(state.selection.paragraphId, state.selection.start, state.selection.end));
    renderDictionary();
    refreshDictionaryLayout();
    updateDictionaryParkedHint();
}

function updateDictionaryParkedHint() {
    const button = dictEl('#dictionary-restore-button');
    if (!button) return;
    const word = dictionaryParked?.state.selection.text;
    button.hidden = !word;
    button.textContent = word ? `Остання відповідь: «${word.length > 24 ? `${word.slice(0, 23)}…` : word}»` : '';
}

function closeDictionarySheet() {
    const sheet = dictEl('#dictionary-sheet');
    if (sheet.hidden) return;
    sheet.hidden = true;
    dictEl('#dictionary-glossary-form').hidden = true;
    dictionaryLastKey = '';
    dictionaryState = null;
    clearDictionaryHighlight();
    positionDictionarySheet();
}

function dictCopyText() {
    const { response, extras } = dictionaryState || {};
    const first = response?.result || extras?.find((item) => item.result)?.result;
    if (!first) {
        return (response?.glossary || []).map((entry) => `${entry.source} — ${entry.target}`).join('\n') || response?.term || '';
    }
    return `${first.term} — ${dictAllTranslations().map((item) => item.text).join(', ')}\n${first.meaningInContext}`;
}

async function copyDictionary() {
    const text = dictCopyText();
    if (!text) return;
    const status = dictEl('#dictionary-status');
    try {
        await navigator.clipboard.writeText(text);
    } catch (error) {
        const area = document.createElement('textarea');
        area.value = text;
        document.body.append(area);
        area.select();
        const copied = document.execCommand && document.execCommand('copy');
        area.remove();
        if (!copied) {
            status.dataset.state = 'error';
            status.textContent = 'Не вдалося скопіювати.';
            return;
        }
    }
    status.dataset.state = '';
    status.textContent = 'Скопійовано.';
}

function openDictionaryGlossaryForm() {
    const { response, extras } = dictionaryState || {};
    if (!response) return;
    const first = response.result || extras.find((item) => item.result)?.result;
    const single = response.mode === 'word' && first?.lemma;
    dictEl('#dictionary-glossary-source').value = single ? first.lemma : (first?.term || response.term);
    dictEl('#dictionary-glossary-target').value = '';
    const chips = dictEl('#dictionary-glossary-chips');
    chips.replaceChildren(...dictAllTranslations().map((item) => {
        const chip = dictNode('button', 'secondary-btn dictionary-chip', item.text);
        chip.type = 'button';
        chip.addEventListener('click', () => { dictEl('#dictionary-glossary-target').value = item.text; });
        return chip;
    }));
    dictEl('#dictionary-glossary-form').hidden = false;
    dictEl('#dictionary-glossary-target').focus();
}

async function saveDictionaryGlossaryEntry(event) {
    event.preventDefault();
    const source = dictEl('#dictionary-glossary-source').value.trim();
    const target = dictEl('#dictionary-glossary-target').value.trim();
    const status = dictEl('#dictionary-status');
    if (!source || !target) {
        status.dataset.state = 'error';
        status.textContent = 'Вкажи оригінал і переклад терміна.';
        return;
    }
    const button = dictEl('#dictionary-glossary-save');
    button.disabled = true;
    try {
        const entry = await WorkbenchApi.createGlossaryEntry({ source, target, note: null, active: true });
        const ids = [...(currentProject.projectGlossaryEntryIds || [])];
        if (!ids.includes(entry.glossaryEntryId)) ids.push(entry.glossaryEntryId);
        applyUpdatedProject(await WorkbenchApi.updateProject(currentProject.projectId, { projectGlossaryEntryIds: ids }));
        dictionaryState.response.glossary = [...(dictionaryState.response.glossary || []), { source, target, note: null }];
        dictEl('#dictionary-glossary-form').hidden = true;
        renderDictionary(true);
        status.dataset.state = '';
        status.textContent = `Додано в глосарій проєкту: ${source} → ${target}.`;
    } catch (error) {
        status.dataset.state = 'error';
        status.textContent = `Не вдалося додати в глосарій: ${error.message}`;
    } finally {
        button.disabled = false;
    }
}

// --- «Модель словника» in ⚙ -----------------------------------------------------------------------

let dictionaryModelList = [];

function dictReadyConnections() {
    return integrationConnections.filter((item) => LLM_TRANSLATION_ENGINES.includes(item.providerId) && isReadyConnection(item));
}

function dictEffectiveConnection() {
    const chosen = dictEl('#dictionary-connection-select').value;
    const ready = dictReadyConnections();
    return ready.find((item) => item.connectionId === chosen) || ready.find((item) => item.providerId === 'claude') || ready[0] || null;
}

function fillDictionaryModelSelect(selected) {
    const select = dictEl('#dictionary-model-select');
    select.replaceChildren(Object.assign(document.createElement('option'), { value: '', textContent: 'Найдешевша з доступних (авто)' }));
    dictionaryModelList.forEach((model) => {
        select.append(Object.assign(document.createElement('option'), {
            value: model.id, textContent: model.displayName && model.displayName !== model.id ? `${model.displayName} (${model.id})` : model.id,
        }));
    });
    if (selected && dictionaryModelList.some((model) => model.id === selected)) {
        select.value = selected;
        dictEl('#dictionary-model-manual').value = '';
    } else if (selected) {
        dictEl('#dictionary-model-manual').value = selected;
    }
}

async function loadDictionaryModels(selected) {
    const status = dictEl('#dictionary-model-status');
    const connection = dictEffectiveConnection();
    dictionaryModelList = [];
    if (!connection) {
        status.textContent = 'Немає перевіреного підключення Claude, GPT чи Gemini: додай його в Connections.';
        fillDictionaryModelSelect(selected);
        return;
    }
    status.textContent = 'Завантажуємо список моделей…';
    try {
        dictionaryModelList = (await WorkbenchApi.listConnectionModels(connection.connectionId)).models || [];
        status.textContent = `Моделей у списку: ${dictionaryModelList.length}. Підключення: ${connection.displayName}.`;
    } catch (error) {
        status.textContent = `Не вдалося отримати список моделей: ${error.message} Можна ввести ID вручну.`;
    }
    fillDictionaryModelSelect(selected);
}

function setupDictionarySettings() {
    const configured = currentProject?.aiConfiguration?.dictionary || {};
    const select = dictEl('#dictionary-connection-select');
    select.replaceChildren(Object.assign(document.createElement('option'), { value: '', textContent: 'Авто (Claude, якщо є)' }));
    dictReadyConnections().forEach((item) => {
        select.append(Object.assign(document.createElement('option'), { value: item.connectionId, textContent: `${TRANSLATION_PROVIDER_LABELS[item.providerId]} · ${item.displayName}` }));
    });
    select.value = dictReadyConnections().some((item) => item.connectionId === configured.connectionId) ? configured.connectionId : '';
    dictEl('#dictionary-model-manual').value = '';
    void loadDictionaryModels(configured.model || '');
}

function collectDictionarySettings() {
    const manual = dictEl('#dictionary-model-manual').value.trim();
    const model = manual || dictEl('#dictionary-model-select').value || null;
    const chosen = dictEl('#dictionary-connection-select').value || null;
    // A model picked from the list belongs to the connection it was listed through.
    return { connectionId: chosen || (model ? dictEffectiveConnection()?.connectionId || null : null), model };
}

// --- wiring ---------------------------------------------------------------------------------------

dictEl('#dictionary-toggle-button').addEventListener('click', () => setDictionaryMode(!dictionaryMode));
dictEl('#dictionary-exit-button').addEventListener('click', () => setDictionaryMode(false));
dictEl('#dictionary-restore-button').addEventListener('click', restoreDictionarySheet);
dictEl('#dictionary-close').addEventListener('click', closeDictionarySheet);
dictEl('#dictionary-show').addEventListener('click', showDictionaryInText);
dictEl('#dictionary-copy').addEventListener('click', () => { void copyDictionary(); });
dictEl('#dictionary-more').addEventListener('click', () => {
    if (dictionaryState?.selection) void openDictionary(dictionaryState.selection, 'more', { keepOpen: true });
});
dictEl('#dictionary-add-glossary').addEventListener('click', openDictionaryGlossaryForm);
dictEl('#dictionary-glossary-cancel').addEventListener('click', () => { dictEl('#dictionary-glossary-form').hidden = true; });
dictEl('#dictionary-glossary-form').addEventListener('submit', (event) => { void saveDictionaryGlossaryEntry(event); });
translationRows.addEventListener('click', handleDictionaryClick);
document.addEventListener('selectionchange', handleDictionarySelectionChange);
document.addEventListener('pointerdown', (event) => {
    dictionaryPointerDown = true;
    const sheet = dictEl('#dictionary-sheet');
    // A tap outside closes it. On the original column in dictionary mode the click that follows decides
    // (a new word replaces the window); closing here would move the text under the finger.
    const onOriginal = event.target.closest && event.target.closest('.original-paragraph') && (dictionaryMode || event.altKey);
    if (!sheet.hidden && !sheet.contains(event.target) && !onOriginal) closeDictionarySheet();
});
document.addEventListener('pointerup', () => {
    dictionaryPointerDown = false;
    if (dictionaryMode) {
        window.clearTimeout(dictionarySelectionTimer);
        dictionarySelectionTimer = window.setTimeout(finishDictionarySelection, DICTIONARY_SELECTION_DELAY_MS);
    }
});
document.addEventListener('pointercancel', () => { dictionaryPointerDown = false; });
document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    if (!dictEl('#dictionary-sheet').hidden) {
        closeDictionarySheet();
    } else if (dictionaryMode) {
        setDictionaryMode(false);
    }
});
setDictionaryMode(dictReadMode(), false);
dictEl('#dictionary-connection-select').addEventListener('change', () => { void loadDictionaryModels(''); });


// --- «Знайти й замінити» in the search dialog -------------------------------------------------------
// Replacement works on the translation text only and only for a Cyrillic query; the server does the
// matching (modes, case forms, formatting, footnotes) and the writing (one transaction). Undo/redo is
// one step per action on the open chapter's stack, like the whole-chapter choice of a variant.


function rEl(selector) {
    return document.querySelector(selector);
}

function replaceQueryIsCyrillic(query) {
    return /[\u0400-\u04FF]/.test(query);
}

function replaceScopeAllowed() {
    return currentSearchScope === 'chapter' || currentSearchScope === 'project';
}

function replaceAvailable() {
    const query = searchInput.value.trim();
    return replaceModeOn && Boolean(query) && replaceQueryIsCyrillic(query) && replaceScopeAllowed() && Boolean(currentProject)
        && (currentSearchScope !== 'chapter' || selectedChapterIndex !== null);
}

function replaceRequestBase() {
    const scope = currentSearchScope;
    return {
        query: searchInput.value.trim(),
        replacement: rEl('#replace-input').value,
        options: { mode: rEl('input[name="replace-mode"]:checked')?.value || 'start', matchCase: rEl('#replace-match-case').checked },
        scope,
        chapterId: scope === 'chapter' ? loadedChapters[selectedChapterIndex]?.chapterId : null,
        includeVariants: rEl('#replace-variants').checked,
        returnChapterId: loadedChapters[selectedChapterIndex]?.chapterId || null,
    };
}

function setReplaceMode(on) {
    replaceModeOn = Boolean(on);
    rEl('#replace-panel').hidden = !replaceModeOn;
    rEl('#replace-mode-toggle').setAttribute('aria-expanded', String(replaceModeOn));
    searchMatchToggle.hidden = replaceModeOn; // the replace modes below take over
    document.querySelectorAll('.replace-only').forEach((button) => { button.hidden = !replaceModeOn; });
    if (!replaceModeOn) {
        hideReplaceConfirm();
        replaceMatches = [];
        replaceMeta = null;
        replaceIndex = -1;
    }
    scheduleParagraphHeightsSync();
    if (searchInput.value.trim()) void runSearch();
    else updateReplaceStatus();
}

// One status for both modes: «збіг 7 з 50 · розділів: 3», or the replace counts («вичитаних абзаців…»).
function updateReplaceStatus() {
    const status = rEl('#search-status');
    const note = rEl('#replace-note');
    const query = searchInput.value.trim();
    let noteText = '';
    if (replaceModeOn && query && !replaceQueryIsCyrillic(query)) {
        noteText = 'Заміна працює лише по тексту перекладу: введіть запит кирилицею. Латинський запит шукає в оригіналі.';
    } else if (replaceModeOn && !replaceScopeAllowed()) {
        noteText = 'Заміна працює в межах розділу чи проєкту: оберіть «Розділ» або «Проєкт».';
    }
    note.textContent = noteText;
    note.hidden = !noteText;
    const replacing = replaceModeOn && replaceAvailable();
    if (replaceModeOn) {
        rEl('#replace-input').disabled = Boolean(noteText);
        rEl('#replace-input').title = noteText;
    }
    const list = searchNavResults;
    const hasList = list.length > 0;
    const hasMatches = replacing ? replaceMatches.length > 0 : false;
    rEl('#replace-one').disabled = !hasMatches || replaceBusy;
    rEl('#replace-all').disabled = !hasMatches || replaceBusy;
    rEl('#search-prev').disabled = !hasList || searchNavIndex <= 0;
    rEl('#search-next').disabled = !hasList || searchNavIndex >= list.length - 1;
    rEl('#search-return').hidden = !(preSearchPosition && searchUserNavigated);
    let text = '';
    if (replacing && replaceMeta) {
        if (!replaceMeta.total) {
            text = replaceMeta.acrossMarkup ? `Збігів нема. Ще ${replaceMeta.acrossMarkup} перетинають форматування й будуть пропущені.` : 'Збігів нема.';
        } else {
            const position = searchNavIndex >= 0 ? `збіг ${searchNavIndex + 1} з ${replaceMeta.total}` : `${replaceMeta.total} ${pluralize(replaceMeta.total, 'збіг', 'збіги', 'збігів')}`;
            const parts = [position, `розділів: ${replaceMeta.chapters}`];
            if (replaceMeta.reviewedParagraphs) parts.push(`вичитаних абзаців: ${replaceMeta.reviewedParagraphs}`);
            if (replaceMeta.acrossMarkup) parts.push(`перетинають форматування й пропускаються: ${replaceMeta.acrossMarkup}`);
            if (replaceMeta.truncated) parts.push('у списку перші 1000');
            text = parts.join(' · ');
        }
    } else if (query && lastSearchQuery === query && !searchResultsPending) {
        if (!hasList) {
            text = 'Збігів нема.';
        } else {
            const parts = [searchNavIndex >= 0 ? `збіг ${searchNavIndex + 1} з ${list.length}` : `${list.length} ${pluralize(list.length, 'збіг', 'збіги', 'збігів')}`];
            if (lastSearchScope !== 'chapter') {
                parts.push(`розділів: ${new Set(list.map((item) => `${item.projectId}|${item.chapterId}`)).size}`);
            }
            if (lastSearchScope === 'all') {
                const projects = new Set(list.map((item) => item.projectId)).size;
                if (projects > 1) parts.push(`проєктів: ${projects}`);
            }
            text = parts.join(' · ');
        }
    }
    status.textContent = text;
    const tab = document.querySelector('#search-collapsed-tab');
    const total = replacing && replaceMeta ? replaceMeta.total : list.length;
    tab.textContent = total ? `Пошук ${searchNavIndex >= 0 ? searchNavIndex + 1 : '–'}/${total}` : 'Пошук';
    tab.setAttribute('aria-label', `Розгорнути панель пошуку${total ? `: ${tab.textContent}` : ''}`);
}

async function runReplaceFind({ keepIndex = false } = {}) {
    const query = searchInput.value.trim();
    const token = ++replaceFindToken;
    hideReplaceConfirm();
    if (!query) {
        replaceMatches = [];
        replaceMeta = null;
        replaceIndex = -1;
        searchNavResults = [];
        searchNavIndex = -1;
        lastSearchResults = [];
        renderSearchPlaceholder('Введіть текст для пошуку.');
        updateReplaceStatus();
        refreshSearchHighlights();
        return;
    }
    if (!replaceQueryIsCyrillic(query) || !replaceScopeAllowed() || !currentProject) {
        replaceMatches = [];
        replaceMeta = null;
        replaceIndex = -1;
        updateReplaceStatus();
        if (replaceScopeAllowed()) {
            await runPlainSearch({ keepIndex }); // a Latin query still searches the original
        } else {
            searchNavResults = [];
            searchNavIndex = -1;
            lastSearchResults = [];
            renderSearchPlaceholder('Заміна працює в межах розділу чи проєкту.');
            refreshSearchHighlights();
        }
        return;
    }
    renderSearchPlaceholder('Шукаю…');
    try {
        const found = await WorkbenchApi.findTranslation(currentProject.projectId, replaceRequestBase());
        if (token !== replaceFindToken) return;
        const previousIndex = searchNavIndex;
        lastSearchQuery = query;
        lastSearchScope = currentSearchScope;
        replaceMeta = found;
        replaceMatches = found.matches.map((match) => ({
            ...match, projectId: currentProject.projectId, projectTitle: currentProject.title, field: 'translation_text',
        }));
        lastSearchResults = replaceMatches;
        searchNavResults = replaceMatches;
        replaceIndex = keepIndex && replaceMatches.length ? Math.min(Math.max(previousIndex, 0), replaceMatches.length - 1) : -1;
        searchNavIndex = replaceIndex;
        renderSearchResults({ results: replaceMatches });
        updateReplaceStatus();
        refreshSearchHighlights();
    } catch (error) {
        if (token !== replaceFindToken) return;
        replaceMatches = [];
        replaceMeta = null;
        renderSearchPlaceholder(error.message);
        updateReplaceStatus();
    }
}

// --- the match ranges of the server (the drawing is in the search highlights above) ---

function clearReplaceHighlight() {
    clearCurrentSearchHighlight();
}

function replaceRangeFor(target, start, end, expected) {
    const walker = document.createTreeWalker(target, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) => (node.parentElement?.closest('.footnote-marker') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
    });
    let offset = 0;
    let node;
    let startPoint = null;
    let endPoint = null;
    while ((node = walker.nextNode())) {
        const length = node.nodeValue.length;
        if (!startPoint && start < offset + length) startPoint = [node, start - offset];
        if (startPoint && end <= offset + length) {
            endPoint = [node, end - offset];
            break;
        }
        offset += length;
    }
    if (!startPoint || !endPoint) return null;
    const range = document.createRange();
    range.setStart(...startPoint);
    range.setEnd(...endPoint);
    const normalize = (text) => text.replace(/[’‘ʼ]/g, "'");
    return normalize(range.toString()) === normalize(expected) ? range : null;
}

// --- actions -----------------------------------------------------------------------------------------

async function refreshChaptersByIds(chapterIds) {
    if (!chapterIds.length || !currentProject) return;
    const fresh = normalizeBookStructure(await WorkbenchApi.getProjectBookStructure(currentProject.projectId));
    fresh.chapters.forEach((chapter) => {
        if (!chapterIds.includes(chapter.chapterId)) return;
        const index = loadedChapters.findIndex((loaded) => loaded.chapterId === chapter.chapterId);
        if (index < 0 || isTranslationDirty(index)) return;
        if (index === selectedChapterIndex) {
            chapter.elements.forEach((element) => {
                const context = element.paragraphId ? variantContexts.get(element.paragraphId) : null;
                if (context) applyParagraphFromServer(context.paragraph, element);
            });
        } else {
            loadedChapters[index].elements = chapter.elements;
            translationStates.delete(index);
        }
    });
}

// Unsaved edits would be overwritten: the open chapter can be saved first, another chapter has to be.
async function ensureReplaceSaved() {
    const dirty = loadedChapters.map((_chapter, index) => index).filter((index) => isTranslationDirty(index));
    const relevant = currentSearchScope === 'chapter' ? dirty.filter((index) => index === selectedChapterIndex) : dirty;
    if (!relevant.length) return true;
    const other = relevant.find((index) => index !== selectedChapterIndex);
    if (other !== undefined) {
        window.alert(`У розділі ${other + 1} є незбережені зміни. Відкрийте його й збережіть перед заміною.`);
        return false;
    }
    return ensureChapterSavedBefore('замінити текст');
}

// The result of a replacement: the open chapter shows the server's paragraphs, the other chapters are read
// again, and the action is one step on the open chapter's undo stack.
async function applyReplaceResult(result, state, before) {
    applyBulkParagraphs(result.paragraphs);
    await refreshChaptersByIds(result.chapterIds || []);
    if (state && result.undo.items.length) {
        before.bulkAction = { kind: 'replace', projectId: currentProject.projectId, chapterId: loadedChapters[selectedChapterIndex]?.chapterId, items: result.undo.items };
        state.undo.push(before);
        state.redo = [];
    }
}

function setReplaceBusy(busy) {
    replaceBusy = busy;
    updateReplaceStatus();
}

function showReplaceError(error) {
    rEl('#search-status').textContent = `Не вдалося замінити: ${error.message}`;
}

async function replaceOne() {
    if (replaceBusy || !replaceAvailable() || !replaceMatches.length) return;
    const match = replaceMatches[Math.max(replaceIndex, 0)];
    if (!(await ensureReplaceSaved())) return;
    setReplaceBusy(true);
    try {
        await navigateToSearchResult(match); // opens its chapter, so the undo step lands there
        const state = translationStates.get(selectedChapterIndex);
        const before = state ? cloneParagraphDrafts(state.draft) : null;
        state && (state.serverActionRunning = true);
        let result;
        try {
            result = await WorkbenchApi.replaceTranslation(currentProject.projectId, {
                ...replaceRequestBase(), target: { paragraphId: match.paragraphId, occurrence: match.occurrence },
            });
            await applyReplaceResult(result, state, before);
        } finally {
            if (state) state.serverActionRunning = false;
            updateTranslationButtons();
        }
        const placed = result.replaced?.[0];
        await runReplaceFind();
        // continue after the new text: the same paragraph further on, or a later paragraph
        const next = replaceMatches.find((item) => placed
            ? item.chapterIndex > match.chapterIndex
                || (item.chapterIndex === match.chapterIndex && (item.paragraphIndex > placed.paragraphIndex
                    || (item.paragraphIndex === placed.paragraphIndex && item.visibleStart >= placed.visibleStart + placed.newLength)))
            : true);
        showBulkStatus('Замінено 1 збіг. Скасувати: ↩.');
        if (next) await navigateToSearchResult(next);
        else {
            replaceIndex = -1;
            updateReplaceStatus();
        }
    } catch (error) {
        showReplaceError(error);
        void runReplaceFind();
    } finally {
        setReplaceBusy(false);
    }
}

function hideReplaceConfirm() {
    replacePending = null;
    rEl('#replace-confirm').hidden = true;
}

async function replaceAllRequest() {
    if (replaceBusy || !replaceAvailable() || !replaceMatches.length) return;
    if (!(await ensureReplaceSaved())) return;
    setReplaceBusy(true);
    try {
        const preview = await WorkbenchApi.replaceTranslation(currentProject.projectId, { ...replaceRequestBase(), dryRun: true });
        const { summary } = preview;
        if (!summary.matches) {
            rEl('#search-status').textContent = 'Нічого замінювати.';
            return;
        }
        rEl('#replace-confirm-title').textContent = `Замінити ${summary.matches} ${pluralize(summary.matches, 'збіг', 'збіги', 'збігів')} у ${summary.chapters} ${pluralize(summary.chapters, 'розділі', 'розділах', 'розділах')}?`;
        const details = [`Абзаців: ${summary.paragraphs}.`];
        if (summary.reviewedParagraphs) details.push(`З них вичитаних: ${summary.reviewedParagraphs} (позначка «Перевірено» лишається).`);
        if (summary.acrossMarkup) details.push(`${summary.acrossMarkup} ${pluralize(summary.acrossMarkup, 'збіг перетинає', 'збіги перетинають', 'збігів перетинають')} форматування й буде пропущено.`);
        if (summary.variantsChanged) details.push(`Варіантів рушіїв зміниться: ${summary.variantsChanged}.`);
        rEl('#replace-confirm-details').textContent = details.join(' ');
        rEl('#replace-confirm-examples').replaceChildren(...preview.examples.map((example) => {
            const item = document.createElement('li');
            const was = document.createElement('div');
            was.className = 'replace-example-was';
            was.innerHTML = highlightSnippet(`було: ${example.before}`);
            const will = document.createElement('div');
            will.className = 'replace-example-will';
            will.innerHTML = highlightSnippet(`стане: ${example.after}`);
            item.append(was, will);
            return item;
        }));
        replacePending = true;
        rEl('#replace-confirm').hidden = false;
        rEl('#replace-confirm-yes').focus();
    } catch (error) {
        showReplaceError(error);
    } finally {
        setReplaceBusy(false);
    }
}

async function replaceAllConfirmed() {
    if (!replacePending || replaceBusy) return;
    hideReplaceConfirm();
    setReplaceBusy(true);
    const state = translationStates.get(selectedChapterIndex);
    const before = state ? cloneParagraphDrafts(state.draft) : null;
    if (state) state.serverActionRunning = true;
    try {
        const result = await WorkbenchApi.replaceTranslation(currentProject.projectId, replaceRequestBase());
        await applyReplaceResult(result, state, before);
        const { summary } = result;
        showBulkStatus(`Замінено ${summary.matches} ${pluralize(summary.matches, 'збіг', 'збіги', 'збігів')} у ${summary.chapters} ${pluralize(summary.chapters, 'розділі', 'розділах', 'розділах')}. Скасувати: ↩.`);
        clearReplaceHighlight();
        await runReplaceFind();
    } catch (error) {
        showReplaceError(error);
    } finally {
        if (state) state.serverActionRunning = false;
        updateTranslationButtons();
        setReplaceBusy(false);
    }
}

rEl('#replace-mode-toggle').addEventListener('click', () => setReplaceMode(!replaceModeOn));
['#replace-match-case', '#replace-variants'].forEach((selector) => rEl(selector).addEventListener('change', () => { if (replaceModeOn) void runReplaceFind({ keepIndex: true }); }));
document.querySelectorAll('input[name="replace-mode"]').forEach((radio) => radio.addEventListener('change', () => { if (replaceModeOn) void runReplaceFind(); }));
rEl('#replace-input').addEventListener('input', updateReplaceStatus);
rEl('#replace-one').addEventListener('click', () => { void replaceOne(); });
rEl('#replace-all').addEventListener('click', () => { void replaceAllRequest(); });
rEl('#replace-confirm-yes').addEventListener('click', () => { void replaceAllConfirmed(); });
rEl('#replace-confirm-no').addEventListener('click', hideReplaceConfirm);

// --- Dropdown menus («Ще ▾» in the chapter actions, «⋯» of a paragraph) -------------------------------
// A button with aria-haspopup/aria-expanded and a panel positioned with position: fixed, so no scrolling
// or clipping container (the pinned actions row) cuts it off. Esc and a click outside close it; the arrow
// keys move between the items, Enter/Space activate them.

let openDropdown = null;
let dropdownCounter = 0;

function dropdownItems(panel) {
    return Array.from(panel.querySelectorAll('button, input, select')).filter((item) => !item.disabled && !item.hidden && item.type !== 'hidden');
}

function positionDropdown(button, panel) {
    panel.style.visibility = 'hidden';
    panel.hidden = false;
    const anchor = button.getBoundingClientRect();
    const width = panel.offsetWidth;
    const height = panel.offsetHeight;
    const left = Math.min(Math.max(8, anchor.right - width), Math.max(8, window.innerWidth - width - 8));
    let top = anchor.bottom + 4;
    if (top + height > window.innerHeight - 8) top = Math.max(8, anchor.top - height - 4);
    panel.style.left = `${left}px`;
    panel.style.top = `${top}px`;
    panel.style.visibility = '';
}

function closeDropdown({ returnFocus = false } = {}) {
    if (!openDropdown) return;
    const { button, panel, home } = openDropdown;
    openDropdown = null;
    panel.hidden = true;
    button.setAttribute('aria-expanded', 'false');
    if (home && panel.parentElement !== home) home.append(panel);
    if (returnFocus) button.focus();
}

function openDropdownMenu(button, panel, { toBody = false, focusFirst = false } = {}) {
    closeDropdown();
    const home = panel.parentElement;
    if (toBody) document.body.append(panel); // the pinned row has a backdrop-filter: fixed children would be placed inside it
    openDropdown = { button, panel, home: toBody ? home : null };
    button.setAttribute('aria-expanded', 'true');
    positionDropdown(button, panel);
    if (focusFirst) dropdownItems(panel)[0]?.focus();
}

function setupDropdown(button, panel, options = {}) {
    dropdownCounter += 1;
    panel.id = panel.id || `menu-panel-${dropdownCounter}`;
    button.setAttribute('aria-haspopup', 'true');
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-controls', panel.id);
    panel.hidden = true;
    panel.classList.add('menu-panel');
    button.addEventListener('click', (event) => {
        event.stopPropagation();
        if (openDropdown?.button === button) closeDropdown();
        else openDropdownMenu(button, panel, options);
    });
    button.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            openDropdownMenu(button, panel, { ...options, focusFirst: true });
        }
    });
    panel.addEventListener('keydown', (event) => {
        const items = dropdownItems(panel);
        const index = items.indexOf(document.activeElement);
        if (event.key === 'Escape') {
            event.preventDefault();
            event.stopPropagation();
            closeDropdown({ returnFocus: true });
        } else if (event.key === 'ArrowDown') {
            event.preventDefault();
            items[(index + 1) % items.length]?.focus();
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            items[(index - 1 + items.length) % items.length]?.focus();
        } else if (event.key === 'Home') {
            event.preventDefault();
            items[0]?.focus();
        } else if (event.key === 'End') {
            event.preventDefault();
            items[items.length - 1]?.focus();
        } else if (event.key === 'Enter' && document.activeElement?.type === 'checkbox') {
            event.preventDefault();
            document.activeElement.click();
        }
    });
}

document.addEventListener('pointerdown', (event) => {
    if (openDropdown && !openDropdown.panel.contains(event.target) && !openDropdown.button.contains(event.target)) closeDropdown();
}, true);
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && openDropdown) closeDropdown({ returnFocus: true });
});
window.addEventListener('scroll', (event) => {
    if (openDropdown && !openDropdown.panel.contains(event.target)) closeDropdown();
}, true);
window.addEventListener('resize', () => closeDropdown());

// «⋯» of a paragraph: the less used flags (the label/checkbox elements keep their classes, so the code
// that reads them by row.querySelector keeps working even while the panel is closed).
function createParagraphMenu(paragraphId, items) {
    const wrap = document.createElement('div');
    wrap.className = 'para-menu';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'para-menu-button';
    button.textContent = '⋯';
    button.setAttribute('aria-label', 'Ще для абзаца: службовий текст, черга на QA, оповідач');
    button.title = 'Службовий текст, черга на QA, оповідач';
    button.addEventListener('focus', () => setCurrentParagraph(paragraphId));
    const panel = document.createElement('div');
    panel.setAttribute('role', 'group');
    panel.setAttribute('aria-label', 'Позначки абзаца');
    panel.append(...items);
    wrap.append(button, panel);
    setupDropdown(button, panel);
    return wrap;
}

// «Ще ▾» of the chapter actions: the secondary actions. The buttons keep their ids.
function setupChapterMoreMenu() {
    const button = document.querySelector('#chapter-more-button');
    const panel = document.querySelector('#chapter-more-panel');
    if (!button || !panel) return;
    setupDropdown(button, panel, { toBody: true });
    panel.addEventListener('click', (event) => {
        if (event.target.closest('button')) closeDropdown();
    });
}
setupChapterMoreMenu();

// --- Density: «Звичайно» / «Компактно» (a per-browser choice) -----------------------------------------

// --- «Усі рушії»: the editor and two read-only panels (A, B) per paragraph --------------------------------
// The editor is the existing text field for the file, unchanged. Panel A (default Claude) sits under the original,
// panel B (default Gemini) under the editor; on a narrow screen they stack: original, editor, A, B. A panel shows
// one version of one engine's variant with «У файл», «Копіювати все у Вручну» and, for a selected fragment, the
// floating «→ Вручну». Panels are filled only for paragraphs near the screen (IntersectionObserver).

const COMPARE_ENGINE_CHOICES = ['claude', 'openai', 'gemini', 'deepl', 'current', 'manual'];
const COMPARE_SLOTS = ['a', 'b'];

function readCompareFlag(key) {
    try { return window.localStorage.getItem(key) === '1'; } catch (error) { return false; }
}

function writeCompareFlag(key, on) {
    try { window.localStorage.setItem(key, on ? '1' : '0'); } catch (error) { /* private mode: the choice still applies to this page */ }
}

function readCompareEngines() {
    // literals on purpose: this runs while the file is still loading, before the consts below exist
    const choices = ['claude', 'openai', 'gemini', 'deepl', 'current', 'manual'];
    try {
        const saved = JSON.parse(window.localStorage.getItem('workbench.compareEngines.engines') || 'null');
        if (saved && typeof saved === 'object') {
            return { a: choices.includes(saved.a) ? saved.a : 'claude', b: choices.includes(saved.b) ? saved.b : 'gemini' };
        }
    } catch (error) { /* ignore: defaults */ }
    return { a: 'claude', b: 'gemini' };
}

function writeCompareEngines() {
    try { window.localStorage.setItem('workbench.compareEngines.engines', JSON.stringify(compareEngines)); } catch (error) { /* private mode */ }
}

const compareToggleButton = document.querySelector('#compare-engines-toggle');
const compareDiffButton = document.querySelector('#compare-diff-toggle');
// paragraphId -> the last cursor/selection range inside that paragraph's editor (a live Range)
const compareEditorRanges = new Map();
const compareObserver = 'IntersectionObserver' in window
    ? new IntersectionObserver((entries) => entries.forEach((entry) => {
        const row = entry.target;
        row.dataset.compareNear = entry.isIntersecting ? '1' : '';
        if (entry.isIntersecting) fillRowComparePanels(row);
    }), { rootMargin: '800px 0px' })
    : null;
const compareSelectionButton = document.createElement('button');
compareSelectionButton.type = 'button';
compareSelectionButton.className = 'compare-selection-button primary-btn';
compareSelectionButton.textContent = '→ Вручну';
compareSelectionButton.title = 'Вставити виділений текст у редактор';
compareSelectionButton.hidden = true;
document.body.append(compareSelectionButton);

function compareEngineLabel(engine) {
    return VARIANT_LABELS[engine] || engine;
}

function comparePanelVariants(context, engine) {
    return (context.paragraph.translationVariants || []).filter((variant) => variant.engine === engine);
}

// The version a panel shows: the one picked with ‹ ›, else the one in the file, else the newest.
function comparePanelShown(context, slot) {
    const engine = compareEngines[slot];
    const versions = comparePanelVariants(context, engine);
    const picked = context.compare?.[slot]?.versionId;
    const shown = versions.find((variant) => variant.variantId === picked)
        || versions.find((variant) => variant.variantId === context.paragraph.selectedVariantId)
        || versions[versions.length - 1] || null;
    return { engine, versions, shown };
}

function attachComparePanels(row, context) {
    context.compare = { a: { versionId: null, expanded: false }, b: { versionId: null, expanded: false } };
    COMPARE_SLOTS.forEach((slot) => {
        const panel = document.createElement('section');
        panel.className = 'compare-panel';
        panel.dataset.slot = slot;
        panel.setAttribute('aria-label', `Панель ${slot.toUpperCase()}`);
        row.append(panel);
    });
    context.comparePanels = true;
    if (compareObserver) compareObserver.observe(row);
    else fillRowComparePanels(row);
}

function detachComparePanels(row, context) {
    row.querySelectorAll('.compare-panel').forEach((panel) => panel.remove());
    if (compareObserver) compareObserver.unobserve(row);
    delete row.dataset.compareNear;
    context.comparePanels = false;
    context.compare = null;
}

function fillRowComparePanels(row) {
    const context = variantContexts.get(row.dataset.paragraphId);
    if (!context?.comparePanels) return;
    COMPARE_SLOTS.forEach((slot) => fillComparePanel(context, slot));
    scheduleCompareDiff(row);
}

// The panels are drawn again after any change of the paragraph's variants (called from renderVariantBar).
function renderComparePanels(context) {
    if (!compareMode || !context.comparePanels) return;
    const row = context.row;
    COMPARE_SLOTS.forEach((slot) => {
        if (row.querySelector(`.compare-panel[data-slot="${slot}"]`)?.dataset.filled === '1') fillComparePanel(context, slot);
    });
    scheduleCompareDiff(row);
}

function compareButton(className, text, title, onClick) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.textContent = text;
    if (title) button.title = title;
    button.addEventListener('click', onClick);
    return button;
}

function fillComparePanel(context, slot) {
    const { paragraph, row } = context;
    const panel = row.querySelector(`.compare-panel[data-slot="${slot}"]`);
    if (!panel) return;
    const { engine, versions, shown } = comparePanelShown(context, slot);
    const state = context.compare[slot];
    panel.dataset.filled = '1';
    panel.dataset.engine = engine;
    panel.classList.toggle('compare-panel--expanded', state.expanded);
    panel.replaceChildren();

    const header = document.createElement('div');
    header.className = 'compare-panel-header';
    const select = document.createElement('select');
    select.className = 'compare-engine-select';
    select.setAttribute('aria-label', `Рушій панелі ${slot.toUpperCase()}`);
    COMPARE_ENGINE_CHOICES.forEach((choice) => select.append(new Option(compareEngineLabel(choice), choice)));
    select.value = engine;
    select.addEventListener('change', () => setCompareEngine(slot, select.value));
    header.append(select);
    if (versions.length > 1) {
        const position = versions.indexOf(shown);
        const step = (delta, label, text) => {
            const button = compareButton('compare-step', text, label, () => {
                const next = versions[Math.min(Math.max(position + delta, 0), versions.length - 1)];
                state.versionId = next.variantId;
                fillComparePanel(context, slot);
                scheduleCompareDiff(row);
            });
            button.disabled = position + delta < 0 || position + delta >= versions.length;
            return button;
        };
        const counter = document.createElement('span');
        counter.className = 'compare-version-counter';
        counter.textContent = `${position + 1}/${versions.length}`;
        counter.title = 'Версії цього рушія';
        header.append(step(-1, 'Попередня версія', '‹'), counter, step(1, 'Наступна версія', '›'));
    }
    const inFile = Boolean(shown && shown.variantId === paragraph.selectedVariantId);
    if (shown) {
        const badge = document.createElement('span');
        badge.className = 'compare-in-file';
        badge.dataset.inFile = inFile ? 'true' : 'false';
        badge.textContent = inFile ? '✓ у файлі' : '≠ не у файлі';
        badge.title = inFile ? 'Ця версія в файлі' : 'У файлі інший текст';
        header.append(badge);
    }
    const expand = compareButton('compare-expand', state.expanded ? '⤡' : '⤢', state.expanded ? 'Згорнути' : 'Розгорнути весь текст', () => {
        state.expanded = !state.expanded;
        fillComparePanel(context, slot);
    });
    expand.setAttribute('aria-pressed', state.expanded ? 'true' : 'false');
    expand.setAttribute('aria-label', state.expanded ? 'Згорнути панель' : 'Розгорнути панель');
    header.append(expand);
    panel.append(header);

    if (!shown) {
        const empty = document.createElement('div');
        empty.className = 'compare-empty';
        const message = document.createElement('p');
        message.textContent = 'немає перекладу';
        empty.append(message);
        if (['claude', 'openai', 'gemini', 'deepl'].includes(engine)) {
            const translate = compareButton('secondary-btn compare-translate', `Перекласти ${compareEngineLabel(engine)}`, '', () => { void translateComparePanel(context, slot, translate); });
            translate.disabled = !paragraph.paragraphId;
            empty.append(translate);
        }
        panel.append(empty);
        clearPanelSearchRanges(panel);
        return;
    }
    const meta = document.createElement('div');
    meta.className = 'compare-meta muted';
    meta.textContent = variantTooltip({ engine, variant: shown });
    meta.title = meta.textContent;
    const text = document.createElement('div');
    text.className = 'compare-panel-text';
    text.setAttribute('role', 'region');
    text.setAttribute('aria-label', `Переклад ${compareEngineLabel(engine)}, тільки для читання`);
    text.tabIndex = 0;
    text.innerHTML = renderFootnoteMarkers(sanitizeRichText(shown.text), paragraph.footnotes);
    panel.append(meta, text);
    const warnings = (shown.warnings || []).filter((warning) => warning.type === 'glossary_missing');
    if (warnings.length) {
        const warning = document.createElement('p');
        warning.className = 'variant-warning compare-warning';
        warning.textContent = `⚠ не використано термін глосарію: ${warnings.map((item) => `${item.source} → ${item.target}`).join('; ')}`;
        panel.append(warning);
    }
    const actions = document.createElement('div');
    actions.className = 'compare-panel-actions';
    const toFile = compareButton('secondary-btn compare-to-file', inFile ? '✓ У файлі' : 'У файл', inFile ? 'Ця версія в файлі' : 'Обрати цю версію для файлу', () => {
        void chooseVariantForFile(context, shown);
    });
    toFile.disabled = inFile || !paragraph.paragraphId;
    const copy = compareButton('secondary-btn compare-copy', 'Копіювати все у Вручну', 'Замінити текст редактора цим перекладом', () => copyVariantToEditor(context, shown, panel));
    actions.append(toFile, copy);
    panel.append(actions);
    const note = document.createElement('p');
    note.className = 'compare-note';
    note.setAttribute('role', 'status');
    note.hidden = true;
    panel.append(note);
    paintPanelSearch(panel);
}

function showCompareNote(panel, message) {
    const note = panel?.querySelector('.compare-note');
    if (!note) return;
    note.textContent = message;
    note.hidden = !message;
}

function setCompareEngine(slot, engine) {
    if (!COMPARE_ENGINE_CHOICES.includes(engine)) return;
    compareEngines[slot] = engine;
    writeCompareEngines();
    variantContexts.forEach((context) => {
        if (!context.comparePanels) return;
        context.compare[slot].versionId = null;
        if (context.row.querySelector(`.compare-panel[data-slot="${slot}"]`)?.dataset.filled === '1') fillComparePanel(context, slot);
        scheduleCompareDiff(context.row);
    });
    scheduleParagraphHeightsSync();
}

// «Перекласти {рушій}» of an empty panel: the same request as the button under the paragraph, with that engine's
// connection (DeepL: the remembered DeepL connection).
async function translateComparePanel(context, slot, button) {
    const { paragraph, state, index } = context;
    const engine = compareEngines[slot];
    const connectionId = engine === 'deepl' ? activeDeepLConnectionId : translationConnectionFor(engine)?.connectionId;
    if (engine !== 'deepl' && !connectionId) {
        window.alert(`Немає підключення ${compareEngineLabel(engine)}: додайте його в Connections.`);
        return;
    }
    button.disabled = true;
    button.textContent = 'Перекладаємо…';
    try {
        const translated = await WorkbenchApi.translateParagraph(paragraph.paragraphId, connectionId);
        if (translated.providerId === 'deepl') {
            setActiveDeepLConnectionId(translated.connectionId || activeDeepLConnectionId);
            void refreshDeepLUsageBadge();
        }
        if ((translated.translationText || '') !== (state.draft[index].translationText || '')) {
            state.undo.push(cloneParagraphDrafts(state.draft));
            state.redo = [];
        }
        const usage = createRunUsage();
        addRunUsage(usage, translated);
        showRunSummary(usage, '1 абзац');
        applyParagraphFromServer(paragraph, translated);
        clearParagraphDraftFromStorage(paragraph.paragraphId);
        updateParagraphVisualStates(state.draft);
        updateTranslationButtons();
    } catch (error) {
        if (error.code === 'quota_exceeded') void showDeepLQuotaDialog(error, () => translateComparePanel(context, slot, button));
        else window.alert(error.message);
    } finally {
        if (button.isConnected) {
            button.disabled = false;
            button.textContent = `Перекласти ${compareEngineLabel(engine)}`;
        }
    }
}

const COMPARE_MARKER_PATTERN = /([^]+)/g;

// «Копіювати все у Вручну»: the editor takes the whole text as an ordinary edit (undo, unsaved state, saved as
// «Вручну»). Footnote markers the editor had and the copied text lacks are appended at the end (never lost).
function copyVariantToEditor(context, variant, panel) {
    const editor = context.translation;
    const before = [...serializeRichText(editor).matchAll(COMPARE_MARKER_PATTERN)].map((match) => match[1]);
    let text = variant.text || '';
    const present = new Set([...text.matchAll(COMPARE_MARKER_PATTERN)].map((match) => match[1]));
    const missing = [...new Set(before)].filter((id) => !present.has(id));
    text += missing.map((id) => `${id}`).join('');
    editor.innerHTML = renderFootnoteMarkers(sanitizeRichText(text), context.paragraph.footnotes);
    editor.dispatchEvent(new Event('input', { bubbles: true }));
    compareEditorRanges.delete(context.paragraph.paragraphId);
    showCompareNote(panel, missing.length ? 'Маркери виносок дописано в кінець абзацу: перемістіть їх на потрібне місце.' : '');
    scheduleParagraphHeightsSync();
}

// --- «→ Вручну»: a selected fragment of a panel goes into the editor --------------------------------------
// The editor loses focus when the button is pressed, so the last cursor/selection inside it is remembered (a live
// Range, kept while the editor's DOM is not replaced). The text replaces that selection, or lands at the cursor;
// without a remembered cursor it is appended at the end after a space.

function compareSelectedText(range) {
    const holder = document.createElement('div');
    holder.append(range.cloneContents());
    holder.querySelectorAll('.footnote-marker').forEach((marker) => marker.remove());
    return holder.textContent || '';
}

function compareElementOf(node) {
    return node && (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement);
}

let compareSelectionFrame = null;
function updateCompareSelection() {
    compareSelectionFrame = null;
    const selection = document.getSelection();
    const hide = () => { compareSelectionButton.hidden = true; delete compareSelectionButton.dataset.paragraphId; };
    if (!compareMode || !selection || selection.rangeCount === 0) return hide();
    const range = selection.getRangeAt(0);
    const editor = compareElementOf(range.commonAncestorContainer)?.closest('.translation-paragraph');
    if (editor && editor.closest('.translation-row')) {
        compareEditorRanges.set(editor.dataset.paragraphId, range.cloneRange());
        return hide();
    }
    const panelText = compareElementOf(range.commonAncestorContainer)?.closest('.compare-panel-text');
    if (selection.isCollapsed || !panelText) return hide();
    const text = compareSelectedText(range);
    if (!text.trim()) return hide();
    const rects = range.getClientRects();
    const last = rects[rects.length - 1] || range.getBoundingClientRect();
    compareSelectionButton.dataset.paragraphId = panelText.closest('.translation-row')?.dataset.paragraphId || '';
    compareSelectionButton.hidden = false;
    const width = compareSelectionButton.offsetWidth || 90;
    const height = compareSelectionButton.offsetHeight || 36;
    // below the selection (on a touch screen the system menu appears above it), kept inside the window
    const left = Math.min(Math.max(8, last.right - width), window.innerWidth - width - 8);
    const top = Math.min(last.bottom + 8, window.innerHeight - height - 8);
    compareSelectionButton.style.left = `${left}px`;
    compareSelectionButton.style.top = `${Math.max(top, 8)}px`;
}

document.addEventListener('selectionchange', () => {
    if (!compareMode) return;
    // the editor's cursor is remembered at once (a later selection in a panel must not hide it); only the
    // floating button is positioned in the next frame
    const selection = document.getSelection();
    if (selection && selection.rangeCount) {
        const range = selection.getRangeAt(0);
        const editor = compareElementOf(range.commonAncestorContainer)?.closest('.translation-paragraph');
        if (editor?.closest('.translation-row')) compareEditorRanges.set(editor.dataset.paragraphId, range.cloneRange());
    }
    if (compareSelectionFrame !== null) return;
    compareSelectionFrame = requestAnimationFrame(updateCompareSelection);
});

function insertIntoEditor(paragraphId, text) {
    const context = variantContexts.get(paragraphId);
    if (!context || !text) return;
    const editor = context.translation;
    let range = compareEditorRanges.get(paragraphId);
    const usable = range && editor.contains(range.startContainer) && editor.contains(range.endContainer);
    if (!usable) {
        range = document.createRange();
        range.selectNodeContents(editor);
        range.collapse(false);
        const current = editor.textContent || '';
        if (current && !/\s$/.test(current)) text = ` ${text}`;
    }
    editor.focus({ preventScroll: true });
    const selection = document.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    let inserted = false;
    try { inserted = document.execCommand('insertText', false, text); } catch (error) { inserted = false; }
    if (!inserted) {
        range.deleteContents();
        const node = document.createTextNode(text);
        range.insertNode(node);
        range.setStartAfter(node);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);
        editor.dispatchEvent(new Event('input', { bubbles: true }));
    }
    if (selection.rangeCount) compareEditorRanges.set(paragraphId, selection.getRangeAt(0).cloneRange());
    scheduleParagraphHeightsSync();
}

['mousedown', 'pointerdown'].forEach((type) => compareSelectionButton.addEventListener(type, (event) => event.preventDefault()));
compareSelectionButton.addEventListener('click', () => {
    const paragraphId = compareSelectionButton.dataset.paragraphId;
    const selection = document.getSelection();
    if (!paragraphId || !selection || selection.rangeCount === 0) return;
    const text = compareSelectedText(selection.getRangeAt(0));
    compareSelectionButton.hidden = true;
    insertIntoEditor(paragraphId, text);
});

// --- the mode switch ---------------------------------------------------------------------------------------

function setCompareMode(on) {
    compareMode = Boolean(on);
    writeCompareFlag('workbench.compareEngines.mode', compareMode);
    compareToggleButton.setAttribute('aria-pressed', compareMode ? 'true' : 'false');
    compareDiffButton.hidden = !compareMode;
    document.body.classList.toggle('compare-mode', compareMode);
    compareSelectionButton.hidden = true;
    const state = translationStates.get(selectedChapterIndex);
    if (compareMode && state?.viewEngine) state.viewEngine = null; // the view selector is not needed here
    variantContexts.forEach((context) => {
        if (compareMode) {
            restoreChosenTextInEditor(context); // the editor shows the text for the file, not an older manual one
            if (!context.comparePanels) attachComparePanels(context.row, context);
            renderVariantBar(context, 'manual');
        } else {
            detachComparePanels(context.row, context);
            renderVariantBar(context, defaultVariantTab(context.paragraph, context.state.draft[context.index]));
        }
    });
    if (!compareMode) clearCompareDiff();
    refreshChapterViewControls(true);
    scheduleParagraphHeightsSync();
}

compareToggleButton.addEventListener('click', () => setCompareMode(!compareMode));
compareToggleButton.setAttribute('aria-pressed', compareMode ? 'true' : 'false');
compareDiffButton.hidden = !compareMode;
compareDiffButton.setAttribute('aria-pressed', compareDiffOn ? 'true' : 'false');
document.body.classList.toggle('compare-mode', compareMode);
compareDiffButton.addEventListener('click', () => {
    compareDiffOn = !compareDiffOn;
    writeCompareFlag('workbench.compareEngines.diff', compareDiffOn);
    compareDiffButton.setAttribute('aria-pressed', compareDiffOn ? 'true' : 'false');
    if (!compareDiffOn) clearCompareDiff();
    else translationRows.querySelectorAll('.translation-row[data-compare-near="1"]').forEach((row) => scheduleCompareDiff(row));
});
if (!(typeof Highlight !== 'undefined' && window.CSS && CSS.highlights)) {
    compareDiffButton.disabled = true;
    compareDiffButton.title = 'Цей браузер не підтримує підсвітку тексту (CSS Custom Highlight API)';
}

// --- search highlights in the panels (highlight only; replacing works on the editor) -----------------------

function clearPanelSearchRanges(panel) {
    const all = window.CSS?.highlights?.get('search-all');
    (panel.__searchRanges || []).forEach((range) => all?.delete(range));
    panel.__searchRanges = [];
}

function paintPanelSearch(panel, all = window.CSS?.highlights?.get('search-all')) {
    clearPanelSearchRanges(panel);
    const text = panel.querySelector('.compare-panel-text');
    if (!all || !text || !lastSearchQuery || searchDialog.hidden || searchQueryField(lastSearchQuery) !== 'translation_text') return;
    panel.__searchRanges = plainSearchRanges(text);
    panel.__searchRanges.forEach((range) => all.add(range));
}

function paintSearchInPanels(row, all) {
    row.querySelectorAll('.compare-panel[data-filled="1"]').forEach((panel) => paintPanelSearch(panel, all));
}

// --- «Підсвітити відмінності»: words that differ between the editor and the panels ---------------------------
// Word-level LCS between the shown texts; a word is marked when it has no counterpart in at least one other text.
// Only paragraphs near the screen are compared (the observer's flag), a few hundred words at most.

const compareDiffRanges = new Map(); // row -> Range[]
let compareDiffHighlight = null;
const compareDiffTimers = new Map();

function clearCompareDiff() {
    compareDiffTimers.forEach((timer) => window.clearTimeout(timer));
    compareDiffTimers.clear();
    compareDiffRanges.clear();
    if (window.CSS?.highlights) CSS.highlights.delete('compare-diff');
    compareDiffHighlight = null;
}

function compareTokens(root) {
    const { nodes, text } = searchTextNodes(root);
    const tokens = [];
    const pattern = /[\p{L}\p{N}]+(?:['’ʼ-][\p{L}\p{N}]+)*/gu;
    let match;
    while ((match = pattern.exec(text))) tokens.push({ word: match[0].toLowerCase(), start: match.index, end: match.index + match[0].length });
    return { nodes, tokens };
}

// For each token of `a`: true when it takes part in a longest common subsequence with `b`.
function compareMatched(a, b) {
    const n = a.length;
    const m = b.length;
    const table = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
    for (let i = n - 1; i >= 0; i -= 1) {
        for (let j = m - 1; j >= 0; j -= 1) {
            table[i][j] = a[i].word === b[j].word ? table[i + 1][j + 1] + 1 : Math.max(table[i + 1][j], table[i][j + 1]);
        }
    }
    const matched = new Array(n).fill(false);
    let i = 0;
    let j = 0;
    while (i < n && j < m) {
        if (a[i].word === b[j].word) { matched[i] = true; i += 1; j += 1; }
        else if (table[i + 1][j] >= table[i][j + 1]) i += 1;
        else j += 1;
    }
    return matched;
}

function scheduleCompareDiff(row) {
    if (!compareMode || !compareDiffOn || !row || !window.CSS?.highlights || typeof Highlight === 'undefined') return;
    window.clearTimeout(compareDiffTimers.get(row));
    compareDiffTimers.set(row, window.setTimeout(() => { compareDiffTimers.delete(row); runCompareDiff(row); }, 120));
}

function runCompareDiff(row) {
    if (!row.isConnected) return;
    if (!compareDiffHighlight) {
        compareDiffHighlight = new Highlight();
        CSS.highlights.set('compare-diff', compareDiffHighlight);
    }
    (compareDiffRanges.get(row) || []).forEach((range) => compareDiffHighlight.delete(range));
    compareDiffRanges.delete(row);
    const roots = [row.querySelector('.translation-paragraph'), ...row.querySelectorAll('.compare-panel-text')].filter(Boolean);
    const sources = roots.map((root) => ({ root, ...compareTokens(root) })).filter((source) => source.tokens.length);
    if (sources.length < 2 || sources.some((source) => source.tokens.length > 350)) return;
    const ranges = [];
    sources.forEach((source, index) => {
        const different = new Array(source.tokens.length).fill(false);
        sources.forEach((other, otherIndex) => {
            if (otherIndex === index) return;
            compareMatched(source.tokens, other.tokens).forEach((matched, tokenIndex) => { if (!matched) different[tokenIndex] = true; });
        });
        different.forEach((isDifferent, tokenIndex) => {
            if (!isDifferent) return;
            const token = source.tokens[tokenIndex];
            const range = searchRangeFromOffsets(source.nodes, token.start, token.end);
            if (range) ranges.push(range);
        });
    });
    ranges.forEach((range) => compareDiffHighlight.add(range));
    compareDiffRanges.set(row, ranges);
}

// a typed or inserted change in the editor moves the differences
translationRows.addEventListener('input', (event) => {
    if (!compareMode || !compareDiffOn) return;
    const row = event.target.closest?.('.translation-row');
    if (row) scheduleCompareDiff(row);
});

const DENSITY_STORAGE_KEY = 'workbench.density';

function readStoredDensity() {
    try {
        const value = window.localStorage.getItem(DENSITY_STORAGE_KEY);
        return value === 'compact' || value === 'normal' ? value : null;
    } catch {
        return null;
    }
}

// Without a choice: compact for a mouse (fine pointer), normal for touch. Touch targets stay >= 44px in both
// (see the pointer: coarse rule in styles.css).
function effectiveDensity() {
    return readStoredDensity() || (window.matchMedia('(pointer: fine)').matches ? 'compact' : 'normal');
}

function applyDensity() {
    document.documentElement.dataset.density = effectiveDensity();
    const select = document.querySelector('#density-select');
    if (select) select.value = effectiveDensity();
    syncTopbarHeight();
    window.requestAnimationFrame(() => { syncTopbarHeight(); syncPinnedRows(); });
}

function setDensity(value) {
    try {
        window.localStorage.setItem(DENSITY_STORAGE_KEY, value);
    } catch {
        // the choice still applies to this page
    }
    applyDensity();
    scheduleParagraphHeightsSync();
}

document.querySelector('#density-select')?.addEventListener('change', (event) => setDensity(event.target.value));
applyDensity();
