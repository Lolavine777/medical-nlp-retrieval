import hashlib
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path


CONCEPT_MEMBER = "rrf/RXNCONSO.RRF"
SUPPORTED_SOURCES = {"RXNORM", "MTHSPL"}


@dataclass(frozen=True, slots=True)
class RxNormTerm:
    rxcui: str
    text: str
    term_type: str
    source: str
    preferred: bool


def read_rxnorm_archive(path: Path, expected_md5: str) -> tuple[RxNormTerm, ...]:
    path = Path(path)
    actual_md5 = _digest(path, "md5")
    if actual_md5.casefold() != expected_md5.casefold():
        raise ValueError(f"RxNorm archive MD5 mismatch: {actual_md5}")
    with zipfile.ZipFile(path) as archive:
        if archive.namelist().count(CONCEPT_MEMBER) != 1:
            raise ValueError(f"archive must contain exactly one {CONCEPT_MEMBER}")
        with archive.open(CONCEPT_MEMBER) as source:
            lines = io.TextIOWrapper(source, encoding="utf-8", errors="strict")
            return tuple(_read_terms(lines))


def _read_terms(lines):
    for line_number, line in enumerate(lines, 1):
        fields = line.rstrip("\r\n").split("|")
        if len(fields) != 19:
            raise ValueError(f"RXNCONSO line {line_number} has {len(fields)} columns")
        rxcui, language = fields[0], fields[1]
        source, term_type, text, suppressed = fields[11], fields[12], fields[14], fields[16]
        if language != "ENG" or source not in SUPPORTED_SOURCES or suppressed != "N":
            continue
        if not rxcui.isdecimal() or not text or not term_type:
            raise ValueError(f"RXNCONSO line {line_number} has invalid required fields")
        yield RxNormTerm(rxcui, text, term_type, source, fields[6] == "Y")


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
