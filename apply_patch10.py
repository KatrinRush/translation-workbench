#!/usr/bin/env python3
"""
apply_patch10.py

Fixes DeepL glossary sync so that updating an ALREADY-synced glossary
(same project, same glossary_rule_id) deletes the old remote glossary
BEFORE creating the new one, instead of after. DeepL allows only one
active glossary per language pair per account, so create-then-delete
briefly needs two glossaries to coexist and hits DeepL's 456 limit
error on the free plan instead of cleanly replacing the old version.

Run from the repository root (the directory containing
backend/translations/service.py):

    python3 apply_patch10.py

Idempotent: running it twice is safe.
"""
from pathlib import Path
import sys

TARGET = Path("backend/translations/service.py")

OLD = '''    def _sync_glossary_with_provider(self, glossary_rule_id: str, connection_id: Any = None) -> dict[str, Any]:
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
        owns_slot = existing_sync and existing_sync["glossaryRuleId"] == glossary_rule_id
        if owns_slot and existing_sync["contentHash"] == glossary["contentHash"]:
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
        previous_remote_glossary_id = existing_sync["remoteGlossaryId"] if existing_sync else None

        if existing_sync and not owns_slot:
            try:
                provider.delete_glossary(credentials, previous_remote_glossary_id)
            except ValueError as error:
                return self._sync_failure("glossary_sync_failed", str(error), 502)
            self._storage.delete_provider_glossary_sync(
                existing_sync["glossaryRuleId"], connection["connectionId"]
            )
            previous_remote_glossary_id = None

        try:
            remote_glossary_id = provider.create_glossary(credentials, definition)
        except GlossaryLimitError as error:
            if not previous_remote_glossary_id:
                return self._sync_failure("glossary_limit_reached", str(error), 502)
            try:
                provider.delete_glossary(credentials, previous_remote_glossary_id)
            except ValueError as delete_error:
                return self._sync_failure("glossary_limit_reached", str(delete_error), 502)
            self._storage.delete_provider_glossary_sync(existing_sync["glossaryRuleId"], connection["connectionId"])
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
        }'''

NEW = '''    def _sync_glossary_with_provider(self, glossary_rule_id: str, connection_id: Any = None) -> dict[str, Any]:
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
            # We already freed the slot we knew about above, so hitting the limit here
            # means something else (untracked on our side) is occupying it.
            return self._sync_failure("glossary_limit_reached", str(error), 502)
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
        }'''


def main():
    if not TARGET.exists():
        sys.exit(f"Не знайдено {TARGET} — запусти скрипт з кореня репозиторію.")

    text = TARGET.read_text(encoding="utf-8")

    if OLD not in text and NEW in text:
        print(f"{TARGET}: патч уже застосовано, нічого робити не треба.")
        return

    if OLD not in text:
        sys.exit(
            f"Не знайшов очікуваний фрагмент у {TARGET} — файл, схоже, "
            "відрізняється від очікуваної версії. Патч не застосовано."
        )

    text = text.replace(OLD, NEW, 1)
    TARGET.write_text(text, encoding="utf-8")
    print(f"{TARGET}: патч успішно застосовано.")


if __name__ == "__main__":
    main()
