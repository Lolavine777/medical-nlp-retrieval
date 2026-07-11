from collections.abc import Mapping


def validate_entity_offset(raw_text: str, entity: Mapping[str, object]) -> None:
    position = entity.get("position")
    text = entity.get("text")
    if (
        not isinstance(position, list)
        or len(position) != 2
        or not all(isinstance(value, int) for value in position)
        or not isinstance(text, str)
    ):
        raise ValueError("entity requires text and a two-integer position")
    start, end = position
    if start < 0 or end < start or end > len(raw_text):
        raise ValueError(f"invalid position: {position}")
    if raw_text[start:end] != text:
        raise ValueError(
            f"offset mismatch at {position}: {raw_text[start:end]!r} != {text!r}"
        )
