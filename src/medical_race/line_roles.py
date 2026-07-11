from dataclasses import dataclass

from medical_race.sections import parse_sections


@dataclass(frozen=True, slots=True)
class LineRole:
    text: str
    start: int
    end: int
    section: str
    role: str


def parse_line_roles(raw_text: str) -> tuple[LineRole, ...]:
    sections = parse_sections(raw_text)
    output = []
    position = 0
    section_index = 0
    for full_line in raw_text.splitlines(keepends=True):
        line_end = position + len(full_line.rstrip("\r\n"))
        while section_index + 1 < len(sections) and position >= sections[section_index].end:
            section_index += 1
        section = sections[section_index]
        start = position
        if section.header_start is not None and position <= section.header_start <= line_end:
            if section.content_start < line_end:
                start = section.content_start
                role = _content_role(section.kind)
            else:
                role = "header"
        else:
            role = "blank" if not raw_text[start:line_end].strip() else _content_role(section.kind)
        output.append(LineRole(raw_text[start:line_end], start, line_end, section.kind, role))
        position += len(full_line)
    return tuple(output)


def _content_role(section: str) -> str:
    return {"medications": "medication", "laboratory": "laboratory"}.get(section, "content")
