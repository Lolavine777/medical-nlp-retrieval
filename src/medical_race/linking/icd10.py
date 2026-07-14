import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True, slots=True)
class ICD10Term:
    code: str
    name: str
    model: str
    is_leaf: bool


def read_icd10_snapshot(path: Path, expected_sha256: str) -> tuple[ICD10Term, ...]:
    data = Path(path).read_bytes()
    actual_sha256 = hashlib.sha256(data).hexdigest()
    if actual_sha256.casefold() != expected_sha256.casefold():
        raise ValueError(f"ICD-10 snapshot SHA-256 mismatch: {actual_sha256}")
    try:
        payload = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid ICD-10 snapshot JSON") from error
    if (
        not isinstance(payload, dict)
        or set(payload) != {"format_version", "source_api", "language", "nodes"}
        or payload["format_version"] != 1
        or not isinstance(payload["source_api"], str)
        or not payload["source_api"]
        or not isinstance(payload["language"], str)
        or not payload["language"]
        or not isinstance(payload["nodes"], list)
    ):
        raise ValueError("invalid ICD-10 snapshot schema")

    terms = []
    identities = set()
    for value in payload["nodes"]:
        term = _parse_term(value)
        identity = value["model"], value["id"]
        if identity in identities:
            raise ValueError(f"duplicate ICD-10 node identity: {identity!r}")
        identities.add(identity)
        terms.append(term)
    return tuple(sorted(terms, key=lambda term: (term.code, term.model, term.name)))


def normalize_icd_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    folded = unicodedata.normalize("NFC", text).casefold()
    return " ".join(TOKEN.findall(folded))


def build_term_index(terms: tuple[ICD10Term, ...]) -> dict[str, ICD10Term]:
    leaf_codes = {term.code for term in terms if term.is_leaf}
    grouped = defaultdict(list)
    for term in terms:
        if term.code not in leaf_codes:
            continue
        normalized = normalize_icd_text(term.name)
        if normalized:
            grouped[normalized].append(term)

    index = {}
    for normalized, values in grouped.items():
        leaves = [term for term in values if term.is_leaf]
        preferred = leaves or values
        by_code = {term.code: term for term in preferred}
        if len(by_code) == 1:
            index[normalized] = next(iter(by_code.values()))
    return index


def link_diagnosis(text: str, index: dict[str, ICD10Term]) -> ICD10Term | None:
    return index.get(normalize_icd_text(text))


def _parse_term(value: object) -> ICD10Term:
    if not isinstance(value, dict) or set(value) != {
        "model",
        "id",
        "code",
        "name",
        "is_leaf",
        "parent",
    }:
        raise ValueError("invalid ICD-10 node schema")
    model = value["model"]
    node_id = value["id"]
    code = value["code"]
    name = value["name"]
    is_leaf = value["is_leaf"]
    parent = value["parent"]
    if (
        not isinstance(model, str)
        or not model
        or not isinstance(node_id, str)
        or not node_id
        or not isinstance(code, str)
        or not code
        or not isinstance(name, str)
        or not name
        or type(is_leaf) is not bool
        or not _valid_parent(parent)
    ):
        raise ValueError("invalid ICD-10 node")
    return ICD10Term(code, name, model, is_leaf)


def _valid_parent(parent: object) -> bool:
    return parent is None or (
        isinstance(parent, dict)
        and set(parent) == {"model", "id"}
        and all(isinstance(parent[field], str) and parent[field] for field in parent)
    )
