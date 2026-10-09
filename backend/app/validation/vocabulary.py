"""Load the integration owner's canonical vocabulary; never create a fallback."""

import json
from dataclasses import dataclass
from pathlib import Path

# Frozen tanaw-v1 validation constraints from docs/architecture/contracts.md.
# These are never used to supply cards or substitute for the canonical JSON file.
APPROVED_GROUPS = (
    ("essential", "no stop help repeat something_else yes"),
    ("core", "i want not more finished"),
    ("actions", "eat drink play go rest"),
    ("drinks", "water milk juice"),
    ("food", "apple banana rice bread"),
    ("activities", "toy ball music"),
    ("places", "home school outside toilet"),
    ("people", "parent teacher"),
)
APPROVED_IDS = tuple(card_id for _, ids in APPROVED_GROUPS for card_id in ids.split())
CARD_FIELDS = {"id", "label", "category", "symbol_path", "audio_path", "order"}


@dataclass(frozen=True)
class Vocabulary:
    version: str
    card_ids: frozenset[str]

    def __post_init__(self) -> None:
        if (self.version != "tanaw-v1" or not isinstance(self.card_ids, frozenset)
                or self.card_ids != frozenset(APPROVED_IDS)):
            raise ValueError("Expected exactly the approved tanaw-v1 IDs.")

    @classmethod
    def load(cls, path: Path) -> "Vocabulary":
        return cls.from_document(json.loads(path.read_text(encoding="utf-8")))

    @classmethod
    def from_document(cls, document: object) -> "Vocabulary":
        """Accept the document returned by shared.vocabulary.load_vocabulary.

        The Lead's shared validator remains the canonical loader. This boundary
        additionally enforces the frozen seed before using its IDs for inference.
        It also validates direct file loads, without a production fixture fallback.
        """
        if (not isinstance(document, dict) or set(document) != {"version", "cards"}
                or document["version"] != "tanaw-v1"):
            raise ValueError("Expected the canonical tanaw-v1 vocabulary.")
        cards = document["cards"]
        if not isinstance(cards, list) or len(cards) != len(APPROVED_IDS):
            raise ValueError("The canonical vocabulary must contain 32 cards.")
        expected = [(card_id, category) for category, ids in APPROVED_GROUPS for card_id in ids.split()]
        for order, (card, (card_id, category)) in enumerate(zip(cards, expected)):
            if not isinstance(card, dict) or set(card) != CARD_FIELDS:
                raise ValueError("Invalid canonical card fields.")
            if card["id"] != card_id:
                raise ValueError("Unknown, missing, duplicated or reordered canonical card ID.")
            if type(card["order"]) is not int or card["order"] != order:
                raise ValueError("Invalid canonical board order.")
            # v1's English labels/categories are fixed, including I/Something else.
            if card["label"] != card_id.replace("_", " ").capitalize() or card["category"] != category:
                raise ValueError("Invalid canonical card label or category.")
            if (card["symbol_path"] != f"symbols/{card_id}.svg"
                    or card["audio_path"] != f"audio/en/{card_id}.wav"):
                raise ValueError("Expected the canonical local symbol/audio paths.")
        return cls(document["version"], frozenset(card["id"] for card in cards))
