import json
import unittest
from pathlib import Path


class ModelBudgetTest(unittest.TestCase):
    def test_qwen_configuration_is_pinned_and_compliant(self):
        budget = json.loads(
            Path("configs/model_budget.json").read_text(encoding="utf-8")
        )
        configurations = json.loads(
            Path("configs/model_configurations.json").read_text(encoding="utf-8")
        )

        model = next(
            value
            for value in budget["models"]
            if value["id"] == "qwen3_4b_instruct_2507"
        )
        self.assertEqual(
            model["revision"],
            "1b4199c4f36b0cef378bfb12390c18780c18af4c",
        )
        self.assertEqual(model["parameters"], 4_000_000_000)
        self.assertEqual(model["license"], "Apache-2.0")

        active = next(
            value
            for value in configurations["configurations"]
            if value["id"] == "qwen_grounded_proposals"
        )
        self.assertEqual(active["active_model_ids"], [model["id"]])
        self.assertEqual(active["combined_parameters"], model["parameters"])
        self.assertLessEqual(
            active["combined_parameters"],
            configurations["budget_limit_parameters"],
        )
        self.assertTrue(active["compliant"])
        self.assertFalse(active["unused_checkpoints_included"])


if __name__ == "__main__":
    unittest.main()
