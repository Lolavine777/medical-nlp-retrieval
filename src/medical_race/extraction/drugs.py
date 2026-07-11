import re

from medical_race.extraction import Span
from medical_race.line_roles import parse_line_roles


MARKER = re.compile(r"\s*(?:[-*]|\d+[.)])\s*")
WHITESPACE = re.compile(r"\s*")
DOSE = re.compile(
    r"(?i)\d+(?:[.,]\d+)?(?:\s*-\s*\d+(?:[.,]\d+)?)?\s*"
    r"(?:mg|mcg|g|ml|mEq|đơn vị)\b"
)
ROUTE = re.compile(r"(?i)\b(?:po|iv|im|sc|bid|tid|qid|qhs|prn|qam|q\d+h|daily|once)\b")
LEADING_CUE = re.compile(
    r"(?i)(?:bắt đầu\s+dùng|được\s+chỉ\s+định\s+điều\s+trị|được\s+cho|"
    r"nhận|đã\s+dùng|dùng|đang\s+dùng|thường\s+dùng)\s+"
)
NON_DRUG = re.compile(r"(?i)^(?:không tuân thủ|chỉ dùng để|liệu pháp lợi tiểu|cách nhập viện)\b")
CUT = re.compile(r"(?i)(?:\s+(?:điều trị|cho)\s+|,\s*(?:không|nhưng)\b)")


def extract_drugs(raw_text: str) -> tuple[Span, ...]:
    output = []
    for line in parse_line_roles(raw_text):
        marker = MARKER.match(line.text)
        prefix = marker or WHITESPACE.match(line.text)
        start = line.start + prefix.end()
        candidate = raw_text[start : line.end]
        cue = LEADING_CUE.match(candidate)
        route_count = len(ROUTE.findall(candidate))
        strong_regimen = (DOSE.search(candidate) and (route_count or cue)) or route_count >= 2
        if line.role != "medication" and not (marker and strong_regimen):
            continue
        if cue:
            start += cue.end()
            candidate = raw_text[start : line.end]
        if NON_DRUG.match(candidate):
            continue
        cut = CUT.search(candidate)
        regimen = DOSE.search(candidate) or ROUTE.search(candidate)
        if cut and regimen and cut.start() < regimen.start():
            continue
        ends = [cut.start()] if cut else []
        parenthesis = candidate.find(" (")
        if parenthesis >= 0:
            ends.append(parenthesis)
        end = start + (min(ends) if ends else len(candidate))
        while end > start and raw_text[end - 1] in " \t,.;":
            end -= 1
        if end > start:
            output.append(Span(raw_text[start:end], start, end))
    return tuple(output)
