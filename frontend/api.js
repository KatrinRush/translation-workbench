const WorkbenchApi = {
    async request(path, options = {}) {
        const response = await fetch(path, {
            headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
            ...options
        });
        if (response.status === 204) {
            return null;
        }
        const rawBody = await response.text();
        let payload = null;
        if (rawBody) {
            try {
                payload = JSON.parse(rawBody);
            } catch {
                throw new Error(`Workbench повернув відповідь без JSON (HTTP ${response.status}).`);
            }
        }
        if (!response.ok) {
            throw new Error(payload?.error || `Запит до Workbench не вдався (HTTP ${response.status}).`);
        }
        if (payload === null) {
            // An empty body on a 2xx means the connection dropped mid-response, usually a restarted backend.
            throw new Error(`Workbench повернув порожню відповідь (HTTP ${response.status}). Перевірте, чи backend не перезапускався під час запиту.`);
        }
        return payload;
    },

    listAuthors() {
        return this.request('/api/authors');
    },

    createAuthor(author) {
        return this.request('/api/authors', { method: 'POST', body: JSON.stringify(author) });
    },

    updateAuthor(authorId, author) {
        return this.request(`/api/authors/${encodeURIComponent(authorId)}`, { method: 'PUT', body: JSON.stringify(author) });
    },

    deleteAuthor(authorId) {
        return this.request(`/api/authors/${encodeURIComponent(authorId)}`, { method: 'DELETE' });
    },

    listSeries() {
        return this.request('/api/series');
    },

    createSeries(series) {
        return this.request('/api/series', { method: 'POST', body: JSON.stringify(series) });
    },

    updateSeries(seriesId, series) {
        return this.request(`/api/series/${encodeURIComponent(seriesId)}`, { method: 'PUT', body: JSON.stringify(series) });
    },

    deleteSeries(seriesId) {
        return this.request(`/api/series/${encodeURIComponent(seriesId)}`, { method: 'DELETE' });
    },

    listIntegrationProviders() {
        return this.request('/api/integration-providers');
    },

    listConnections() {
        return this.request('/api/connections');
    },

    createConnection(connection) {
        return this.request('/api/connections', { method: 'POST', body: JSON.stringify(connection) });
    },

    updateConnection(connectionId, connection) {
        return this.request(`/api/connections/${encodeURIComponent(connectionId)}`, {
            method: 'PUT',
            body: JSON.stringify(connection)
        });
    },

    testConnection(connectionId) {
        return this.request(`/api/connections/${encodeURIComponent(connectionId)}/test`, { method: 'POST' });
    },

    deleteConnection(connectionId) {
        return this.request(`/api/connections/${encodeURIComponent(connectionId)}`, { method: 'DELETE' });
    },

    listRules() {
        return this.request('/api/rules');
    },

    createRule(rule) {
        return this.request('/api/rules', { method: 'POST', body: JSON.stringify(rule) });
    },

    updateRule(ruleId, rule) {
        return this.request(`/api/rules/${encodeURIComponent(ruleId)}`, { method: 'PUT', body: JSON.stringify(rule) });
    },

    deleteRule(ruleId) {
        return this.request(`/api/rules/${encodeURIComponent(ruleId)}`, { method: 'DELETE' });
    },

    listGlossary() {
        return this.request('/api/glossary');
    },

    createGlossaryEntry(entry) {
        return this.request('/api/glossary', { method: 'POST', body: JSON.stringify(entry) });
    },

    updateGlossaryEntry(entryId, entry) {
        return this.request(`/api/glossary/${encodeURIComponent(entryId)}`, { method: 'PUT', body: JSON.stringify(entry) });
    },

    deleteGlossaryEntry(entryId) {
        return this.request(`/api/glossary/${encodeURIComponent(entryId)}`, { method: 'DELETE' });
    },

    getSeriesAuthorContext(seriesId, authorId) {
        return this.request(`/api/series-author-contexts/${encodeURIComponent(seriesId)}/${encodeURIComponent(authorId)}`);
    },

    saveSeriesAuthorContext(seriesId, authorId, context) {
        return this.request(`/api/series-author-contexts/${encodeURIComponent(seriesId)}/${encodeURIComponent(authorId)}`, {
            method: 'PUT',
            body: JSON.stringify(context)
        });
    },

    listProjects() {
        return this.request('/api/projects');
    },

    createProject(project) {
        return this.request('/api/projects', { method: 'POST', body: JSON.stringify(project) });
    },

    getProject(projectId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}`);
    },

    updateProject(projectId, project) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}`, {
            method: 'PUT',
            body: JSON.stringify(project)
        });
    },

    updateProjectTranslationRules(projectId, translationRules) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/translation-rules`, {
            method: 'PUT',
            body: JSON.stringify({ translationRules })
        });
    },

    listProjectTranslationGlossaries(projectId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/translation-glossaries`);
    },

    saveProjectTranslationGlossary(projectId, glossary) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/translation-glossaries`, {
            method: 'PUT',
            body: JSON.stringify(glossary)
        });
    },

    getProjectTranslationGlossaryCurrentVersion(projectId, glossaryRuleId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/translation-glossaries/${encodeURIComponent(glossaryRuleId)}/current-version`);
    },

    materializeProjectTranslationGlossaryVersion(projectId, glossaryRuleId, versionId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/translation-glossaries/${encodeURIComponent(glossaryRuleId)}/versions/${encodeURIComponent(versionId)}`);
    },

    commitProjectTranslationGlossaryDraft(projectId, draft) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/translation-glossaries/commit`, {
            method: 'POST',
            body: JSON.stringify(draft)
        });
    },

    deleteProject(projectId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}`, { method: 'DELETE' });
    },

    async uploadProjectCover(projectId, file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/cover`, {
            method: 'POST',
            body: formData,
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.error || 'Не вдалося завантажити обкладинку.');
        }
        return payload;
    },

    deleteProjectCover(projectId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/cover`, { method: 'DELETE' });
    },

    getProjectBookStructure(projectId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/book/structure`);
    },

    async downloadProjectBookArchive(projectId, translations) {
        const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/book/archive`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ translations })
        });
        if (!response.ok) {
            const payload = await response.json();
            throw new Error(payload.error || 'Не вдалося сформувати архів.');
        }
        return { blob: await response.blob(), filename: response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] || 'workbench_archive.zip' };
    },

    updateParagraph(paragraphId, data) {
        return this.request(`/api/paragraphs/${encodeURIComponent(paragraphId)}`, { method: 'PUT', body: JSON.stringify(data) });
    },

    translateParagraph(paragraphId) {
        return this.request(`/api/paragraphs/${encodeURIComponent(paragraphId)}/translate`, {
            method: 'POST',
            body: JSON.stringify({})
        });
    },

    translateChapter(projectId, chapterId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/chapters/${encodeURIComponent(chapterId)}/translate`, {
            method: 'POST',
            body: JSON.stringify({})
        });
    },

    updateChapterTitle(chapterId, data) {
        return this.request(`/api/chapters/${encodeURIComponent(chapterId)}/title`, { method: 'PUT', body: JSON.stringify(data) });
    },

    inlineImageUrl(imageId) {
        return `/api/inline-images/${encodeURIComponent(imageId)}`;
    },

    listProjectBrief(projectId) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/brief`);
    },

    createProjectBriefEntry(projectId, data) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/brief`, { method: 'POST', body: JSON.stringify(data) });
    },

    updateProjectBriefEntry(projectId, entryId, data) {
        return this.request(`/api/projects/${encodeURIComponent(projectId)}/brief/${encodeURIComponent(entryId)}`, { method: 'PATCH', body: JSON.stringify(data) });
    }
};