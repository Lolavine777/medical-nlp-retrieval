import hashlib
import json
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path

from medical_race.output import DEFAULT_SCHEMAS, serialize_entities, validate_entities


INPUT_NAMES = tuple(f"input/{i}.txt" for i in range(1, 101))
OUTPUT_NAMES = tuple(f"output/{i}.json" for i in range(1, 101))
FIXED_DATE = (1980, 1, 1, 0, 0, 0)


def build_output_zip(
    documents: Mapping[str, str],
    predictions: Mapping[str, object],
    destination: Path,
    schemas: Mapping[str, Sequence[str]] = DEFAULT_SCHEMAS,
) -> dict[str, object]:
    _validate_keys("document", documents)
    _validate_keys("prediction", predictions)
    destination = Path(destination)
    if not destination.parent.is_dir():
        raise ValueError(f"destination parent does not exist: {destination.parent}")
    if destination.exists():
        raise FileExistsError(destination)

    payloads = []
    entity_count = 0
    empty_count = 0
    for input_name, output_name in zip(INPUT_NAMES, OUTPUT_NAMES, strict=True):
        raw_text = documents[input_name]
        if not isinstance(raw_text, str):
            raise ValueError(f"document {input_name} must be text")
        entities = predictions[input_name]
        payloads.append(
            (
                output_name,
                serialize_entities(raw_text, entities, schemas).encode("utf-8"),
            )
        )
        entity_count += len(entities)
        empty_count += not entities

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in payloads:
            info = zipfile.ZipInfo(name, FIXED_DATE)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100600 << 16
            archive.writestr(info, payload)
    data = buffer.getvalue()
    _verify_archive(data, documents, schemas)
    with destination.open("xb") as stream:
        stream.write(data)
    return {
        "entry_count": len(payloads),
        "entity_count": entity_count,
        "empty_document_count": empty_count,
        "byte_count": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _validate_keys(label: str, values: object) -> None:
    if not isinstance(values, Mapping):
        raise ValueError(f"{label} values must be a mapping")
    actual = set(values)
    expected = set(INPUT_NAMES)
    if actual != expected:
        missing = [name for name in INPUT_NAMES if name not in actual]
        extra = sorted(repr(name) for name in actual if name not in expected)
        raise ValueError(f"{label} keys mismatch; missing={missing}; extra={extra}")


def _verify_archive(
    data: bytes,
    documents: Mapping[str, str],
    schemas: Mapping[str, Sequence[str]],
) -> None:
    _validate_output_bytes(data, documents, schemas)


def validate_output_zip(
    path: Path,
    documents: Mapping[str, str],
    schemas: Mapping[str, Sequence[str]] = DEFAULT_SCHEMAS,
) -> dict[str, object]:
    _validate_keys("document", documents)
    return _validate_output_bytes(Path(path).read_bytes(), documents, schemas)


def _validate_output_bytes(
    data: bytes,
    documents: Mapping[str, str],
    schemas: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = tuple(archive.namelist())
        if names != OUTPUT_NAMES:
            _raise_archive_shape_error(names)
        entities = []
        for input_name, output_name in zip(INPUT_NAMES, OUTPUT_NAMES, strict=True):
            try:
                values = json.loads(archive.read(output_name).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError(f"invalid UTF-8 JSON in {output_name}") from error
            validate_entities(documents[input_name], values, schemas)
            entities.extend(values)
    counts = Counter(entity["type"] for entity in entities)
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "entry_count": len(OUTPUT_NAMES),
        "entity_count": len(entities),
        "candidate_count": sum(len(entity.get("candidates", [])) for entity in entities),
        "assertion_count": sum(len(entity.get("assertions", [])) for entity in entities),
        "entity_counts": dict(sorted(counts.items())),
    }


def _raise_archive_shape_error(names: tuple[str, ...]) -> None:
    if any(
        name == "manifest.json"
        or name.endswith("/manifest.json")
        or name.startswith("documents/")
        or "/documents/" in name
        for name in names
    ):
        raise ValueError("intermediate model-proposal archive, not a leaderboard submission")
    prefixes = {name.split("/", 1)[0] for name in names if "/" in name}
    if len(prefixes) == 1 and next(iter(prefixes)) != "output":
        raise ValueError("submission is nested under a wrapper directory")
    raise ValueError("submission must contain exactly output/1.json through output/100.json")
