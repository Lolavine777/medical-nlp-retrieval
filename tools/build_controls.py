import argparse
import json
from pathlib import Path

from medical_race.submission import validate_output_zip
from medical_race.submission_diff import diff_submission_archives
from tools.audit_sources import read_zip_documents, validate_document_names
from tools.build_submission import (
    DEFAULT_ICD10_PATH,
    PINNED_ICD10_SHA256,
    PUBLISHED_RXNORM_MD5,
    build_submission,
)


RULE_CONFIG = Path("configs/submissions/07_add_diagnoses.json")
QWEN_CONFIG = Path("configs/submissions/08_qwen_grounded.json")
TARGET_NAMES = (
    "rule-control.zip",
    "rule-control.report.json",
    "qwen-control.zip",
    "qwen-control.report.json",
    "rule-to-qwen.diff.json",
    "controls.summary.json",
)


def build_controls(
    input_zip: Path,
    rxnorm_zip: Path,
    icd_path: Path,
    proposal_root: Path,
    destination: Path,
    expected_md5: str = PUBLISHED_RXNORM_MD5,
    expected_icd_sha256: str = PINNED_ICD10_SHA256,
    rule_config: Path = RULE_CONFIG,
    qwen_config: Path = QWEN_CONFIG,
) -> dict[str, object]:
    destination = Path(destination)
    proposal_root = Path(proposal_root)
    if not destination.is_dir():
        raise ValueError(f"output directory does not exist: {destination}")
    if not proposal_root.is_dir():
        raise ValueError(f"model proposal directory does not exist: {proposal_root}")
    targets = {name: destination / name for name in TARGET_NAMES}
    existing = [path for path in targets.values() if path.exists()]
    if existing:
        raise FileExistsError(existing[0])

    documents = read_zip_documents(Path(input_zip))
    validate_document_names(list(documents))
    rule_report = build_submission(
        input_zip,
        rxnorm_zip,
        rule_config,
        targets["rule-control.zip"],
        expected_md5,
        icd_path,
        expected_icd_sha256,
    )
    if not rule_report["entity_count"] or not rule_report["candidate_count"]:
        raise ValueError("rule control produced no entities or candidates")
    rule_preflight = validate_output_zip(targets["rule-control.zip"], documents)

    qwen_report = build_submission(
        input_zip,
        rxnorm_zip,
        qwen_config,
        targets["qwen-control.zip"],
        expected_md5,
        icd_path,
        expected_icd_sha256,
        model_proposals_path=proposal_root,
    )
    if not qwen_report["entity_count"] or not qwen_report["candidate_count"]:
        raise ValueError("Qwen control produced no entities or candidates")
    qwen_preflight = validate_output_zip(targets["qwen-control.zip"], documents)
    diff = diff_submission_archives(
        targets["rule-control.zip"],
        targets["qwen-control.zip"],
    )
    diff_counts = {key: value for key, value in diff.items() if key != "details"}
    summary = {
        "rule": {
            "archive": str(targets["rule-control.zip"]),
            "report": str(targets["rule-control.report.json"]),
            "preflight": rule_preflight,
        },
        "qwen": {
            "archive": str(targets["qwen-control.zip"]),
            "report": str(targets["qwen-control.report.json"]),
            "preflight": qwen_preflight,
        },
        "diff": {
            "report": str(targets["rule-to-qwen.diff.json"]),
            **diff_counts,
        },
    }
    _write_json(targets["rule-control.report.json"], rule_report)
    _write_json(targets["qwen-control.report.json"], qwen_report)
    _write_json(targets["rule-to-qwen.diff.json"], diff)
    _write_json(targets["controls.summary.json"], summary)
    return summary


def _write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("input.zip"))
    parser.add_argument(
        "--rxnorm",
        type=Path,
        default=Path("ontologies/rxnorm/RxNorm_full_prescribe_07062026.zip"),
    )
    parser.add_argument("--icd", type=Path, default=DEFAULT_ICD10_PATH)
    parser.add_argument("--model-proposals", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rule-config", type=Path, default=RULE_CONFIG)
    parser.add_argument("--qwen-config", type=Path, default=QWEN_CONFIG)
    parser.add_argument("--expected-md5", default=PUBLISHED_RXNORM_MD5)
    parser.add_argument("--expected-icd-sha256", default=PINNED_ICD10_SHA256)
    args = parser.parse_args()
    summary = build_controls(
        args.input,
        args.rxnorm,
        args.icd,
        args.model_proposals,
        args.output_dir,
        args.expected_md5,
        args.expected_icd_sha256,
        args.rule_config,
        args.qwen_config,
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
