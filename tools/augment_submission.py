import argparse
import json
import re
import subprocess
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from medical_race.linking.icd10 import build_term_index, read_icd10_snapshot
from medical_race.linking.rxnorm import read_rxnorm_archive
from medical_race.model_proposals import (
    accept_model_proposals,
    read_proposal_directory,
    read_proposal_manifest,
)
from medical_race.pipeline import load_submission_config
from medical_race.submission import (
    INPUT_NAMES,
    OUTPUT_NAMES,
    build_output_zip,
    validate_output_zip,
)
from medical_race.submission_diff import diff_submission_archives
from tools.audit_sources import read_zip_documents, sha256, validate_document_names
from tools.build_submission import (
    DEFAULT_ICD10_PATH,
    PINNED_ICD10_SHA256,
PUBLISHED_RXNORM_MD5,
)


MODEL_ACTION_CUES = (
    "điều trị",
    "tự điều trị",
    "can thiệp",
    "gọi cho",
    "bác sĩ",
    "bệnh nhân được",
    "khuyên dùng",
    "xuất viện",
)
MODEL_PROCEDURE_CUES = (
    "chọc dò",
    "thủ thuật",
    "lấy mẫu",
    "chụp ",
    "siêu âm ",
    "tạo ảnh",
    "stent ",
)
MODEL_CONTEXT_FRAGMENTS = frozenset(
    {
        "bên trái",
        "bên phải",
        "liên tục",
        "kém",
        "khoảng vài năm",
        "2 tháng trước",
        "sự kiện trước khi nhập viện",
        "đặc biệt là khi hít thở sâu",
        "khi hít thở sâu",
    }
)


def augment_submission(
    input_zip: Path,
    parent_zip: Path,
    proposal_root: Path,
    rxnorm_zip: Path,
    config_path: Path,
    destination: Path,
    icd_path: Path = DEFAULT_ICD10_PATH,
    expected_md5: str = PUBLISHED_RXNORM_MD5,
    expected_icd_sha256: str = PINNED_ICD10_SHA256,
) -> dict[str, object]:
    input_zip = Path(input_zip)
    parent_zip = Path(parent_zip)
    proposal_root = Path(proposal_root)
    rxnorm_zip = Path(rxnorm_zip)
    config_path = Path(config_path)
    destination = Path(destination)
    icd_path = Path(icd_path)
    if not destination.parent.is_dir():
        raise ValueError(f"destination parent does not exist: {destination.parent}")
    if destination.exists():
        raise FileExistsError(destination)

    documents = read_zip_documents(input_zip)
    validate_document_names(list(documents))
    parent_predictions, parent_preflight = _read_parent_predictions(
        parent_zip,
        documents,
    )
    config = load_submission_config(config_path)
    if not config.include_model_proposals:
        raise ValueError("augmentation config must enable model proposals")
    proposals = read_proposal_directory(proposal_root, documents)
    manifest = read_proposal_manifest(proposal_root)
    terms = read_rxnorm_archive(rxnorm_zip, expected_md5)
    icd_index = (
        build_term_index(read_icd10_snapshot(icd_path, expected_icd_sha256))
        if config.include_diagnoses
        else {}
    )

    model_report = Counter()
    predictions = {}
    for name, raw_text in documents.items():
        parent_entities = parent_predictions[name]
        filtered_proposals, filtered_count = _filter_precision_proposals(
            proposals[name]
        )
        model_report["precision_filter"] += filtered_count
        result = accept_model_proposals(
            raw_text,
            filtered_proposals,
            parent_entities,
            terms,
            icd_index,
            config.concept_level,
            config.candidate_output,
        )
        model_report.update(result.rejected)
        predictions[name] = sorted(
            [*parent_entities, *result.entities],
            key=lambda entity: (
                entity["position"][0],
                entity["position"][1],
                entity["type"],
            ),
        )

    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        temporary_zip = Path(directory) / destination.name
        build_output_zip(documents, predictions, temporary_zip)
        child_preflight = validate_output_zip(temporary_zip, documents)
        diff = diff_submission_archives(parent_zip, temporary_zip)
        if (
            diff["removed_entities"]
            or diff["changed_entities"]
            or child_preflight["candidate_count"]
            != parent_preflight["candidate_count"]
            or not diff["added_entities"]
        ):
            raise ValueError("augmentation failed the parent-preservation gate")
        temporary_zip.replace(destination)

    diff_summary = {key: value for key, value in diff.items() if key != "details"}
    report = {
        "commit": _commit(),
        "input_sha256": sha256(input_zip),
        "parent_sha256": sha256(parent_zip),
        "config_sha256": sha256(config_path),
        "ontology_sha256": sha256(rxnorm_zip),
        "output_sha256": child_preflight["sha256"],
        "entry_count": child_preflight["entry_count"],
        "entity_count": child_preflight["entity_count"],
        "entity_counts": child_preflight["entity_counts"],
        "candidate_count": child_preflight["candidate_count"],
        "assertion_count": child_preflight["assertion_count"],
        "model_id": manifest["model_id"],
        "model_revision": manifest["model_revision"],
        "model_parameters": manifest["model_parameters"],
        "prompt_sha256": manifest["prompt_sha256"],
        "model_proposal_count": sum(len(values) for values in proposals.values()),
        "model_parse_error_count": _proposal_parse_error_count(
            proposal_root,
            documents,
        ),
        "model_added_entity_count": model_report["accepted"],
        "model_rejections": {
            key: value for key, value in model_report.items() if key != "accepted"
        },
        "diff": diff_summary,
        "promotion_eligible": True,
    }
    return report


def _proposal_parse_error_count(root, documents):
    return sum(
        json.loads(
            (Path(root) / "documents" / f"{Path(name).stem}.json").read_text(
                encoding="utf-8"
            )
        )["parse_error_count"]
        for name in documents
    )


def _filter_precision_proposals(proposals):
    selected = []
    rejected = 0
    for proposal in proposals:
        folded = " ".join(proposal.text.casefold().split())
        if proposal.entity_type == "TRIỆU_CHỨNG":
            invalid = (
                folded in MODEL_CONTEXT_FRAGMENTS
                or folded.startswith(MODEL_ACTION_CUES)
                or re.search(r"\b(?:trước|sau)\b$", folded) is not None
            )
        elif proposal.entity_type == "TÊN_XÉT_NGHIỆM":
            invalid = any(cue in folded for cue in MODEL_PROCEDURE_CUES)
        else:
            invalid = False
        if invalid:
            rejected += 1
        else:
            selected.append(proposal)
    return tuple(selected), rejected


def _commit():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
        encoding="utf-8",
    ).strip()


def _read_parent_predictions(path, documents):
    preflight = validate_output_zip(path, documents)
    with zipfile.ZipFile(path) as archive:
        predictions = {
            input_name: json.loads(archive.read(output_name).decode("utf-8"))
            for input_name, output_name in zip(INPUT_NAMES, OUTPUT_NAMES, strict=True)
        }
    return predictions, preflight


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("input.zip"))
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--model-proposals", type=Path, required=True)
    parser.add_argument(
        "--rxnorm",
        type=Path,
        default=Path("ontologies/rxnorm/RxNorm_full_prescribe_07062026.zip"),
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--icd", type=Path, default=DEFAULT_ICD10_PATH)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-md5", default=PUBLISHED_RXNORM_MD5)
    parser.add_argument("--expected-icd-sha256", default=PINNED_ICD10_SHA256)
    args = parser.parse_args()
    report = augment_submission(
        args.input,
        args.parent,
        args.model_proposals,
        args.rxnorm,
        args.config,
        args.output,
        args.icd,
        args.expected_md5,
        args.expected_icd_sha256,
    )
    with args.report.open("x", encoding="utf-8") as output:
        json.dump(report, output, ensure_ascii=False, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
