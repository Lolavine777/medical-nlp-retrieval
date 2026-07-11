from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RawDocument:
    name: str
    raw_text: str


@dataclass(frozen=True, slots=True)
class MappedText:
    text: str
    normalized_to_raw: tuple[int, ...]

    def raw_span(self, start: int, end: int) -> tuple[int, int]:
        if start < 0 or end < start or end >= len(self.normalized_to_raw):
            raise ValueError(f"invalid normalized span: [{start}, {end}]")
        return self.normalized_to_raw[start], self.normalized_to_raw[end]


def load_document(name: str, data: bytes) -> RawDocument:
    return RawDocument(name=name, raw_text=data.decode("utf-8", errors="strict"))


def casefold_with_mapping(raw_text: str) -> MappedText:
    pieces: list[str] = []
    boundaries = [0]
    for raw_index, character in enumerate(raw_text):
        folded = character.casefold()
        pieces.append(folded)
        boundaries.extend(
            raw_index if index < len(folded) - 1 else raw_index + 1
            for index in range(len(folded))
        )
    return MappedText("".join(pieces), tuple(boundaries))
