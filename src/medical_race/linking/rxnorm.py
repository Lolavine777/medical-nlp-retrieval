import hashlib
import io
import re
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


CONCEPT_MEMBER = "rrf/RXNCONSO.RRF"
SUPPORTED_SOURCES = {"RXNORM", "MTHSPL"}
INGREDIENT_TERM_TYPES = {"IN", "PIN", "MIN"}
NON_DRUG_TERM_TYPES = {"DF", "DFG"}
NON_WORD = re.compile(r"[^\w]+")
ALNUM_BOUNDARY = re.compile(r"(?<=\d)(?=[^\W\d_])|(?<=[^\W\d_])(?=\d)")


@dataclass(frozen=True, slots=True)
class RxNormTerm:
    rxcui: str
    text: str
    term_type: str
    source: str
    preferred: bool


@dataclass(frozen=True, slots=True)
class LinkResult:
    candidates: tuple[str, ...]
    matched_text: str


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


def link_drug(
    text: str,
    terms: tuple[RxNormTerm, ...],
    concept_level: str = "all_retrievable",
    candidate_output: str = "top1",
) -> LinkResult | None:
    if concept_level not in {"all_retrievable", "ingredient"}:
        raise ValueError(f"unknown concept level: {concept_level!r}")
    if candidate_output not in {"top1", "top2"}:
        raise ValueError(f"unknown candidate output: {candidate_output!r}")
    ranked = rank_drug_candidates(text, terms, concept_level)
    if not ranked:
        return None
    limit = 1 if candidate_output == "top1" else 2
    return LinkResult(tuple(term.rxcui for term in ranked[:limit]), ranked[0].text)


def rank_drug_candidates(
    text: str,
    terms: tuple[RxNormTerm, ...],
    concept_level: str = "all_retrievable",
) -> tuple[RxNormTerm, ...]:
    if concept_level not in {"all_retrievable", "ingredient"}:
        raise ValueError(f"unknown concept level: {concept_level!r}")
    normalized_text = _normalize(text)
    if not normalized_text:
        return ()
    by_text, by_first_token = _term_index(terms)
    words = normalized_text.split()
    matching_texts = {
        " ".join(words[start:end])
        for start in range(len(words))
        for end in range(start + 1, len(words) + 1)
        if " ".join(words[start:end]) in by_text
    }
    matching_texts.update(
        normalized_term
        for normalized_term in by_first_token.get(words[0], ())
        if f" {normalized_text} " in f" {normalized_term} "
    )
    matches = []
    for normalized_term in matching_texts:
        for term in by_text[normalized_term]:
            if concept_level == "ingredient" and term.term_type not in INGREDIENT_TERM_TYPES:
                continue
            matches.append(
                (
                    normalized_text == normalized_term,
                    len(normalized_term),
                    term.source == "RXNORM",
                    term.preferred,
                    term,
                )
            )
    matches.sort(
        key=lambda match: (
            -match[0],
            -match[1],
            -match[2],
            -match[3],
            int(match[4].rxcui),
            match[4].text.casefold(),
        )
    )
    ranked = []
    seen = set()
    for match in matches:
        term = match[4]
        if term.rxcui not in seen:
            ranked.append(term)
            seen.add(term.rxcui)
    return tuple(ranked)


def normalize_rxnorm_text(text: str) -> str:
    return _normalize(text)


@lru_cache(maxsize=None)
def _normalize(text: str) -> str:
    separated = ALNUM_BOUNDARY.sub(" ", text.casefold())
    return " ".join(NON_WORD.sub(" ", separated).split())


@lru_cache(maxsize=2)
def _term_index(terms: tuple[RxNormTerm, ...]):
    by_text = {}
    by_first_token = {}
    for term in terms:
        if term.term_type in NON_DRUG_TERM_TYPES:
            continue
        normalized = _normalize(term.text)
        if not normalized:
            continue
        by_text.setdefault(normalized, []).append(term)
        by_first_token.setdefault(normalized.split()[0], set()).add(normalized)
    return (
        {text: tuple(values) for text, values in by_text.items()},
        {token: tuple(sorted(values)) for token, values in by_first_token.items()},
    )


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
