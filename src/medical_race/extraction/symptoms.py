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
