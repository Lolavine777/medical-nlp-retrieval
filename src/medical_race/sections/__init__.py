import re
from dataclasses import dataclass


HEADERS = (
    ("Thuốc trước khi nhập viện lần này", "medications"),
    ("Thuốc trước khi nhập viện", "medications"),
    ("Tiền sử bệnh hiện tại", "current_illness"),
    ("Tiền sử bệnh nội khoa", "past_history"),
    ("Phát hiện chẩn đoán", "diagnosis"),
    ("Đánh giá tại bệnh viện", "assessment"),
    ("Triệu chứng khi nhập viện", "symptoms"),
    ("Lịch sử bệnh hiện tại", "current_illness"),
    ("Bệnh sử hiện tại", "current_illness"),
    ("Triệu chứng hiện tại", "symptoms"),
    ("Tiền sử phẫu thuật / thủ thuật", "past_history"),
    ("Chẩn đoán hình ảnh", "imaging"),
    ("Lý do nhập viện", "admission_reason"),
    ("Các bệnh lý mãn tính", "past_history"),
    ("Các bệnh lý mạn tính", "past_history"),
    ("Diễn biến bệnh", "course"),
    ("Khám tại bệnh viện", "exam"),
    ("Tiền sử bệnh", "past_history"),
    ("Chẩn đoán", "diagnosis"),
    ("Xét nghiệm", "laboratory"),
    ("Diễn biến", "course"),
    ("Khám lâm sàng", "exam"),
    ("Khám", "exam"),
)
PREFIX = re.compile(r"\s*(?:\d+\.\s*)?")


@dataclass(frozen=True, slots=True)
class Section:
    kind: str
    title: str | None
    start: int
    header_start: int | None
    header_end: int | None
    content_start: int
    end: int


def _match_header(line: str, line_start: int, full_line_length: int) -> Section | None:
    prefix_end = PREFIX.match(line).end()
    remainder = line[prefix_end:]
    folded = remainder.casefold()
    for label, kind in HEADERS:
        if not folded.startswith(label.casefold()):
            continue
        tail = remainder[len(label) :]
        if not tail.strip():
            content_start = line_start + full_line_length
        else:
            colon = tail.find(":")
            if colon < 0 or tail[:colon].strip():
                continue
            content_offset = prefix_end + len(label) + colon + 1
            while content_offset < len(line) and line[content_offset].isspace():
                content_offset += 1
            content_start = line_start + content_offset
        header_start = line_start + prefix_end
        header_end = header_start + len(label)
        return Section(
            kind=kind,
            title=line[prefix_end : prefix_end + len(label)],
            start=line_start,
            header_start=header_start,
            header_end=header_end,
            content_start=content_start,
            end=0,
        )
    return None


def parse_sections(raw_text: str) -> tuple[Section, ...]:
    found: list[Section] = []
    position = 0
    for full_line in raw_text.splitlines(keepends=True):
        line = full_line.rstrip("\r\n")
        section = _match_header(line, position, len(full_line))
        if section is not None:
            found.append(section)
        position += len(full_line)

    if not found:
        return (Section("unsectioned", None, 0, None, None, 0, len(raw_text)),)

    sections: list[Section] = []
    if found[0].start:
        sections.append(Section("unsectioned", None, 0, None, None, 0, found[0].start))
    for index, section in enumerate(found):
        end = found[index + 1].start if index + 1 < len(found) else len(raw_text)
        sections.append(
            Section(
                section.kind,
                section.title,
                section.start,
                section.header_start,
                section.header_end,
                section.content_start,
                end,
            )
        )
    return tuple(sections)
