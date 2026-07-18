import argparse
import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path

from medical_race.model_proposals import (
    ModelProposal,
    PROMPT_ALLOWED_TYPES,
    parse_model_response,
    prompt_chunks,
    read_proposal_directory,
    salvage_model_response,
)
from tools.audit_sources import read_zip_documents, validate_document_names


def replay_proposals(
    input_zip: Path,
    proposal_zip: Path,
    diagnostics_zip: Path,
    output: Path,
) -> dict[str, object]:
    documents = read_zip_documents(Path(input_zip))
    validate_document_names(list(documents))
    manifest, records = _read_proposal_archive(Path(proposal_zip))
    prompt_version = manifest["prompt_version"]
    allowed_types = PROMPT_ALLOWED_TYPES[prompt_version]
    if set(records) != set(documents):
        raise ValueError("proposal archive documents do not match input")

    proposals_by_document = {}
    for name, record in records.items():
        proposals_by_document[name] = set(
            _parse_record_proposals(record, allowed_types)
        )

    recovered = 0
    rejected = 0
    diagnostics_count = 0
    with zipfile.ZipFile(diagnostics_zip) as archive:
        for member in archive.namelist():
            if not member.endswith(".json"):
                continue
            diagnostic = json.loads(archive.read(member))
            diagnostics_count += len(diagnostic["failures"])
            name = diagnostic["name"]
            if name not in documents:
                raise ValueError(f"diagnostic references unknown document: {name}")
            for failure in diagnostic["failures"]:
                if failure["document"] != name:
                    raise ValueError("diagnostic document fields differ")
                if failure["prompt_version"] != prompt_version:
                    raise ValueError("diagnostic prompt versions differ")
                response = failure["raw_response"]
                try:
                    payload = json.loads(response)
                    item_count = len(payload) if isinstance(payload, list) else 1
                except (TypeError, json.JSONDecodeError):
                    item_count = 1
                chunks = prompt_chunks(documents[name], 2500, prompt_version)
                chunk_index = failure["chunk_index"]
                if chunk_index >= len(chunks):
                    raise ValueError(f"diagnostic chunk index is invalid: {name}")
                accepted, _ = salvage_model_response(
                    documents[name],
                    response,
                    frozenset(chunks[chunk_index].line_indices),
                    allowed_types,
                )
                rejected += max(0, item_count - len(accepted))
                existing = proposals_by_document[name]
                new_proposals = set(accepted) - existing
                recovered += len(new_proposals)
                existing.update(new_proposals)

    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    (output / "documents").mkdir(parents=True)
    _write_json(output / "manifest.json", manifest)
    for name, record in records.items():
        proposals = sorted(
            proposals_by_document[name],
            key=lambda value: (value.line_index, value.text, value.entity_type),
        )
        record = dict(record)
        record["proposals"] = [_proposal_json(value) for value in proposals]
        _write_json(output / "documents" / f"{Path(name).stem}.json", record)

    validated = read_proposal_directory(output, documents)
    type_counts = Counter(
        proposal.entity_type
        for values in validated.values()
        for proposal in values
    )
    return {
        "documents": len(validated),
        "diagnostic_failures": diagnostics_count,
        "original_proposals": sum(
            len(_parse_record_proposals(record, allowed_types))
            for record in records.values()
        ),
        "recovered": recovered,
        "rejected": rejected,
        "proposals": sum(len(values) for values in validated.values()),
        "type_counts": dict(sorted(type_counts.items())),
    }


def _read_proposal_archive(
    path: Path,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    with zipfile.ZipFile(path) as archive:
        manifest_names = [name for name in archive.namelist() if name.endswith("/manifest.json")]
        if len(manifest_names) != 1:
            raise ValueError("proposal archive must contain one manifest")
        manifest = json.loads(archive.read(manifest_names[0]))
        records = {}
        for name in archive.namelist():
            if "/documents/" not in name or not name.endswith(".json"):
                continue
            record = json.loads(archive.read(name))
            document_name = record.get("name")
            if not isinstance(document_name, str) or document_name in records:
                raise ValueError("proposal archive has invalid document records")
            records[document_name] = record
    return manifest, records


def _parse_record_proposals(
    record: dict[str, object],
    allowed_types: frozenset[str],
) -> tuple[ModelProposal, ...]:
    serialized = json.dumps(record["proposals"], ensure_ascii=False)
    return parse_model_response(serialized, allowed_types)


def _proposal_json(value: ModelProposal) -> dict[str, object]:
    return {
        "line_index": value.line_index,
        "text": value.text,
        "type": value.entity_type,
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--proposals", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            replay_proposals(args.input, args.proposals, args.diagnostics, args.output),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
