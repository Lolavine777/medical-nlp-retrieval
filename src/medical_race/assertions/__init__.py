import re
from dataclasses import dataclass

from medical_race.extraction import Span
from medical_race.offsets import validate_entity_offset
from medical_race.sections import parse_sections


BOUNDARY = re.compile(r"(?i)[.;!?]|\b(?:nhưng|tuy nhiên)\b")
NEGATION_BEFORE = re.compile(r"(?i)\b(?:không|chưa|phủ nhận|không có|không ghi nhận)\b")
NEGATION_AFTER = re.compile(r"(?i)\bâm tính\b")
HISTORICAL = re.compile(
    r"(?i)\b(?:tiền sử|trước đây|đã từng|trước khi|cách đây|mạn tính|mãn tính|"
    r"đã ngừng|đã hết)\b"
)
HYPOTHETICAL = re.compile(r"(?i)\b(?:nếu|sẽ|dự kiến|kế hoạch|nguy cơ)\b")
RELATIVE = re.compile(r"(?i)\b(?:mẹ|bố|cha|vợ|chồng|anh|chị|em|gia đình)\b")
FAMILY_REPORTER = re.compile(
    r"(?i)\b(?:gia đình|mẹ|bố|cha|vợ|chồng|anh|chị|em)\b.*"
    r"\b(?:nhận thấy|cho biết|báo cáo)\b.*\bbệnh nhân\b"
)


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


def _clause(raw_text: str, span: Span) -> tuple[str, int, int]:
    line_start = raw_text.rfind("\n", 0, span.start) + 1
    line_end = raw_text.find("\n", span.end)
    if line_end < 0:
        line_end = len(raw_text)
    relative_start = span.start - line_start
    relative_end = span.end - line_start
    line = raw_text[line_start:line_end]
    left = 0
    right = len(line)
    for boundary in BOUNDARY.finditer(line):
        if boundary.end() <= relative_start:
            left = boundary.end()
        elif boundary.start() >= relative_end:
            right = boundary.start()
            break
    return line[left:right], relative_start - left, relative_end - left


def _section_kind(raw_text: str, position: int) -> str:
    return next(
        section.kind
        for section in parse_sections(raw_text)
        if section.start <= position < section.end
    )
