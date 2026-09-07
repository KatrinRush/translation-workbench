import unittest

from backend.translations.context import build_deepl_context


class DeepLContextTests(unittest.TestCase):
    def test_non_service_paragraphs_keep_existing_context_behavior(self):
        structure = self._book(["Before.", "Target.", "After."])

        self.assertEqual("Before. After.", build_deepl_context(structure, ["p2"]))

    def test_service_paragraph_is_excluded_from_context(self):
        structure = {
            "chapters": [{"elements": [
                {"type": "paragraph", "paragraphId": "p1", "originalText": "Before."},
                {"type": "paragraph", "paragraphId": "p2", "originalText": "Service label.", "isService": True},
                {"type": "paragraph", "paragraphId": "p3", "originalText": "Target."},
                {"type": "paragraph", "paragraphId": "p4", "originalText": "After."},
            ]}]
        }

        self.assertEqual("Before. After.", build_deepl_context(structure, ["p3"]))

    def test_context_skips_service_paragraph_between_artistic_paragraphs(self):
        structure = {
            "chapters": [{"elements": [
                {"type": "paragraph", "paragraphId": "p1", "originalText": "Before one. Before two."},
                {"type": "paragraph", "paragraphId": "p2", "originalText": "Service one. Service two. Service three.", "isService": True},
                {"type": "paragraph", "paragraphId": "p3", "originalText": "Target."},
                {"type": "paragraph", "paragraphId": "p4", "originalText": "After one. After two."},
            ]}]
        }

        self.assertEqual("Before one. Before two. After one. After two.", build_deepl_context(structure, ["p3"]))

    def test_service_target_returns_none(self):
        structure = self._book(["Before.", "Service target.", "After."])
        structure["chapters"][0]["elements"][1]["isService"] = True

        self.assertIsNone(build_deepl_context(structure, ["p2"]))

    def test_middle_of_paragraph_excludes_all_target_sentences(self):
        structure = self._book(
            ["Before.", "Target one. Target two. Target three.", "After one. After two. After three."]
        )

        self.assertEqual(
            "Before. After one. After two. After three.",
            build_deepl_context(structure, ["p2"]),
        )

    def test_context_crosses_paragraph_boundary_in_source_order(self):
        structure = self._book(
            ["Before one. Before two.", "Target.", "After one. After two."]
        )

        self.assertEqual(
            "Before one. Before two. After one. After two.",
            build_deepl_context(structure, ["p2"]),
        )

    def test_beginning_of_book_uses_only_following_sentences(self):
        structure = self._book(
            ["Current one.", "After one.", "After two.", "After three.", "After four."]
        )

        self.assertEqual(
            "After one. After two. After three.",
            build_deepl_context(structure, ["p1"]),
        )

    def test_middle_of_book_uses_three_sentences_on_each_side(self):
        structure = self._book(
            ["Before one.", "Before two.", "Before three.", "Current.", "After one.", "After two.", "After three."]
        )

        self.assertEqual(
            "Before one. Before two. Before three. After one. After two. After three.",
            build_deepl_context(structure, ["p4"]),
        )

    def test_beginning_of_chapter_uses_previous_chapter_sentences(self):
        structure = {
            "chapters": [
                {"elements": [{"type": "paragraph", "paragraphId": "p1", "originalText": "Previous one. Previous two."}]},
                {"elements": [{"type": "paragraph", "paragraphId": "p2", "originalText": "Current."}, {"type": "paragraph", "paragraphId": "p3", "originalText": "After."}]},
            ]
        }

        self.assertEqual("Previous one. Previous two. After.", build_deepl_context(structure, ["p2"]))

    def test_chapter_metadata_and_translation_fields_are_ignored(self):
        structure = {
            "chapters": [{
                "title": "Chapter title. Do not use.",
                "translationTitle": "Translated title. Do not use.",
                "elements": [
                    {"type": "image", "imageId": "image-1", "originalText": "Image text. Do not use."},
                    {
                        "type": "paragraph",
                        "paragraphId": "p1",
                        "originalText": "Current.",
                        "translationText": "Translated sentence. Do not use.",
                        "reviewed": True,
                    },
                    {"type": "paragraph", "paragraphId": "p2", "originalText": "After."},
                ],
            }]
        }

        self.assertEqual("After.", build_deepl_context(structure, ["p1"]))

    def test_end_of_chapter_uses_next_chapter_sentences(self):
        structure = {
            "chapters": [
                {"elements": [{"type": "paragraph", "paragraphId": "p1", "originalText": "Before."}, {"type": "paragraph", "paragraphId": "p2", "originalText": "Current."}]},
                {"elements": [{"type": "paragraph", "paragraphId": "p3", "originalText": "Next one. Next two."}]},
            ]
        }

        self.assertEqual("Before. Next one. Next two.", build_deepl_context(structure, ["p2"]))

    def test_end_of_book_uses_only_preceding_sentences(self):
        structure = self._book(["Before one.", "Before two.", "Before three.", "Current."])

        self.assertEqual(
            "Before one. Before two. Before three.",
            build_deepl_context(structure, ["p4"]),
        )

    @staticmethod
    def _book(texts):
        return {
            "chapters": [{
                "elements": [
                    {"type": "paragraph", "paragraphId": f"p{index}", "originalText": text}
                    for index, text in enumerate(texts, 1)
                ]
            }]
        }


if __name__ == "__main__":
    unittest.main()
