import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from medical_race.model_proposals import (  # noqa: E402
    MODEL_ID,
    MODEL_REVISION,
    PROMPT_HEADERS,
    prompt_chunks,
    read_proposal_directory,
    read_proposal_manifest,
)

RUN_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def validate_run_name(value: str) -> str:
    if not isinstance(value, str) or RUN_NAME.fullmatch(value) is None:
        raise ValueError(
            "run name must contain only letters, numbers, dot, underscore, and hyphen"
        )
    return value
from tools.audit_sources import (  # noqa: E402
    read_zip_documents,
    validate_document_names,
)


def _directory_candidates(root: Path) -> list[Path]:
    candidates = []
    for first in root.rglob("1.txt"):
        directory = first.parent
        if all((directory / f"{index}.txt").is_file() for index in range(1, 101)):
            candidates.append(directory)
    return candidates


def _directory_signature(directory: Path) -> tuple[str, ...]:
    return tuple(
        hashlib.sha256((directory / f"{index}.txt").read_bytes()).hexdigest()
        for index in range(1, 101)
    )


def prepare_input_zip(input_root: Path, destination: Path) -> Path:
    input_root = Path(input_root)
    destination = Path(destination)
    valid_archives = []
    for candidate in sorted(input_root.rglob("input.zip")):
        try:
            documents = read_zip_documents(candidate)
            validate_document_names(list(documents))
        except (OSError, ValueError, zipfile.BadZipFile):
            continue
        valid_archives.append(candidate)
    if valid_archives:
        hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in valid_archives}
        if len(hashes) != 1:
            raise ValueError("ambiguous input.zip sources")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(valid_archives[0], destination)
        return destination

    candidates = _directory_candidates(input_root)
    signatures = {_directory_signature(directory) for directory in candidates}
    if not candidates:
        raise ValueError("no canonical input.zip or 100-document directory found")
    if len(signatures) != 1:
        raise ValueError("ambiguous 100-document input sources")
    source = candidates[0]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as archive:
        for index in range(1, 101):
            archive.write(source / f"{index}.txt", f"input/{index}.txt")
    documents = read_zip_documents(destination)
    validate_document_names(list(documents))
    return destination


def _worker_environment(index: int) -> dict[str, str]:
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = str(index)
    environment["PYTHONPATH"] = f"{PROJECT_ROOT / 'src'}:{PROJECT_ROOT}"
    return environment


def wait_for_workers(processes: Sequence[object]) -> tuple[int, ...]:
    return tuple(int(process.wait()) for process in processes)


def merge_shards(
    shards: Sequence[Path],
    final: Path,
    documents: Mapping[str, str],
    max_chars: int,
) -> dict[str, int]:
    if len(shards) != 2:
        raise ValueError("exactly two shards are required")
    validate_document_names(list(documents))
    final = Path(final)
    if final.exists():
        shutil.rmtree(final)
    document_root = final / "documents"
    document_root.mkdir(parents=True)
    manifests = []
    copied = set()
    for shard in shards:
        shard = Path(shard)
        manifest_path = shard / "manifest.json"
        manifests.append(read_proposal_manifest(shard))
        for source in (shard / "documents").glob("*.json"):
            if source.name in copied:
                raise ValueError(f"duplicate shard document: {source.name}")
            copied.add(source.name)
            shutil.copy2(source, document_root / source.name)
    if len({json.dumps(manifest, sort_keys=True) for manifest in manifests}) != 1:
        raise ValueError("shard manifests differ")
    manifest = manifests[0]
    shutil.copy2(Path(shards[0]) / "manifest.json", final / "manifest.json")
    proposals = read_proposal_directory(final, documents)
    records = [json.loads(path.read_text(encoding="utf-8")) for path in document_root.glob("*.json")]
    if any(
        record["chunk_count"]
        != len(
            prompt_chunks(
                documents[record["name"]],
                max_chars,
                manifest["prompt_version"],
            )
        )
        for record in records
    ):
        raise ValueError("shard record uses the wrong chunk size")
    return {
        "documents": len(proposals),
        "chunks": sum(record["chunk_count"] for record in records),
        "parse_errors": sum(record["parse_error_count"] for record in records),
        "proposals": sum(len(values) for values in proposals.values()),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(args: argparse.Namespace) -> dict[str, object]:
    run_name = validate_run_name(args.run_name)
    if type(args.prompt_version) is not int or args.prompt_version not in PROMPT_HEADERS:
        raise ValueError("unsupported prompt version")
    work_root = Path(args.work_root)
    input_zip = prepare_input_zip(Path(args.input_root), work_root / "input.zip")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")
    if args.model_path:
        model_path = Path(args.model_path)
    else:
        from huggingface_hub import snapshot_download

        model_path = Path(
            snapshot_download(MODEL_ID, revision=MODEL_REVISION, max_workers=1)
        )

    documents = read_zip_documents(input_zip)
    validate_document_names(list(documents))
    generator = PROJECT_ROOT / "tools" / "generate_model_proposals.py"
    base = [
        sys.executable,
        str(generator),
        "--input", str(input_zip),
        "--model-path", str(model_path),
        "--max-chars", str(args.max_chars),
        "--prompt-version", str(args.prompt_version),
        "--shard-count", "2",
    ]
    processes = []
    logs = []
    for index in range(2):
        shard = work_root / f"{run_name}-shard-{index}"
        diagnostics = work_root / f"{run_name}-diagnostics-shard-{index}"
        log_path = work_root / f"{run_name}-shard-{index}.log"
        log = log_path.open("w", encoding="utf-8", buffering=1)
        environment = _worker_environment(index)
        processes.append(
            subprocess.Popen(
                base
                + [
                    "--shard-index",
                    str(index),
                    "--output",
                    str(shard),
                    "--diagnostics-output",
                    str(diagnostics),
                ],
                cwd=PROJECT_ROOT,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
        )
        logs.append((log, log_path))
    while any(process.poll() is None for process in processes):
        counts = [
            len(
                list(
                    (
                        work_root / f"{run_name}-shard-{index}" / "documents"
                    ).glob("*.json")
                )
            )
            for index in range(2)
        ]
        print(f"Completed documents: {counts[0]}/50, {counts[1]}/50", flush=True)
        time.sleep(args.poll_seconds)
    codes = wait_for_workers(processes)
    for log, _ in logs:
        log.close()
    if any(codes):
        details = "\n".join(
            f"shard {index}: exit {code}\n{path.read_text(encoding='utf-8')[-2000:]}"
            for index, (code, (_, path)) in enumerate(zip(codes, logs))
        )
        raise RuntimeError(f"Qwen workers failed:\n{details}")

    summary = merge_shards(
        [work_root / f"{run_name}-shard-{index}" for index in range(2)],
        work_root / run_name,
        documents,
        args.max_chars,
    )
    diagnostics_root = work_root / f"{run_name}-diagnostics"
    if diagnostics_root.exists():
        shutil.rmtree(diagnostics_root)
    diagnostics_root.mkdir(parents=True)
    copied_diagnostics = set()
    for index in range(2):
        source_root = work_root / f"{run_name}-diagnostics-shard-{index}"
        for source in source_root.glob("*.json"):
            if source.name in copied_diagnostics:
                raise ValueError(f"duplicate diagnostic document: {source.name}")
            copied_diagnostics.add(source.name)
            shutil.copy2(source, diagnostics_root / source.name)
    archive = Path(
        shutil.make_archive(
            str(work_root / run_name),
            "zip",
            root_dir=work_root,
            base_dir=run_name,
        )
    )
    diagnostics_archive = Path(
        shutil.make_archive(
            str(work_root / f"{run_name}-diagnostics"),
            "zip",
            root_dir=work_root,
            base_dir=f"{run_name}-diagnostics",
        )
    )
    result = {
        **summary,
        "prompt_version": args.prompt_version,
        "archive": str(archive),
        "sha256": _sha256(archive),
        "diagnostics_archive": str(diagnostics_archive),
        "diagnostics_sha256": _sha256(diagnostics_archive),
    }
    print(json.dumps(result, indent=2), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--work-root", type=Path, default=Path("/kaggle/working"))
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--max-chars", type=int, default=2500)
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--run-name", default="qwen3-4b-s009")
    parser.add_argument(
        "--prompt-version",
        type=int,
        choices=sorted(PROMPT_HEADERS),
        default=1,
    )
    run(parser.parse_args())


if __name__ == "__main__":
    main()
