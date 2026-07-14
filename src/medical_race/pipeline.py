import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from medical_race.assertions import classify_assertions
from medical_race.extraction import Span
from medical_race.extraction.diagnoses import extract_diagnoses
from medical_race.extraction.drugs import extract_drugs
from medical_race.extraction.labs import extract_labs
from medical_race.extraction.symptoms import extract_symptoms
from medical_race.linking.icd10 import ICD10Term
from medical_race.linking.rxnorm import RxNormTerm, link_drug
from medical_race.model_proposals import ModelProposal, accept_model_proposals
from medical_race.output import validate_entities


REQUIRED_CONFIG_FIELDS = {"include_labs", "span_policy", "concept_level", "candidate_output"}
OPTIONAL_CONFIG_FIELDS = {
    "include_symptoms",
    "include_diagnoses",
    "include_model_proposals",
}


@dataclass(frozen=True, slots=True)
class SubmissionConfig:
    include_labs: bool
    span_policy: str
    concept_level: str
    candidate_output: str
    include_symptoms: bool = False
    include_diagnoses: bool = False
    include_model_proposals: bool = False

    def __post_init__(self):
        if type(self.include_labs) is not bool:
            raise ValueError("include_labs must be boolean")
        if type(self.include_symptoms) is not bool:
            raise ValueError("include_symptoms must be boolean")
        if type(self.include_diagnoses) is not bool:
            raise ValueError("include_diagnoses must be boolean")
        if type(self.include_model_proposals) is not bool:
            raise ValueError("include_model_proposals must be boolean")
        if self.span_policy not in {"regimen", "core"}:
            raise ValueError(f"unknown span policy: {self.span_policy!r}")
        if self.concept_level not in {"all_retrievable", "ingredient"}:
            raise ValueError(f"unknown concept level: {self.concept_level!r}")
        if self.candidate_output not in {"top1", "top2"}:
            raise ValueError(f"unknown candidate output: {self.candidate_output!r}")


def load_submission_config(path: Path) -> SubmissionConfig:
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(values, dict):
        raise ValueError("config must be an object")
    fields = set(values)
    allowed = REQUIRED_CONFIG_FIELDS | OPTIONAL_CONFIG_FIELDS
    if not REQUIRED_CONFIG_FIELDS <= fields or fields - allowed:
        raise ValueError(
            f"config fields must contain {sorted(REQUIRED_CONFIG_FIELDS)} "
            f"and only use {sorted(allowed)}"
        )
    values.setdefault("include_symptoms", False)
    values.setdefault("include_diagnoses", False)
    values.setdefault("include_model_proposals", False)
    return SubmissionConfig(**values)


def predict_document(
    raw_text: str,
    terms: tuple[RxNormTerm, ...],
    config: SubmissionConfig,
    icd_index: dict[str, ICD10Term] | None = None,
    model_proposals: tuple[ModelProposal, ...] = (),
    model_report: Counter | None = None,
) -> list[dict[str, object]]:
    if config.include_diagnoses and icd_index is None:
        raise ValueError("verified ICD-10 term index is required when diagnoses are enabled")
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
    if config.include_symptoms:
        for span in extract_symptoms(raw_text):
            entities.append(
                {
                    "text": span.text,
                    "type": "TRIỆU_CHỨNG",
                    "assertions": list(classify_assertions(raw_text, span).labels()),
                    "position": [span.start, span.end],
                }
            )
    if config.include_diagnoses:
        for match in extract_diagnoses(raw_text, icd_index):
            span = Span(match.text, match.start, match.end)
            entities.append(
                {
                    "text": span.text,
                    "type": "CHẨN_ĐOÁN",
                    "candidates": [match.code],
                    "assertions": list(classify_assertions(raw_text, span).labels()),
                    "position": [span.start, span.end],
                }
            )
    if config.include_model_proposals:
        result = accept_model_proposals(
            raw_text,
            model_proposals,
            entities,
            terms,
            icd_index or {},
            config.concept_level,
            config.candidate_output,
        )
        entities.extend(result.entities)
        if model_report is not None:
            model_report.update(result.rejected)
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
