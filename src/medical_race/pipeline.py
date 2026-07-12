import json
import re
from dataclasses import dataclass
from pathlib import Path

from medical_race.assertions import classify_assertions
from medical_race.extraction import Span
from medical_race.extraction.drugs import extract_drugs
from medical_race.extraction.labs import extract_labs
from medical_race.linking.rxnorm import RxNormTerm, link_drug
from medical_race.output import validate_entities


CONFIG_FIELDS = {"include_labs", "span_policy", "concept_level", "candidate_output"}


@dataclass(frozen=True, slots=True)
class SubmissionConfig:
    include_labs: bool
    span_policy: str
    concept_level: str
    candidate_output: str

    def __post_init__(self):
        if type(self.include_labs) is not bool:
            raise ValueError("include_labs must be boolean")
        if self.span_policy not in {"regimen", "core"}:
            raise ValueError(f"unknown span policy: {self.span_policy!r}")
        if self.concept_level not in {"all_retrievable", "ingredient"}:
            raise ValueError(f"unknown concept level: {self.concept_level!r}")
        if self.candidate_output not in {"top1", "top2"}:
            raise ValueError(f"unknown candidate output: {self.candidate_output!r}")


def load_submission_config(path: Path) -> SubmissionConfig:
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(values, dict) or set(values) != CONFIG_FIELDS:
        raise ValueError(f"config fields must be exactly {sorted(CONFIG_FIELDS)}")
    return SubmissionConfig(**values)


def predict_document(
    raw_text: str,
    terms: tuple[RxNormTerm, ...],
    config: SubmissionConfig,
) -> list[dict[str, object]]:
    entities = []
    for extracted in extract_drugs(raw_text):
        link = link_drug(
            extracted.text,
            terms,
            config.concept_level,
            config.candidate_output,
        )
        if link is None:
            continue
        span = extracted if config.span_policy == "regimen" else _core_span(extracted, link.matched_text)
        if span is None:
            continue
        entities.append(
            {
                "text": span.text,
                "type": "THUỐC",
                "candidates": list(link.candidates),
                "assertions": list(classify_assertions(raw_text, span).labels()),
                "position": [span.start, span.end],
            }
        )
    if config.include_labs:
        for result in extract_labs(raw_text):
            entities.extend(
                (
                    {
                        "text": result.name.text,
                        "type": "TÊN_XÉT_NGHIỆM",
                        "position": [result.name.start, result.name.end],
                    },
                    {
                        "text": result.value.text,
                        "type": "KẾT_QUẢ_XÉT_NGHIỆM",
                        "position": [result.value.start, result.value.end],
                    },
                )
            )
    entities.sort(key=lambda entity: (entity["position"][0], entity["position"][1], entity["type"]))
    validate_entities(raw_text, entities)
    return entities


def _core_span(span: Span, matched_text: str) -> Span | None:
    tokens = re.findall(r"\w+", matched_text)
    if not tokens:
        return None
    pattern = re.compile(
        r"(?i)(?<!\w)" + r"[^\w]*".join(map(re.escape, tokens)) + r"(?!\w)"
    )
    matches = list(pattern.finditer(span.text))
    if len(matches) != 1:
        return None
    match = matches[0]
    start = span.start + match.start()
    end = span.start + match.end()
    return Span(span.text[match.start() : match.end()], start, end)
