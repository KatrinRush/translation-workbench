"""Application service for translating one imported text unit."""

from __future__ import annotations

from typing import Any
import hashlib
import json
import logging
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as _xml_escape

from ..integrations.base import GlossaryDefinition, GlossaryLimitError, QuotaExceededError, TranslationRequest
from ..integrations.credentials import CredentialVault, CredentialVaultError
from ..integrations.registry import ProviderRegistry
from ..usage import UsageRecorder, capture_usage, summarize
from .chunker import chapter_paragraph_units
from .chunking_service import ChunkPreparationService
from .context import build_deepl_context
from .glossary_check import find_glossary_hits, missing_terms
from .llm_prompt import (
    build_system_prompt, build_user_message, engine_instructions_block, glossary_terms_in_text, is_character, prompt_hash,
    select_glossary_entries,
)
from .narrator import effective_narrators


class TranslationServiceError(RuntimeError):
    def __init__(
        self,
        message: str,
        http_status: int = 400,
        code: str = "translation_error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.http_status = http_status
        self.code = code
        self.details = details or {}


class TranslationService:
    def __init__(self, storage, vault: CredentialVault, registry: ProviderRegistry):
        self._storage = storage
        self._vault = vault
        self._registry = registry

    def list_project_glossaries(self, project_id: str, connection_id: str | None = None) -> list[dict[str, Any]]:
        if self._storage.get_project(project_id) is None:
            raise TranslationServiceError("Project not found.", 404, "not_found")
        return self._storage.list_project_translation_glossaries(project_id, self._default_connection_id(connection_id))

    def release_project_glossaries(self, project_id: str) -> None:
        """Best-effort deletion of provider-side glossaries linked to a project being removed."""
        connections = {item["connectionId"]: item for item in self._storage.list_integration_connections()}
        for glossary in self._storage.list_project_translation_glossaries(project_id):
            provider_sync = glossary.get("providerSync")
            if not provider_sync or provider_sync["glossaryRuleId"] != glossary["glossaryRuleId"]:
                continue
            connection_id = provider_sync["connectionId"]
            try:
                connection = connections.get(connection_id)
                if connection is not None:
                    provider, credentials = self._provider_credentials(connection)
                    provider.delete_glossary(credentials, provider_sync["remoteGlossaryId"])
            except Exception:
                # Best-effort cleanup: remote deletion failures must not block project deletion.
                pass
            finally:
                self._storage.delete_provider_glossary_sync(glossary["glossaryRuleId"], connection_id)

    def release_connection_glossaries(self, connection_id: str) -> None:
        """Best-effort deletion of provider-side glossaries synced through a connection being removed.

        Deleting an integration connection has no foreign key back to provider_glossary_sync,
        so without this the remote glossaries created through it are never released and pile up
        on the provider account (eventually hitting its account-wide glossary limit), while the
        local rows become dangling references to a connection_id that no longer exists.
        """
        connection = self._storage.get_integration_connection(connection_id)
        if connection is None:
            return
        try:
            provider, credentials = self._provider_credentials(connection)
        except TranslationServiceError:
            provider, credentials = None, None
        for sync in self._storage.list_provider_glossary_sync_for_connection(connection_id):
            if provider is not None:
                try:
                    provider.delete_glossary(credentials, sync["remoteGlossaryId"])
                except Exception:
                    # Best-effort cleanup: remote deletion failures must not block connection deletion.
                    pass
        self._storage.delete_provider_glossary_sync_for_connection(connection_id)

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
        saved = self._storage.get_project_translation_glossary(
            glossary["glossaryRuleId"], self._default_connection_id(data.get("connectionId"))
        )
        saved["providerSyncResult"] = sync_result
        return saved

    def _sync_glossary_with_provider(self, glossary_rule_id: str, connection_id: Any = None) -> dict[str, Any]:
        """Publish the current local version to the provider's language-pair slot."""
        glossary = self._storage.get_project_translation_glossary(glossary_rule_id)
        if glossary is None:
            return self._sync_failure("not_found", "Glossary not found.", 404)

        try:
            connection = self._resolve_connection(connection_id)
            provider, credentials = self._provider_credentials(connection)
        except TranslationServiceError as error:
            return self._sync_failure(error.code, str(error), error.http_status)

        existing_sync = self._storage.get_provider_glossary_sync(
            connection["connectionId"],
            glossary["sourceLanguage"],
            glossary["targetLanguage"],
        )
        if (
            existing_sync
            and existing_sync["glossaryRuleId"] == glossary_rule_id
            and existing_sync["contentHash"] == glossary["contentHash"]
        ):
            return {
                "status": "synced",
                "remoteGlossaryId": existing_sync["remoteGlossaryId"],
                "contentHash": glossary["contentHash"],
            }

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

        # DeepL allows only one active glossary per language pair per account, so any
        # previously-synced glossary for this slot — whether it belongs to this same
        # glossary_rule_id (an update) or a different one (another project/book) — must
        # be deleted BEFORE we attempt to create the new version. Creating first and
        # deleting after only works for the "different owner" case; for a same-owner
        # update it means two glossaries briefly coexist, which the free plan rejects
        # with a 456 limit error instead of the intended clean replacement.
        if existing_sync:
            try:
                provider.delete_glossary(credentials, existing_sync["remoteGlossaryId"])
            except ValueError as error:
                return self._sync_failure("glossary_sync_failed", str(error), 502)
            self._storage.delete_provider_glossary_sync(
                existing_sync["glossaryRuleId"], connection["connectionId"]
            )

        try:
            remote_glossary_id = provider.create_glossary(credentials, definition)
        except GlossaryLimitError as error:
            # We already freed the slot we knew about above (if any), so hitting the limit
            # here means the account already holds a glossary for this pair that our local
            # bookkeeping never learned about. That happens because provider_glossary_sync is
            # keyed by our own connection_id, not by the actual DeepL account — e.g. the slot
            # was synced through a connection that has since been deleted and recreated. Ask
            # the provider directly what occupies the pair and take it over too, instead of
            # surfacing the limit error to the user.
            remote_glossary_id, recovery_failure = self._take_over_untracked_slot(
                provider, credentials, connection, definition, error
            )
            if recovery_failure is not None:
                return recovery_failure
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
        except Exception:
            logging.exception(
                "Failed to save provider glossary sync for glossary_rule_id=%s connection_id=%s",
                glossary_rule_id,
                connection["connectionId"],
            )
            try:
                provider.delete_glossary(credentials, remote_glossary_id)
            except ValueError:
                pass
            return self._sync_failure(
                "glossary_sync_state_failed",
                "Локальний глосарій збережено, але не вдалося завершити синхронізацію з DeepL.",
                500,
            )

        return {
            "status": "synced",
            "remoteGlossaryId": remote_glossary_id,
            "versionId": current_version["versionId"],
            "contentHash": glossary["contentHash"],
        }

    def _take_over_untracked_slot(
        self,
        provider,
        credentials,
        connection: dict[str, Any],
        definition: GlossaryDefinition,
        original_error: GlossaryLimitError,
    ) -> tuple[str | None, dict[str, Any] | None]:
        """Recover from a glossary-limit error by asking the provider what actually occupies
        the language-pair slot, deleting it, and retrying the create once.

        Returns (remote_glossary_id, None) on success, or (None, failure_dict) if the slot
        still could not be freed.
        """
        try:
            remote_glossaries = provider.list_glossaries(credentials)
        except ValueError:
            remote_glossaries = []

        conflicting = [
            item for item in remote_glossaries
            if item.source_language == definition.source_language
            and item.target_language == definition.target_language
        ]
        if not conflicting:
            # The provider either doesn't support listing or genuinely has no glossary for
            # this pair, in which case the limit is a real account-wide cap we can't work around.
            return None, self._sync_failure("glossary_limit_reached", str(original_error), 502)

        for item in conflicting:
            try:
                provider.delete_glossary(credentials, item.glossary_id)
            except ValueError:
                continue
            self._storage.delete_provider_glossary_sync_by_remote_id(
                connection["providerId"], item.glossary_id
            )

        try:
            return provider.create_glossary(credentials, definition), None
        except GlossaryLimitError as error:
            return None, self._sync_failure("glossary_limit_reached", str(error), 502)
        except ValueError as error:
            return None, self._sync_failure("glossary_sync_failed", str(error), 502)

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
        return self._storage.get_project_translation_glossary(
            glossary["glossaryRuleId"], self._default_connection_id(data.get("connectionId"))
        )

    def _ensure_synced_project_glossary(
        self, project_id: str | None, connection: dict[str, Any], target_language: str
    ) -> dict[str, Any] | None:
        """Look up the project's synced glossary for this connection, auto-syncing it first
        if the connection has never synced it (or synced an outdated version).

        Without this, switching to a different DeepL connection — another account, or a
        connection that replaced a deleted one — silently drops the glossary from every
        translation until someone happens to open glossary settings and re-save it, with no
        error to explain why: find_synced_project_glossary just returns None and translation
        proceeds without a glossary_id.
        """
        if project_id is None or connection["providerId"] != "deepl":
            return None
        glossary = self._storage.find_synced_project_glossary(project_id, connection["connectionId"], target_language)
        if glossary is not None:
            return glossary
        candidate = next(
            (
                item for item in self._storage.list_project_translation_glossaries(project_id)
                if item["targetLanguage"] == target_language and item["currentVersionId"]
            ),
            None,
        )
        if candidate is None:
            return None
        sync_result = self._sync_glossary_with_provider(candidate["glossaryRuleId"], connection["connectionId"])
        if sync_result["status"] != "synced":
            logging.warning(
                "Auto-sync of glossary %s to connection %s failed: %s",
                candidate["glossaryRuleId"], connection["connectionId"], sync_result.get("message"),
            )
            return None
        return self._storage.find_synced_project_glossary(project_id, connection["connectionId"], target_language)

    @staticmethod
    def _prepare_context(context: str | None, tag_handling: str | None) -> str | None:
        """DeepL parses the `context` field as XML whenever tag_handling="xml", the same
        as the text itself — an unescaped '&' or '<' in the surrounding source sentences
        (e.g. "... mailing list & get the exclusive story ...", pulled verbatim from the
        book) breaks that parser with a 400 "Tag handling parsing failed", which aborts
        the whole chapter since one failed chunk stops translate_chapter's loop.
        """
        if not context or tag_handling != "xml":
            return context
        return _xml_escape(context)

    def translate_paragraph(self, paragraph_id: str, data: dict[str, Any]) -> dict[str, Any]:
        paragraph = self._storage.get_paragraph(paragraph_id)
        if paragraph is None:
            raise TranslationServiceError("Paragraph not found.", 404, "not_found")

        connection = self._resolve_translation_connection(
            self._storage.get_project_id_for_paragraph(paragraph_id), data.get("connectionId")
        )
        provider, credentials = self._provider_credentials(connection)
        if connection["providerId"] in self._LLM_TRANSLATION_PROVIDERS:
            return self._translate_paragraph_llm(paragraph_id, connection, provider, credentials)

        try:
            project_id = self._storage.get_project_id_for_paragraph(paragraph_id)
            book_structure = self._storage.get_book_structure(project_id) if project_id else None
            glossary = self._ensure_synced_project_glossary(project_id, connection, "UK")
            print(
                "[DEEPL DEBUG]",
                f"current_version_id={glossary.get('currentVersionId') if glossary else None!r}",
                f"remote_glossary_id={glossary.get('providerSync', {}).get('remoteGlossaryId') if glossary else None!r}",
                f"glossary_id={glossary.get('providerSync', {}).get('remoteGlossaryId') if glossary else None!r}",
            )
            result = provider.translate(
                credentials,
                TranslationRequest(
                    text=self._build_chunk_xml([{"paragraphId": paragraph_id, "originalText": paragraph["originalText"]}]),
                    target_language="UK",
                    source_language=glossary["sourceLanguage"] if glossary else None,
                    tag_handling="xml",
                    tag_handling_version="v2",
                    model_type="quality_optimized",
                    context=self._prepare_context(
                        build_deepl_context(book_structure or {}, [paragraph_id])
                        if connection["providerId"] == "deepl"
                        else self._storage.get_translation_rules_for_paragraph(paragraph_id) or None,
                        "xml",
                    ),
                    glossary_id=glossary["providerSync"]["remoteGlossaryId"] if glossary else None,
                ),
            )
        except QuotaExceededError as error:
            raise TranslationServiceError(
                str(error), 409, "quota_exceeded",
                details={"connectionId": connection["connectionId"], "providerId": connection["providerId"]},
            ) from error
        except ValueError as error:
            logging.error(
                "translate_paragraph failed for paragraph_id=%s connection_id=%s provider_id=%s: %s",
                paragraph_id, connection["connectionId"], connection["providerId"], error,
            )
            raise TranslationServiceError(str(error), 502, "provider_error") from error

        translated_text = self._parse_chunk_xml_result(result.text, [paragraph_id])[paragraph_id]

        updated = self._storage.add_translation_variant(paragraph_id, "deepl", translated_text, self._DEEPL_MODEL)
        return {
            **updated,
            "providerId": connection["providerId"],
            "connectionId": connection["connectionId"],
            "detectedSourceLanguage": result.detected_source_language,
        }

    def translate_chapter(self, project_id: str, chapter_id: str, data: dict[str, Any]) -> dict[str, Any]:
        connection = self._resolve_translation_connection(project_id, data.get("connectionId"))
        provider, credentials = self._provider_credentials(connection)
        if connection["providerId"] in self._LLM_TRANSLATION_PROVIDERS:
            return self._translate_chapter_llm(project_id, chapter_id, connection, provider, credentials, data)

        try:
            # Reviewed paragraphs are skipped for whole-chapter runs; the per-paragraph button still translates them.
            payload = ChunkPreparationService(self._storage).build_chapter_payload(project_id, chapter_id, skip_reviewed=True)
        except ValueError as error:
            raise TranslationServiceError(str(error), 404, "not_found") from error

        translated_by_paragraph_id: dict[str, str] = {}
        detected_source_language = None
        project = self._storage.get_project(project_id)
        translation_rules = project.get("translationRules", "") if project else ""
        book_structure = self._storage.get_book_structure(project_id) or {}
        glossary = self._ensure_synced_project_glossary(project_id, connection, "UK")
        for chunk in payload["chunks"]:
            source_paragraph_ids = chunk["sourceParagraphIds"]
            if not isinstance(source_paragraph_ids, list) or not all(isinstance(item, str) for item in source_paragraph_ids):
                raise TranslationServiceError("Chunk payload is invalid.", 500, "chunk_payload_invalid")
            paragraphs = self._get_source_paragraphs(source_paragraph_ids)
            request_text = self._build_chunk_xml(paragraphs)
            try:
                print(
                    "[DEEPL DEBUG]",
                    f"current_version_id={glossary.get('currentVersionId') if glossary else None!r}",
                    f"remote_glossary_id={glossary.get('providerSync', {}).get('remoteGlossaryId') if glossary else None!r}",
                    f"glossary_id={glossary.get('providerSync', {}).get('remoteGlossaryId') if glossary else None!r}",
                )
                result = provider.translate(
                    credentials,
                    TranslationRequest(
                        text=request_text,
                        target_language="UK",
                        source_language=glossary["sourceLanguage"] if glossary else None,
                        tag_handling="xml",
                        tag_handling_version="v2",
                        model_type="quality_optimized",
                        context=self._prepare_context(
                            build_deepl_context(book_structure, source_paragraph_ids)
                            if connection["providerId"] == "deepl"
                            else translation_rules or None,
                            "xml",
                        ),
                        glossary_id=glossary["providerSync"]["remoteGlossaryId"] if glossary else None,
                    ),
                )
            except QuotaExceededError as error:
                raise TranslationServiceError(
                    str(error), 409, "quota_exceeded",
                    details={"connectionId": connection["connectionId"], "providerId": connection["providerId"]},
                ) from error
            except ValueError as error:
                logging.error(
                    "translate_chapter failed for chapter_id=%s connection_id=%s provider_id=%s: %s",
                    chapter_id, connection["connectionId"], connection["providerId"], error,
                )
                raise TranslationServiceError(str(error), 502, "provider_error") from error

            mapped = self._parse_chunk_xml_result(result.text, source_paragraph_ids)
            translated_by_paragraph_id.update(mapped)
            detected_source_language = detected_source_language or result.detected_source_language

        updated_paragraphs = []
        for paragraph_id in translated_by_paragraph_id:
            updated = self._storage.add_translation_variant(paragraph_id, "deepl", translated_by_paragraph_id[paragraph_id], self._DEEPL_MODEL)
            if updated is None:
                raise TranslationServiceError("Paragraph not found.", 404, "not_found")
            updated_paragraphs.append(updated)

        return {
            "projectId": project_id,
            "chapterId": chapter_id,
            "providerId": connection["providerId"],
            "connectionId": connection["connectionId"],
            "detectedSourceLanguage": detected_source_language,
            "sourceParagraphIds": list(translated_by_paragraph_id.keys()),
            "translatedParagraphCount": len(updated_paragraphs),
            "skippedReviewedParagraphIds": self._reviewed_paragraph_ids(
                ChunkPreparationService._find_chapter(book_structure, chapter_id)
            ),
            "chunks": payload["chunks"],
            "paragraphs": updated_paragraphs,
        }

    @staticmethod
    def _reviewed_paragraph_ids(chapter: dict[str, Any] | None) -> list[str]:
        return [
            element["paragraphId"]
            for element in (chapter or {}).get("elements", [])
            if element.get("type") == "paragraph" and (element.get("reviewed") or element.get("proofread")) and element.get("paragraphId")
        ]

    # --- LLM translation (Claude, OpenAI, Gemini) -----------------------------------
    #
    # Unlike DeepL, an LLM needs tens of seconds per chunk, so a whole chapter in one
    # HTTP request would hit Cloudflare's 524 (~100 s). Same approach as AI QA: one
    # request translates and saves one small batch, the frontend walks batchIndex
    # up to totalBatches.
    _LLM_TRANSLATION_PROVIDERS = frozenset({"claude", "openai", "gemini"})
    _PROVIDER_LABELS = {"deepl": "DeepL", "claude": "Claude", "openai": "OpenAI", "gemini": "Gemini"}
    # DeepL has no model choice here: every request asks for model_type=quality_optimized.
    _DEEPL_MODEL = "quality_optimized"
    _LLM_BATCH_MAX_CHARS = 1500
    _LLM_BATCH_MAX_PARAGRAPHS = 8
    # Allowed project settings (aiConfiguration.translationBatch): (min, max) per field.
    BATCH_CHARS_RANGE = (500, 6000)
    BATCH_PARAGRAPHS_RANGE = (1, 20)
    REASONING_LEVELS = ("minimal", "low", "medium")
    DEFAULT_REASONING = "low"
    _REASONING_PROVIDERS = frozenset({"openai", "gemini"})
    _LLM_SOURCE_CONTEXT_PARAGRAPHS = 3
    _LLM_TRANSLATED_CONTEXT_PARAGRAPHS = 3
    _LLM_BATCH_ATTEMPTS = 2

    def _resolve_translation_connection(self, project_id: str | None, connection_id: Any) -> dict[str, Any]:
        """The project's translation provider choice (aiConfiguration.translationConnectionId)
        wins only when it points at an LLM connection. Anything else — no choice, a DeepL
        connection, a connection deleted since — keeps the pre-existing DeepL resolution,
        including the frontend's active DeepL connection used for quota switching."""
        project = self._storage.get_project(project_id) if project_id else None
        configured_id = ((project or {}).get("aiConfiguration") or {}).get("translationConnectionId")
        if configured_id:
            configured = self._storage.get_integration_connection(configured_id)
            if configured is not None and configured["providerId"] in self._LLM_TRANSLATION_PROVIDERS:
                if not configured["enabled"] or configured["testStatus"] != "connected":
                    raise TranslationServiceError(
                        f"Підключення {self._PROVIDER_LABELS.get(configured['providerId'], configured['providerId'])} для перекладу має бути активним і перевіреним. Налаштуйте його в розділі Connections.",
                        409,
                        "translation_connection_not_ready",
                        details={"connectionId": configured["connectionId"], "providerId": configured["providerId"]},
                    )
                return configured
        return self._resolve_connection(connection_id)

    @classmethod
    def _llm_batches(
        cls, paragraph_ids_and_texts: list[tuple[str, str]], max_chars: int | None = None, max_paragraphs: int | None = None
    ) -> list[list[str]]:
        max_chars = max_chars or cls._LLM_BATCH_MAX_CHARS
        max_paragraphs = max_paragraphs or cls._LLM_BATCH_MAX_PARAGRAPHS
        batches: list[list[str]] = []
        current: list[str] = []
        current_chars = 0
        for paragraph_id, text in paragraph_ids_and_texts:
            size = len(text)
            if current and (current_chars + size > max_chars or len(current) >= max_paragraphs):
                batches.append(current)
                current, current_chars = [], 0
            current.append(paragraph_id)
            current_chars += size
        if current:
            batches.append(current)
        return batches

    @classmethod
    def batch_limits(cls, project: dict[str, Any] | None) -> tuple[int, int]:
        """(max chars, max paragraphs) of a batch: the project's aiConfiguration.translationBatch,
        each value clamped to its allowed range, else the defaults."""
        configuration = ((project or {}).get("aiConfiguration") or {}).get("translationBatch")
        configuration = configuration if isinstance(configuration, dict) else {}

        def pick(key: str, default: int, bounds: tuple[int, int]) -> int:
            value = configuration.get(key)
            if isinstance(value, bool) or not isinstance(value, int):
                return default
            return min(max(value, bounds[0]), bounds[1])

        return (
            pick("maxChars", cls._LLM_BATCH_MAX_CHARS, cls.BATCH_CHARS_RANGE),
            pick("maxParagraphs", cls._LLM_BATCH_MAX_PARAGRAPHS, cls.BATCH_PARAGRAPHS_RANGE),
        )

    @classmethod
    def reasoning_level(cls, project: dict[str, Any] | None, provider_id: str) -> str | None:
        """aiConfiguration.translationReasoning[provider] for GPT and Gemini (default "low");
        None for providers without the setting (Claude)."""
        if provider_id not in cls._REASONING_PROVIDERS:
            return None
        levels = ((project or {}).get("aiConfiguration") or {}).get("translationReasoning")
        level = levels.get(provider_id) if isinstance(levels, dict) else None
        return level if level in cls.REASONING_LEVELS else cls.DEFAULT_REASONING

    def _translate_chapter_llm(self, project_id: str, chapter_id: str, connection, provider, credentials, data: dict[str, Any]) -> dict[str, Any]:
        batch_index = data.get("batchIndex", 0)
        if isinstance(batch_index, bool) or not isinstance(batch_index, int) or batch_index < 0:
            raise TranslationServiceError("Invalid batch index.", 400, "translation_invalid")
        book_structure = self._storage.get_book_structure(project_id)
        chapter = ChunkPreparationService._find_chapter(book_structure or {}, chapter_id)
        if chapter is None:
            raise TranslationServiceError("Chapter not found.", 404, "not_found")
        # Reviewed paragraphs are skipped for whole-chapter runs (as on the DeepL path).
        # Batches are recomputed per request; translated paragraphs are saved unreviewed,
        # so the list stays stable while the frontend walks it.
        units = chapter_paragraph_units(chapter, skip_reviewed=True)
        max_chars, max_paragraphs = self.batch_limits(self._storage.get_project(project_id))
        batches = self._llm_batches([(unit.paragraph_id, unit.original_text) for unit in units], max_chars, max_paragraphs)
        skipped = self._reviewed_paragraph_ids(chapter)
        if not batches:
            # Nothing left to translate (e.g. every paragraph is reviewed): not an error.
            return {
                "projectId": project_id,
                "chapterId": chapter_id,
                "providerId": connection["providerId"],
                "connectionId": connection["connectionId"],
                "model": None,
                "detectedSourceLanguage": None,
                "batchIndex": batch_index,
                "totalBatches": 0,
                "sourceParagraphIds": [],
                "translatedParagraphCount": 0,
                "skippedReviewedParagraphIds": skipped,
                "paragraphs": [],
                "usage": {},
            }
        if batch_index >= len(batches):
            raise TranslationServiceError("Batch index out of range.", 400, "translation_invalid")
        batch_ids = batches[batch_index]

        translated, result, usage, warnings, usage_summary = self._run_llm_translation(
            project_id, book_structure, chapter, batch_ids, connection, provider, credentials,
            f"chapter={chapter_id} batch={batch_index + 1}/{len(batches)}",
        )
        updated_paragraphs = []
        for paragraph_id in batch_ids:
            updated = self._storage.add_translation_variant(
                paragraph_id, connection["providerId"], translated[paragraph_id], result.model, warnings.get(paragraph_id),
                usage_summary.get("promptHash"),
            )
            if updated is None:
                raise TranslationServiceError("Paragraph not found.", 404, "not_found")
            updated_paragraphs.append(updated)
        return {
            "projectId": project_id,
            "chapterId": chapter_id,
            "providerId": connection["providerId"],
            "connectionId": connection["connectionId"],
            "model": result.model,
            "detectedSourceLanguage": None,
            "batchIndex": batch_index,
            "totalBatches": len(batches),
            "sourceParagraphIds": list(batch_ids),
            "translatedParagraphCount": len(updated_paragraphs),
            "skippedReviewedParagraphIds": skipped,
            "paragraphs": updated_paragraphs,
            "usage": usage,
            "usageSummary": usage_summary,
            "reasoning": result.reasoning,
        }

    def _translate_paragraph_llm(self, paragraph_id: str, connection, provider, credentials) -> dict[str, Any]:
        project_id = self._storage.get_project_id_for_paragraph(paragraph_id)
        book_structure = self._storage.get_book_structure(project_id) if project_id else None
        chapter = next(
            (
                item for item in (book_structure or {}).get("chapters", [])
                if any(element.get("paragraphId") == paragraph_id for element in item.get("elements", []))
            ),
            None,
        )
        if chapter is None:
            raise TranslationServiceError("Paragraph not found.", 404, "not_found")
        translated, result, usage, warnings, usage_summary = self._run_llm_translation(
            project_id, book_structure, chapter, [paragraph_id], connection, provider, credentials,
            f"paragraph={paragraph_id}",
        )
        updated = self._storage.add_translation_variant(
            paragraph_id, connection["providerId"], translated[paragraph_id], result.model, warnings.get(paragraph_id),
            usage_summary.get("promptHash"),
        )
        if updated is None:
            raise TranslationServiceError("Paragraph not found.", 404, "not_found")
        return {
            **updated,
            "providerId": connection["providerId"],
            "connectionId": connection["connectionId"],
            "model": result.model,
            "detectedSourceLanguage": None,
            "usage": usage,
            "usageSummary": usage_summary,
            "reasoning": result.reasoning,
        }

    @staticmethod
    def _translation_model_for(project: dict[str, Any], provider_id: str) -> str | None:
        """aiConfiguration.translationModels[provider]; the older single translationModel
        field still counts for Claude. None means the provider's default."""
        configuration = project.get("aiConfiguration") or {}
        models = configuration.get("translationModels") if isinstance(configuration.get("translationModels"), dict) else {}
        model = models.get(provider_id)
        if not (isinstance(model, str) and model.strip()) and provider_id == "claude":
            model = configuration.get("translationModel")
        return model.strip() if isinstance(model, str) and model.strip() else None

    def _llm_glossary_entries(self, project: dict[str, Any]) -> list[dict[str, Any]]:
        """Union of the two places a project keeps terms, catalog first so it wins on duplicates:

        - the project catalog: glossary_entries linked through project_glossary
          (projectGlossaryEntryIds) plus the inherited series/author entries;
        - the active EN→UK translation glossary, i.e. what is synced to DeepL:
          project_translation_glossaries.current_version_id →
          project_translation_glossary_version_items → glossary_entries.
        Saving a term in the translation glossary does not link it into project_glossary,
        so reading the catalog alone silently drops those terms.
        """
        catalog_ids = list(project.get("projectGlossaryEntryIds", [])) + [
            item["glossaryEntryId"] for item in project.get("inheritedGlossary", [])
        ]
        translation_ids: list[str] = []
        for glossary in self._storage.list_project_translation_glossaries(project["projectId"]) if project.get("projectId") else []:
            if (
                glossary.get("currentVersionId")
                and str(glossary.get("sourceLanguage", "")).upper().startswith("EN")
                and str(glossary.get("targetLanguage", "")).upper() == "UK"
            ):
                version = self._storage.materialize_translation_glossary_version(glossary["currentVersionId"])
                translation_ids.extend((version or {}).get("glossaryEntryIds", []))
        by_id = {item["glossaryEntryId"]: item for item in self._storage.list_glossary()}
        catalog = [by_id[item_id] for item_id in dict.fromkeys(catalog_ids) if item_id in by_id]
        # A term DeepL translates with is in force even if its catalog row is deactivated.
        translation = [{**by_id[item_id], "active": True} for item_id in dict.fromkeys(translation_ids) if item_id in by_id]
        return catalog + translation

    def engine_instruction_block(self, project_id: str | None, engine: str | None) -> str:
        """The user's instructions for an LLM engine: global text, then the project's addition ("" when none
        or for an engine that has no instructions, such as DeepL)."""
        if engine not in self._LLM_TRANSLATION_PROVIDERS:
            return ""
        return engine_instructions_block(
            self._storage.get_engine_instructions(engine),
            self._storage.get_engine_instructions(engine, project_id) if project_id else "",
        )

    def _llm_system_prompt(
        self, project: dict[str, Any], engine: str | None = None, instructions_block: str | None = None,
    ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
        """`instructions_block` replaces the stored instructions (a draft preview); None reads them."""
        rule_ids = set(project.get("projectRuleIds", [])) | {item["ruleId"] for item in project.get("inheritedRules", [])}
        rules = [item for item in self._storage.list_rules() if item["ruleId"] in rule_ids]
        glossary = select_glossary_entries(self._llm_glossary_entries(project))
        block = self.engine_instruction_block(project.get("projectId"), engine) if instructions_block is None else instructions_block
        return build_system_prompt(glossary, rules, project.get("translationRules"), block), glossary, rules

    def engine_prompt_preview(
        self, project_id: str, engine: str, draft: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """The system prompt a batch of this engine would carry for this project, all layers, no book text.
        `draft` ({"global": text, "project": text}, either may be missing) previews unsaved texts instead
        of the stored ones; nothing is written."""
        if engine not in self._LLM_TRANSLATION_PROVIDERS:
            raise TranslationServiceError("Фінальний промпт є лише для Claude, GPT і Gemini.", 400, "translation_invalid")
        project = self._storage.get_project(project_id)
        if project is None:
            raise TranslationServiceError("Проєкт не знайдено.", 404, "not_found")
        if draft is None:
            block = self.engine_instruction_block(project_id, engine)
        else:
            block = engine_instructions_block(
                *(self._draft_text(draft, scope, self._storage.get_engine_instructions(engine, project_id if scope == "project" else None))
                  for scope in ("global", "project"))
            )
        prompt = self._llm_system_prompt(project, engine, block)[0]
        return {
            "projectId": project_id, "engine": engine, "prompt": prompt, "chars": len(prompt),
            "approxTokens": round(len(prompt) / 3.0), "promptHash": prompt_hash(engine, block), "draft": draft is not None,
        }

    def _draft_text(self, draft: dict[str, Any], scope: str, saved: str) -> str:
        """A draft text (validated like a saved one) or, when the draft has none for this scope, the saved one."""
        if draft.get(scope) is None:
            return saved
        try:
            return self._storage.validate_engine_instructions(draft[scope])
        except ValueError as error:
            raise TranslationServiceError(str(error), 400, "translation_invalid") from error

    @classmethod
    def _llm_preceding_context(cls, book_structure: dict[str, Any], first_paragraph_id: str) -> tuple[list[str], list[str]]:
        """Up to N source paragraphs right before the batch, and the last N translations
        already made before it (possibly from an earlier chapter) for name/tone continuity."""
        preceding = []
        for chapter in book_structure.get("chapters", []):
            for element in chapter.get("elements", []):
                if element.get("type") != "paragraph":
                    continue
                if element.get("paragraphId") == first_paragraph_id:
                    break
                if not element.get("isService"):
                    preceding.append(element)
            else:
                continue
            break
        source = [item["originalText"].strip() for item in preceding if (item.get("originalText") or "").strip()]
        translated = [item["translationText"].strip() for item in preceding if (item.get("translationText") or "").strip()]
        return source[-cls._LLM_SOURCE_CONTEXT_PARAGRAPHS:], translated[-cls._LLM_TRANSLATED_CONTEXT_PARAGRAPHS:]

    def _run_llm_translation(
        self,
        project_id: str,
        book_structure: dict[str, Any],
        chapter: dict[str, Any],
        batch_ids: list[str],
        connection: dict[str, Any],
        provider,
        credentials,
        label: str,
        queue_id: str | None = None,
        model_override: str | None = None,
        reasoning_override: str | None = None,
    ) -> tuple[dict[str, str], Any, dict[str, int], dict[str, list[dict[str, str]]], dict[str, Any]]:
        """Translate one batch; no variant is saved here, so any failure leaves them untouched.
        Every API call is recorded in translation_usage as it happens (a failed batch and the
        glossary retry too). Returns the paragraphs, the provider result, summed usage,
        per-paragraph warnings and the priced usage summary of this batch."""
        project = self._storage.get_project(project_id) or {}
        chapter_paragraphs = [element for element in chapter.get("elements", []) if element.get("type") == "paragraph"]
        by_id = {element["paragraphId"]: element for element in chapter_paragraphs}
        chunk_xml = self._build_chunk_xml([
            {"paragraphId": paragraph_id, "originalText": by_id[paragraph_id].get("originalText") or ""}
            for paragraph_id in batch_ids
        ])
        source_context, translated_context = self._llm_preceding_context(book_structure, batch_ids[0])
        instructions, glossary, rules = self._llm_system_prompt(project, connection["providerId"])
        instructions_hash = prompt_hash(connection["providerId"], self.engine_instruction_block(project_id, connection["providerId"]))
        glossary_hits = glossary_terms_in_text(glossary, chunk_xml)
        reasoning = reasoning_override or self.reasoning_level(project, connection["providerId"])
        # One line per batch describing what the prompt carried (term source forms only, no book text).
        log_prefix = connection["providerId"].upper()
        print(f"[{log_prefix} PROMPT]", json.dumps({
            "projectId": project_id,
            "batch": label,
            "glossaryTermCount": len(glossary),
            "glossarySources": [entry["source"] for entry in glossary],
            "characterCount": sum(1 for entry in glossary if is_character(entry)),
            "ruleCount": len(rules) + (1 if (project.get("translationRules") or "").strip() else 0),
            "batchGlossaryHits": [entry["source"] for entry in glossary_hits],
            "reasoning": reasoning,
            "promptHash": instructions_hash,
            "systemPromptChars": len(instructions or ""),  # a stable prefix below the model's cache minimum is never cached
        }, ensure_ascii=False))
        narrators = effective_narrators(project.get("narratorGender"), chapter_paragraphs)
        model = model_override or self._translation_model_for(project, connection["providerId"])
        # source_chars: what the batch asks the engine to translate, for the cost estimate of later queues
        recorder = UsageRecorder(
            self._storage, project_id, chapter.get("chapterId"), connection["providerId"], "translate",
            queue_id=queue_id, source_chars=sum(len(by_id[paragraph_id].get("originalText") or "") for paragraph_id in batch_ids),
        )

        def request_for(extra_reminder: str | None = None) -> TranslationRequest:
            message = build_user_message(chunk_xml, batch_ids, narrators, source_context, translated_context, glossary_hits)
            if extra_reminder:
                message = f"{extra_reminder}\n\n{message}"
            return TranslationRequest(text=message, target_language="UK", instructions=instructions, model=model, reasoning=reasoning)

        usage_total: dict[str, int] = {}
        call = {"attempt": 0}

        def translate_once(request: TranslationRequest, xml_attempts: int, kind: str = "translate"):
            """One request (plus retries for unusable XML); returns (paragraphs, result).
            Any call after the first one of a batch is recorded as kind "retry"."""
            last_error: TranslationServiceError | None = None
            for attempt_in_run in range(xml_attempts):
                call["attempt"] += 1
                recorder.kind = kind if attempt_in_run == 0 else "retry"
                try:
                    with capture_usage(recorder):
                        result = provider.translate(credentials, request)
                except QuotaExceededError as error:
                    raise TranslationServiceError(
                        str(error), 409, "quota_exceeded",
                        details={"connectionId": connection["connectionId"], "providerId": connection["providerId"]},
                    ) from error
                except ValueError as error:
                    logging.error(
                        "LLM translation failed for %s project_id=%s connection_id=%s provider_id=%s: %s",
                        label, project_id, connection["connectionId"], connection["providerId"], error,
                    )
                    raise TranslationServiceError(str(error), 502, "provider_error") from error
                usage = result.usage or {}
                for key, value in usage.items():
                    usage_total[key] = usage_total.get(key, 0) + (value or 0)
                # One JSON line per API call (retries included — each one is billed) for cost accounting.
                print(f"[{log_prefix} USAGE]", json.dumps({
                    "projectId": project_id,
                    "batch": label,
                    "attempt": call["attempt"],
                    "providerId": connection["providerId"],
                    "model": result.model,
                    "inputTokens": usage.get("input_tokens", 0),
                    "outputTokens": usage.get("output_tokens", 0),
                    "cacheReadTokens": usage.get("cache_read_input_tokens", 0),
                    "cacheWriteTokens": usage.get("cache_creation_input_tokens", 0),
                    # all input the model saw; cacheReadTokens/promptTokens shows whether the prefix was cached
                    "promptTokens": usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0) + usage.get("cache_creation_input_tokens", 0),
                    "kind": recorder.kind,
                    "reasoning": result.reasoning,
                    "promptHash": instructions_hash,
                }, ensure_ascii=False))
                try:
                    return self._parse_chunk_xml_result(result.text, list(batch_ids)), result
                except TranslationServiceError as error:
                    last_error = error
                    logging.warning("LLM translation %s attempt %s returned unusable XML: %s", label, call["attempt"], error)
            raise last_error

        translated, result = translate_once(request_for(), self._LLM_BATCH_ATTEMPTS)

        # Glossary check: a term found in a paragraph's original must have its equivalent (in
        # any case/number) in that paragraph's translation. One retry with the misses spelled
        # out; whatever is still missing becomes a warning next to the paragraph.
        hits_by_paragraph = {
            paragraph_id: find_glossary_hits(glossary, by_id[paragraph_id].get("originalText") or "")
            for paragraph_id in batch_ids
        }

        def misses(paragraphs: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
            found = {}
            for paragraph_id, hits in hits_by_paragraph.items():
                missing = missing_terms(hits, paragraphs.get(paragraph_id, "")) if hits else []
                if missing:
                    found[paragraph_id] = missing
            return found

        missing = misses(translated)
        retried = False
        if missing:
            retried = True
            reminder = (
                "У ПОПЕРЕДНІЙ СПРОБІ ПЕРЕКЛАДУ ЦЬОГО ФРАГМЕНТА НЕ ВИКОРИСТАНО ОБОВ'ЯЗКОВІ ВІДПОВІДНИКИ З ГЛОСАРІЮ. "
                "Використай саме їх (змінюй лише відмінок/число):\n"
                + "\n".join(
                    f"- [{paragraph_id}] {entry['source']} → {entry['target']}"
                    for paragraph_id, entries in missing.items() for entry in entries
                )
            )
            try:
                retry_translated, retry_result = translate_once(request_for(reminder), 1, "retry")
            except TranslationServiceError as error:
                if error.code != "chunk_mapping_failed":
                    raise
                logging.warning("LLM translation %s glossary retry returned unusable XML; keeping the first result", label)
            else:
                retry_missing = misses(retry_translated)
                if sum(map(len, retry_missing.values())) <= sum(map(len, missing.values())):
                    translated, result, missing = retry_translated, retry_result, retry_missing
        warnings = {
            paragraph_id: [{"type": "glossary_missing", "source": entry["source"], "target": entry["target"]} for entry in entries]
            for paragraph_id, entries in missing.items()
        }
        if retried:
            print(f"[{log_prefix} GLOSSARY CHECK]", json.dumps({
                "projectId": project_id,
                "batch": label,
                "retried": True,
                "stillMissing": {paragraph_id: [item["source"] for item in items] for paragraph_id, items in warnings.items()},
            }, ensure_ascii=False))
        return translated, result, usage_total, warnings, {**summarize(recorder.rows, self._storage.list_model_prices()), "promptHash": instructions_hash}

    def translate_queue_batch(
        self, project_id: str, chapter_id: str, paragraph_ids: list[str], connection_id: str, queue_id: str,
        model: str | None, reasoning: str | None,
    ) -> dict[str, Any]:
        """One batch of a translation queue: the same request as a single-chapter batch (prompt, XML id check,
        90 s timeout, glossary retry, usage records) with the engine, model and reasoning frozen when the
        queue was created. Nothing is saved here; the queue stores the entries atomically."""
        connection = self._storage.get_integration_connection(connection_id)
        if connection is None or connection["providerId"] not in self._LLM_TRANSLATION_PROVIDERS:
            raise TranslationServiceError("Підключення для черги більше не доступне.", 409, "translation_connection_not_ready")
        if not connection["enabled"] or connection["testStatus"] != "connected":
            raise TranslationServiceError("Підключення для черги має бути активним і перевіреним.", 409, "translation_connection_not_ready")
        provider, credentials = self._provider_credentials(connection)
        book_structure = self._storage.get_book_structure(project_id)
        chapter = ChunkPreparationService._find_chapter(book_structure or {}, chapter_id)
        if chapter is None:
            raise TranslationServiceError("Розділ більше не існує.", 404, "not_found")
        known = {element.get("paragraphId") for element in chapter.get("elements", []) if element.get("type") == "paragraph"}
        if not paragraph_ids or any(paragraph_id not in known for paragraph_id in paragraph_ids):
            raise TranslationServiceError("Абзац більше не існує.", 404, "not_found")
        translated, result, usage, warnings, usage_summary = self._run_llm_translation(
            project_id, book_structure, chapter, list(paragraph_ids), connection, provider, credentials,
            f"queue={queue_id} chapter={chapter_id}", queue_id=queue_id, model_override=model, reasoning_override=reasoning,
        )
        return {
            "entries": [
                {"paragraphId": paragraph_id, "text": translated[paragraph_id], "model": result.model, "warnings": warnings.get(paragraph_id),
                 "promptHash": usage_summary.get("promptHash")}
                for paragraph_id in paragraph_ids
            ],
            "model": result.model, "usage": usage, "usageSummary": usage_summary,
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
                with capture_usage(UsageRecorder(self._storage, project_id, chapter_id, provider_id, "analysis")):
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

    # Canonical inline formatting markers produced by the EPUB parser
    # (backend/parsers/epub.py's _FORMATTING_TAGS): bold/italic/strikethrough
    # spans are stored in originalText as literal "<b>...</b>" etc. text.
    _INLINE_TAGS = {"b", "i", "s"}
    _INLINE_TAG_PATTERN = re.compile(r"<(/?)(b|i|s)>")

    @classmethod
    def _append_inline_markup(cls, parent: ET.Element, text: str) -> None:
        """Turn literal <b>/<i>/<s> markers in `text` into real nested
        sub-elements of `parent`, so DeepL's tag_handling=xml can carry the
        formatting through the translation instead of seeing it as plain text."""
        stack = [parent]

        def append_chunk(chunk: str) -> None:
            if not chunk:
                return
            current = stack[-1]
            if len(current) == 0:
                current.text = (current.text or "") + chunk
            else:
                last_child = current[-1]
                last_child.tail = (last_child.tail or "") + chunk

        pos = 0
        for match in cls._INLINE_TAG_PATTERN.finditer(text):
            append_chunk(text[pos:match.start()])
            pos = match.end()
            closing, tag = match.group(1), match.group(2)
            if closing:
                # Only pop a matching open tag; ignore stray/unbalanced closers
                # defensively rather than raising on malformed source markup.
                if len(stack) > 1 and stack[-1].tag == tag:
                    stack.pop()
            else:
                stack.append(ET.SubElement(stack[-1], tag))
        append_chunk(text[pos:])

    @staticmethod
    def _serialize_inline_markup(element: ET.Element) -> str:
        """Inverse of _append_inline_markup: walk a translated <p> element back
        into the same literal "<b>...</b>" text form used everywhere else
        (storage, export), instead of flattening/losing the tags."""
        parts: list[str] = []
        if element.text:
            parts.append(element.text)
        for child in element:
            tag = child.tag
            parts.append(f"<{tag}>")
            parts.append(TranslationService._serialize_inline_markup(child))
            parts.append(f"</{tag}>")
            if child.tail:
                parts.append(child.tail)
        return "".join(parts)

    @classmethod
    def _build_chunk_xml(cls, paragraphs: list[dict[str, str]]) -> str:
        root = ET.Element("chunk")
        for paragraph in paragraphs:
            element = ET.SubElement(root, "p", {"id": paragraph["paragraphId"]})
            cls._append_inline_markup(element, paragraph["originalText"])
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
            translated[paragraph_id] = TranslationService._serialize_inline_markup(element)

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

    def _default_connection_id(self, connection_id: Any = None) -> str | None:
        """Same resolution _resolve_connection uses, but returns None instead of raising.

        Used for read-only glossary status display, where "no ready connection yet" is a
        normal state to show rather than an error to surface.
        """
        try:
            return self._resolve_connection(connection_id)["connectionId"]
        except TranslationServiceError:
            return None

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