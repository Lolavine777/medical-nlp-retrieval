# Deterministic Output Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a byte-deterministic ZIP containing exactly `output/1.json` through `output/100.json`, validate it before writing, and generate a clearly non-submittable empty dry-run.

**Architecture:** One stdlib module serializes every prediction list, writes fixed-metadata entries into an in-memory ZIP, reopens and validates all 100 entries, then writes the verified bytes with exclusive creation. A documentation-only second task records the real dry-run checksum.

**Tech Stack:** Python 3.12 standard library, `io.BytesIO`, `zipfile`, `hashlib`, `json`, `unittest`, existing serializer and ZIP input loader.

## Global Constraints

- Require exactly `input/1.txt` through `input/100.txt` for documents and predictions.
- Ignore mapping insertion order and emit numeric document order.
- Include only `output/1.json` through `output/100.json` in the archive.
- Validate every entity list before packaging and again after reopening the ZIP.
- Build and verify bytes before filesystem writes.
- Refuse to overwrite an existing destination or create a missing parent directory.
- Use fixed metadata and `ZIP_STORED` for deterministic bytes.
- Never include raw text, manifests, metadata, or extra files in the ZIP.
- Name the empty dry-run `outputs/NON_SUBMITTABLE-empty-output.zip` and never submit it.
- Add no dependency, model, ontology code, or evaluator behavior.

---

### Task 1: In-memory deterministic ZIP builder

**Files:**
- Create: `src/medical_race/submission.py`
- Create: `tests/test_submission.py`

**Interfaces:**
- Consumes: `Mapping[str, str]` documents, prediction mappings, destination `Path`, and the existing schema mapping.
- Produces: `build_output_zip(documents, predictions, destination, schemas=DEFAULT_SCHEMAS) -> dict[str, object]`.

- [ ] **Step 1: Write failing determinism and rejection tests**

```python
import tempfile
import unittest
import zipfile
from pathlib import Path

from medical_race.submission import build_output_zip


def documents():
    return {f"input/{i}.txt": f"document {i}" for i in range(100, 0, -1)}


def predictions():
    return {f"input/{i}.txt": [] for i in range(1, 101)}


class SubmissionPackageTest(unittest.TestCase):
    def test_builds_identical_verified_archives_in_numeric_order(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.zip"
            second = Path(directory) / "second.zip"
            report = build_output_zip(documents(), predictions(), first)
            build_output_zip(documents(), predictions(), second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(report["entry_count"], 100)
            self.assertEqual(report["entity_count"], 0)
            self.assertEqual(report["empty_document_count"], 100)
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(
                    archive.namelist(),
                    [f"output/{i}.json" for i in range(1, 101)],
                )
                self.assertTrue(all(archive.read(name) == b"[]\n" for name in archive.namelist()))

    def test_rejects_missing_extra_and_invalid_predictions(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "output.zip"
            missing = predictions()
            del missing["input/100.txt"]
            with self.assertRaisesRegex(ValueError, "prediction keys"):
                build_output_zip(documents(), missing, target)
            extra = predictions()
            extra["input/101.txt"] = []
            with self.assertRaisesRegex(ValueError, "prediction keys"):
                build_output_zip(documents(), extra, target)
            invalid = predictions()
            invalid["input/1.txt"] = [{"text": "document", "type": "THUỐC"}]
            with self.assertRaisesRegex(ValueError, "entity 0"):
                build_output_zip(documents(), invalid, target)

    def test_refuses_existing_destination_and_missing_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory) / "existing.zip"
            existing.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                build_output_zip(documents(), predictions(), existing)
            with self.assertRaisesRegex(ValueError, "parent"):
                build_output_zip(
                    documents(),
                    predictions(),
                    Path(directory) / "missing" / "output.zip",
                )
            self.assertEqual(existing.read_bytes(), b"keep")
```

- [ ] **Step 2: Run the focused test to verify RED**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_submission.py' -v`

Expected: ERROR with `ModuleNotFoundError: No module named 'medical_race.submission'`.

- [ ] **Step 3: Implement the minimum builder**

```python
import hashlib
import json
import zipfile
from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path

from medical_race.output import DEFAULT_SCHEMAS, serialize_entities, validate_entities


INPUT_NAMES = tuple(f"input/{i}.txt" for i in range(1, 101))
OUTPUT_NAMES = tuple(f"output/{i}.json" for i in range(1, 101))
FIXED_DATE = (1980, 1, 1, 0, 0, 0)


def build_output_zip(
    documents: Mapping[str, str],
    predictions: Mapping[str, object],
    destination: Path,
    schemas: Mapping[str, Sequence[str]] = DEFAULT_SCHEMAS,
) -> dict[str, object]:
    _validate_keys("document", documents)
    _validate_keys("prediction", predictions)
    destination = Path(destination)
    if not destination.parent.is_dir():
        raise ValueError(f"destination parent does not exist: {destination.parent}")
    if destination.exists():
        raise FileExistsError(destination)

    payloads = []
    entity_count = 0
    empty_count = 0
    for input_name, output_name in zip(INPUT_NAMES, OUTPUT_NAMES, strict=True):
        raw_text = documents[input_name]
        if not isinstance(raw_text, str):
            raise ValueError(f"document {input_name} must be text")
        entities = predictions[input_name]
        payloads.append((output_name, serialize_entities(raw_text, entities, schemas).encode("utf-8")))
        entity_count += len(entities)
        empty_count += not entities

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in payloads:
            info = zipfile.ZipInfo(name, FIXED_DATE)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100600 << 16
            archive.writestr(info, payload)
    data = buffer.getvalue()
    _verify_archive(data, documents, schemas)
    with destination.open("xb") as stream:
        stream.write(data)
    return {
        "entry_count": len(payloads),
        "entity_count": entity_count,
        "empty_document_count": empty_count,
        "byte_count": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _validate_keys(label: str, values: object) -> None:
    if not isinstance(values, Mapping):
        raise ValueError(f"{label} values must be a mapping")
    actual = set(values)
    expected = set(INPUT_NAMES)
    if actual != expected:
        missing = [name for name in INPUT_NAMES if name not in actual]
        extra = [repr(name) for name in actual if name not in expected]
        raise ValueError(f"{label} keys mismatch; missing={missing}; extra={extra}")


def _verify_archive(data: bytes, documents, schemas) -> None:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        if tuple(archive.namelist()) != OUTPUT_NAMES:
            raise ValueError("archive entry names mismatch")
        for input_name, output_name in zip(INPUT_NAMES, OUTPUT_NAMES, strict=True):
            entities = json.loads(archive.read(output_name).decode("utf-8"))
            validate_entities(documents[input_name], entities, schemas)
```

- [ ] **Step 4: Run focused and full tests**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_submission.py' -v`

Expected: 3 tests pass.

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: Existing 46 tests plus 3 submission tests pass.

- [ ] **Step 5: Commit the builder**

```powershell
git add src/medical_race/submission.py tests/test_submission.py
git commit -m "feat: add deterministic output package"
```

### Task 2: Pinned non-submittable dry-run

**Files:**
- Generate, ignored: `outputs/NON_SUBMITTABLE-empty-output.zip`
- Create: `docs/package_checkpoint_2026-07-12.md`

**Interfaces:**
- Consumes: pinned `input.zip`, `read_zip_documents`, and the Task 1 builder.
- Produces: a verified format-only ZIP and a committed evidence record.

- [ ] **Step 1: Generate the empty dry-run once**

Run:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -c "from pathlib import Path; from tools.audit_sources import read_zip_documents; from medical_race.submission import build_output_zip; d=read_zip_documents(Path('input.zip')); print(build_output_zip(d,{name:[] for name in d},Path('outputs/NON_SUBMITTABLE-empty-output.zip')))"
```

Expected: `entry_count=100`, `entity_count=0`, and `empty_document_count=100`.

- [ ] **Step 2: Reopen and verify the pinned artifact independently**

Run:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -c "import hashlib,json,zipfile; from pathlib import Path; p=Path('outputs/NON_SUBMITTABLE-empty-output.zip'); z=zipfile.ZipFile(p); names=z.namelist(); assert names==[f'output/{i}.json' for i in range(1,101)]; assert all(json.loads(z.read(n))==[] for n in names); print(len(names),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())"
```

Expected: 100 entries and a stable byte size and SHA-256 value.

- [ ] **Step 3: Record evidence and limits**

Create `docs/package_checkpoint_2026-07-12.md` with the pinned input hash, dry-run path, byte size, SHA-256, entry count, entity count, access date, confidence, strategic impact, `NON_SUBMITTABLE` warning, and parameter budget `0 / 9B`.

- [ ] **Step 4: Run final verification**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: All tests pass.

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m compileall -q src tools tests`

Expected: Exit 0.

Run: `git diff --check`

Expected: Exit 0.

- [ ] **Step 5: Commit the checkpoint evidence**

```powershell
git add docs/package_checkpoint_2026-07-12.md
git commit -m "docs: record deterministic package evidence"
```
