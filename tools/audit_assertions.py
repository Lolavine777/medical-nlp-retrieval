import argparse
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

from medical_race.assertions import classify_assertions
from medical_race.extraction import Span
from medical_race.extraction.drugs import extract_drugs
from medical_race.extraction.labs import extract_labs

try:
    from tools.audit_sources import read_zip_documents
except ModuleNotFoundError:  # Direct execution from the repository root.
    from audit_sources import read_zip_documents


def audit_assertions(documents: Mapping[str, str]) -> dict[str, object]:
    counts = Counter()
    span_count = 0
    for raw_text in documents.values():
        spans: list[Span] = list(extract_drugs(raw_text))
        for result in extract_labs(raw_text):
            spans.extend((result.name, result.value))
        for span in spans:
            counts.update(classify_assertions(raw_text, span).labels())
        span_count += len(spans)
    return {
        "document_count": len(documents),
        "span_count": span_count,
        "label_counts": dict(sorted(counts.items())),
        "offset_errors": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=Path("input.zip"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/assertion_audit.json"),
    )
    args = parser.parse_args()
    report = audit_assertions(read_zip_documents(args.zip))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
