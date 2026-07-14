import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from medical_race.assertions import classify_assertions
from medical_race.extraction import Span
from medical_race.extraction.labs import NUMERIC, QUALITATIVE
from medical_race.extraction.symptoms import (
    CURRENT_HEADINGS,
    LEADING_CUE,
    NORMAL_STATE,
    REJECT_PREFIXES,
)
from medical_race.line_roles import parse_line_roles
from medical_race.linking.icd10 import ICD10Term, is_diagnosis_code, link_diagnosis
from medical_race.linking.rxnorm import RxNormTerm, link_drug


ALLOWED_TYPES = frozenset(
    {
        "TRIỆU_CHỨNG",
        "TÊN_XÉT_NGHIỆM",
        "KẾT_QUẢ_XÉT_NGHIỆM",
        "CHẨN_ĐOÁN",
        "THUỐC",
    }
)
TYPE_SECTIONS = {
    "TRIỆU_CHỨNG": {
        "unsectioned",
        "current_illness",
        "symptoms",
        "admission_reason",
        "course",
        "exam",
        "assessment",
    },
    "TÊN_XÉT_NGHIỆM": {"laboratory", "assessment"},
    "KẾT_QUẢ_XÉT_NGHIỆM": {"laboratory", "assessment"},
    "CHẨN_ĐOÁN": {"past_history", "diagnosis", "imaging", "assessment"},
    "THUỐC": {"medications", "course", "assessment"},
}
MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
MODEL_REVISION = "1b4199c4f36b0cef378bfb12390c18780c18af4c"
MODEL_PARAMETERS = 4_000_000_000
PROMPT_VERSION = 1
PROMPT_HEADER = """Extract clinical mentions from the supplied raw lines.
Return only a JSON array.
Each object must contain exactly line_index, text, and type.
Copy text verbatim from one supplied line.
Use only these types: CHẨN_ĐOÁN, KẾT_QUẢ_XÉT_NGHIỆM, THUỐC, TRIỆU_CHỨNG, TÊN_XÉT_NGHIỆM.
Include every genuine mention occurrence and no headings or metadata.
Lines are formatted as line_index, section, role, and raw text separated by tabs.
"""


@dataclass(frozen=True, slots=True)
class ModelProposal:
    line_index: int
    text: str
    entity_type: str


@dataclass(frozen=True, slots=True)
class PromptChunk:
    line_indices: tuple[int, ...]
    prompt: str


@dataclass(frozen=True, slots=True)
class GroundedProposal:
    span: Span
    entity_type: str
    section: str
    role: str


@dataclass(frozen=True, slots=True)
class ModelMergeResult:
    entities: tuple[dict[str, object], ...]
    rejected: dict[str, int]


def parse_model_response(value: str) -> tuple[ModelProposal, ...]:
    if not isinstance(value, str):
        raise ValueError("model response must be a string")
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError("model response must be strict JSON") from error
    if not isinstance(payload, list):
        raise ValueError("model response must be a JSON array")

    proposals = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict) or set(item) != {"line_index", "text", "type"}:
            raise ValueError(f"proposal {index} must contain exactly line_index, text, and type")
        line_index = item["line_index"]
        text = item["text"]
        entity_type = item["type"]
        if type(line_index) is not int or line_index < 0:
            raise ValueError(f"proposal {index} line_index must be a nonnegative integer")
        if not isinstance(text, str) or not text:
            raise ValueError(f"proposal {index} text must be a non-empty string")
        if not isinstance(entity_type, str) or entity_type not in ALLOWED_TYPES:
            raise ValueError(f"proposal {index} has unknown type: {entity_type!r}")
        proposals.append(ModelProposal(line_index, text, entity_type))
    return tuple(proposals)


def prompt_chunks(raw_text: str, max_chars: int = 6000) -> tuple[PromptChunk, ...]:
    if not isinstance(raw_text, str):
        raise TypeError("raw_text must be a string")
    if type(max_chars) is not int or max_chars <= 0:
        raise ValueError("max_chars must be a positive integer")

    lines = parse_line_roles(raw_text)
    groups: list[list[tuple[int, object]]] = []
    current: list[tuple[int, object]] = []
    current_chars = 0
    for index, line in enumerate(lines):
        if line.role == "blank":
            continue
        line_chars = len(line.text) + 1
        if current and current_chars + line_chars > max_chars:
            groups.append(current)
            current = []
            current_chars = 0
        current.append((index, line))
        current_chars += line_chars
    if current:
        groups.append(current)

    return tuple(
        PromptChunk(
            tuple(index for index, _ in group),
            PROMPT_HEADER
            + "\n"
            + "\n".join(
                f"{index}\t{line.section}\t{line.role}\t{line.text}"
                for index, line in group
            ),
        )
        for group in groups
    )


def ground_proposals(
    raw_text: str,
    proposals: tuple[ModelProposal, ...],
) -> tuple[GroundedProposal, ...]:
    lines = parse_line_roles(raw_text)
    grounded = []
    for proposal in proposals:
        if not isinstance(proposal, ModelProposal):
            raise ValueError("proposals must contain ModelProposal values")
        if proposal.line_index >= len(lines):
            raise ValueError(f"invalid line_index: {proposal.line_index}")
        line = lines[proposal.line_index]
        cursor = 0
        found_any = False
        while True:
            relative_start = line.text.find(proposal.text, cursor)
            if relative_start < 0:
                break
            found_any = True
            start = line.start + relative_start
            end = start + len(proposal.text)
            grounded.append(
                GroundedProposal(
                    Span(raw_text[start:end], start, end),
                    proposal.entity_type,
                    line.section,
                    line.role,
                )
            )
            cursor = relative_start + len(proposal.text)
        if not found_any:
            raise ValueError(
                f"proposal text not found verbatim on line {proposal.line_index}: "
                f"{proposal.text!r}"
            )
    return tuple(
        sorted(
            grounded,
            key=lambda value: (
                value.span.start,
                value.span.end,
                value.entity_type,
            ),
        )
    )


def accept_model_proposals(
    raw_text: str,
    proposals: tuple[ModelProposal, ...],
    stable_entities: list[dict[str, object]],
    terms: tuple[RxNormTerm, ...],
    icd_index: dict[str, ICD10Term],
    concept_level: str,
    candidate_output: str,
) -> ModelMergeResult:
    rejected = Counter()
    grounded = []
    for proposal in proposals:
        try:
            grounded.extend(ground_proposals(raw_text, (proposal,)))
        except ValueError:
            rejected["not_grounded"] += 1

    stable_spans = [tuple(entity["position"]) for entity in stable_entities]
    filtered = {}
    for value in grounded:
        if value.role in {"header", "blank"} or value.section not in TYPE_SECTIONS[value.entity_type]:
            rejected["invalid_section"] += 1
            continue
        if not _valid_model_structure(value):
            rejected["invalid_structure"] += 1
            continue
        if any(_overlaps(value.span.start, value.span.end, start, end) for start, end in stable_spans):
            rejected["stable_overlap"] += 1
            continue
        filtered[(value.span.start, value.span.end, value.entity_type)] = value

    by_span = defaultdict(list)
    for value in filtered.values():
        by_span[(value.span.start, value.span.end)].append(value)
    unambiguous = []
    for values in by_span.values():
        if len({value.entity_type for value in values}) > 1:
            rejected["ambiguous_type"] += len(values)
        else:
            unambiguous.extend(values)

    selected = []
    for value in sorted(
        unambiguous,
        key=lambda item: (-(item.span.end - item.span.start), item.span.start, item.entity_type),
    ):
        if any(_overlaps(value.span.start, value.span.end, other.span.start, other.span.end) for other in selected):
            rejected["model_overlap"] += 1
            continue
        selected.append(value)

    entities = []
    for value in sorted(selected, key=lambda item: (item.span.start, item.span.end, item.entity_type)):
        entity = _build_entity(
            raw_text,
            value,
            terms,
            icd_index,
            concept_level,
            candidate_output,
        )
        if entity is None:
            rejected["unlinked_candidate"] += 1
            continue
        entities.append(entity)
        rejected["accepted"] += 1
    return ModelMergeResult(tuple(entities), dict(sorted(rejected.items())))


def _valid_model_structure(value: GroundedProposal) -> bool:
    text = value.span.text
    folded = " ".join(text.casefold().split())
    words = len(text.split())
    if (
        text != text.strip(" \t")
        or text.lstrip().startswith(("-", "*"))
        or text.rstrip().endswith((".", ";"))
    ):
        return False
    if value.entity_type == "TRIỆU_CHỨNG":
        return (
            words <= 8
            and len(text) <= 60
            and not any(mark in text for mark in ":;,")
            and folded not in CURRENT_HEADINGS
            and not folded.startswith("các triệu chứng")
            and not folded.startswith(REJECT_PREFIXES)
            and LEADING_CUE.match(text) is None
            and NORMAL_STATE.search(text) is None
        )
    if value.entity_type == "KẾT_QUẢ_XÉT_NGHIỆM":
        return (
            words <= 5
            and len(text) <= 40
            and ":" not in text
            and (NUMERIC.search(text) is not None or QUALITATIVE.search(text) is not None)
        )
    if value.entity_type == "TÊN_XÉT_NGHIỆM":
        return words <= 6 and len(text) <= 40 and ":" not in text
    if value.entity_type == "THUỐC":
        return (
            words <= 8
            and len(text) <= 60
            and ":" not in text
            and not folded.startswith(("được ", "đã ", "tự "))
        )
    return True


def _build_entity(
    raw_text: str,
    value: GroundedProposal,
    terms: tuple[RxNormTerm, ...],
    icd_index: dict[str, ICD10Term],
    concept_level: str,
    candidate_output: str,
) -> dict[str, object] | None:
    span = value.span
    entity = {
        "text": span.text,
        "type": value.entity_type,
        "position": [span.start, span.end],
    }
    if value.entity_type == "CHẨN_ĐOÁN":
        link = link_diagnosis(span.text, icd_index)
        if link is None or not is_diagnosis_code(link.code):
            return None
        entity["candidates"] = [link.code]
        entity["assertions"] = list(classify_assertions(raw_text, span).labels())
    elif value.entity_type == "THUỐC":
        link = link_drug(span.text, terms, concept_level, candidate_output)
        if link is None:
            return None
        entity["candidates"] = list(link.candidates)
        entity["assertions"] = list(classify_assertions(raw_text, span).labels())
    elif value.entity_type == "TRIỆU_CHỨNG":
        entity["assertions"] = list(classify_assertions(raw_text, span).labels())
    return entity


def _overlaps(left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
    return left_start < right_end and right_start < left_end


MANIFEST_FIELDS = frozenset(
    {
        "format_version",
        "model_id",
        "model_revision",
        "model_parameters",
        "prompt_version",
        "prompt_sha256",
        "generation",
    }
)
DOCUMENT_FIELDS = frozenset(
    {"name", "raw_sha256", "chunk_count", "parse_error_count", "proposals"}
)
GENERATION_CONFIG = {"do_sample": False, "max_new_tokens": 2048}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def prompt_sha256() -> str:
    return hashlib.sha256(PROMPT_HEADER.encode("utf-8")).hexdigest()


def read_proposal_manifest(root: Path) -> dict[str, object]:
    manifest = _read_json_object(Path(root) / "manifest.json", "manifest")
    if set(manifest) != MANIFEST_FIELDS:
        raise ValueError("invalid proposal manifest fields")
    if (
        type(manifest["format_version"]) is not int
        or manifest["format_version"] != 1
    ):
        raise ValueError("unsupported proposal format version")
    if manifest["model_id"] != MODEL_ID:
        raise ValueError("unexpected model ID")
    if manifest["model_revision"] != MODEL_REVISION:
        raise ValueError("unexpected model revision")
    if (
        type(manifest["model_parameters"]) is not int
        or manifest["model_parameters"] != MODEL_PARAMETERS
    ):
        raise ValueError("unexpected model parameter count")
    if (
        type(manifest["prompt_version"]) is not int
        or manifest["prompt_version"] != PROMPT_VERSION
    ):
        raise ValueError("unexpected prompt version")
    prompt_hash = manifest["prompt_sha256"]
    if (
        not isinstance(prompt_hash, str)
        or SHA256_PATTERN.fullmatch(prompt_hash) is None
        or prompt_hash != prompt_sha256()
    ):
        raise ValueError("unexpected prompt SHA-256")
    generation = manifest["generation"]
    if (
        not isinstance(generation, dict)
        or set(generation) != set(GENERATION_CONFIG)
        or generation["do_sample"] is not False
        or type(generation["max_new_tokens"]) is not int
        or generation["max_new_tokens"] != GENERATION_CONFIG["max_new_tokens"]
    ):
        raise ValueError("unexpected generation configuration")
    return manifest


def read_proposal_directory(
    root: Path,
    documents: Mapping[str, str],
) -> dict[str, tuple[ModelProposal, ...]]:
    root = Path(root)
    read_proposal_manifest(root)
    document_root = root / "documents"
    expected_files = {f"{Path(name).stem}.json" for name in documents}
    actual_files = (
        {path.name for path in document_root.glob("*.json")}
        if document_root.is_dir()
        else set()
    )
    if actual_files != expected_files:
        raise ValueError("proposal document files do not match expected documents")

    output = {}
    for name, raw_text in documents.items():
        if not isinstance(name, str) or not isinstance(raw_text, str):
            raise ValueError("documents must map names to raw text")
        record = _read_json_object(
            document_root / f"{Path(name).stem}.json",
            f"proposal document {name}",
        )
        if set(record) != DOCUMENT_FIELDS:
            raise ValueError(f"invalid proposal document fields: {name}")
        if record["name"] != name:
            raise ValueError(f"proposal document name mismatch: {name}")
        expected_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        if record["raw_sha256"] != expected_hash:
            raise ValueError(f"input SHA-256 mismatch: {name}")
        chunk_count = record["chunk_count"]
        parse_error_count = record["parse_error_count"]
        if type(chunk_count) is not int or chunk_count < 0:
            raise ValueError(f"invalid chunk count: {name}")
        if (
            type(parse_error_count) is not int
            or parse_error_count < 0
            or parse_error_count > chunk_count
        ):
            raise ValueError(f"invalid parse error count: {name}")
        try:
            serialized = json.dumps(record["proposals"], ensure_ascii=False)
            proposals = parse_model_response(serialized)
            ground_proposals(raw_text, proposals)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid proposals: {name}") from error
        ordered = tuple(
            sorted(
                proposals,
                key=lambda value: (value.line_index, value.text, value.entity_type),
            )
        )
        if proposals != ordered:
            raise ValueError(f"proposals are not in deterministic order: {name}")
        output[name] = proposals
    return output


def _read_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid {label}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value
