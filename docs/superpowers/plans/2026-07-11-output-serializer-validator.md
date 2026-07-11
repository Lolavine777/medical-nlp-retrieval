# Output Serializer and Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject invalid type-dependent entity lists and serialize valid lists deterministically without changing text, offsets, ordering, or duplicate mentions.

**Architecture:** One standard-library module owns the final per-document boundary. It validates an explicit schema mapping, reuses the shared offset validator, and emits fields in schema order with UTF-8 JSON.

**Tech Stack:** Python 3.12 standard library, `json`, `collections.abc`, `unittest`, existing official fixture and offset validator.

## Global Constraints

- Reject the entire document on the first invalid entity.
- Never repair, drop, deduplicate, sort, or supplement entities.
- Preserve `raw_text[start:end] == text`, entity order, and duplicate mentions.
- Emit no field outside the selected schema.
- Require non-empty candidates when a type schema includes `candidates`.
- Permit only `isNegated`, `isFamily`, and `isHistorical` assertions.
- Keep hidden laboratory schema policy injectable through one mapping argument.
- Add no dependency, ontology code, packager, or model parameter.

---

### Task 1: Strict validator and deterministic serializer

**Files:**
- Create: `src/medical_race/output.py`
- Create: `tests/test_output.py`

**Interfaces:**
- Consumes: a raw string, a JSON-style entity list, and an optional `Mapping[str, Sequence[str]]` schema.
- Produces: `DEFAULT_SCHEMAS`, `validate_entities(raw_text, entities, schemas=DEFAULT_SCHEMAS) -> None`, and `serialize_entities(raw_text, entities, schemas=DEFAULT_SCHEMAS) -> str`.

- [ ] **Step 1: Write failing official-fixture and strict-error tests**

```python
import copy
import json
import unittest
from pathlib import Path

from medical_race.output import DEFAULT_SCHEMAS, serialize_entities, validate_entities


FIXTURE = Path("tests/fixtures/official_example.json")


class OutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_official_entities_round_trip_with_unicode_and_duplicates(self):
        serialized = serialize_entities(
            self.example["raw_text"],
            self.example["entities"],
        )
        entities = json.loads(serialized)
        self.assertEqual(entities, self.example["entities"])
        self.assertIn("đau nhức", serialized)
        validate_entities(self.example["raw_text"], entities)

    def test_rejects_missing_candidate_and_extra_field(self):
        entity = copy.deepcopy(self.example["entities"][0])
        del entity["candidates"]
        with self.assertRaisesRegex(ValueError, "entity 0.*missing"):
            validate_entities(self.example["raw_text"], [entity])
        entity = copy.deepcopy(self.example["entities"][0])
        entity["relations"] = []
        with self.assertRaisesRegex(ValueError, "entity 0.*extra"):
            validate_entities(self.example["raw_text"], [entity])

    def test_rejects_invalid_lists_offsets_and_type(self):
        entity = copy.deepcopy(self.example["entities"][0])
        entity["assertions"] = ["unknown"]
        with self.assertRaisesRegex(ValueError, "assertions"):
            validate_entities(self.example["raw_text"], [entity])
        entity = copy.deepcopy(self.example["entities"][0])
        entity["candidates"] = ["308135", "308135"]
        with self.assertRaisesRegex(ValueError, "candidates"):
            validate_entities(self.example["raw_text"], [entity])
        entity = copy.deepcopy(self.example["entities"][0])
        entity["position"] = [True, 83]
        with self.assertRaisesRegex(ValueError, "position"):
            validate_entities(self.example["raw_text"], [entity])
        entity = copy.deepcopy(self.example["entities"][0])
        entity["type"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "unknown type"):
            validate_entities(self.example["raw_text"], [entity])

    def test_laboratory_schema_is_configurable_without_extra_code_path(self):
        raw = "kali"
        entity = {
            "text": "kali",
            "type": "TÊN_XÉT_NGHIỆM",
            "assertions": [],
            "position": [0, 4],
        }
        schemas = dict(DEFAULT_SCHEMAS)
        schemas["TÊN_XÉT_NGHIỆM"] = ("text", "type", "assertions", "position")
        validate_entities(raw, [entity], schemas)
        with self.assertRaisesRegex(ValueError, "extra"):
            validate_entities(raw, [entity])
```

- [ ] **Step 2: Run the focused test to verify RED**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_output.py' -v`

Expected: ERROR with `ModuleNotFoundError: No module named 'medical_race.output'`.

- [ ] **Step 3: Implement the minimum boundary**

```python
import json
from collections.abc import Mapping, Sequence

from medical_race.offsets import validate_entity_offset


DEFAULT_SCHEMAS = {
    "THUỐC": ("text", "type", "candidates", "assertions", "position"),
    "CHẨN_ĐOÁN": ("text", "type", "candidates", "assertions", "position"),
    "TRIỆU_CHỨNG": ("text", "type", "assertions", "position"),
    "TÊN_XÉT_NGHIỆM": ("text", "type", "position"),
    "KẾT_QUẢ_XÉT_NGHIỆM": ("text", "type", "position"),
}
KNOWN_FIELDS = {"text", "type", "candidates", "assertions", "position"}
KNOWN_ASSERTIONS = {"isNegated", "isFamily", "isHistorical"}


def validate_entities(
    raw_text: str,
    entities: object,
    schemas: Mapping[str, Sequence[str]] = DEFAULT_SCHEMAS,
) -> None:
    if not isinstance(entities, list):
        raise ValueError("entities must be a list")
    _validate_schemas(schemas)
    for index, entity in enumerate(entities):
        try:
            _validate_entity(raw_text, entity, schemas)
        except ValueError as error:
            raise ValueError(f"entity {index}: {error}") from error


def serialize_entities(
    raw_text: str,
    entities: object,
    schemas: Mapping[str, Sequence[str]] = DEFAULT_SCHEMAS,
) -> str:
    validate_entities(raw_text, entities, schemas)
    ordered = [
        {field: entity[field] for field in schemas[entity["type"]]}
        for entity in entities
    ]
    return json.dumps(ordered, ensure_ascii=False, separators=(",", ":")) + "\n"


def _validate_schemas(schemas: Mapping[str, Sequence[str]]) -> None:
    for entity_type, fields in schemas.items():
        field_set = set(fields)
        if not {"text", "type", "position"} <= field_set or not field_set <= KNOWN_FIELDS:
            raise ValueError(f"invalid schema for {entity_type}")
        if len(fields) != len(field_set):
            raise ValueError(f"duplicate schema field for {entity_type}")


def _validate_entity(raw_text: str, entity: object, schemas) -> None:
    if not isinstance(entity, Mapping):
        raise ValueError("must be an object")
    entity_type = entity.get("type")
    if entity_type not in schemas:
        raise ValueError(f"unknown type: {entity_type!r}")
    expected = set(schemas[entity_type])
    actual = set(entity)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise ValueError(f"missing fields: {sorted(missing)}")
    if extra:
        raise ValueError(f"extra fields: {sorted(extra)}")
    if not isinstance(entity["text"], str) or not entity["text"]:
        raise ValueError("text must be a non-empty string")
    position = entity["position"]
    if (
        not isinstance(position, list)
        or len(position) != 2
        or any(type(value) is not int for value in position)
    ):
        raise ValueError("position must be a two-integer list")
    validate_entity_offset(raw_text, entity)
    if "assertions" in expected:
        _validate_string_list(entity["assertions"], "assertions", allow_empty=True)
        if not set(entity["assertions"]) <= KNOWN_ASSERTIONS:
            raise ValueError("assertions contain an unknown value")
    if "candidates" in expected:
        _validate_string_list(entity["candidates"], "candidates", allow_empty=False)


def _validate_string_list(value: object, name: str, allow_empty: bool) -> None:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError(f"{name} must contain unique non-empty strings")
```

- [ ] **Step 4: Run focused and full tests**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_output.py' -v`

Expected: 4 tests pass.

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: Existing 40 tests plus 4 output tests pass.

- [ ] **Step 5: Commit the strict boundary**

```powershell
git add src/medical_race/output.py tests/test_output.py
git commit -m "feat: add strict output serializer"
```

### Task 2: Official fixture checksum and checkpoint evidence

**Files:**
- Create: `docs/output_checkpoint_2026-07-11.md`

**Interfaces:**
- Consumes: the Task 1 serializer and official fixture.
- Produces: verified round-trip and SHA-256 evidence without adding another production code path.

- [ ] **Step 1: Generate and verify the official fixture output**

Run:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -c "import hashlib,json; from pathlib import Path; from medical_race.output import serialize_entities,validate_entities; x=json.loads(Path('tests/fixtures/official_example.json').read_text(encoding='utf-8')); s=serialize_entities(x['raw_text'],x['entities']); y=json.loads(s); validate_entities(x['raw_text'],y); print(len(y),hashlib.sha256(s.encode('utf-8')).hexdigest())"
```

Expected: entity count `19` and a stable SHA-256 value.

- [ ] **Step 2: Record evidence and limitations**

Create `docs/output_checkpoint_2026-07-11.md` with the command result, official fixture provenance, access date, evidence, confidence, strategic impact, provisional laboratory schema warning, strict-rejection behavior, and model budget `0 / 9B`.

- [ ] **Step 3: Run final verification**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: All tests pass.

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m compileall -q src tools tests`

Expected: Exit 0.

Run: `git diff --check`

Expected: Exit 0.

- [ ] **Step 4: Commit checkpoint evidence**

```powershell
git add docs/output_checkpoint_2026-07-11.md
git commit -m "docs: record output boundary evidence"
```
