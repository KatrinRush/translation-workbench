"""
Patch 34: persist AI QA findings and retry failed batches automatically.

Катя's decisions from testing patch 33:
  1. Only UNRESOLVED findings should ever be stored — once she accepts or
     dismisses one (✔️/✖️), it's no longer needed and should be gone, not
     kept around as dead weight. So: findings persist in a new
     chapter_qa_findings table until explicitly resolved, at which point
     they're deleted outright (no "resolved" flag, no history row).
  2. A batch that fails to parse should retry automatically rather than
     silently leaving those paragraphs unchecked until she notices and
     re-runs by hand.

This patch is backend-only (storage.py schema/methods + qa/service.py +
new server.py routes). Frontend wiring (fetch-on-open, delete-on-mark) is
a separate follow-up patch.

New endpoints:
  GET    /api/projects/{projectId}/chapters/{chapterId}/qa-findings
         -> current pending findings for the chapter (same shape as the
            qa-check response, for restoring state when reopening a chapter)
  DELETE /api/qa-findings/{findingId}
         -> marks a finding resolved by deleting it outright

check_chapter_translation_quality now:
  - retries a batch once before recording it as failed
  - saves new findings via INSERT OR IGNORE (the table's UNIQUE constraint
    on chapter+paragraph+category+quote+model does the same dedup patch 33
    did client-side, now enforced server-side)
  - always returns the full current pending set (this run's new findings
    merged with whatever was already stored), not just what this call found

Depends on patches 25-33 already being applied.

Run from the repo root (same folder as backend/):
    python apply_patch34.py
"""
from pathlib import Path

STORAGE_PATH = Path("backend/storage.py")
QA_SERVICE_PATH = Path("backend/qa/service.py")
SERVER_PATH = Path("backend/server.py")


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
    # === storage.py ===

    # 1. Schema: new table, same shape/pattern as paragraph_footnotes
    apply(
        STORAGE_PATH,
        '''CREATE TABLE IF NOT EXISTS paragraph_footnotes (
    footnote_id TEXT PRIMARY KEY,
    paragraph_id TEXT NOT NULL REFERENCES book_paragraphs(paragraph_id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paragraph_footnotes_paragraph ON paragraph_footnotes(paragraph_id);''',
        '''CREATE TABLE IF NOT EXISTS paragraph_footnotes (
    footnote_id TEXT PRIMARY KEY,
    paragraph_id TEXT NOT NULL REFERENCES book_paragraphs(paragraph_id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paragraph_footnotes_paragraph ON paragraph_footnotes(paragraph_id);

-- AI QA findings pending review. A finding is deleted outright (not
-- flagged resolved) once accepted or dismissed in the UI -- only
-- not-yet-decided findings are worth keeping around.
CREATE TABLE IF NOT EXISTS chapter_qa_findings (
    finding_id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL REFERENCES book_chapters(chapter_id) ON DELETE CASCADE,
    paragraph_id TEXT NOT NULL,
    category TEXT NOT NULL,
    quote TEXT NOT NULL,
    explanation TEXT,
    suggestion TEXT,
    source_model TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(chapter_id, paragraph_id, category, quote, source_model)
);

CREATE INDEX IF NOT EXISTS idx_chapter_qa_findings_chapter ON chapter_qa_findings(chapter_id);''',
    )

    # 2. Storage methods: list / add (dedup via INSERT OR IGNORE) / delete
    apply(
        STORAGE_PATH,
        '''    def list_paragraph_footnotes(self, paragraph_id: str) -> list[dict[str, Any]]:''',
        '''    def list_chapter_qa_findings(self, chapter_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM chapter_qa_findings WHERE chapter_id = ? ORDER BY created_at",
                (chapter_id,),
            ).fetchall()
        return [self._qa_finding_from_row(row) for row in rows]

    def add_chapter_qa_findings(self, chapter_id: str, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timestamp = _now()
        with self.connection() as connection:
            for finding in findings:
                connection.execute(
                    "INSERT OR IGNORE INTO chapter_qa_findings"
                    "(finding_id, chapter_id, paragraph_id, category, quote, explanation, suggestion, source_model, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        _new_id("qa-finding"),
                        chapter_id,
                        finding["paragraphId"],
                        finding["category"],
                        finding["quote"],
                        finding.get("explanation"),
                        finding.get("suggestion"),
                        finding["sourceModel"],
                        timestamp,
                    ),
                )
        return self.list_chapter_qa_findings(chapter_id)

    def delete_chapter_qa_finding(self, finding_id: str) -> bool:
        with self.connection() as connection:
            cursor = connection.execute("DELETE FROM chapter_qa_findings WHERE finding_id = ?", (finding_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _qa_finding_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "findingId": row["finding_id"],
            "chapterId": row["chapter_id"],
            "paragraphId": row["paragraph_id"],
            "category": row["category"],
            "quote": row["quote"],
            "explanation": row["explanation"],
            "suggestion": row["suggestion"],
            "sourceModel": row["source_model"],
            "createdAt": row["created_at"],
        }

    def list_paragraph_footnotes(self, paragraph_id: str) -> list[dict[str, Any]]:''',
    )

    # === qa/service.py ===

    # 3. Replace check_chapter_translation_quality: retry once per batch,
    #    persist new findings, and return the full current pending set.
    apply(
        QA_SERVICE_PATH,
        '''    def check_chapter_translation_quality(self, project_id: str, chapter_id: str, connection_ids: list[str]) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise QaServiceError("Project not found.", 404, "not_found")
        if not isinstance(connection_ids, list) or not connection_ids or not all(isinstance(item, str) and item.strip() for item in connection_ids):
            raise QaServiceError("Choose at least one AI connection.", 400, "qa_invalid")

        paragraphs = self._storage.get_chapter_paragraphs(chapter_id)
        translatable = [p for p in paragraphs if not p["isService"] and p.get("translationText")]
        if not translatable:
            raise QaServiceError("Chapter has no translated paragraphs to check.", 400, "qa_empty")
        paragraph_by_id = {p["paragraphId"]: p for p in translatable}
        batches = [
            translatable[i:i + self._QUALITY_BATCH_SIZE]
            for i in range(0, len(translatable), self._QUALITY_BATCH_SIZE)
        ]

        speech_registers = self._storage.get_project_character_registers(project_id)

        connections = {item["connectionId"]: item for item in self._storage.list_integration_connections()}
        findings_by_paragraph: dict[str, list[dict[str, Any]]] = {}
        error_messages: dict[str, list[str]] = {}

        for connection_id in dict.fromkeys(connection_ids):
            connection = connections.get(connection_id)
            if connection is None or not connection["enabled"] or connection["testStatus"] != "connected":
                error_messages[connection_id] = ["AI connection is not active and tested."]
                continue
            provider_id = connection["providerId"]
            if provider_id == "deepl":
                error_messages[connection_id] = ["This connection cannot run AI QA."]
                continue
            try:
                provider, credentials = self._provider_credentials(connection)
            except QaServiceError as error:
                error_messages[connection_id] = [str(error)]
                continue
            for batch in batches:
                prompt = self._build_quality_prompt(batch, speech_registers)
                try:
                    raw_text = provider.analyze(credentials, prompt)
                    parsed = self._parse_quality_response(raw_text)
                except (ValueError, QaServiceError) as error:
                    error_messages.setdefault(connection_id, []).append(str(error))
                    continue
                for item in parsed:
                    paragraph_id = item.get("paragraphId")
                    if paragraph_id not in paragraph_by_id:
                        continue
                    findings_by_paragraph.setdefault(paragraph_id, []).append({
                        "category": item["category"],
                        "quote": item.get("quote", ""),
                        "explanation": item.get("explanation", ""),
                        "suggestion": item.get("suggestion", ""),
                        "sourceModel": provider_id,
                    })

        counts = {"critical": 0, "stylistic": 0, "typo": 0}
        for findings in findings_by_paragraph.values():
            for finding in findings:
                counts[finding["category"]] += 1

        errors = {
            connection_id: f"{len(messages)} з {len(batches)} частин розділу не вдалося перевірити: {messages[0]}"
            for connection_id, messages in error_messages.items()
        }

        return {
            "chapterId": chapter_id,
            "counts": counts,
            "paragraphResults": [
                {"paragraphId": paragraph_id, "findings": findings}
                for paragraph_id, findings in findings_by_paragraph.items()
            ],
            "errors": errors,
        }''',
        '''    _QUALITY_BATCH_ATTEMPTS = 2

    def check_chapter_translation_quality(self, project_id: str, chapter_id: str, connection_ids: list[str]) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise QaServiceError("Project not found.", 404, "not_found")
        if not isinstance(connection_ids, list) or not connection_ids or not all(isinstance(item, str) and item.strip() for item in connection_ids):
            raise QaServiceError("Choose at least one AI connection.", 400, "qa_invalid")

        paragraphs = self._storage.get_chapter_paragraphs(chapter_id)
        translatable = [p for p in paragraphs if not p["isService"] and p.get("translationText")]
        if not translatable:
            raise QaServiceError("Chapter has no translated paragraphs to check.", 400, "qa_empty")
        paragraph_by_id = {p["paragraphId"]: p for p in translatable}
        batches = [
            translatable[i:i + self._QUALITY_BATCH_SIZE]
            for i in range(0, len(translatable), self._QUALITY_BATCH_SIZE)
        ]

        speech_registers = self._storage.get_project_character_registers(project_id)

        connections = {item["connectionId"]: item for item in self._storage.list_integration_connections()}
        new_findings: list[dict[str, Any]] = []
        error_messages: dict[str, list[str]] = {}

        for connection_id in dict.fromkeys(connection_ids):
            connection = connections.get(connection_id)
            if connection is None or not connection["enabled"] or connection["testStatus"] != "connected":
                error_messages[connection_id] = ["AI connection is not active and tested."]
                continue
            provider_id = connection["providerId"]
            if provider_id == "deepl":
                error_messages[connection_id] = ["This connection cannot run AI QA."]
                continue
            try:
                provider, credentials = self._provider_credentials(connection)
            except QaServiceError as error:
                error_messages[connection_id] = [str(error)]
                continue
            for batch in batches:
                prompt = self._build_quality_prompt(batch, speech_registers)
                parsed = None
                last_error: Exception | None = None
                for _attempt in range(self._QUALITY_BATCH_ATTEMPTS):
                    try:
                        raw_text = provider.analyze(credentials, prompt)
                        parsed = self._parse_quality_response(raw_text)
                        break
                    except (ValueError, QaServiceError) as error:
                        last_error = error
                if parsed is None:
                    error_messages.setdefault(connection_id, []).append(str(last_error))
                    continue
                for item in parsed:
                    paragraph_id = item.get("paragraphId")
                    if paragraph_id not in paragraph_by_id:
                        continue
                    new_findings.append({
                        "paragraphId": paragraph_id,
                        "category": item["category"],
                        "quote": item.get("quote", ""),
                        "explanation": item.get("explanation", ""),
                        "suggestion": item.get("suggestion", ""),
                        "sourceModel": provider_id,
                    })

        if new_findings:
            self._storage.add_chapter_qa_findings(chapter_id, new_findings)
        current_findings = self._storage.list_chapter_qa_findings(chapter_id)

        errors = {
            connection_id: f"{len(messages)} з {len(batches)} частин розділу не вдалося перевірити: {messages[0]}"
            for connection_id, messages in error_messages.items()
        }

        return {
            "chapterId": chapter_id,
            "counts": self._count_findings(current_findings),
            "paragraphResults": self._group_findings_by_paragraph(current_findings),
            "errors": errors,
        }

    def list_chapter_qa_findings(self, chapter_id: str) -> dict[str, Any]:
        current_findings = self._storage.list_chapter_qa_findings(chapter_id)
        return {
            "chapterId": chapter_id,
            "counts": self._count_findings(current_findings),
            "paragraphResults": self._group_findings_by_paragraph(current_findings),
        }

    def resolve_chapter_qa_finding(self, finding_id: str) -> None:
        if not self._storage.delete_chapter_qa_finding(finding_id):
            raise QaServiceError("Finding not found.", 404, "not_found")

    @staticmethod
    def _count_findings(findings: list[dict[str, Any]]) -> dict[str, int]:
        counts = {"critical": 0, "stylistic": 0, "typo": 0}
        for finding in findings:
            if finding["category"] in counts:
                counts[finding["category"]] += 1
        return counts

    @staticmethod
    def _group_findings_by_paragraph(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for finding in findings:
            grouped.setdefault(finding["paragraphId"], []).append({
                "findingId": finding["findingId"],
                "category": finding["category"],
                "quote": finding["quote"],
                "explanation": finding.get("explanation") or "",
                "suggestion": finding.get("suggestion") or "",
                "sourceModel": finding["sourceModel"],
            })
        return [
            {"paragraphId": paragraph_id, "findings": findings}
            for paragraph_id, findings in grouped.items()
        ]''',
    )

    # === server.py ===

    # 4. Import QaServiceError is already done in patch 29; add the two new routes
    apply(
        SERVER_PATH,
        '''            data = self.read_json()
            connection_ids = data.get("connectionIds", [])
            return 200, qa_service.check_chapter_translation_quality(parts[2], parts[4], connection_ids)''',
        '''            data = self.read_json()
            connection_ids = data.get("connectionIds", [])
            return 200, qa_service.check_chapter_translation_quality(parts[2], parts[4], connection_ids)
        if (
            len(parts) == 6
            and parts[0] == "api"
            and parts[1] == "projects"
            and parts[3] == "chapters"
            and parts[5] == "qa-findings"
            and method == "GET"
        ):
            return 200, qa_service.list_chapter_qa_findings(parts[4])
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "qa-findings" and method == "DELETE":
            qa_service.resolve_chapter_qa_finding(parts[2])
            return 204, None''',
    )

    print("Patch 34 applied successfully.")


if __name__ == "__main__":
    main()
