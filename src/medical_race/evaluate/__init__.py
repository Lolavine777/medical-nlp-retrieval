from collections.abc import Mapping
from dataclasses import dataclass
from math import isclose, isfinite


MATCHING_POLICIES = {"type_position", "type_text_position"}
TEXT_SCORE_POLICIES = {"one_minus_wer_clipped", "one_minus_wer"}


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_unit_interval(value: object, name: str) -> None:
    if not _is_number(value) or not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a finite value in [0, 1]")


@dataclass(frozen=True)
class EvaluationPolicy:
    matching_policy: str = "type_position"
    text_score_policy: str = "one_minus_wer_clipped"
    empty_set_score: float = 1.0
    weights: tuple[float, float, float] = (0.3, 0.3, 0.4)

    def __post_init__(self) -> None:
        if self.matching_policy not in MATCHING_POLICIES:
            raise ValueError(f"unknown matching policy: {self.matching_policy!r}")
        if self.text_score_policy not in TEXT_SCORE_POLICIES:
            raise ValueError(f"unknown text score policy: {self.text_score_policy!r}")
        _validate_unit_interval(self.empty_set_score, "empty_set_score")
        if (
            not isinstance(self.weights, tuple)
            or len(self.weights) != 3
            or any(not _is_number(value) for value in self.weights)
            or any(
                not isfinite(value) or not 0.0 <= value <= 1.0
                for value in self.weights
            )
            or not isclose(sum(self.weights), 1.0)
        ):
            raise ValueError(
                "weights must be three finite values in [0, 1] summing to 1"
            )


def word_error_rate(reference: str, hypothesis: str) -> float:
    if not isinstance(reference, str) or not isinstance(hypothesis, str):
        raise ValueError("reference and hypothesis must be strings")
    reference_words = reference.split()
    hypothesis_words = hypothesis.split()
    if not reference_words:
        return 0.0 if not hypothesis_words else 1.0
    previous = list(range(len(hypothesis_words) + 1))
    for reference_index, reference_word in enumerate(reference_words, 1):
        current = [reference_index]
        for hypothesis_index, hypothesis_word in enumerate(hypothesis_words, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[hypothesis_index] + 1,
                    previous[hypothesis_index - 1]
                    + (reference_word != hypothesis_word),
                )
            )
        previous = current
    return previous[-1] / len(reference_words)


def set_jaccard(left: object, right: object, empty_score: float = 1.0) -> float:
    _validate_unit_interval(empty_score, "empty_score")
    left_set = _string_set(left, "left")
    right_set = _string_set(right, "right")
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else float(empty_score)


def match_mentions(
    gold: object,
    predictions: object,
    matching_policy: str = "type_position",
) -> list[tuple[int | None, int | None]]:
    EvaluationPolicy(matching_policy=matching_policy)
    gold_entities = _validate_entities(gold, "gold")
    prediction_entities = _validate_entities(predictions, "predictions")
    used_predictions: set[int] = set()
    pairs: list[tuple[int | None, int | None]] = []
    for gold_index, gold_entity in enumerate(gold_entities):
        gold_key = _mention_key(gold_entity, matching_policy)
        prediction_index = next(
            (
                index
                for index, prediction in enumerate(prediction_entities)
                if index not in used_predictions
                and _mention_key(prediction, matching_policy) == gold_key
            ),
            None,
        )
        pairs.append((gold_index, prediction_index))
        if prediction_index is not None:
            used_predictions.add(prediction_index)
    pairs.extend(
        (None, index)
        for index in range(len(prediction_entities))
        if index not in used_predictions
    )
    return pairs


def evaluate_entities(
    gold: object,
    predictions: object,
    policy: EvaluationPolicy = EvaluationPolicy(),
) -> dict[str, object]:
    if not isinstance(policy, EvaluationPolicy):
        raise ValueError("policy must be an EvaluationPolicy")
    gold_entities = _validate_entities(gold, "gold")
    prediction_entities = _validate_entities(predictions, "predictions")
    records = []
    for gold_index, prediction_index in match_mentions(
        gold_entities, prediction_entities, policy.matching_policy
    ):
        if gold_index is None or prediction_index is None:
            records.append(
                {
                    "status": (
                        "unmatched_prediction"
                        if gold_index is None
                        else "unmatched_gold"
                    ),
                    "gold_index": gold_index,
                    "prediction_index": prediction_index,
                    "wer": None,
                    "text_score": 0.0,
                    "assertions_score": 0.0,
                    "candidates_score": 0.0,
                }
            )
            continue
        gold_entity = gold_entities[gold_index]
        prediction_entity = prediction_entities[prediction_index]
        wer = word_error_rate(gold_entity["text"], prediction_entity["text"])
        records.append(
            {
                "status": "matched",
                "gold_index": gold_index,
                "prediction_index": prediction_index,
                "wer": wer,
                "text_score": (
                    max(0.0, 1.0 - wer)
                    if policy.text_score_policy == "one_minus_wer_clipped"
                    else 1.0 - wer
                ),
                "assertions_score": set_jaccard(
                    gold_entity.get("assertions", []),
                    prediction_entity.get("assertions", []),
                    policy.empty_set_score,
                ),
                "candidates_score": set_jaccard(
                    gold_entity.get("candidates", []),
                    prediction_entity.get("candidates", []),
                    policy.empty_set_score,
                ),
            }
        )
    if records:
        text_score = _mean(records, "text_score")
        assertions_score = _mean(records, "assertions_score")
        candidates_score = _mean(records, "candidates_score")
    else:
        text_score = assertions_score = candidates_score = 1.0
    total_score = sum(
        weight * score
        for weight, score in zip(
            policy.weights,
            (text_score, assertions_score, candidates_score),
            strict=True,
        )
    )
    return {
        "matching_policy": policy.matching_policy,
        "text_score_policy": policy.text_score_policy,
        "records": records,
        "text_score": text_score,
        "assertions_score": assertions_score,
        "candidates_score": candidates_score,
        "total_score": total_score,
    }


def _validate_entities(value: object, name: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    for index, entity in enumerate(value):
        if not isinstance(entity, Mapping):
            raise ValueError(f"{name} entity {index} must be an object")
        if not isinstance(entity.get("text"), str):
            raise ValueError(f"{name} entity {index} text must be a string")
        if not isinstance(entity.get("type"), str):
            raise ValueError(f"{name} entity {index} type must be a string")
        position = entity.get("position")
        if (
            not isinstance(position, list)
            or len(position) != 2
            or any(type(value) is not int for value in position)
        ):
            raise ValueError(f"{name} entity {index} position must be two integers")
        for field in ("assertions", "candidates"):
            if field in entity:
                _string_set(
                    entity[field], f"{name} entity {index} {field}", list_only=True
                )
    return value


def _mention_key(entity: Mapping[str, object], policy: str) -> tuple[object, ...]:
    position = tuple(entity["position"])
    if policy == "type_position":
        return entity["type"], position
    return entity["type"], entity["text"], position


def _string_set(value: object, name: str, list_only: bool = False) -> set[str]:
    allowed = (list,) if list_only else (list, tuple, set, frozenset)
    if not isinstance(value, allowed) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{name} must contain strings")
    return set(value)


def _mean(records: list[dict[str, object]], field: str) -> float:
    return sum(record[field] for record in records) / len(records)
