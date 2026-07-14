import json
import unittest

from tools.fetch_icd10_vn import canonical_snapshot, collect_catalog


BASE = "https://example.test/api/ICD10"


class FakeFetch:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        return self.responses[url]


def node(model, node_id, code, name, is_leaf):
    return {
        "model": model,
        "id": node_id,
        "is_leaf": is_leaf,
        "data": {"id": node_id, "code": code, "name": name, "html": None},
    }


class ICD10AcquisitionTests(unittest.TestCase):
    def test_recursively_collects_and_stably_orders_hierarchy(self):
        fetch = FakeFetch(
            {
                f"{BASE}/root?lang=vi": {
                    "status": "success",
                    "data": [
                        node("chapter", "II", "II", "U tân sinh", False),
                        node("chapter", "I", "I", "Bệnh truyền nhiễm", False),
                    ],
                },
                f"{BASE}/childs/chapter?id=I&lang=vi": {
                    "status": "success",
                    "data": [node("type", "A00", "A00", "Bệnh tả", True)],
                },
                f"{BASE}/childs/chapter?id=II&lang=vi": {
                    "status": "success",
                    "data": [node("type", "C00", "C00", "U ác tính", True)],
                },
            }
        )

        catalog = collect_catalog(fetch, BASE, "vi")

        self.assertEqual(
            [(item["model"], item["id"]) for item in catalog],
            [("type", "A00"), ("type", "C00"), ("chapter", "I"), ("chapter", "II")],
        )
        a00 = next(item for item in catalog if item["id"] == "A00")
        self.assertEqual(a00["parent"], {"model": "chapter", "id": "I"})
        self.assertEqual(len(fetch.calls), 3)

    def test_collapses_identical_duplicate_nodes(self):
        duplicate = node("chapter", "I", "I", "Bệnh truyền nhiễm", True)
        fetch = FakeFetch(
            {
                f"{BASE}/root?lang=vi": {
                    "status": "success",
                    "data": [duplicate, duplicate],
                }
            }
        )

        self.assertEqual(len(collect_catalog(fetch, BASE, "vi")), 1)

    def test_rejects_conflicting_duplicate_nodes(self):
        fetch = FakeFetch(
            {
                f"{BASE}/root?lang=vi": {
                    "status": "success",
                    "data": [
                        node("chapter", "I", "I", "First", True),
                        node("chapter", "I", "I", "Second", True),
                    ],
                }
            }
        )

        with self.assertRaisesRegex(ValueError, "conflicting duplicate"):
            collect_catalog(fetch, BASE, "vi")

    def test_rejects_hierarchy_cycles(self):
        fetch = FakeFetch(
            {
                f"{BASE}/root?lang=vi": {
                    "status": "success",
                    "data": [node("chapter", "I", "I", "Root", False)],
                },
                f"{BASE}/childs/chapter?id=I&lang=vi": {
                    "status": "success",
                    "data": [node("chapter", "I", "I", "Root", False)],
                },
            }
        )

        with self.assertRaisesRegex(ValueError, "cycle"):
            collect_catalog(fetch, BASE, "vi")

    def test_rejects_unsuccessful_or_malformed_responses(self):
        bad_responses = (
            {"status": "error", "data": []},
            {"status": "success", "data": "not a list"},
            {"status": "success", "data": [{"model": "chapter"}]},
        )
        for response in bad_responses:
            with self.subTest(response=response):
                fetch = FakeFetch({f"{BASE}/root?lang=vi": response})
                with self.assertRaises(ValueError):
                    collect_catalog(fetch, BASE, "vi")

    def test_canonical_snapshot_is_deterministic_utf8_json(self):
        nodes = [
            {
                "model": "type",
                "id": "A00",
                "code": "A00",
                "name": "Bệnh tả",
                "is_leaf": True,
                "parent": {"model": "chapter", "id": "I"},
            }
        ]

        first = canonical_snapshot(nodes, BASE, "vi")
        second = canonical_snapshot(list(reversed(nodes)), BASE, "vi")

        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))
        self.assertIn("Bệnh tả", first.decode("utf-8"))
        self.assertEqual(json.loads(first)["format_version"], 1)


if __name__ == "__main__":
    unittest.main()
