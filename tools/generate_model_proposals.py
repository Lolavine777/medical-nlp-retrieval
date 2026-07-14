import argparse
import hashlib
import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path

from medical_race.model_proposals import (
    GENERATION_CONFIG,
    MODEL_ID,
    MODEL_PARAMETERS,
    MODEL_REVISION,
    PROMPT_VERSION,
    ModelProposal,
    ground_proposals,
    parse_model_response,
    prompt_chunks,
    prompt_sha256,
    read_proposal_directory,
)
from tools.audit_sources import read_zip_documents, validate_document_names


def select_document_shard(
    documents: Mapping[str, str],
    shard_index: int,
    shard_count: int,
) -> dict[str, str]:
    if shard_count < 1:
        raise ValueError("shard count must be positive")
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError("shard index must be between zero and shard count minus one")
    try:
        return {
            name: raw_text
            for name, raw_text in documents.items()
            if (int(Path(name).stem) - 1) % shard_count == shard_index
        }
    except ValueError as error:
        raise ValueError("document names must have numeric stems") from error


def generate_document(
    raw_text: str,
    generate: Callable[[str], str],
    max_chars: int = 6000,
) -> dict[str, object]:
    chunks = prompt_chunks(raw_text, max_chars)
    proposals = []
    parse_error_count = 0
    for chunk in chunks:
        try:
            parsed = parse_model_response(generate(chunk.prompt))
            if any(value.line_index not in chunk.line_indices for value in parsed):
                raise ValueError("proposal refers outside its prompt chunk")
            ground_proposals(raw_text, parsed)
        except (TypeError, ValueError):
            parse_error_count += 1
            continue
        proposals.extend(parsed)
    proposals.sort(key=lambda value: (value.line_index, value.text, value.entity_type))
    return {
        "chunk_count": len(chunks),
        "parse_error_count": parse_error_count,
        "proposals": [_proposal_json(value) for value in proposals],
    }


def generate_proposal_directory(
    documents: Mapping[str, str],
    output: Path,
    generate: Callable[[str], str],
    max_chars: int = 6000,
) -> None:
    output = Path(output)
    document_root = output / "documents"
    document_root.mkdir(parents=True, exist_ok=True)
    expected_manifest = _manifest()
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        try:
            current_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("existing proposal manifest is invalid") from error
        if current_manifest != expected_manifest:
            raise ValueError("existing proposal manifest does not match this generator")
    else:
        _write_json_atomic(manifest_path, expected_manifest)

    for name, raw_text in documents.items():
        path = document_root / f"{Path(name).stem}.json"
        if _is_complete(path, name, raw_text, max_chars):
            continue
        record = {
            "name": name,
            "raw_sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
            **generate_document(raw_text, generate, max_chars),
        }
        _write_json_atomic(path, record)
    read_proposal_directory(output, documents)


def _manifest() -> dict[str, object]:
    return {
        "format_version": 1,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_parameters": MODEL_PARAMETERS,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": prompt_sha256(),
        "generation": dict(GENERATION_CONFIG),
    }


def _proposal_json(value: ModelProposal) -> dict[str, object]:
    return {
        "line_index": value.line_index,
        "text": value.text,
        "type": value.entity_type,
    }


def _is_complete(path: Path, name: str, raw_text: str, max_chars: int) -> bool:
    if not path.is_file():
        return False
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        expected_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        if (
            not isinstance(record, dict)
            or record.get("name") != name
            or record.get("raw_sha256") != expected_hash
            or record.get("chunk_count") != len(prompt_chunks(raw_text, max_chars))
        ):
            return False
        serialized = json.dumps(record.get("proposals"), ensure_ascii=False)
        proposals = parse_model_response(serialized)
        ground_proposals(raw_text, proposals)
        return (
            set(record)
            == {"name", "raw_sha256", "chunk_count", "parse_error_count", "proposals"}
            and type(record.get("parse_error_count")) is int
            and 0 <= record["parse_error_count"] <= record["chunk_count"]
            and proposals
            == tuple(
                sorted(
                    proposals,
                    key=lambda value: (value.line_index, value.text, value.entity_type),
                )
            )
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return False


def _write_json_atomic(path: Path, value: object) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _load_generator(model_path: Path | None) -> Callable[[str], str]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    source = str(model_path) if model_path is not None else MODEL_ID
    load_options = (
        {"local_files_only": True}
        if model_path is not None
        else {"revision": MODEL_REVISION}
    )
    tokenizer = AutoTokenizer.from_pretrained(source, **load_options)
    model = AutoModelForCausalLM.from_pretrained(
        source,
        torch_dtype=torch.float16,
        device_map="cuda",
        **load_options,
    )

    def generate(prompt: str) -> str:
        encoded = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
        encoded = {key: value.to(model.device) for key, value in encoded.items()}
        output = model.generate(
            **encoded,
            do_sample=GENERATION_CONFIG["do_sample"],
            max_new_tokens=GENERATION_CONFIG["max_new_tokens"],
        )
        new_tokens = output[0, encoded["input_ids"].shape[1] :]
        return tokenizer.decode(new_tokens, skip_special_tokens=True)

    return generate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("input.zip"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/model_proposals/qwen3-4b-s008"),
    )
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--max-chars", type=int, default=6000)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    args = parser.parse_args()

    print(json.dumps(_manifest(), sort_keys=True))
    documents = read_zip_documents(args.input)
    validate_document_names(list(documents))
    documents = select_document_shard(documents, args.shard_index, args.shard_count)
    generate_proposal_directory(
        documents,
        args.output,
        _load_generator(args.model_path),
        args.max_chars,
    )


if __name__ == "__main__":
    main()
