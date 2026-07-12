import json
import zipfile
from pathlib import Path

from medical_race.submission import OUTPUT_NAMES


IDENTITY_FIELDS = ("type", "text", "position")
COMPARED_FIELDS = ("type", "text", "position", "candidates", "assertions")


def diff_submission_archives(parent: Path, child: Path) -> dict[str, object]:
    parent_documents = _read_archive(Path(parent))
    child_documents = _read_archive(Path(child))
    counts = {
        "added_entities": 0,
        "removed_entities": 0,
        "changed_entities": 0,
        "changed_candidates": 0,
        "changed_assertions": 0,
        "changed_text": 0,
        "changed_type": 0,
        "changed_position": 0,
    }
    details = []
    for name in OUTPUT_NAMES:
        parent_entities = parent_documents[name]
        child_entities = child_documents[name]
        pairs, parent_left, child_left = _pair_exact(parent_entities, child_entities)
        overlap_pairs, parent_left, child_left = _pair_overlap(
            parent_entities, child_entities, parent_left, child_left
        )
        for parent_index, child_index in pairs + overlap_pairs:
            changed = [
                field
                for field in COMPARED_FIELDS
                if parent_entities[parent_index].get(field)
                != child_entities[child_index].get(field)
            ]
            if not changed:
                continue
            counts["changed_entities"] += 1
            for field in changed:
                counts[f"changed_{field}"] += 1
            details.append(
                {
                    "document": name,
                    "status": "changed",
                    "fields": changed,
                    "parent": parent_entities[parent_index],
                    "child": child_entities[child_index],
                }
            )
        for index in parent_left:
            counts["removed_entities"] += 1
            details.append(
                {"document": name, "status": "removed", "parent": parent_entities[index]}
            )
        for index in child_left:
            counts["added_entities"] += 1
            details.append(
                {"document": name, "status": "added", "child": child_entities[index]}
            )
    return {**counts, "details": details}


def _read_archive(path: Path) -> dict[str, list[dict[str, object]]]:
    with zipfile.ZipFile(path) as archive:
        if tuple(archive.namelist()) != OUTPUT_NAMES:
            raise ValueError("submission archive entry names mismatch")
        documents = {}
        for name in OUTPUT_NAMES:
            entities = json.loads(archive.read(name).decode("utf-8"))
            if not isinstance(entities, list) or any(
                not isinstance(entity, dict) for entity in entities
            ):
                raise ValueError(f"invalid entity list in {name}")
            documents[name] = entities
        return documents


def _pair_exact(parent, child):
    child_left = set(range(len(child)))
    pairs = []
    parent_left = []
    for parent_index, entity in enumerate(parent):
        identity = tuple(entity.get(field) for field in IDENTITY_FIELDS)
        child_index = next(
            (
                index
                for index in sorted(child_left)
                if tuple(child[index].get(field) for field in IDENTITY_FIELDS) == identity
            ),
            None,
        )
        if child_index is None:
            parent_left.append(parent_index)
        else:
            pairs.append((parent_index, child_index))
            child_left.remove(child_index)
    return pairs, parent_left, sorted(child_left)


def _pair_overlap(parent, child, parent_left, child_left):
    available = set(child_left)
    pairs = []
    remaining = []
    for parent_index in parent_left:
        parent_entity = parent[parent_index]
        child_index = next(
            (
                index
                for index in sorted(available)
                if child[index].get("type") == parent_entity.get("type")
                and _overlaps(parent_entity.get("position"), child[index].get("position"))
            ),
            None,
        )
        if child_index is None:
            remaining.append(parent_index)
        else:
            pairs.append((parent_index, child_index))
            available.remove(child_index)
    return pairs, remaining, sorted(available)


def _overlaps(left, right):
    return (
        isinstance(left, list)
        and isinstance(right, list)
        and len(left) == len(right) == 2
        and max(left[0], right[0]) < min(left[1], right[1])
    )
