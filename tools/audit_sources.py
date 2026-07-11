import argparse
import hashlib
import html
import json
import re
import statistics
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path


DRUG_LINE = re.compile(
    r"(?i)(\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|đơn vị|units?)\b|"
    r"\b(?:po|iv|im|sc|bid|tid|qid|qhs|prn|qam|q\d+h|xl)\b|thuốc)"
)
LAB_LINE = re.compile(
    r"(?i)(xét nghiệm|huyết học|sinh hóa|công thức máu|creatinin|glucose|"
    r"hemoglobin|bạch cầu|tiểu cầu|natri|kali|ast|alt|bilirubin|albumin|inr|"
    r"crp|procalcitonin)"
)
CUES = {
    "negation": re.compile(r"(?i)\b(không|chưa|phủ nhận|âm tính)\b"),
    "family": re.compile(r"(?i)\b(gia đình|mẹ|bố|cha|vợ|chồng|anh|chị|em)\b"),
    "history": re.compile(
        r"(?i)\b(tiền sử|trước đây|trước khi|đã từng|mạn tính|phẫu thuật)\b"
    ),
}
SECTION_HEADER = re.compile(
    r"(?i)^(tiền sử|bệnh sử|lịch sử|lý do nhập viện|diễn biến|triệu chứng|"
    r"đánh giá|khám|xét nghiệm|chẩn đoán|phát hiện|thuốc|các bệnh|các yếu tố)"
)
ABBREVIATIONS = ("po", "bid", "qid", "qhs", "prn", "xl", "RUE AVF", "OSH", "RUQ", "ERCP", "HIDA")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_zip_documents(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        entries = [entry for entry in archive.infolist() if entry.filename.endswith(".txt")]
        entries.sort(key=lambda entry: int(Path(entry.filename).stem))
        return {
            entry.filename: archive.read(entry).decode("utf-8", errors="strict")
            for entry in entries
        }


def validate_document_names(names: Sequence[str]) -> None:
    expected = [f"input/{identifier}.txt" for identifier in range(1, 101)]
    if list(names) != expected:
        raise ValueError("ZIP must contain input/1.txt through input/100.txt exactly")


def _summary(values: list[int]) -> dict[str, float | int]:
    return {
        "min": min(values),
        "median": statistics.median(values),
        "mean": round(statistics.fmean(values), 2),
        "max": max(values),
        "sum": sum(values),
        "documents_nonzero": sum(value > 0 for value in values),
    }


def audit_documents(documents: Mapping[str, str]) -> dict[str, object]:
    rows = []
    section_headers = Counter()
    abbreviation_counts = Counter()
    for name, text in documents.items():
        lines = text.splitlines()
        for line in lines:
            stripped = re.sub(r"^\d+\.\s*", "", line.strip().removesuffix(":"))
            if 0 < len(stripped) <= 100 and SECTION_HEADER.match(stripped):
                section_headers[stripped] += 1
        for abbreviation in ABBREVIATIONS:
            count = len(
                re.findall(
                    rf"(?i)(?<!\w){re.escape(abbreviation)}(?!\w)",
                    text,
                )
            )
            abbreviation_counts[abbreviation] += count
        rows.append(
            {
                "name": name,
                "bytes": len(text.encode("utf-8")),
                "characters": len(text),
                "lines": len(lines),
                "drug_like_lines": sum(bool(DRUG_LINE.search(line)) for line in lines),
                "lab_like_lines": sum(bool(LAB_LINE.search(line)) for line in lines),
                **{
                    f"{cue}_cues": len(pattern.findall(text))
                    for cue, pattern in CUES.items()
                },
            }
        )
    keys = {
        "byte_count": "bytes",
        "character_count": "characters",
        "line_count": "lines",
        "drug_like_line_count": "drug_like_lines",
        "lab_like_line_count": "lab_like_lines",
        "negation_cue_count": "negation_cues",
        "family_cue_count": "family_cues",
        "history_cue_count": "history_cues",
    }
    return {
        "document_count": len(rows),
        "section_headers": dict(
            sorted(section_headers.items(), key=lambda item: (-item[1], item[0]))
        ),
        "abbreviation_counts": dict(sorted(abbreviation_counts.items())),
        **{output: _summary([row[source] for row in rows]) for output, source in keys.items()},
        "documents": rows,
    }


def audit_official_html(path: Path) -> dict[str, object]:
    source = path.read_text(encoding="utf-8")
    match = re.search(
        r'<pre><code class="language-json">(.*?)</code></pre>',
        source,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError("official JSON example not found")
    entities = json.loads(html.unescape(match.group(1)))
    duplicates = {
        text: count
        for text, count in Counter(entity["text"] for entity in entities).items()
        if count > 1
    }
    visible = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", source)))
    return {
        "example_entity_count": len(entities),
        "type_schemas": {
            entity_type: sorted(
                set().union(*(entity.keys() for entity in entities if entity["type"] == entity_type))
            )
            for entity_type in sorted({entity["type"] for entity in entities})
        },
        "duplicate_surface_counts": duplicates,
        "mentions_wer": "Word Error Rate (WER)" in visible,
        "mentions_jaccard": "Jaccard similarity" in visible,
        "mentions_score_weights": all(token in visible for token in ("final_score", "0.3", "0.4")),
        "mentions_self_host": "self-host" in visible,
        "mentions_9b_limit": "9B params" in visible,
    }


def audit_sources(zip_path: Path, html_path: Path) -> dict[str, object]:
    documents = read_zip_documents(zip_path)
    validate_document_names(list(documents))
    return {
        "artifacts": {
            str(zip_path): {"sha256": sha256(zip_path)},
            str(html_path): {"sha256": sha256(html_path)},
        },
        "official_html": audit_official_html(html_path),
        "dataset": audit_documents(documents),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=Path("input.zip"))
    parser.add_argument(
        "--html",
        type=Path,
        default=Path("AI Race 2026 - Cuộc đua AI cho kỹ sư Việt Nam.html"),
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/source_audit.json"))
    args = parser.parse_args()
    report = audit_sources(args.zip, args.html)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
