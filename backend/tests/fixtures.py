"""Synthetic contract fixtures, never a production vocabulary fallback."""

from pathlib import Path
import re
import sys

# Root discovery adds backend/tests, while standalone discovery starts in backend.
# Resolve the same app package in both contexts without changing production setup.
BACKEND_ROOT = str(Path(__file__).resolve().parents[1])
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.validation.vocabulary import Vocabulary

IDS = (
    "no stop help repeat something_else yes i want not more finished eat drink play go rest "
    "water milk juice apple banana rice bread toy ball music home school outside toilet parent teacher"
).split()
VOCABULARY = Vocabulary("tanaw-v1", frozenset(IDS))


def vocabulary_document():
    """Test data from the approved table, independently of production constraints."""
    text = (Path(__file__).resolve().parents[2] / "docs/architecture/contracts.md").read_text(encoding="utf-8")
    cards = []
    for category, entries in re.findall(
            r"^\| (Essential|Core|Actions|Drinks|Food|Activities|Places|People) \| (.*?) \|$", text, re.M):
        for card_id, label in re.findall(r"`([a-z_]+)` ([^;]+)(?:;|$)", entries):
            cards.append({"id": card_id, "label": label, "category": category.lower(), "order": len(cards),
                          "symbol_path": f"symbols/{card_id}.svg", "audio_path": f"audio/en/{card_id}.wav"})
    if len(cards) != 32:
        raise ValueError("Approved test fixture table must contain 32 cards.")
    return {"version": "tanaw-v1", "cards": cards}

# Twelve distinct supported fixtures, including both negation and explicit/implicit I.
SUPPORTED = [
    ["want", "eat", "apple"], ["not", "want", "eat", "apple"],
    ["i", "want", "drink", "water"], ["i", "not", "want", "drink", "milk"],
    ["want", "banana"], ["not", "want", "toy"],
    ["i", "want", "ball"], ["i", "not", "want", "rice"],
    ["want", "drink", "juice"], ["not", "want", "eat", "bread"],
    ["i", "want", "eat", "banana"], ["i", "not", "want", "water"],
]
UNSUPPORTED = [
    ["water"], ["eat", "apple"], ["no"], ["no", "want", "apple"],
    ["want", "apple", "apple"], ["want", "go", "home"], ["want", "drink", "apple"],
    ["want", "eat", "water"], ["want", "apple", "not"], ["not", "not", "want", "apple"],
    ["want", "more", "apple"], ["help", "stop"],
]


def request_body(ids=None, **changes):
    body = {"request_id": "11111111-1111-4111-8111-111111111111", "revision": 3,
            "vocabulary_version": "tanaw-v1", "locale": "en",
            "selected_card_ids": ids if ids is not None else SUPPORTED[0]}
    return body | changes
