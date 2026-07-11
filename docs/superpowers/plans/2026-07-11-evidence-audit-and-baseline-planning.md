# Evidence Audit and Baseline Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a reproducible audit of the official artifacts, record sourced research and assumptions, verify offset behavior in code, create the minimum repository structure, and publish a checkpointed plan for the rule baseline.

**Architecture:** Standard-library Python reads the canonical root artifacts without extracting or modifying them and emits deterministic JSON evidence.
The documentation layer separates verified facts, inferences, and unresolved assumptions, while the future baseline remains decomposed into offset-safe parsing, extraction, assertion, linking, serialization, validation, and evaluation checkpoints.

**Tech Stack:** Python 3 standard library, `unittest`, Markdown, JSON, and Git.

## Global Constraints

- Keep `input.zip` and the saved official HTML immutable at the repository root.
- Do not copy `input.zip` into `data/raw/`.
- Preserve exact UTF-8 raw text and use end-exclusive offsets.
- Preserve repeated mentions at different positions.
- Never emit an ICD or RxNorm identifier absent from an approved local snapshot.
- Do not add model code, model dependencies, or external inference calls in this milestone.
- Run Python through `.venv\Scripts\python.exe` or `uv run`.
- Put every complete sentence in long Markdown files on its own physical line.

---

## File map

- `pyproject.toml` defines the minimum package and test metadata without runtime dependencies.
- `.gitignore` excludes virtual environments, caches, derived reports, generated outputs, and local ontology payloads while retaining provenance files.
- `tools/audit_sources.py` computes deterministic evidence from the ZIP and saved HTML.
- `src/medical_race/offsets.py` contains the shared raw-span invariant used by later components.
- `tests/fixtures/official_example.json` preserves the official raw example with escaped CRLF and leading spaces plus its 19 entities.
- `tests/test_audit_sources.py` protects ZIP membership, UTF-8 validation, line counting, and deterministic statistics.
- `tests/test_offsets.py` protects end-exclusive slicing, schema observations, and repeated mentions.
- `research/notes.md` records sourced findings with access date, evidence, confidence, uncertainty, and strategic impact.
- `research/sources.jsonl` provides one machine-readable record per source.
- `docs/assumptions.md` records unresolved claims and how each can be falsified.
- `docs/annotation_policy.md` defines only policies supported by official evidence and clearly marks provisional rules.
- `docs/baseline_plan.md` defines implementation checkpoints and leaderboard experiments after the evidence review.
- `README.md` documents the canonical artifacts, reproducible commands, and repository layout.
- `data/`, `ontologies/`, `configs/`, and `outputs/` are created as directories without duplicate raw artifacts or placeholder files.

### Task 1: Minimal project tooling and deterministic source audit

**Files:**

- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `tools/audit_sources.py`
- Create: `tests/test_audit_sources.py`
- Generate: `outputs/source_audit.json`

**Interfaces:**

- Consumes: `input.zip` and the saved official HTML path.
- Produces: `read_zip_documents(path: Path) -> dict[str, str]`.
- Produces: `audit_documents(documents: Mapping[str, str]) -> dict[str, object]`.
- Produces: `audit_sources(zip_path: Path, html_path: Path) -> dict[str, object]`.

- [ ] **Step 1: Create the virtual environment and minimal metadata**

Run:

```powershell
py -m venv .venv
```

Create `pyproject.toml` with no third-party dependencies:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "medical-race-viettel"
version = "0.1.0"
requires-python = ">=3.11"

[tool.setuptools.packages.find]
where = ["src"]
```

Create `.gitignore`:

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
outputs/*
!outputs/README.md
data/external/*
data/processed/*
data/synthetic/*
ontologies/icd/*
!ontologies/icd/README.md
ontologies/rxnorm/*
!ontologies/rxnorm/README.md
```

- [ ] **Step 2: Write failing audit tests**

Create `tests/test_audit_sources.py`:

```python
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.audit_sources import audit_documents, read_zip_documents


class AuditSourcesTest(unittest.TestCase):
    def test_reads_utf8_txt_entries_in_numeric_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("input/2.txt", "hai\n")
                archive.writestr("input/1.txt", "một\n")
            self.assertEqual(
                list(read_zip_documents(path)),
                ["input/1.txt", "input/2.txt"],
            )

    def test_rejects_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("input/1.txt", b"\xff")
            with self.assertRaises(UnicodeDecodeError):
                read_zip_documents(path)

    def test_counts_physical_lines_without_adding_trailing_empty_line(self):
        report = audit_documents({"input/1.txt": "a\nb\n"})
        self.assertEqual(report["line_count"]["sum"], 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests and verify the expected failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_audit_sources -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'tools.audit_sources'`.

- [ ] **Step 4: Implement the minimum audit**

Create `tools/audit_sources.py` with these exact behaviors:

```python
import argparse
import hashlib
import json
import re
import statistics
import zipfile
from collections.abc import Mapping
from pathlib import Path


DRUG_LINE = re.compile(
    r"(?i)(\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|đơn vị|units?)\b|"
    r"\b(?:po|iv|im|sc|bid|tid|qid|qhs|prn|qam|q\d+h|xl)\b|thuốc)"
)
LAB_LINE = re.compile(
    r"(?i)(xét nghiệm|huyết học|sinh hóa|công thức máu|creatinin|glucose|"
    r"hemoglobin|bạch cầu|tiểu cầu|natri|kali|ast|alt|bilirubin|albumin|inr|"
    r"crp|procalcitonin)"
)
CUES = {
    "negation": re.compile(r"(?i)\b(không|chưa|phủ nhận|âm tính)\b"),
    "family": re.compile(r"(?i)\b(gia đình|mẹ|bố|cha|vợ|chồng|anh|chị|em)\b"),
    "history": re.compile(
        r"(?i)\b(tiền sử|trước đây|trước khi|đã từng|mạn tính|phẫu thuật)\b"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_zip_documents(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        entries = [entry for entry in archive.infolist() if entry.filename.endswith(".txt")]
        entries.sort(key=lambda entry: int(Path(entry.filename).stem))
        return {
            entry.filename: archive.read(entry).decode("utf-8", errors="strict")
            for entry in entries
        }


def _summary(values: list[int]) -> dict[str, float | int]:
    return {
        "min": min(values),
        "median": statistics.median(values),
        "mean": round(statistics.fmean(values), 2),
        "max": max(values),
        "sum": sum(values),
        "documents_nonzero": sum(value > 0 for value in values),
    }


def audit_documents(documents: Mapping[str, str]) -> dict[str, object]:
    rows = []
    for name, text in documents.items():
        lines = text.splitlines()
        rows.append(
            {
                "name": name,
                "characters": len(text),
                "lines": len(lines),
                "drug_like_lines": sum(bool(DRUG_LINE.search(line)) for line in lines),
                "lab_like_lines": sum(bool(LAB_LINE.search(line)) for line in lines),
                **{
                    f"{cue}_cues": len(pattern.findall(text))
                    for cue, pattern in CUES.items()
                },
            }
        )
    keys = {
        "character_count": "characters",
        "line_count": "lines",
        "drug_like_line_count": "drug_like_lines",
        "lab_like_line_count": "lab_like_lines",
        "negation_cue_count": "negation_cues",
        "family_cue_count": "family_cues",
        "history_cue_count": "history_cues",
    }
    return {
        "document_count": len(rows),
        **{output: _summary([row[source] for row in rows]) for output, source in keys.items()},
        "documents": rows,
    }


def audit_sources(zip_path: Path, html_path: Path) -> dict[str, object]:
    documents = read_zip_documents(zip_path)
    ids = [int(Path(name).stem) for name in documents]
    if ids != list(range(1, 101)):
        raise ValueError("ZIP must contain input/1.txt through input/100.txt exactly")
    return {
        "artifacts": {
            str(zip_path): {"sha256": sha256(zip_path)},
            str(html_path): {"sha256": sha256(html_path)},
        },
        "dataset": audit_documents(documents),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=Path("input.zip"))
    parser.add_argument(
        "--html",
        type=Path,
        default=Path("AI Race 2026 - Cuộc đua AI cho kỹ sư Việt Nam.html"),
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/source_audit.json"))
    args = parser.parse_args()
    report = audit_sources(args.zip, args.html)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run focused tests and generate the real audit**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_audit_sources -v
.\.venv\Scripts\python.exe tools\audit_sources.py
```

Expected: three tests pass and `outputs/source_audit.json` reports 100 documents.

- [ ] **Step 6: Commit the audit foundation**

```powershell
git add pyproject.toml .gitignore tools/audit_sources.py tests/test_audit_sources.py
git commit -m "feat: add reproducible source audit"
```

### Task 2: Official offset fixture and shared validator

**Files:**

- Create: `src/medical_race/__init__.py`
- Create: `src/medical_race/offsets.py`
- Create: `tests/fixtures/official_example.json`
- Create: `tests/test_offsets.py`

**Interfaces:**

- Consumes: `raw_text: str` and an entity mapping with `text` and `position`.
- Produces: `validate_entity_offset(raw_text: str, entity: Mapping[str, object]) -> None`.
- Raises: `ValueError` for malformed or nonmatching spans.

- [ ] **Step 1: Write the official fixture**

Create `tests/fixtures/official_example.json` with one JSON object containing `raw_text` and the exact 19 output objects copied from the saved official HTML.
Encode every line boundary in `raw_text` as `\r\n ` so JSON parsing reconstructs the 554-character source used by the official offsets.
Do not normalize accents, spaces, case, or punctuation.

- [ ] **Step 2: Write failing offset tests**

Create `tests/test_offsets.py`:

```python
import json
import unittest
from collections import Counter
from pathlib import Path

from medical_race.offsets import validate_entity_offset


FIXTURE = Path("tests/fixtures/official_example.json")


class OffsetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_all_official_offsets_are_end_exclusive(self):
        for entity in self.example["entities"]:
            validate_entity_offset(self.example["raw_text"], entity)

    def test_repeated_mentions_are_preserved(self):
        counts = Counter(entity["text"] for entity in self.example["entities"])
        self.assertEqual(counts["táo bón"], 2)
        self.assertEqual(counts["lo âu"], 2)

    def test_observed_schema_is_type_dependent(self):
        drug = next(e for e in self.example["entities"] if e["type"] == "THUỐC")
        symptom = next(
            e for e in self.example["entities"] if e["type"] == "TRIỆU_CHỨNG"
        )
        self.assertIn("candidates", drug)
        self.assertNotIn("candidates", symptom)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests and verify the expected failure**

Run:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m unittest tests.test_offsets -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'medical_race.offsets'`.

- [ ] **Step 4: Implement the validator**

Create `src/medical_race/offsets.py`:

```python
from collections.abc import Mapping


def validate_entity_offset(raw_text: str, entity: Mapping[str, object]) -> None:
    position = entity.get("position")
    text = entity.get("text")
    if (
        not isinstance(position, list)
        or len(position) != 2
        or not all(isinstance(value, int) for value in position)
        or not isinstance(text, str)
    ):
        raise ValueError("entity requires text and a two-integer position")
    start, end = position
    if start < 0 or end < start or end > len(raw_text):
        raise ValueError(f"invalid position: {position}")
    if raw_text[start:end] != text:
        raise ValueError(
            f"offset mismatch at {position}: {raw_text[start:end]!r} != {text!r}"
        )
```

- [ ] **Step 5: Run focused and full tests**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected: all tests pass and all 19 official entities validate.

- [ ] **Step 6: Commit offset evidence**

```powershell
git add src/medical_race tests/fixtures/official_example.json tests/test_offsets.py
git commit -m "test: verify official end-exclusive offsets"
```

### Task 3: Research ledger, assumptions, and annotation policy

**Files:**

- Create: `research/notes.md`
- Create: `research/sources.jsonl`
- Create: `docs/assumptions.md`
- Create: `docs/annotation_policy.md`

**Interfaces:**

- Consumes: verified local audit evidence and primary or official web sources.
- Produces: human-readable claims and one JSONL provenance record per cited source.

- [ ] **Step 1: Write the research ledger from collected primary sources**

For every finding in `research/notes.md`, use this exact field sequence:

```markdown
### Finding title

- Status: Verified fact | Evidence-backed inference | Unknown.
- Source: [Descriptive title](URL).
- Accessed: 2026-07-11.
- Evidence: A concise paraphrase of what the source directly supports.
- Confidence: High | Medium | Low.
- Uncertainty: What the source does not establish for this competition.
- Strategic impact: The concrete baseline or experiment decision affected.
```

Cover Vietnamese and multilingual clinical NER, ICD-10 linking, RxNorm normalization, BioSyn, SapBERT, newer biomedical linkers, NegEx, ConText, section-aware extraction, and Jaccard candidate-set calibration.
Use the official WHO, NLM, Ministry of Health when available, PubMed or PMC original papers, and ACL Anthology papers as primary evidence.

- [ ] **Step 2: Add machine-readable source records**

Write one line per source in `research/sources.jsonl` with this schema:

```json
{"url":"https://example.org/source","accessed":"2026-07-11","kind":"official|primary-paper","claims":["stable claim identifier"],"confidence":"high|medium|low","uncertainty":"competition-specific limitation"}
```

Validate it:

```powershell
.\.venv\Scripts\python.exe -c "import json, pathlib; [json.loads(line) for line in pathlib.Path('research/sources.jsonl').read_text(encoding='utf-8').splitlines()]"
```

Expected: exit code 0.

- [ ] **Step 3: Write the assumption register**

For each entry in `docs/assumptions.md`, record the assumption, current evidence, confidence, risk if wrong, default behavior, and a specific falsification method.
Include at least the exact ICD edition, RxNorm snapshot, target RxNorm term type, complete schema for three unobserved entity types, mention matching, whether position affects scoring, historical priors, family experiencer rules, and multi-code ground truth frequency.

- [ ] **Step 4: Write the annotation policy**

Separate `Verified rules` from `Provisional rules` in `docs/annotation_policy.md`.
Verified rules must include exact raw text, end-exclusive offsets, mention-level preservation, observed drug regimen spans, observed type-dependent fields, and no unapproved fields.
Provisional rules must include section priors, clause-bounded negation, family reporter versus experiencer, and diagnosis-versus-symptom context.

- [ ] **Step 5: Check traceability and forbidden certainty**

Run:

```powershell
rg -n "TBD|TODO|obviously|certainly|must be ICD-10-CM|must be SCD" research docs
rg -n "Accessed:|Confidence:|Strategic impact:" research/notes.md
```

Expected: the first command has no unsupported certainty or placeholders and the second shows all three fields for every finding.

- [ ] **Step 6: Commit the evidence documents**

```powershell
git add research/notes.md research/sources.jsonl docs/assumptions.md docs/annotation_policy.md
git commit -m "docs: record clinical NLP research evidence"
```

### Task 4: Repository structure, baseline checkpoints, and report

**Files:**

- Create: `README.md`
- Create: `docs/baseline_plan.md`
- Create: `data/`, `data/raw/`, `data/external/`, `data/synthetic/`, `data/processed/`
- Create: `ontologies/icd/`, `ontologies/rxnorm/`
- Create: `configs/`, `outputs/`

**Interfaces:**

- Consumes: `outputs/source_audit.json`, research notes, assumptions, and annotation policy.
- Produces: reproducible commands, final verified findings, critical unknowns, architecture, baseline checkpoints, and leaderboard experiments.

- [ ] **Step 1: Create only the approved directories**

Run:

```powershell
New-Item -ItemType Directory -Force configs,data/raw,data/external,data/synthetic,data/processed,ontologies/icd,ontologies/rxnorm,research,src/medical_race,tests,outputs | Out-Null
```

Do not create `.gitkeep` files or copy `input.zip`.

- [ ] **Step 2: Write the baseline checkpoint plan**

Create `docs/baseline_plan.md` with these ordered checkpoints:

1. Freeze source hashes, schema observations, and offset fixtures.
2. Implement the offset-safe loader and raw-to-normalized index mapping.
3. Implement the section parser and line-role rules from observed headers.
4. Implement drug-regimen extraction and laboratory name/result extraction.
5. Implement conservative assertion rules with clause and section scope.
6. Load only approved ICD and RxNorm snapshots and build lexical candidate retrieval.
7. Implement the type-dependent serializer and output validator.
8. Implement the provisional local evaluator with assumptions isolated in configuration.
9. Generate all 100 JSON files and `output.zip` in one command.
10. Run focused tests, the full suite, raw-offset validation, JSON validation, and sample generation.

For every checkpoint, specify its inputs, outputs, acceptance command, expected evidence, and stop condition.
Checkpoint 6 must remain blocked until the ontology files and target versions are verified.
Checkpoint 8 must label the mention-matching algorithm provisional until official clarification or controlled leaderboard evidence exists.

- [ ] **Step 3: Record high-information leaderboard experiments**

Add a final section to `docs/baseline_plan.md` that orders experiments by information gain:

1. Candidate cardinality sweep with the entity spans and assertions frozen.
2. RxNorm term-type ablation across IN, SCDC, SCD, BN, and SBD only after the official snapshot is known.
3. ICD namespace/version probe using unambiguous codes shared or separated across WHO ICD-10 and the Vietnamese catalog.
4. Assertion ablation by negation, historical, and family flags with spans frozen.
5. Section-prior ablation for history-of-present-illness versus past-history sections.
6. Type precision threshold sweep with candidate and assertion outputs frozen.

Each experiment must alter one factor, retain its config and commit, record submission time and score, and state the competing hypotheses before submission.

- [ ] **Step 4: Write the repository README and final report section**

Document these reproducible commands in `README.md`:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools\audit_sources.py
```

State the two artifact SHA-256 values, the canonical raw artifact policy, the current verified statistics, the unresolved ontology/schema questions, and the no-large-model gate.
Link to the research notes, assumptions, annotation policy, design spec, and baseline plan.

- [ ] **Step 5: Run final verification**

Run:

```powershell
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools\audit_sources.py
.\.venv\Scripts\python.exe -c "import json, pathlib; json.loads(pathlib.Path('outputs/source_audit.json').read_text(encoding='utf-8')); [json.loads(line) for line in pathlib.Path('research/sources.jsonl').read_text(encoding='utf-8').splitlines()]"
git diff --check
git status --short
```

Expected: all tests pass, both JSON formats parse, `git diff --check` is clean, and no canonical artifact has changed hash.

- [ ] **Step 6: Commit the milestone report**

```powershell
git add README.md docs/baseline_plan.md
git commit -m "docs: publish verified baseline plan"
```

## Plan self-review

- Every design deliverable maps to one of Tasks 1 through 4.
- Runtime source code is limited to the audit and shared offset invariant.
- The plan adds no model or ontology dependency.
- Function names and paths are consistent across tests, implementation, and commands.
- Competition-specific unknowns remain explicit and block only the checkpoints they materially affect.
