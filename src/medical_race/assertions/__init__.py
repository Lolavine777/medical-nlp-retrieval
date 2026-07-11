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
