import argparse
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

from medical_race.extraction.diagnoses import extract_diagnoses
from medical_race.extraction.drugs import extract_drugs
from medical_race.linking.icd10 import (
    ICD10Term,
    build_term_index,
    exact_icd_candidates,
    normalize_icd_text,
    read_icd10_snapshot,
)
from medical_race.linking.rxnorm import (
    RxNormTerm,
    normalize_rxnorm_text,
    rank_drug_candidates,
    read_rxnorm_archive,
)
from medical_race.model_proposals import (
    ModelProposal,
    ground_proposals,
    read_proposal_directory,
)
from tools.audit_sources import read_zip_documents, validate_document_names
from tools.build_submission import (
    DEFAULT_ICD10_PATH,
    PINNED_ICD10_SHA256,
    PUBLISHED_RXNORM_MD5,
)


def audit_linking(
    documents: Mapping[str, str],
    rxnorm_terms: tuple[RxNormTerm, ...],
    icd_terms: tuple[ICD10Term, ...],
    model_proposals: Mapping[str, tuple[ModelProposal, ...]] | None = None,
) -> dict[str, object]:
    icd_index = build_term_index(icd_terms)
    queries = []
    for name in sorted(documents, key=_document_key):
        raw_text = documents[name]
        queries.extend(
            (name, span.start, span.end, "THUỐC", "rule", span.text)
            for span in extract_drugs(raw_text)
        )
        queries.extend(
            (name, value.start, value.end, "CHẨN_ĐOÁN", "rule", value.text)
            for value in extract_diagnoses(raw_text, icd_index)
        )
        if model_proposals is not None:
            for value in ground_proposals(raw_text, model_proposals.get(name, ())):
                if value.entity_type not in {"THUỐC", "CHẨN_ĐOÁN"}:
                    continue
                queries.append(
                    (
                        name,
                        value.span.start,
                        value.span.end,
                        value.entity_type,
                        "qwen",
                        value.span.text,
                    )
                )

    records = []
    for name, start, end, entity_type, source, text in sorted(
        set(queries),
        key=lambda value: (
            _document_key(value[0]), value[1], value[2], value[3], value[4]
        ),
    ):
        if entity_type == "THUỐC":
            ranked = rank_drug_candidates(text, rxnorm_terms)
            candidates = [
                {
                    "id": term.rxcui,
                    "text": term.text,
                    "term_type": term.term_type,
                    "source": term.source,
                    "preferred": term.preferred,
                }
                for term in ranked
            ]
            normalized = normalize_rxnorm_text(text)
        else:
            ranked = exact_icd_candidates(text, icd_terms)
            candidates = [
                {
                    "id": term.code,
                    "text": term.name,
                    "model": term.model,
                    "is_leaf": term.is_leaf,
                }
                for term in ranked
            ]
            normalized = normalize_icd_text(text)
        distinct_ids = {candidate["id"] for candidate in candidates}
        if not distinct_ids:
            status = "unlinked"
        elif len(distinct_ids) > 1:
            status = "ambiguous"
        else:
            status = "linked"
        records.append(
            {
                "document": name,
                "text": text,
                "type": entity_type,
                "source": source,
                "position": [start, end],
                "normalized_query": normalized,
                "status": status,
                "candidates": candidates,
            }
        )
    counts = Counter(record["status"] for record in records)
    return {
        "summary": {
            "queries": len(records),
            "linked": counts["linked"],
            "ambiguous": counts["ambiguous"],
            "unlinked": counts["unlinked"],
        },
        "records": records,
    }


def _document_key(name: str) -> tuple[int, int | str]:
    stem = Path(name).stem
    return (0, int(stem)) if stem.isdecimal() else (1, name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("input.zip"))
    parser.add_argument(
        "--rxnorm",
        type=Path,
        default=Path("ontologies/rxnorm/RxNorm_full_prescribe_07062026.zip"),
    )
    parser.add_argument("--icd", type=Path, default=DEFAULT_ICD10_PATH)
    parser.add_argument("--model-proposals", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-md5", default=PUBLISHED_RXNORM_MD5)
    parser.add_argument("--expected-icd-sha256", default=PINNED_ICD10_SHA256)
    args = parser.parse_args()
    documents = read_zip_documents(args.input)
    validate_document_names(list(documents))
    proposals = (
        read_proposal_directory(args.model_proposals, documents)
        if args.model_proposals is not None
        else None
    )
    report = audit_linking(
        documents,
        read_rxnorm_archive(args.rxnorm, args.expected_md5),
        read_icd10_snapshot(args.icd, args.expected_icd_sha256),
        proposals,
    )
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
