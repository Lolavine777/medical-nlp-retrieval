import json
from dataclasses import dataclass

from medical_race.extraction import Span
from medical_race.line_roles import parse_line_roles


ALLOWED_TYPES = frozenset(
    {
        "TRIỆU_CHỨNG",
        "TÊN_XÉT_NGHIỆM",
        "KẾT_QUẢ_XÉT_NGHIỆM",
        "CHẨN_ĐOÁN",
        "THUỐC",
    }
)
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
