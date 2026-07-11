from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Span:
    text: str
    start: int
    end: int
