import unittest

from medical_race.model_proposals import (
    GroundedProposal,
    ModelProposal,
    PROMPT_ALLOWED_TYPES,
    PROMPT_HEADERS,
    ground_proposals,
    parse_model_response,
    prompt_chunks,
    prompt_sha256,
    salvage_model_response,
)


class ModelResponseTest(unittest.TestCase):
    def test_parses_only_exact_three_field_objects(self):
        value = '[{"line_index":1,"text":"đau ngực","type":"TRIỆU_CHỨNG"}]'

        self.assertEqual(
            parse_model_response(value),
            (ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),),
        )

    def test_rejects_non_json_unknown_fields_bad_indices_and_unknown_types(self):
        invalid = [
            "not json",
            "{}",
            "```json\n[]\n```",
            '[{"line_index":0,"text":"ho","type":"TRIỆU_CHỨNG","score":1}]',
            '[{"line_index":true,"text":"ho","type":"TRIỆU_CHỨNG"}]',
            '[{"line_index":-1,"text":"ho","type":"TRIỆU_CHỨNG"}]',
            '[{"line_index":0,"text":"","type":"TRIỆU_CHỨNG"}]',
            '[{"line_index":0,"text":"ho","type":"OTHER"}]',
        ]

        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_model_response(value)

    def test_salvage_keeps_valid_item_beside_invalid_grounding_item(self):
        valid_type = sorted(PROMPT_ALLOWED_TYPES[2])[0]
        response = (
            '[{"line_index":1,"text":"cough","type":"'
            + valid_type
            + '"},{"line_index":1,"text":"fever","type":"'
            + valid_type
            + '"}]'
        )

        proposals, category = salvage_model_response(
            "symptoms\ncough\n",
            response,
            frozenset({1}),
            PROMPT_ALLOWED_TYPES[2],
        )

        self.assertEqual(proposals, (ModelProposal(1, "cough", valid_type),))
        self.assertEqual(category, "grounding")

    def test_salvage_keeps_valid_item_beside_unknown_type(self):
        valid_type = sorted(PROMPT_ALLOWED_TYPES[2])[0]
        response = (
            '[{"line_index":1,"text":"cough","type":"'
            + valid_type
            + '"},{"line_index":1,"text":"cough","type":"NOT_ALLOWED"}]'
        )

        proposals, category = salvage_model_response(
            "symptoms\ncough\n",
            response,
            frozenset({1}),
            PROMPT_ALLOWED_TYPES[2],
        )

        self.assertEqual(proposals, (ModelProposal(1, "cough", valid_type),))
        self.assertEqual(category, "parse")

    def test_salvage_rejects_non_array_response(self):
        proposals, category = salvage_model_response(
            "symptoms\ncough\n",
            "not json",
            frozenset({1}),
            PROMPT_ALLOWED_TYPES[2],
        )

        self.assertEqual(proposals, ())
        self.assertEqual(category, "parse")

    def test_salvage_accepts_empty_array_without_error(self):
        proposals, category = salvage_model_response(
            "symptoms\ncough\n",
            "[]",
            frozenset({1}),
            PROMPT_ALLOWED_TYPES[2],
        )

        self.assertEqual(proposals, ())
        self.assertIsNone(category)


class PromptChunkTest(unittest.TestCase):
    def test_prompt_profiles_preserve_v1_and_target_v2(self):
        self.assertEqual(set(PROMPT_HEADERS), {1, 2})
        self.assertNotEqual(prompt_sha256(1), prompt_sha256(2))
        self.assertEqual(
            PROMPT_ALLOWED_TYPES[2],
            frozenset(
                {
                    "TRIỆU_CHỨNG",
                    "TÊN_XÉT_NGHIỆM",
                    "KẾT_QUẢ_XÉT_NGHIỆM",
                }
            ),
        )
        prompt = prompt_chunks(
            "Triệu chứng hiện tại\nHo\n",
            prompt_version=2,
        )[0].prompt
        self.assertNotIn("CHẨN_ĐOÁN", prompt)
        self.assertNotIn("THUỐC", prompt)

    def test_chunks_nonblank_lines_once_with_global_indices(self):
        raw = "Chẩn đoán\nViêm phổi\n\nTriệu chứng hiện tại\nHo\n"

        chunks = prompt_chunks(raw, max_chars=20)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(
            tuple(index for chunk in chunks for index in chunk.line_indices),
            (0, 1, 3, 4),
        )
        self.assertEqual(chunks, prompt_chunks(raw, max_chars=20))
        for chunk in chunks:
            self.assertTrue(chunk.line_indices)
            for index in chunk.line_indices:
                self.assertIn(f"{index}\t", chunk.prompt)

    def test_keeps_one_oversized_line_whole(self):
        raw = "một dòng rất dài"

        chunks = prompt_chunks(raw, max_chars=3)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].line_indices, (0,))
        self.assertIn(raw, chunks[0].prompt)

    def test_rejects_nonpositive_chunk_limit(self):
        with self.assertRaisesRegex(ValueError, "max_chars"):
            prompt_chunks("text", max_chars=0)


class ProposalGroundingTest(unittest.TestCase):
    def test_grounds_every_exact_duplicate(self):
        raw = "Triệu chứng hiện tại\n- đau ngực, đau ngực\n"

        grounded = ground_proposals(
            raw,
            (ModelProposal(1, "đau ngực", "TRIỆU_CHỨNG"),),
        )

        self.assertEqual(
            [value.span.text for value in grounded],
            ["đau ngực", "đau ngực"],
        )
        self.assertTrue(all(isinstance(value, GroundedProposal) for value in grounded))
        self.assertEqual([value.section for value in grounded], ["symptoms", "symptoms"])
        for value in grounded:
            self.assertEqual(raw[value.span.start : value.span.end], value.span.text)

    def test_rejects_normalized_text_and_invalid_line_index(self):
        raw = "Triệu chứng hiện tại\n- đau ngực\n"

        with self.assertRaisesRegex(ValueError, "not found verbatim"):
            ground_proposals(
                raw,
                (ModelProposal(1, "dau nguc", "TRIỆU_CHỨNG"),),
            )
        with self.assertRaisesRegex(ValueError, "line_index"):
            ground_proposals(
                raw,
                (ModelProposal(20, "đau ngực", "TRIỆU_CHỨNG"),),
            )

    def test_returns_deterministic_raw_offset_order(self):
        raw = "Triệu chứng hiện tại\n- ho và sốt\n"
        proposals = (
            ModelProposal(1, "sốt", "TRIỆU_CHỨNG"),
            ModelProposal(1, "ho", "TRIỆU_CHỨNG"),
        )

        grounded = ground_proposals(raw, proposals)

        self.assertEqual([value.span.text for value in grounded], ["ho", "sốt"])


if __name__ == "__main__":
    unittest.main()
