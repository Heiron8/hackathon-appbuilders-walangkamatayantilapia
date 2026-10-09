"""Validate the one bundled vocabulary; no network or runtime dependency."""
import json
from pathlib import Path

VOCABULARY_PATH = Path(__file__).resolve().with_name("vocabulary.json")
VERSION = "tanaw-v1"
CATEGORIES = {"essential", "core", "actions", "drinks", "food", "activities", "places", "people"}
CARD_FIELDS = {"id", "label", "category", "symbol_path", "audio_path", "order"}


def validate_vocabulary(data):
    if not isinstance(data, dict) or set(data) != {"version", "cards"}:
        raise ValueError("Vocabulary must contain only version and cards")
    if data["version"] != VERSION or not isinstance(data["cards"], list) or len(data["cards"]) != 32:
        raise ValueError("Expected tanaw-v1 with exactly 32 cards")
    seen = set()
    for order, card in enumerate(data["cards"]):
        if not isinstance(card, dict) or set(card) != CARD_FIELDS:
            raise ValueError("Invalid card fields")
        card_id = card["id"]
        if not isinstance(card_id, str) or not card_id or any(c not in "abcdefghijklmnopqrstuvwxyz_" for c in card_id):
            raise ValueError("Invalid card ID")
        if card_id in seen or type(card["order"]) is not int or card["order"] != order:
            raise ValueError("Duplicate ID or invalid board order")
        if not isinstance(card["label"], str) or not card["label"].strip():
            raise ValueError("Invalid card label")
        if not isinstance(card["category"], str) or card["category"] not in CATEGORIES:
            raise ValueError("Unknown category")
        if card["symbol_path"] != f"symbols/{card_id}.svg" or card["audio_path"] != f"audio/en/{card_id}.wav":
            raise ValueError("Expected local symbol/audio paths")
        seen.add(card_id)
    return data


def load_vocabulary(path=VOCABULARY_PATH):
    return validate_vocabulary(json.loads(Path(path).read_text(encoding="utf-8")))
