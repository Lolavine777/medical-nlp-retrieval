import re
from dataclasses import dataclass

from medical_race.extraction import Span
from medical_race.line_roles import parse_line_roles


NAME = re.compile(
    r"(?i)(?<!\w)(?:bảng công thức sinh hóa máu cơ bản|bảng công thức máu|"
    r"bilirubin toàn phần(?:\s*\(tbili\))?|"
    r"ast(?:\s*\(aspartate aminotransferase\))?|"
    r"alt(?:\s*\(alanine aminotransferase\))?|"
    r"creatinin(?:e)?|glucose|hemoglobin|bạch cầu(?:\s*\(wbc\))?|"
    r"tiểu cầu|natri|kali(?:\s*\(k\))?|albumin|inr|crp|procalcitonin)(?!\w)"
)
NUMERIC = re.compile(
    r"(?i)\d+(?:[.,]\d+)?(?:\s*-\s*\d+(?:[.,]\d+)?)?"
    r"(?:\s*(?:mg/dl|mmol/l|g/dl|iu/l|u/l|mEq/l|%))?"
)
QUALITATIVE = re.compile(r"(?i)(?:bình thường|âm tính|dương tính|tăng|giảm)")
LAB_CUE = re.compile(r"(?i)(?:xét nghiệm|kết quả|cho thấy|ghi nhận)")
RESULT_CUE = re.compile(r"(?i)(?:\blà\b|ở mức|tăng|giảm|ổn định|cải thiện|xuống|lên)")


@dataclass(frozen=True, slots=True)
class LabResult:
    name: Span
    value: Span


def extract_labs(raw_text: str) -> tuple[LabResult, ...]:
    output = []
    for line in parse_line_roles(raw_text):
        names = list(NAME.finditer(line.text))
        for index, match in enumerate(names):
            search_end = names[index + 1].start() if index + 1 < len(names) else len(line.text)
            value = NUMERIC.search(line.text, match.end(), search_end)
            if value is None:
                value = QUALITATIVE.search(line.text, match.end(), search_end)
            if value is None:
                continue
            between = line.text[match.end() : value.start()]
            if line.role != "laboratory" and not (
                LAB_CUE.search(line.text) or RESULT_CUE.search(between)
            ):
                continue
            name_start = line.start + match.start()
            name_end = line.start + match.end()
            value_start = line.start + value.start()
            value_end = line.start + value.end()
            output.append(
                LabResult(
                    Span(raw_text[name_start:name_end], name_start, name_end),
                    Span(raw_text[value_start:value_end], value_start, value_end),
                )
            )
    return tuple(output)
