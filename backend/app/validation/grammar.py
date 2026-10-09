"""Finite approved Want/Not-Want grammar, independent of model judgment."""

from .contracts import ModelCandidate

FOOD = {"apple": "an apple", "banana": "a banana", "rice": "rice", "bread": "bread"}
DRINK = {"water": "water", "milk": "milk", "juice": "juice"}
OBJECT = FOOD | DRINK | {"toy": "a toy", "ball": "a ball"}


def permitted_renderings(card_ids: list[str]) -> tuple[str, ...]:
    remaining = card_ids.copy()
    if remaining and remaining[0] == "i":
        remaining.pop(0)
    negative = bool(remaining and remaining[0] == "not")
    if negative:
        remaining.pop(0)
    if not remaining or remaining.pop(0) != "want":
        return ()
    if len(remaining) == 1 and remaining[0] in OBJECT:
        complement = OBJECT[remaining[0]]
    elif len(remaining) == 2 and remaining[0] == "eat" and remaining[1] in FOOD:
        complement = "to eat " + FOOD[remaining[1]]
    elif len(remaining) == 2 and remaining[0] == "drink" and remaining[1] in DRINK:
        complement = "to drink " + DRINK[remaining[1]]
    else:
        return ()
    if negative:
        return (f"I do not want {complement}.",)
    return (f"I want {complement}.", f"I would like {complement}.")


def normalize(text: str) -> str:
    # Only whitespace, case, and terminal sentence punctuation may differ.
    return " ".join(text.split()).rstrip(".!?").casefold()


def validate_candidate(candidate: ModelCandidate, source_ids: list[str]) -> bool:
    return (candidate.source_card_ids == source_ids
            and normalize(candidate.text) in {normalize(text) for text in permitted_renderings(source_ids)})
