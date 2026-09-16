"""Regression coverage for the data-loss class of bug found in _write_project:
INSERT OR REPLACE INTO book_projects deletes and reinserts the row, which
cascades to wipe every child table keyed on project_id (project_rules,
project_glossary, project_translation_glossaries, project_brief_entries,
project_chat_messages) on every single project write.

_write_project itself is covered in test_projects_api.py. This file locks in
the broader guarantee: no OTHER write path that touches book_projects (or
any table keyed on it) may ever drop project_rules/project_glossary either.
It runs a project through a representative sequence of everyday actions —
translating a paragraph, reviewing it, toggling QA/service flags, marking a
narrator POV switch, changing project status/narratorGender, saving
translation rules text, adding QA findings, a project brief entry, a chat
message, committing a DeepL-style translation glossary version, uploading
and clearing a cover, updating AI configuration, and re-importing the EPUB
structure — asserting project_glossary/project_rules survive every step.

It also covers book_documents (title/filename/cover_image/...): unlike
project_rules/project_glossary, book_documents has no ON DELETE CASCADE on
book_projects, so it isn't at risk from that class of bug. But
save_book_structure (EPUB (re)import) does its own DELETE+INSERT of
book_documents by design — and a real, separate bug was found there: an
auto-extracted cover (cover_uploaded_by_user=0) was silently discarded on
re-import whenever the new EPUB didn't carry its own cover, instead of being
kept like a manually-uploaded one already was."""
import base64
import tempfile
import unittest
from pathlib import Path

from backend.storage import Storage

TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
)
# A genuinely different 1x1 PNG (distinct pixel data), not just different bytes
# that normalize to the same image — needed to prove a *replacement* actually happened.
OTHER_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff\x3f\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
)


class BookProjectsWriteSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage = Storage(Path(self.temporary_directory.name) / "workbench.sqlite3")

        self.author = self.storage.create_author({"name": "Author"})
        self.series = self.storage.create_series({"name": "Series"})
        self.rule = self.storage.create_rule({"text": "Keep names romanized."})
        self.glossary_entry = self.storage.create_glossary_entry({"source": "wraith", "target": "привид"})
        self.project = self.storage.create_project({
            "title": "Book",
            "authorId": self.author["authorId"],
            "seriesId": self.series["seriesId"],
            "status": "translation",
            "projectRuleIds": [self.rule["ruleId"]],
            "projectGlossaryEntryIds": [self.glossary_entry["glossaryEntryId"]],
        })
        self.project_id = self.project["projectId"]

        # Cover comes from the EPUB itself (auto-extracted), not a manual upload —
        # exactly the scenario the re-import bug silently dropped.
        structure = self.storage.save_book_structure(
            self.project_id, "book.epub", "application/epub+zip", b"epub-bytes",
            {
                "chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Hello"}]}],
                "coverImage": base64.b64encode(TINY_PNG).decode(),
            },
        )
        self.chapter_id = structure["chapters"][0]["chapterId"]
        self.paragraph_id = structure["chapters"][0]["elements"][0]["paragraphId"]
        self.expected_cover = self.storage.get_project_cover(self.project_id)
        self.assertIsNotNone(self.expected_cover, "test setup should have produced an auto-extracted cover")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _assert_links_survive(self, step: str):
        project = self.storage.get_project(self.project_id)
        self.assertEqual([self.rule["ruleId"]], project["projectRuleIds"], f"project_rules lost after: {step}")
        self.assertEqual(
            [self.glossary_entry["glossaryEntryId"]], project["projectGlossaryEntryIds"],
            f"project_glossary lost after: {step}",
        )

    def _assert_book_document_survives(self, step: str):
        structure = self.storage.get_book_structure(self.project_id)
        self.assertIsNotNone(structure, f"book_documents row lost after: {step}")
        self.assertEqual("book.epub", structure["filename"], f"book_documents.file_name changed after: {step}")
        self.assertEqual(
            self.expected_cover, self.storage.get_project_cover(self.project_id),
            f"book_documents.cover_image lost after: {step}",
        )

    def test_representative_daily_actions_never_drop_glossary_or_rules(self):
        self._assert_links_survive("initial seed")
        self._assert_book_document_survives("initial seed")

        self.storage.update_paragraph(self.paragraph_id, translation_text="Привіт", reviewed=False)
        self._assert_links_survive("save paragraph translation")
        self._assert_book_document_survives("save paragraph translation")

        self.storage.update_paragraph(self.paragraph_id, translation_text="Привіт", reviewed=True)
        self._assert_links_survive("mark paragraph reviewed")
        self._assert_book_document_survives("mark paragraph reviewed")

        self.storage.update_paragraph(self.paragraph_id, translation_text="Привіт", reviewed=True, is_service=True)
        self._assert_links_survive("toggle paragraph service flag on")
        self.storage.update_paragraph(self.paragraph_id, translation_text="Привіт", reviewed=True, is_service=False)
        self._assert_links_survive("toggle paragraph service flag off")
        self._assert_book_document_survives("toggle paragraph service flag")

        self.storage.set_paragraphs_qa_queue([self.paragraph_id], True)
        self._assert_links_survive("queue paragraph for QA")
        self.storage.set_paragraphs_qa_queue([self.paragraph_id], False)
        self._assert_links_survive("dequeue paragraph from QA")
        self._assert_book_document_survives("queue/dequeue paragraph for QA")

        self.storage.set_paragraph_narrator_change(self.paragraph_id, "femn")
        self._assert_links_survive("set paragraph narrator POV marker")
        self._assert_book_document_survives("set paragraph narrator POV marker")

        self.storage.update_project(self.project_id, {"status": "audit"})
        self._assert_links_survive("change project status")
        self._assert_book_document_survives("change project status")

        self.storage.update_project(self.project_id, {"narratorGender": "femn"})
        self._assert_links_survive("set project narratorGender")
        self._assert_book_document_survives("set project narratorGender")

        self.storage.update_project_translation_rules(self.project_id, "Sample translation rules text.")
        self._assert_links_survive("save free-text translation rules")
        self._assert_book_document_survives("save free-text translation rules")

        findings = self.storage.add_chapter_qa_findings(self.chapter_id, [{
            "paragraphId": self.paragraph_id, "category": "typo",
            "quote": "x", "explanation": "", "suggestion": "", "sourceModel": "test",
        }])
        self._assert_links_survive("add chapter QA finding")
        self.storage.delete_chapter_qa_finding(findings[0]["findingId"])
        self._assert_links_survive("resolve chapter QA finding")
        self._assert_book_document_survives("add/resolve chapter QA finding")

        self.storage.create_project_brief_entry(self.project_id, {"text": "Brief note"})
        self._assert_links_survive("add project brief entry")
        self._assert_book_document_survives("add project brief entry")

        self.storage.add_chat_message(self.project_id, "user", "hi", None)
        self._assert_links_survive("add project chat message")
        self._assert_book_document_survives("add project chat message")

        glossary = self.storage.get_or_create_project_translation_glossary(self.project_id, "EN", "UK")
        item_ids = self.storage.resolve_glossary_item_ids([{"source": "ghoul", "target": "вурдалак"}])
        self.storage.commit_translation_glossary_version(glossary["glossaryRuleId"], item_ids)
        self._assert_links_survive("commit DeepL-style translation glossary version")
        self._assert_book_document_survives("commit DeepL-style translation glossary version")

        self.storage.update_project(self.project_id, {"aiConfiguration": {"translationConnectionId": None}})
        self._assert_links_survive("update AI configuration")
        self._assert_book_document_survives("update AI configuration")

        # Re-importing the EPUB (with its own fresh cover) rebuilds book_documents/
        # chapters/paragraphs from scratch but must still leave the project's own
        # glossary/rules alone. Cover-preservation-on-reimport itself is covered by
        # the dedicated tests below, since this step's new EPUB carries its own cover.
        self.storage.save_book_structure(
            self.project_id, "book-v2.epub", "application/epub+zip", b"epub-bytes-v2",
            {"chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Hello again"}]}]},
        )
        self._assert_links_survive("re-import EPUB structure")

    def test_manual_cover_upload_and_clear_do_not_drop_glossary_or_rules(self):
        self.storage.set_project_cover(self.project_id, TINY_PNG)
        self._assert_links_survive("upload project cover")
        self.storage.clear_project_cover(self.project_id)
        self._assert_links_survive("clear project cover")

    def test_reimport_without_new_cover_keeps_auto_extracted_cover(self):
        # The actual bug: re-importing (e.g. replacing the EPUB with a fixed source
        # file) used to silently discard an auto-extracted cover whenever the new
        # analysis didn't itself carry a coverImage, instead of keeping the old one.
        self.storage.save_book_structure(
            self.project_id, "book-v2.epub", "application/epub+zip", b"epub-bytes-v2",
            {"chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Hello again"}]}]},
        )
        self.assertEqual(self.expected_cover, self.storage.get_project_cover(self.project_id))

    def test_reimport_with_new_cover_replaces_auto_extracted_cover(self):
        self.storage.save_book_structure(
            self.project_id, "book-v2.epub", "application/epub+zip", b"epub-bytes-v2",
            {
                "chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Hello again"}]}],
                "coverImage": base64.b64encode(OTHER_TINY_PNG).decode(),
            },
        )
        new_cover = self.storage.get_project_cover(self.project_id)
        self.assertIsNotNone(new_cover)
        self.assertNotEqual(self.expected_cover, new_cover)

    def test_manually_uploaded_cover_wins_over_reimport_even_with_a_new_cover(self):
        self.storage.set_project_cover(self.project_id, OTHER_TINY_PNG)
        expected = self.storage.get_project_cover(self.project_id)

        self.storage.save_book_structure(
            self.project_id, "book-v2.epub", "application/epub+zip", b"epub-bytes-v2",
            {
                "chapters": [{"title": "One", "elements": [{"type": "paragraph", "text": "Hello again"}]}],
                "coverImage": base64.b64encode(TINY_PNG).decode(),
            },
        )
        self.assertEqual(expected, self.storage.get_project_cover(self.project_id))


if __name__ == "__main__":
    unittest.main()
