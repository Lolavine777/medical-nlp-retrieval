import json
from collections.abc import Mapping, Sequence

from medical_race.offsets import validate_entity_offset


DEFAULT_SCHEMAS = {
    "THUỐC": ("text", "type", "candidates", "assertions", "position"),
    "CHẨN_ĐOÁN": ("text", "type", "candidates", "assertions", "position"),
    "TRIỆU_CHỨNG": ("text", "type", "assertions", "position"),
    "TÊN_XÉT_NGHIỆM": ("text", "type", "position"),
    "KẾT_QUẢ_XÉT_NGHIỆM": ("text", "type", "position"),
}
KNOWN_FIELDS = {"text", "type", "candidates", "assertions", "position"}
KNOWN_ASSERTIONS = {"isNegated", "isFamily", "isHistorical"}


def validate_entities(
    raw_text: str,
    entities: object,
    schemas: Mapping[str, Sequence[str]] = DEFAULT_SCHEMAS,
) -> None:
    if not isinstance(entities, list):
        raise ValueError("entities must be a list")
    _validate_schemas(schemas)
    for index, entity in enumerate(entities):
        try:
            _validate_entity(raw_text, entity, schemas)
        except ValueError as error:
            raise ValueError(f"entity {index}: {error}") from error


def serialize_entities(
    raw_text: str,
    entities: object,
    schemas: Mapping[str, Sequence[str]] = DEFAULT_SCHEMAS,
) -> str:
    validate_entities(raw_text, entities, schemas)
    ordered = [
        {field: entity[field] for field in schemas[entity["type"]]}
        for entity in entities
    ]
    return json.dumps(ordered, ensure_ascii=False, separators=(",", ":")) + "\n"


def _validate_schemas(schemas: Mapping[str, Sequence[str]]) -> None:
    for entity_type, fields in schemas.items():
        field_set = set(fields)
        if not {"text", "type", "position"} <= field_set or not field_set <= KNOWN_FIELDS:
            raise ValueError(f"invalid schema for {entity_type}")
        if len(fields) != len(field_set):
            raise ValueError(f"duplicate schema field for {entity_type}")


def _validate_entity(
    raw_text: str,
    entity: object,
    schemas: Mapping[str, Sequence[str]],
) -> None:
    if not isinstance(entity, Mapping):
        raise ValueError("must be an object")
    entity_type = entity.get("type")
    if not isinstance(entity_type, str) or entity_type not in schemas:
        raise ValueError(f"unknown type: {entity_type!r}")
    expected = set(schemas[entity_type])
    actual = set(entity)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise ValueError(f"missing fields: {sorted(missing)}")
    if extra:
        raise ValueError(f"extra fields: {sorted(extra)}")
    if not isinstance(entity["text"], str) or not entity["text"]:
        raise ValueError("text must be a non-empty string")
    position = entity["position"]
    if (
        not isinstance(position, list)
        or len(position) != 2
        or any(type(value) is not int for value in position)
    ):
        raise ValueError("position must be a two-integer list")
    validate_entity_offset(raw_text, entity)
    if "assertions" in expected:
        _validate_string_list(entity["assertions"], "assertions", allow_empty=True)
        if not set(entity["assertions"]) <= KNOWN_ASSERTIONS:
            raise ValueError("assertions contain an unknown value")
    if "candidates" in expected:
        _validate_string_list(entity["candidates"], "candidates", allow_empty=False)


def _validate_string_list(value: object, name: str, allow_empty: bool) -> None:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError(f"{name} must contain unique non-empty strings")
