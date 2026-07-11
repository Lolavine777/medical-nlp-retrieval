# Conservative Assertion Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Classify exact raw spans with conservative Vietnamese negation, temporality, and experiencer rules and map only verified states to organizer-known assertion labels.

**Architecture:** A standard-library assertion module validates the shared `Span`, isolates its physical clause, applies local cues before conservative section priors, and returns an immutable internal state. A separate audit command measures deterministic rule output across the pinned corpus without claiming evaluator accuracy.

**Tech Stack:** Python 3.12 standard library, `dataclasses`, `re`, `unittest`, existing section parser and exact-span validator.

## Global Constraints

- Never mutate raw text or entity offsets.
- Reject any span that does not satisfy `raw_text[start:end] == text`.
- Emit only `isNegated`, `isHistorical`, and `isFamily` from the assertion component.
- Keep current-illness sections non-historical unless a local cue says otherwise.
- Treat family reporter and family experiencer as different cases.
- Keep model parameters at `0 / 9B` for this rule checkpoint.
- Add no external dependency, ontology code, output field, or public-test-specific rule.

---

### Task 1: Assertion state and exact-span boundary

**Files:**
- Create: `src/medical_race/assertions/__init__.py`
- Create: `tests/test_assertions.py`

**Interfaces:**
- Consumes: `medical_race.extraction.Span` and `medical_race.offsets.validate_entity_offset`.
- Produces: `AssertionState`, `classify_assertions(raw_text: str, span: Span) -> AssertionState`, and `AssertionState.labels() -> tuple[str, ...]`.

- [ ] **Step 1: Write the failing state and validation tests**

```python
import unittest

from medical_race.assertions import AssertionState, classify_assertions
from medical_race.extraction import Span


class AssertionStateTest(unittest.TestCase):
    def test_default_state_maps_to_no_organizer_labels(self):
        raw = "Bệnh nhân đau ngực"
        start = raw.index("đau ngực")
        state = classify_assertions(raw, Span("đau ngực", start, start + len("đau ngực")))
        self.assertEqual(state, AssertionState(False, "current", "patient"))
        self.assertEqual(state.labels(), ())

    def test_labels_have_stable_known_order(self):
        state = AssertionState(True, "historical", "family")
        self.assertEqual(state.labels(), ("isNegated", "isFamily", "isHistorical"))

    def test_rejects_empty_or_mismatched_span(self):
        with self.assertRaises(ValueError):
            classify_assertions("đau ngực", Span("", 0, 0))
        with self.assertRaisesRegex(ValueError, "offset mismatch"):
            classify_assertions("đau ngực", Span("đau", 1, 5))
```

- [ ] **Step 2: Run the test to verify RED**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_assertions -v`

Expected: ERROR with `ModuleNotFoundError: No module named 'medical_race.assertions'`.

- [ ] **Step 3: Implement the immutable state and validation boundary**

```python
from dataclasses import dataclass

from medical_race.extraction import Span
from medical_race.offsets import validate_entity_offset


@dataclass(frozen=True, slots=True)
class AssertionState:
    negated: bool
    temporality: str
    experiencer: str

    def labels(self) -> tuple[str, ...]:
        labels = []
        if self.negated:
            labels.append("isNegated")
        if self.experiencer == "family":
            labels.append("isFamily")
        if self.temporality == "historical":
            labels.append("isHistorical")
        return tuple(labels)


def classify_assertions(raw_text: str, span: Span) -> AssertionState:
    if not span.text:
        raise ValueError("assertion span must be non-empty")
    validate_entity_offset(
        raw_text,
        {"text": span.text, "position": [span.start, span.end]},
    )
    return AssertionState(False, "current", "patient")
```

- [ ] **Step 4: Run the focused and full tests**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_assertions -v`

Expected: 3 tests pass.

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: Existing 30 tests plus the new assertion tests pass.

- [ ] **Step 5: Commit the validation boundary**

```powershell
git add src/medical_race/assertions/__init__.py tests/test_assertions.py
git commit -m "feat: add assertion state boundary"
```

### Task 2: Clause-scoped assertion rules

**Files:**
- Modify: `src/medical_race/assertions/__init__.py`
- Modify: `tests/test_assertions.py`

**Interfaces:**
- Consumes: the Task 1 `AssertionState` and exact validated `Span`.
- Produces: deterministic `negated`, `temporality`, and `experiencer` values using clause-local cues and `parse_sections(raw_text)`.

- [ ] **Step 1: Add failing rule tests**

```python
def span_for(raw: str, text: str) -> Span:
    start = raw.index(text)
    return Span(text, start, start + len(text))


class AssertionRuleTest(unittest.TestCase):
    def test_negation_stops_at_contrast_terminator(self):
        raw = "không đau ngực nhưng sốt"
        self.assertTrue(classify_assertions(raw, span_for(raw, "đau ngực")).negated)
        self.assertFalse(classify_assertions(raw, span_for(raw, "sốt")).negated)

    def test_post_mention_negative_result_is_negated(self):
        raw = "xét nghiệm viêm gan âm tính"
        self.assertTrue(classify_assertions(raw, span_for(raw, "viêm gan")).negated)

    def test_section_priors_distinguish_past_from_current_illness(self):
        past = "Tiền sử bệnh\n- tăng huyết áp"
        current = "Bệnh sử hiện tại\n- đau ngực"
        self.assertEqual(
            classify_assertions(past, span_for(past, "tăng huyết áp")).temporality,
            "historical",
        )
        self.assertEqual(
            classify_assertions(current, span_for(current, "đau ngực")).temporality,
            "current",
        )

    def test_local_temporality_overrides_section_default(self):
        historical = "Đánh giá tại bệnh viện\nBệnh nhân đã từng đột quỵ"
        hypothetical = "Tiền sử bệnh\nNếu xuất hiện sốt sẽ tái khám"
        self.assertEqual(
            classify_assertions(historical, span_for(historical, "đột quỵ")).temporality,
            "historical",
        )
        self.assertEqual(
            classify_assertions(hypothetical, span_for(hypothetical, "sốt")).temporality,
            "hypothetical",
        )

    def test_family_experiencer_differs_from_family_reporter(self):
        family = "Mẹ của bệnh nhân bị ung thư phổi"
        reporter = "Gia đình nhận thấy bệnh nhân đau ngực"
        self.assertEqual(
            classify_assertions(family, span_for(family, "ung thư phổi")).experiencer,
            "family",
        )
        self.assertEqual(
            classify_assertions(reporter, span_for(reporter, "đau ngực")).experiencer,
            "patient",
        )
```

- [ ] **Step 2: Run the focused tests to verify RED**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_assertions.AssertionRuleTest -v`

Expected: FAIL because the Task 1 implementation always returns the default state.

- [ ] **Step 3: Implement the smallest clause and cue engine**

Add compiled cue patterns for:

```python
BOUNDARY = re.compile(r"(?i)[.;!?]|\b(?:nhưng|tuy nhiên)\b")
NEGATION_BEFORE = re.compile(r"(?i)\b(?:không|chưa|phủ nhận|không có|không ghi nhận)\b")
NEGATION_AFTER = re.compile(r"(?i)\b(?:âm tính)\b")
HISTORICAL = re.compile(r"(?i)\b(?:tiền sử|trước đây|đã từng|trước khi|cách đây|mạn tính|mãn tính|đã ngừng|đã hết)\b")
HYPOTHETICAL = re.compile(r"(?i)\b(?:nếu|sẽ|dự kiến|kế hoạch|nguy cơ)\b")
RELATIVE = re.compile(r"(?i)\b(?:mẹ|bố|cha|vợ|chồng|anh|chị|em|gia đình)\b")
FAMILY_REPORTER = re.compile(r"(?i)\b(?:gia đình|mẹ|bố|cha|vợ|chồng|anh|chị|em)\b.*\b(?:nhận thấy|cho biết|báo cáo)\b.*\bbệnh nhân\b")
```

Implement `_clause(raw_text, span)` by taking the physical line containing the span and selecting the text between the nearest `BOUNDARY` matches on each side.
Return the clause plus entity-relative start and end indices so cue direction remains explicit.

In `classify_assertions`:

```python
clause, relative_start, relative_end = _clause(raw_text, span)
before = clause[:relative_start]
after = clause[relative_end:]
negated = bool(NEGATION_BEFORE.search(before) or NEGATION_AFTER.search(after))

if HYPOTHETICAL.search(clause):
    temporality = "hypothetical"
elif HISTORICAL.search(clause) or _section_kind(raw_text, span.start) in {
    "past_history",
    "medications",
}:
    temporality = "historical"
else:
    temporality = "current"

if FAMILY_REPORTER.search(before):
    experiencer = "patient"
elif RELATIVE.search(before):
    experiencer = "family"
else:
    experiencer = "patient"

return AssertionState(negated, temporality, experiencer)
```

Implement `_section_kind` by returning the kind of the parsed section satisfying `section.start <= position < section.end`.

- [ ] **Step 4: Run focused and full verification**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_assertions -v`

Expected: 8 tests pass.

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: All tests pass with no failures or errors.

- [ ] **Step 5: Commit the rule engine**

```powershell
git add src/medical_race/assertions/__init__.py tests/test_assertions.py
git commit -m "feat: add clause-scoped assertion rules"
```

### Task 3: Corpus audit and checkpoint evidence

**Files:**
- Create: `tools/audit_assertions.py`
- Create: `tests/test_audit_assertions.py`
- Create: `docs/assertion_checkpoint_2026-07-11.md`

**Interfaces:**
- Consumes: `read_zip_documents`, `extract_drugs`, `extract_labs`, and `classify_assertions`.
- Produces: `audit_assertions(documents: Mapping[str, str]) -> dict[str, object]` and a deterministic JSON report.

- [ ] **Step 1: Write a failing audit test**

```python
import unittest

from tools.audit_assertions import audit_assertions


class AssertionAuditTest(unittest.TestCase):
    def test_counts_spans_and_labels_without_changing_offsets(self):
        documents = {
            "input/1.txt": "Thuốc trước khi nhập viện: aspirin 81mg po daily\n",
            "input/2.txt": "Kết quả xét nghiệm: kali là 2.4 mmol/L\n",
        }
        report = audit_assertions(documents)
        self.assertEqual(report["document_count"], 2)
        self.assertEqual(report["span_count"], 3)
        self.assertEqual(report["label_counts"], {"isHistorical": 1})
        self.assertEqual(report["offset_errors"], 0)
```

- [ ] **Step 2: Run the test to verify RED**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_audit_assertions -v`

Expected: ERROR with `ModuleNotFoundError: No module named 'tools.audit_assertions'`.

- [ ] **Step 3: Implement the deterministic audit**

For each document, classify every drug span and both the name and value spans from each laboratory pair.
Validate offsets through `classify_assertions`, count labels with `Counter`, and return sorted label counts with `offset_errors` fixed at zero after successful validation.

Add an `argparse` entry point with defaults `--zip input.zip` and `--output outputs/assertion_audit.json`.
Write UTF-8 JSON with `ensure_ascii=False`, `indent=2`, and one trailing newline.

- [ ] **Step 4: Run the audit test and pinned corpus audit**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_audit_assertions -v`

Expected: 1 test passes.

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe tools\audit_assertions.py --zip input.zip --output outputs\assertion_audit.json`

Expected: Exit 0 and a report for exactly 100 documents with zero offset errors.

- [ ] **Step 5: Record verified results and limitations**

Create `docs/assertion_checkpoint_2026-07-11.md` with the pinned input SHA-256, exact corpus counts from `outputs/assertion_audit.json`, access date, confidence, evidence, strategic impact, and these limitations:

- Assertion counts are deterministic rule outputs, not ground-truth accuracy.
- Hypothetical and other-experiencer states have no verified organizer output label.
- Cue lists and section priors remain frozen-span leaderboard variables.
- No model or ontology code was added, so the parameter budget remains `0 / 9B`.

- [ ] **Step 6: Run final verification**

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: All tests pass.

Run: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m compileall -q src tools tests`

Expected: Exit 0.

Run: `git diff --check`

Expected: Exit 0.

- [ ] **Step 7: Commit the audit checkpoint**

```powershell
git add tools/audit_assertions.py tests/test_audit_assertions.py docs/assertion_checkpoint_2026-07-11.md
git commit -m "test: audit assertion rules across corpus"
```
