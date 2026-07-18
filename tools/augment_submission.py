import json
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from medical_race.linking.icd10 import build_term_index, read_icd10_snapshot
from medical_race.linking.rxnorm import read_rxnorm_archive
from medical_race.model_proposals import (
    accept_model_proposals,
    read_proposal_directory,
)
from medical_race.pipeline import load_submission_config
from medical_race.submission import (
    INPUT_NAMES,
    OUTPUT_NAMES,
    build_output_zip,
    validate_output_zip,
)
from medical_race.submission_diff import diff_submission_archives
from tools.audit_sources import read_zip_documents, validate_document_names
from tools.build_submission import (
    DEFAULT_ICD10_PATH,
    PINNED_ICD10_SHA256,
    PUBLISHED_RXNORM_MD5,
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
        result = accept_model_proposals(
            raw_text,
            proposals[name],
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

    return {
        "model_added_entity_count": model_report["accepted"],
        "model_rejections": {
            key: value for key, value in model_report.items() if key != "accepted"
        },
        "diff": {key: value for key, value in diff.items() if key != "details"},
    }


def _read_parent_predictions(path, documents):
    preflight = validate_output_zip(path, documents)
    with zipfile.ZipFile(path) as archive:
        predictions = {
            input_name: json.loads(archive.read(output_name).decode("utf-8"))
            for input_name, output_name in zip(INPUT_NAMES, OUTPUT_NAMES, strict=True)
        }
    return predictions, preflight
