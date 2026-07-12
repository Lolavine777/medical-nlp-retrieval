import argparse
import json
from pathlib import Path

from medical_race.submission_diff import diff_submission_archives


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", type=Path)
    parser.add_argument("child", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = diff_submission_archives(args.parent, args.child)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, ensure_ascii=False, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps({key: value for key, value in report.items() if key != "details"}, sort_keys=True))


if __name__ == "__main__":
    main()
