import re
from collections import defaultdict
from dataclasses import dataclass

from medical_race.linking.icd10 import ICD10Term, is_diagnosis_code, normalize_icd_text
from medical_race.sections import Section, parse_sections


TOKEN = re.compile(r"[^\W_]+", re.UNICODE)
DIAGNOSIS_SUBHEADINGS = (
    "các phát hiện chẩn đoán khác",
    "các kết quả chẩn đoán khác",
    "phát hiện chẩn đoán khác",
    "kết quả chẩn đoán khác",
)
STOP_HEADINGS = (
    "điều trị",
    "các thủ thuật",
    "thủ thuật",
    "các thuốc",
    "thuốc",
    "dấu hiệu lâm sàng",
    "kết quả khám",
    "kết quả xét",
    "kết quả phòng thí nghiệm",
    "kết quả chụp",
    "kế hoạch",
    "diễn biến",
)


@dataclass(frozen=True, slots=True)
class LinkedDiagnosis:
    text: str
    start: int
    end: int
    code: str


def extract_diagnoses(
    raw_text: str,
    term_index: dict[str, ICD10Term],
) -> tuple[LinkedDiagnosis, ...]:
    patterns = _patterns(term_index)
    candidates = []
    for start, end in _context_ranges(raw_text):
        tokens = [
            (normalize_icd_text(match.group()), match.start(), match.end())
            for match in TOKEN.finditer(raw_text, start, end)
        ]
        words = tuple(token[0] for token in tokens)
        for position, word in enumerate(words):
            for pattern, term in patterns.get(word, ()):
                pattern_end = position + len(pattern)
                if words[position:pattern_end] != pattern:
                    continue
                match_start = tokens[position][1]
                match_end = _extend_terminal_closers(
                    raw_text,
                    tokens[pattern_end - 1][2],
                    end,
                    term.name,
                )
                candidates.append(
                    LinkedDiagnosis(
                        raw_text[match_start:match_end],
                        match_start,
                        match_end,
                        term.code,
                    )
                )
    return _longest_non_overlapping(candidates)


def _patterns(term_index: dict[str, ICD10Term]):
    output = defaultdict(list)
    for normalized, term in term_index.items():
        pattern = tuple(normalized.split())
        if len(pattern) < 2 or not is_diagnosis_code(term.code):
            continue
        output[pattern[0]].append((pattern, term))
    for values in output.values():
        values.sort(key=lambda value: (-len(value[0]), value[1].code))
    return output


def _context_ranges(raw_text: str):
    for section in parse_sections(raw_text):
        if section.kind == "diagnosis":
            end = _first_stop(raw_text, section.content_start, section.end)
            if section.content_start < end:
                yield section.content_start, end
        elif section.kind in {"past_history", "imaging"}:
            if section.content_start < section.end:
                yield section.content_start, section.end
        elif section.kind == "assessment":
            yield from _assessment_ranges(raw_text, section)


def _first_stop(raw_text: str, start: int, end: int) -> int:
    position = start
    for full_line in raw_text[start:end].splitlines(keepends=True):
        line = full_line.rstrip("\r\n")
        if _starts_with(line, STOP_HEADINGS):
            return position
        position += len(full_line)
    return end


def _assessment_ranges(raw_text: str, section: Section):
    active_start = None
    position = section.content_start
    for full_line in raw_text[section.content_start : section.end].splitlines(keepends=True):
        line = full_line.rstrip("\r\n")
        diagnosis_offset = _subheading_content_offset(line)
        if diagnosis_offset is not None:
            if active_start is not None and active_start < position:
                yield active_start, position
            active_start = position + diagnosis_offset
        elif active_start is not None and _starts_with(line, STOP_HEADINGS):
            if active_start < position:
                yield active_start, position
            active_start = None
        position += len(full_line)
    if active_start is not None and active_start < section.end:
        yield active_start, section.end


def _subheading_content_offset(line: str) -> int | None:
    leading = len(line) - len(line.lstrip(" \t*-"))
    content = line[leading:]
    folded = content.casefold()
    for heading in DIAGNOSIS_SUBHEADINGS:
        if not folded.startswith(heading):
            continue
        offset = leading + len(heading)
        while offset < len(line) and line[offset] in " \t:*-":
            offset += 1
        return offset
    return None


def _starts_with(line: str, prefixes: tuple[str, ...]) -> bool:
    folded = line.lstrip(" \t*-0123456789.)").casefold()
    return folded.startswith(prefixes)


def _extend_terminal_closers(raw_text: str, end: int, limit: int, term_name: str) -> int:
    stripped = term_name.rstrip()
    suffix_start = len(stripped)
    while suffix_start and stripped[suffix_start - 1] in ")]}“”":
        suffix_start -= 1
    suffix = stripped[suffix_start:]
    if suffix and end + len(suffix) <= limit and raw_text.startswith(suffix, end):
        return end + len(suffix)
    return end


def _longest_non_overlapping(candidates):
    selected = []
    unique = {(value.start, value.end, value.code): value for value in candidates}
    for value in sorted(
        unique.values(),
        key=lambda item: (-(item.end - item.start), item.start, item.code),
    ):
        if any(value.start < other.end and other.start < value.end for other in selected):
            continue
        selected.append(value)
    return tuple(sorted(selected, key=lambda value: (value.start, value.end, value.code)))
