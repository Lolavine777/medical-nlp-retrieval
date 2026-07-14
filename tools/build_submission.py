import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from medical_race.extraction.drugs import extract_drugs
from medical_race.linking.icd10 import build_term_index, read_icd10_snapshot
from medical_race.linking.rxnorm import read_rxnorm_archive
from medical_race.pipeline import load_submission_config, predict_document
from medical_race.submission import build_output_zip
from tools.audit_sources import read_zip_documents, sha256, validate_document_names


PUBLISHED_RXNORM_MD5 = "767678e3b5b1d6fe358b61c21659f3ef"
PINNED_ICD10_SHA256 = "72b81f78e3fb971c2c44250d3a5ae67f7c41bef3b5bf1ded59954250e479212f"
DEFAULT_ICD10_PATH = Path("ontologies/icd/icd10_vn_2020.json")


def build_submission(
    input_zip: Path,
    rxnorm_zip: Path,
    config_path: Path,
    destination: Path,
    expected_md5: str = PUBLISHED_RXNORM_MD5,
    icd_path: Path = DEFAULT_ICD10_PATH,
    expected_icd_sha256: str = PINNED_ICD10_SHA256,
) -> dict[str, object]:
    input_zip = Path(input_zip)
    rxnorm_zip = Path(rxnorm_zip)
    config_path = Path(config_path)
    destination = Path(destination)
    icd_path = Path(icd_path)
    input_sha256 = sha256(input_zip)
    ontology_sha256 = sha256(rxnorm_zip)
    config_sha256 = sha256(config_path)
    config = load_submission_config(config_path)
    icd_ontology_sha256 = sha256(icd_path) if config.include_diagnoses else None
    documents = read_zip_documents(input_zip)
    validate_document_names(list(documents))
    terms = read_rxnorm_archive(rxnorm_zip, expected_md5)
    icd_index = None
    if config.include_diagnoses:
        icd_terms = read_icd10_snapshot(icd_path, expected_icd_sha256)
        icd_index = build_term_index(icd_terms)
    predictions = {
        name: predict_document(raw_text, terms, config, icd_index)
        for name, raw_text in documents.items()
    }
    package = build_output_zip(documents, predictions, destination)
    entities = [entity for values in predictions.values() for entity in values]
    entity_counts = Counter(entity["type"] for entity in entities)
    extracted_drugs = sum(len(extract_drugs(raw_text)) for raw_text in documents.values())
    linked_drugs = entity_counts["THUỐC"]
    report = {
        "commit": _commit(),
        "input_sha256": input_sha256,
        "ontology_sha256": ontology_sha256,
        "config_sha256": config_sha256,
        "output_sha256": package["sha256"],
        "entry_count": package["entry_count"],
        "entity_count": package["entity_count"],
        "empty_document_count": package["empty_document_count"],
        "byte_count": package["byte_count"],
        "entity_counts": dict(sorted(entity_counts.items())),
        "candidate_count": sum(len(entity.get("candidates", [])) for entity in entities),
        "assertion_count": sum(len(entity.get("assertions", [])) for entity in entities),
        "linked_drug_count": linked_drugs,
        "dropped_drug_count": extracted_drugs - linked_drugs,
        "model_parameters": 0,
    }
    if config.include_diagnoses:
        candidate_counts = Counter(
            entity["type"]
            for entity in entities
            for _ in entity.get("candidates", [])
        )
        report.update(
            {
                "icd_ontology_sha256": icd_ontology_sha256,
                "diagnosis_count": entity_counts["CHẨN_ĐOÁN"],
                "candidate_counts_by_type": dict(sorted(candidate_counts.items())),
            }
        )
    return report


def _console_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, encoding="utf-8"
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("input.zip"))
    parser.add_argument(
        "--rxnorm",
        type=Path,
        default=Path("ontologies/rxnorm/RxNorm_full_prescribe_07062026.zip"),
    )
    parser.add_argument("--icd", type=Path, default=DEFAULT_ICD10_PATH)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--expected-md5", default=PUBLISHED_RXNORM_MD5)
    parser.add_argument("--expected-icd-sha256", default=PINNED_ICD10_SHA256)
    args = parser.parse_args()
    report = build_submission(
        args.input,
        args.rxnorm,
        args.config,
        args.output,
        args.expected_md5,
        args.icd,
        args.expected_icd_sha256,
    )
    report_path = args.report or args.output.with_suffix(".report.json")
    with report_path.open("x", encoding="utf-8") as output:
        json.dump(report, output, ensure_ascii=False, indent=2, sort_keys=True)
        output.write("\n")
    print(_console_json(report))


if __name__ == "__main__":
    main()
