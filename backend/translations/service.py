"""Application service for translating one imported text unit."""

from __future__ import annotations

from typing import Any
import hashlib
import json
import xml.etree.ElementTree as ET

from ..integrations.base import GlossaryDefinition, GlossaryLimitError, TranslationRequest
from ..integrations.credentials import CredentialVault, CredentialVaultError
from ..integrations.registry import ProviderRegistry
from .chunking_service import ChunkPreparationService


class TranslationServiceError(RuntimeError):
    def __init__(self, message: str, http_status: int = 400, code: str = "translation_error"):
        super().__init__(message)
        self.http_status = http_status
        self.code = code


class TranslationService:
    def __init__(self, storage, vault: CredentialVault, registry: ProviderRegistry):
        self._storage = storage
        self._vault = vault
        self._registry = registry

    def list_project_glossaries(self, project_id: str) -> list[dict[str, Any]]:
        if self._storage.get_project(project_id) is None:
            raise TranslationServiceError("Project not found.", 404, "not_found")
        return self._storage.list_project_translation_glossaries(project_id)

    def get_project_glossary_current_version(self, project_id: str, glossary_rule_id: str) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise TranslationServiceError("Project not found.", 404, "not_found")
        glossary = self._storage.get_project_translation_glossary(glossary_rule_id)
        if glossary is None or glossary.get("projectId") != project_id:
            raise TranslationServiceError("Glossary not found.", 404, "not_found")
        current_version = self._storage.get_translation_glossary_current_version(glossary_rule_id)
        if current_version is None:
            raise TranslationServiceError("Glossary current version is unavailable.", 409, "version_unavailable")
        return current_version

    def materialize_project_glossary_version(self, project_id: str, glossary_rule_id: str, version_id: str | None = None) -> dict[str, Any]:
        current = self.get_project_glossary_current_version(project_id, glossary_rule_id)
        resolved_version_id = version_id or current["versionId"]
        materialized = self._storage.materialize_translation_glossary_version(resolved_version_id)
        if materialized is None or materialized["glossaryRuleId"] != glossary_rule_id:
            raise TranslationServiceError("Glossary version not found.", 404, "not_found")
        return materialized

    def commit_project_glossary_version(self, project_id: str, glossary_rule_id: str, glossary_entry_ids: list[str]) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise TranslationServiceError("Project not found.", 404, "not_found")
        glossary = self._storage.get_project_translation_glossary(glossary_rule_id)
        if glossary is None or glossary.get("projectId") != project_id:
            raise TranslationServiceError("Glossary not found.", 404, "not_found")
        try:
            return self._storage.commit_translation_glossary_version(glossary_rule_id, glossary_entry_ids)
        except ValueError as error:
            raise TranslationServiceError(str(error), 400, "version_commit_invalid") from error

    def commit_project_glossary_draft(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise TranslationServiceError("Project not found.", 404, "not_found")

        source_language = str(data.get("sourceLanguage", "")).strip().upper()
        target_language = str(data.get("targetLanguage", "")).strip().upper()
        glossary_rule_id = data.get("glossaryRuleId")
        glossary_entry_ids = data.get("glossaryEntryIds")

        if not source_language or not target_language:
            raise TranslationServiceError("Вкажіть мови глосарію.", 400, "version_commit_invalid")
        if not isinstance(glossary_entry_ids, list):
            raise TranslationServiceError("Передайте список GlossaryItem ID.", 400, "version_commit_invalid")

        try:
            glossary = self._storage.get_or_create_project_translation_glossary(
                project_id,
                source_language,
                target_language,
                glossary_rule_id,
            )
            self._storage.commit_translation_glossary_version(
                glossary["glossaryRuleId"],
                glossary_entry_ids,
            )
        except ValueError as error:
            raise TranslationServiceError(str(error), 400, "version_commit_invalid") from error

        sync_result = self._sync_glossary_with_provider(
            glossary["glossaryRuleId"],
            data.get("connectionId"),
        )
        saved = self._storage.get_project_translation_glossary(glossary["glossaryRuleId"])
        saved["providerSyncResult"] = sync_result
        return saved

    def _sync_glossary_with_provider(self, glossary_rule_id: str, connection_id: Any = None) -> dict[str, Any]:
        """Publish the current local version to the provider, keeping one remote glossary per rule."""
        glossary = self._storage.get_project_translation_glossary(glossary_rule_id)
        existing_sync = glossary.get("providerSync") if glossary else None
        if glossary is None:
            return self._sync_failure("not_found", "Glossary not found.", 404)
        if existing_sync and existing_sync["contentHash"] == glossary["contentHash"]:
            return {
                "status": "synced",
                "remoteGlossaryId": existing_sync["remoteGlossaryId"],
                "contentHash": glossary["contentHash"],
            }

        try:
            connection = self._resolve_connection(connection_id)
            provider, credentials = self._provider_credentials(connection)
        except TranslationServiceError as error:
            return self._sync_failure(error.code, str(error), error.http_status)

        current_version = self._storage.get_translation_glossary_current_version(glossary_rule_id)
        if current_version is None:
            return self._sync_failure("version_unavailable", "Glossary current version is unavailable.", 409)
        materialized = self._storage.materialize_translation_glossary_version(current_version["versionId"])
        entries = materialized["entries"] if materialized else []
        if not entries:
            return self._sync_failure("empty_glossary", "Глосарій не містить термінів для синхронізації.", 400)

        definition = GlossaryDefinition(
            name=f"Workbench {glossary['projectId'][-8:]} {glossary['sourceLanguage']}-{glossary['targetLanguage']}",
            source_language=glossary["sourceLanguage"],
            target_language=glossary["targetLanguage"],
            entries=tuple((entry["source"], entry["target"]) for entry in entries),
        )
        previous_remote_glossary_id = existing_sync["remoteGlossaryId"] if existing_sync else None

        try:
            remote_glossary_id = provider.create_glossary(credentials, definition)
        except GlossaryLimitError as error:
            if not previous_remote_glossary_id:
                return self._sync_failure("glossary_limit_reached", str(error), 502)
            # The account limit is reached, so release the slot held by this rule's own outdated
            # remote glossary before retrying. Only glossaries tracked in provider sync are removed.
            try:
                provider.delete_glossary(credentials, previous_remote_glossary_id)
            except ValueError as delete_error:
                return self._sync_failure("glossary_limit_reached", str(delete_error), 502)
            self._storage.delete_provider_glossary_sync(glossary_rule_id, connection["connectionId"])
            previous_remote_glossary_id = None
            try:
                remote_glossary_id = provider.create_glossary(credentials, definition)
            except ValueError as retry_error:
                return self._sync_failure("glossary_sync_failed", str(retry_error), 502)
        except ValueError as error:
            return self._sync_failure("glossary_sync_failed", str(error), 502)

        try:
            self._storage.save_provider_glossary_sync(
                glossary_rule_id,
                connection["connectionId"],
                connection["providerId"],
                remote_glossary_id,
                glossary["contentHash"],
            )
        except Exception as error:
            try:
                provider.delete_glossary(credentials, remote_glossary_id)
            except ValueError:
                pass
            return self._sync_failure(
                "glossary_sync_state_failed",
                "Локальний глосарій збережено, але не вдалося завершити синхронізацію з DeepL.",
                500,
            )

        if previous_remote_glossary_id and previous_remote_glossary_id != remote_glossary_id:
            try:
                provider.delete_glossary(credentials, previous_remote_glossary_id)
            except ValueError:
                # Keep the new synced glossary active even if old remote cleanup fails.
                pass

        return {
            "status": "synced",
            "remoteGlossaryId": remote_glossary_id,
            "versionId": current_version["versionId"],
            "contentHash": glossary["contentHash"],
        }

    @staticmethod
    def _sync_failure(code: str, message: str, http_status: int) -> dict[str, Any]:
        return {"status": "failed", "code": code, "message": message, "httpStatus": http_status}

    def save_project_glossary(self, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        if project is None:
            raise TranslationServiceError("Project not found.", 404, "not_found")
        glossary_data = self._validate_glossary(data)
        try:
            glossary = self._storage.get_or_create_project_translation_glossary(
                project_id,
                glossary_data["sourceLanguage"],
                glossary_data["targetLanguage"],
                glossary_data["glossaryRuleId"],
            )
            item_ids = self._storage.resolve_glossary_item_ids(glossary_data["entries"])
            self._storage.commit_translation_glossary_version(glossary["glossaryRuleId"], item_ids)
        except ValueError as error:
            raise TranslationServiceError(str(error), 400, "version_commit_invalid") from error

        sync_result = self._sync_glossary_with_provider(glossary["glossaryRuleId"], data.get("connectionId"))
        if sync_result["status"] != "synced":
            raise TranslationServiceError(
                sync_result["message"],
                sync_result["httpStatus"],
                sync_result["code"],
            )
        return self._storage.get_project_translation_glossary(glossary["glossaryRuleId"])

    def translate_paragraph(self, paragraph_id: str, data: dict[str, Any]) -> dict[str, Any]:
        paragraph = self._storage.get_paragraph(paragraph_id)
        if paragraph is None:
            raise TranslationServiceError("Paragraph not found.", 404, "not_found")

        connection = self._resolve_connection(data.get("connectionId"))
        provider, credentials = self._provider_credentials(connection)

        try:
            translation_rules = self._storage.get_translation_rules_for_paragraph(paragraph_id)
            project_id = self._storage.get_project_id_for_paragraph(paragraph_id)
            glossary = self._storage.find_synced_project_glossary(project_id, connection["connectionId"], "UK") if project_id else None
            result = provider.translate(
                credentials,
                TranslationRequest(
                    text=paragraph["originalText"],
                    target_language="UK",
                    source_language=glossary["sourceLanguage"] if glossary else None,
                    context=translation_rules or None,
                    glossary_id=glossary["providerSync"]["remoteGlossaryId"] if glossary else None,
                ),
            )
        except ValueError as error:
            raise TranslationServiceError(str(error), 502, "provider_error") from error

        updated = self._storage.update_paragraph(paragraph_id, result.text, False)
        return {
            **updated,
            "providerId": connection["providerId"],
            "detectedSourceLanguage": result.detected_source_language,
        }

    def translate_chapter(self, project_id: str, chapter_id: str, data: dict[str, Any]) -> dict[str, Any]:
        connection = self._resolve_connection(data.get("connectionId"))
        provider, credentials = self._provider_credentials(connection)

        try:
            payload = ChunkPreparationService(self._storage).build_chapter_payload(project_id, chapter_id)
        except ValueError as error:
            raise TranslationServiceError(str(error), 404, "not_found") from error

        translated_by_paragraph_id: dict[str, str] = {}
        detected_source_language = None
        project = self._storage.get_project(project_id)
        translation_rules = project.get("translationRules", "") if project else ""
        glossary = self._storage.find_synced_project_glossary(project_id, connection["connectionId"], "UK")
        for chunk in payload["chunks"]:
            source_paragraph_ids = chunk["sourceParagraphIds"]
            if not isinstance(source_paragraph_ids, list) or not all(isinstance(item, str) for item in source_paragraph_ids):
                raise TranslationServiceError("Chunk payload is invalid.", 500, "chunk_payload_invalid")
            paragraphs = self._get_source_paragraphs(source_paragraph_ids)
            request_text = self._build_chunk_xml(paragraphs)
            try:
                result = provider.translate(
                    credentials,
                    TranslationRequest(
                        text=request_text,
                        target_language="UK",
                        source_language=glossary["sourceLanguage"] if glossary else None,
                        tag_handling="xml",
                        context=translation_rules or None,
                        glossary_id=glossary["providerSync"]["remoteGlossaryId"] if glossary else None,
                    ),
                )
            except ValueError as error:
                raise TranslationServiceError(str(error), 502, "provider_error") from error

            mapped = self._parse_chunk_xml_result(result.text, source_paragraph_ids)
            translated_by_paragraph_id.update(mapped)
            detected_source_language = detected_source_language or result.detected_source_language

        updated_paragraphs = []
        for paragraph_id in translated_by_paragraph_id:
            updated = self._storage.update_paragraph(paragraph_id, translated_by_paragraph_id[paragraph_id], False)
            if updated is None:
                raise TranslationServiceError("Paragraph not found.", 404, "not_found")
            updated_paragraphs.append(updated)

        return {
            "projectId": project_id,
            "chapterId": chapter_id,
            "providerId": connection["providerId"],
            "detectedSourceLanguage": detected_source_language,
            "sourceParagraphIds": list(translated_by_paragraph_id.keys()),
            "translatedParagraphCount": len(updated_paragraphs),
            "chunks": payload["chunks"],
            "paragraphs": updated_paragraphs,
        }

    def analyze_chapter(self, project_id: str, chapter_id: str, data: dict[str, Any]) -> dict[str, Any]:
        project = self._storage.get_project(project_id)
        structure = self._storage.get_book_structure(project_id)
        chapter = next((item for item in (structure or {}).get("chapters", []) if item["chapterId"] == chapter_id), None)
        if project is None or chapter is None:
            raise TranslationServiceError("Chapter not found.", 404, "not_found")

        categories = data.get("categories", [])
        connection_ids = data.get("connectionIds", [])
        raw_custom_prompt = data.get("customPrompt", "")
        if not isinstance(raw_custom_prompt, str):
            raise TranslationServiceError("Additional AI task must be text.", 400, "analysis_invalid")
        custom_prompt = raw_custom_prompt.strip()
        if not isinstance(categories, list) or not all(isinstance(item, str) and item.strip() for item in categories):
            raise TranslationServiceError("Analysis categories must be a list of names.", 400, "analysis_invalid")
        if not isinstance(connection_ids, list) or not connection_ids or not all(isinstance(item, str) and item.strip() for item in connection_ids):
            raise TranslationServiceError("Choose at least one AI connection.", 400, "analysis_invalid")
        configured_ids = set((project.get("aiConfiguration") or {}).get("analysisConnectionIds", []))
        if not set(connection_ids).issubset(configured_ids):
            raise TranslationServiceError("Choose AI connections configured for this project analysis.", 400, "analysis_connection_invalid")

        paragraphs = [element["originalText"] for element in chapter.get("elements", []) if element.get("type") == "paragraph"]
        source_text = "\n\n".join(paragraphs).strip()
        if not source_text:
            raise TranslationServiceError("The chapter has no original text to analyze.", 400, "analysis_empty")
        prompt = self._build_chapter_analysis_prompt(project, categories, custom_prompt, source_text)
        results = {}
        connections = {item["connectionId"]: item for item in self._storage.list_integration_connections()}
        for connection_id in dict.fromkeys(connection_ids):
            connection = connections.get(connection_id)
            if connection is None or not connection["enabled"] or connection["testStatus"] != "connected":
                results[connection_id] = {"status": "failed", "message": "AI connection is not active and tested."}
                continue
            provider_id = connection["providerId"]
            provider = self._registry.get(provider_id)
            if provider is None or provider_id == "deepl":
                results[connection_id] = {"status": "failed", "message": "This connection cannot analyze chapters."}
                continue
            try:
                provider_instance, credentials = self._provider_credentials(connection)
                text = provider_instance.analyze(credentials, prompt)
                result = {"status": "completed", "providerId": provider_id, "text": text, "categories": categories, "customPrompt": custom_prompt}
            except (TranslationServiceError, ValueError) as error:
                result = {"status": "failed", "providerId": provider_id, "message": str(error)}
            self._storage.save_chapter_ai_analysis(chapter_id, provider_id, result)
            results[provider_id] = result
        saved_chapter = self._storage.get_chapter(chapter_id)
        return {"projectId": project_id, "chapterId": chapter_id, "results": results, "savedResults": saved_chapter["aiAnalysisResults"] if saved_chapter else {}}

    def _build_chapter_analysis_prompt(self, project: dict[str, Any], categories: list[str], custom_prompt: str, source_text: str) -> str:
        rule_ids = set(project.get("projectRuleIds", [])) | {item["ruleId"] for item in project.get("inheritedRules", [])}
        glossary_ids = set(project.get("projectGlossaryEntryIds", [])) | {item["glossaryEntryId"] for item in project.get("inheritedGlossary", [])}
        rules = [item for item in self._storage.list_rules() if item["ruleId"] in rule_ids]
        glossary = [item for item in self._storage.list_glossary() if item["glossaryEntryId"] in glossary_ids]
        sections = "\n".join(f"- {category}" for category in categories)
        additional = custom_prompt or "Немає."
        return (
            "Проаналізуй лише оригінал розділу для підготовки ТЗ перекладу. Не оцінюй і не виправляй переклад. "
            "Відповідь дай українською у структурованому форматі з окремим заголовком для кожної вибраної категорії "
            "і окремим заголовком для відповіді на додаткове завдання, якщо воно є; "
            "не витрачай детальний аналіз на невибрані категорії.\n\n"
            f"Вибрані категорії:\n{sections}\n\n"
            f"Додаткове завдання користувача:\n{additional}\n\n"
            f"Правила проєкту:\n{json.dumps(rules, ensure_ascii=False)}\n\n"
            f"Glossary проєкту:\n{json.dumps(glossary, ensure_ascii=False)}\n\n"
            f"Оригінал розділу:\n{source_text}"
        )

    def _get_source_paragraphs(self, paragraph_ids: list[str]) -> list[dict[str, str]]:
        paragraphs = []
        for paragraph_id in paragraph_ids:
            paragraph = self._storage.get_paragraph(paragraph_id)
            if paragraph is None:
                raise TranslationServiceError("Paragraph not found.", 404, "not_found")
            paragraphs.append({
                "paragraphId": paragraph["paragraphId"],
                "originalText": paragraph["originalText"],
            })
        return paragraphs

    @staticmethod
    def _build_chunk_xml(paragraphs: list[dict[str, str]]) -> str:
        root = ET.Element("chunk")
        for paragraph in paragraphs:
            element = ET.SubElement(root, "p", {"id": paragraph["paragraphId"]})
            element.text = paragraph["originalText"]
        return ET.tostring(root, encoding="unicode")

    @staticmethod
    def _parse_chunk_xml_result(text: str, expected_paragraph_ids: list[str]) -> dict[str, str]:
        try:
            root = ET.fromstring(text)
        except ET.ParseError as error:
            raise TranslationServiceError("Provider response did not preserve chunk XML.", 502, "chunk_mapping_failed") from error

        translated: dict[str, str] = {}
        actual_paragraph_ids = []
        for element in root.findall(".//p"):
            paragraph_id = element.attrib.get("id")
            if paragraph_id is None:
                continue
            actual_paragraph_ids.append(paragraph_id)
            translated[paragraph_id] = "".join(element.itertext())

        if actual_paragraph_ids != expected_paragraph_ids:
            raise TranslationServiceError("Provider response paragraph IDs did not match chunk source IDs.", 502, "chunk_mapping_failed")
        return translated

    def _resolve_connection(self, connection_id: Any) -> dict[str, Any]:
        connections = self._storage.list_integration_connections()
        if connection_id:
            connection = next((item for item in connections if item["connectionId"] == connection_id), None)
        else:
            connection = next((
                item for item in connections
                if item["providerId"] == "deepl" and item["enabled"] and item["testStatus"] == "connected"
            ), None)
        if connection is None:
            raise TranslationServiceError(
                "Налаштуйте та перевірте підключення DeepL у Connections.",
                409,
                "connection_required",
            )
        if not connection["enabled"] or connection["testStatus"] != "connected":
            raise TranslationServiceError(
                "Підключення DeepL має бути активним і перевіреним.",
                409,
                "connection_not_ready",
            )
        return connection

    def _provider_credentials(self, connection: dict[str, Any]):
        provider = self._registry.get(connection["providerId"])
        if provider is None:
            raise TranslationServiceError("Translation provider is unavailable.", 503, "provider_unavailable")
        if not self._vault.available:
            raise TranslationServiceError("Credential storage is unavailable.", 503, "credential_storage_unavailable")
        record = self._storage.get_integration_connection_record(connection["connectionId"])
        try:
            credentials = self._vault.decrypt(record["credentialsCiphertext"])
        except (CredentialVaultError, TypeError) as error:
            raise TranslationServiceError("Stored credentials are unavailable.", 503, "credentials_locked") from error
        return provider, credentials

    @staticmethod
    def _validate_glossary(data: dict[str, Any]) -> dict[str, Any]:
        source_language = str(data.get("sourceLanguage", "")).strip().upper()
        target_language = str(data.get("targetLanguage", "")).strip().upper()
        raw_entries = data.get("entries")
        if not source_language or not target_language or not isinstance(raw_entries, list) or not raw_entries:
            raise TranslationServiceError("Вкажіть мови та щонайменше один термін.")
        entries = []
        seen_sources = set()
        for item in raw_entries:
            if not isinstance(item, dict):
                raise TranslationServiceError("Некоректний запис глосарію.")
            source = str(item.get("source", "")).strip()
            target = str(item.get("target", "")).strip()
            context = str(item.get("context", "")).strip()
            if not source or not target:
                raise TranslationServiceError("Оригінал і переклад терміна обов’язкові.")
            normalized_source = source.casefold()
            if normalized_source in seen_sources:
                raise TranslationServiceError("Оригінальні терміни не повинні дублюватися.")
            seen_sources.add(normalized_source)
            entries.append({"source": source, "target": target, "context": context})
        provider_payload = {
            "sourceLanguage": source_language,
            "targetLanguage": target_language,
            "entries": [{"source": item["source"], "target": item["target"]} for item in entries],
        }
        return {
            "glossaryRuleId": data.get("glossaryRuleId"),
            "sourceLanguage": source_language,
            "targetLanguage": target_language,
            "entries": entries,
            "contentHash": hashlib.sha256(json.dumps(provider_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
        }