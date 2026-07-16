import argparse
import json
from pathlib import Path

from medical_race.submission import validate_output_zip
from tools.audit_sources import read_zip_documents, validate_document_names


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--input", type=Path, default=Path("input.zip"))
    args = parser.parse_args()
    documents = read_zip_documents(args.input)
    validate_document_names(list(documents))
    print(json.dumps(validate_output_zip(args.archive, documents), sort_keys=True))


if __name__ == "__main__":
    main()
