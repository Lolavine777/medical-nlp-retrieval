# High-Precision Symptom Submission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add conservative exact-offset symptom extraction to the stable Submission 2 pipeline and produce one controlled, validated, deterministic upload artifact.

**Architecture:** A structural extractor reads existing section boundaries, accepts only inline chief complaints and short bullets inside explicit current-symptom blocks, and returns existing `Span` values. The pipeline attaches existing assertion labels, serializes the approved symptom schema, and gates the behavior behind a backward-compatible optional configuration field.

**Tech Stack:** Python standard library, `unittest`, existing section parser, assertion classifier, strict output validator, deterministic ZIP builder, and semantic diff tool.

## Global Constraints

- Work inline on `master` as already authorized.
- Preserve raw UTF-8 text, whitespace, line endings, and duplicate mentions.
- Require `raw_text[start:end] == text` for every symptom.
- Do not derive a symptom lexicon from public test phrases.
- Do not add dependencies, models, external runtime calls, ontology identifiers, candidate values, or output fields.
- Keep the five historical configuration files and their hashes unchanged.
- Keep every Submission 2 drug, laboratory entity, assertion, span, and candidate unchanged.
- Keep active model parameters at `0 / 9B`.
- Use Submission 2 as the experiment parent and change only symptom inclusion.
- Follow RED, GREEN, and full verification before artifact handoff.

---

### Task 1: Structural symptom extractor

**Files:**

- Create: `src/medical_race/extraction/symptoms.py`
- Create: `tests/test_symptom_extraction.py`

**Interfaces:**

- Consumes: `raw_text: str` and `parse_sections(raw_text)`.
- Produces: `extract_symptoms(raw_text: str) -> tuple[Span, ...]`.
- Returns only exact contiguous raw spans and preserves repeated mentions at different offsets.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_symptom_extraction.py`:

```python
import unittest

from medical_race.extraction.symptoms import extract_symptoms


RAW = (
    "Lý do nhập viện: đau ngực\n"
    "Thời điểm khởi phát triệu chứng: hôm qua\n"
    "Các triệu chứng hiện tại\n"
    "- Không chóng mặt\n"
    "- **khó thở khi gắng sức:**\n"
    "- Bệnh nhân có đau bụng vùng thượng vị\n"
    "- Được chụp x-quang ngực\n"
    "Đặc điểm triệu chứng\n"
    "- Vị trí: ngực\n"
    "Các sự kiện trước khi nhập viện\n"
    "- Nhập viện khoa Nội\n"
)


class SymptomExtractionTest(unittest.TestCase):
    def test_extracts_only_chief_complaint_and_active_short_bullets(self):
        spans = extract_symptoms(RAW)
        self.assertEqual(
            [span.text for span in spans],
            ["đau ngực", "chóng mặt", "khó thở khi gắng sức", "đau bụng vùng thượng vị"],
        )
        self.assertTrue(all(RAW[span.start : span.end] == span.text for span in spans))

    def test_rejects_actions_and_stops_at_characteristics(self):
        texts = [span.text for span in extract_symptoms(RAW)]
        self.assertNotIn("Được chụp x-quang ngực", texts)
        self.assertNotIn("Vị trí: ngực", texts)
        self.assertNotIn("Nhập viện khoa Nội", texts)

    def test_preserves_duplicate_mentions_at_distinct_offsets(self):
        raw = "Triệu chứng hiện tại\n- ho\n- ho\nCác sự kiện trước khi nhập viện\n- về nhà"
        spans = extract_symptoms(raw)
        self.assertEqual([span.text for span in spans], ["ho", "ho"])
        self.assertNotEqual(spans[0].start, spans[1].start)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe -m unittest tests.test_symptom_extraction -v
```

Expected: FAIL with `ModuleNotFoundError` for `medical_race.extraction.symptoms`.

- [ ] **Step 3: Implement the minimum extractor**

Create `src/medical_race/extraction/symptoms.py`:

```python
import re

from medical_race.extraction import Span
from medical_race.sections import parse_sections


INDENT = re.compile(r"\s*")
MARKER = re.compile(r"\s*(?:[-*]|\d+[.)])\s*")
CURRENT_HEADINGS = {
    "triệu chứng hiện tại",
    "các triệu chứng hiện tại",
    "triệu chứng chính",
}
STOP_PREFIXES = (
    "đặc điểm triệu chứng",
    "các sự kiện trước khi nhập viện",
    "thời điểm khởi phát",
    "diễn biến",
    "đánh giá",
    "khám",
    "xét nghiệm",
    "chẩn đoán",
    "điều trị",
)
REJECT_PREFIXES = (
    "vị trí",
    "mức độ nghiêm trọng",
    "thời gian",
    "tần suất",
    "chiếu xạ",
    "các yếu tố",
    "có triệu chứng",
    "được ",
    "đã ",
    "sau đó",
    "nhập viện",
    "chuyển viện",
    "bắt đầu",
    "ngừng",
    "dùng ",
    "chụp ",
    "xét nghiệm",
    "ecg ",
    "tỉnh dậy",
)
LEADING_CUE = re.compile(
    r"(?i)(?:(?:không|chưa|không còn)\s+|"
    r"bệnh nhân\s+(?:có|bị|cảm thấy)\s+|"
    r"(?:cảm thấy|cảm giác)\s+)"
)
PARENTHETICAL = re.compile(r"\s*\([^()]*\)\s*$")


def extract_symptoms(raw_text: str) -> tuple[Span, ...]:
    output = []
    for section in parse_sections(raw_text):
        if section.kind not in {"symptoms", "admission_reason"}:
            continue
        active = section.kind == "symptoms"
        first_content = True
        position = section.content_start
        content = raw_text[section.content_start : section.end]
        for full_line in content.splitlines(keepends=True):
            line_end = position + len(full_line.rstrip("\r\n"))
            line = raw_text[position:line_end]
            stripped = line.strip()
            folded = stripped.casefold().strip(" :*")
            if folded in CURRENT_HEADINGS:
                active = True
                first_content = False
                position += len(full_line)
                continue
            if folded.startswith(STOP_PREFIXES):
                active = False
                first_content = False
                position += len(full_line)
                continue
            marker = MARKER.match(line)
            eligible = active and marker is not None
            if section.kind == "admission_reason" and first_content and stripped and marker is None:
                eligible = True
            if eligible:
                span = _candidate_span(raw_text, position, line_end)
                if span is not None:
                    output.append(span)
            if stripped:
                first_content = False
            position += len(full_line)
    return tuple(output)


def _candidate_span(raw_text: str, line_start: int, line_end: int) -> Span | None:
    line = raw_text[line_start:line_end]
    marker = MARKER.match(line)
    start = line_start + (marker.end() if marker else INDENT.match(line).end())
    end = line_end
    while start < end and raw_text.startswith("**", start):
        start += 2
    while end > start and raw_text[end - 1].isspace():
        end -= 1
    if end - start >= 2 and raw_text[end - 2 : end] == "**":
        end -= 2
    cue = LEADING_CUE.match(raw_text[start:end])
    if cue:
        start += cue.end()
    parenthetical = PARENTHETICAL.search(raw_text[start:end])
    if parenthetical:
        end = start + parenthetical.start()
    while end > start and raw_text[end - 1] in " \t:;,.!*":
        end -= 1
    text = raw_text[start:end]
    folded = text.casefold()
    if not text or len(text.split()) > 8 or ":" in text:
        return None
    if folded in {"n/a", "na", "không có triệu chứng"} or folded.startswith(REJECT_PREFIXES):
        return None
    return Span(text, start, end)
```

Do not add a document identifier or a public-test-specific phrase to any rule.
Fix shared structural patterns only through a failing regression test.

- [ ] **Step 4: Run GREEN and neighboring tests**

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe -m unittest tests.test_symptom_extraction tests.test_extraction tests.test_section_regressions -v
```

Expected: every listed test PASS with no warnings or errors.

- [ ] **Step 5: Commit**

```powershell
git add -- src/medical_race/extraction/symptoms.py tests/test_symptom_extraction.py
git diff --cached --check
git commit -m "feat: extract structured symptom spans"
```

---

### Task 2: Backward-compatible pipeline integration

**Files:**

- Modify: `src/medical_race/pipeline.py`
- Modify: `tests/test_pipeline.py`
- Create: `configs/submissions/06_add_symptoms.json`

**Interfaces:**

- Consumes: `extract_symptoms(raw_text) -> tuple[Span, ...]`.
- Produces: `SubmissionConfig.include_symptoms: bool = False`.
- Loads historical configs with the absent field defaulting to `False`.
- Emits symptom dictionaries with exactly `text`, `type`, `assertions`, and `position`.

- [ ] **Step 1: Add failing integration tests**

Add to `tests/test_pipeline.py`:

```python
    def test_symptom_toggle_adds_only_valid_symptom_entities(self):
        raw = "Lý do nhập viện: đau ngực\nCác triệu chứng hiện tại\n- Không chóng mặt"
        without = predict_document(raw, TERMS, config())
        enabled = predict_document(raw, TERMS, config(include_symptoms=True))
        self.assertEqual([e for e in enabled if e["type"] != "TRIỆU_CHỨNG"], without)
        self.assertEqual(
            [e for e in enabled if e["type"] == "TRIỆU_CHỨNG"],
            [
                {
                    "text": "đau ngực",
                    "type": "TRIỆU_CHỨNG",
                    "assertions": [],
                    "position": [raw.index("đau ngực"), raw.index("đau ngực") + len("đau ngực")],
                },
                {
                    "text": "chóng mặt",
                    "type": "TRIỆU_CHỨNG",
                    "assertions": ["isNegated"],
                    "position": [raw.index("chóng mặt"), raw.index("chóng mặt") + len("chóng mặt")],
                },
            ],
        )
        validate_entities(raw, enabled)

    def test_legacy_config_defaults_symptoms_off_and_rejects_bad_optional_field(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            values = {
                "include_labs": True,
                "span_policy": "regimen",
                "concept_level": "all_retrievable",
                "candidate_output": "top1",
            }
            path.write_text(json.dumps(values), encoding="utf-8")
            self.assertFalse(load_submission_config(path).include_symptoms)
            values["include_symptoms"] = "yes"
            path.write_text(json.dumps(values), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "include_symptoms"):
                load_submission_config(path)
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe -m unittest tests.test_pipeline -v
```

Expected: FAIL because the dataclass has no `include_symptoms` field and the pipeline emits no symptoms.

- [ ] **Step 3: Implement the compatibility boundary**

Replace the single exact field set in `src/medical_race/pipeline.py` with:

```python
REQUIRED_CONFIG_FIELDS = {"include_labs", "span_policy", "concept_level", "candidate_output"}
OPTIONAL_CONFIG_FIELDS = {"include_symptoms"}
```

Add `include_symptoms: bool = False` as the last dataclass field and validate it with:

```python
        if type(self.include_symptoms) is not bool:
            raise ValueError("include_symptoms must be boolean")
```

Replace `load_submission_config` with:

```python
def load_submission_config(path: Path) -> SubmissionConfig:
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(values, dict):
        raise ValueError("config must be an object")
    fields = set(values)
    allowed = REQUIRED_CONFIG_FIELDS | OPTIONAL_CONFIG_FIELDS
    if not REQUIRED_CONFIG_FIELDS <= fields or fields - allowed:
        raise ValueError(
            f"config fields must contain {sorted(REQUIRED_CONFIG_FIELDS)} "
            f"and only use {sorted(allowed)}"
        )
    values.setdefault("include_symptoms", False)
    return SubmissionConfig(**values)
```

Import `extract_symptoms` and append this branch before sorting and validation:

```python
    if config.include_symptoms:
        for span in extract_symptoms(raw_text):
            entities.append(
                {
                    "text": span.text,
                    "type": "TRIỆU_CHỨNG",
                    "assertions": list(classify_assertions(raw_text, span).labels()),
                    "position": [span.start, span.end],
                }
            )
```

Do not modify any historical config.

- [ ] **Step 4: Add the new config**

Create `configs/submissions/06_add_symptoms.json`:

```json
{
  "include_labs": true,
  "span_policy": "regimen",
  "concept_level": "all_retrievable",
  "candidate_output": "top1",
  "include_symptoms": true
}
```

- [ ] **Step 5: Run GREEN and compatibility checks**

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe -m unittest tests.test_pipeline tests.test_build_submission tests.test_submission_diff -v
git diff --name-only -- configs/submissions/01_drugs_top1.json configs/submissions/02_add_labs.json configs/submissions/03_core_spans.json configs/submissions/04_ingredient_only.json configs/submissions/05_top2.json
```

Expected: all tests PASS and the historical-config diff command prints nothing.

- [ ] **Step 6: Commit**

```powershell
git add -- src/medical_race/pipeline.py tests/test_pipeline.py configs/submissions/06_add_symptoms.json
git diff --cached --check
git commit -m "feat: add symptom submission variant"
```

---

### Task 3: Audit, build, verify, and hand off the artifact

**Files:**

- Generate ignored: `outputs/submissions/06_add_symptoms.zip`
- Generate ignored: `outputs/submissions/06_add_symptoms.report.json`
- Generate ignored: `outputs/submissions/02_add_labs_to_06_add_symptoms.diff.json`
- Create: `docs/next_submission_queue_2026-07-14.md`

**Interfaces:**

- Consumes canonical `input.zip`, pinned RxNorm, Submission 2, and the new config.
- Produces one deterministic 100-record upload ZIP.
- Produces a diff containing only added symptoms.
- Documents commit, config, checksum, parent, hypothesis, counts, and model budget.

- [ ] **Step 1: Run full pre-build verification**

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src tools tests
git diff --check
```

Expected: every test PASS, compilation exits `0`, and the diff check prints no errors.

- [ ] **Step 2: Build the artifact**

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe tools/build_submission.py --config configs/submissions/06_add_symptoms.json --output outputs/submissions/06_add_symptoms.zip --report outputs/submissions/06_add_symptoms.report.json
```

Expected report invariants: `entry_count == 100`, positive `TRIỆU_CHỨNG` count, `candidate_count == 61`, and `model_parameters == 0`.

- [ ] **Step 3: Diff against Submission 2**

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe tools/diff_submissions.py outputs/submissions/02_add_labs.zip outputs/submissions/06_add_symptoms.zip --output outputs/submissions/02_add_labs_to_06_add_symptoms.diff.json
.\.venv\Scripts\python.exe -c "import json; d=json.load(open('outputs/submissions/02_add_labs_to_06_add_symptoms.diff.json',encoding='utf-8')); assert d['added_entities']>0; assert d['removed_entities']==d['changed_entities']==d['changed_candidates']==d['changed_assertions']==0; assert all(x['child']['type']=='TRIỆU_CHỨNG' for x in d['details']); print(d['added_entities'])"
```

Expected: the assertion command prints the added symptom count and exits `0`.

- [ ] **Step 4: Inspect every symptom**

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "import json,zipfile; z=zipfile.ZipFile('outputs/submissions/06_add_symptoms.zip'); rows=[(n,e['text'],e['assertions'],e['position']) for n in sorted(z.namelist()) for e in json.loads(z.read(n)) if e['type']=='TRIỆU_CHỨNG']; print('symptoms',len(rows)); [print(*r,sep='\t') for r in rows]"
```

Reject generic headings, metadata, procedures, medications, tests, admissions, transfers, clinician actions, corrupted boundaries, and implausibly long spans.
For each real error, add one structural regression test, observe RED, implement one general rule, and rerun GREEN before rebuilding.
Never key a rule to a document number or a unique public-test phrase.

- [ ] **Step 5: Prove deterministic rebuild identity**

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe tools/build_submission.py --config configs/submissions/06_add_symptoms.json --output outputs/submissions/06_add_symptoms.rebuild.zip --report outputs/submissions/06_add_symptoms.rebuild.report.json
.\.venv\Scripts\python.exe -c "import hashlib,pathlib; p=[pathlib.Path('outputs/submissions/06_add_symptoms.zip'),pathlib.Path('outputs/submissions/06_add_symptoms.rebuild.zip')]; h=[hashlib.sha256(x.read_bytes()).hexdigest() for x in p]; assert h[0]==h[1]; print(h[0])"
```

Expected: one identical SHA-256 prints and the command exits `0`.

- [ ] **Step 6: Document the upload handoff**

Create `docs/next_submission_queue_2026-07-14.md` with the artifact and config hashes, implementation commit, parent `local-s002`, parent score `5.00940`, hypothesis, exact counts, semantic diff, input and ontology hashes, and model budget `0 / 9B`.
State that only `06_add_symptoms.zip` is uploadable and list the portal fields the user should return.

- [ ] **Step 7: Final verification and documentation commit**

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src tools tests
git diff --check
git status --short
git add -- docs/next_submission_queue_2026-07-14.md
git diff --cached --check
git commit -m "docs: prepare symptom submission probe"
```

Expected: all tests PASS, compilation exits `0`, the diff check is clean, and only intended tracked files are committed.
After the portal result returns, append `local-s006` to `docs/submissions.csv` with timestamp, implementation commit, config, checksum, parent, hypothesis, diff, changed counts, component scores, conclusion, confidence, generalization class, and promotion decision.
