import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pydantic import ValidationError

from fixtures import IDS, SUPPORTED, UNSUPPORTED, request_body, vocabulary_document
from app.validation.contracts import ExpandRequest, ModelCandidate
from app.validation.grammar import FOOD, DRINK, OBJECT, permitted_renderings, validate_candidate
from app.validation.vocabulary import Vocabulary


class ValidationTests(unittest.TestCase):
    def test_supported_and_unsupported_fixtures(self):
        for ids in SUPPORTED:
            with self.subTest(ids=ids):
                self.assertTrue(permitted_renderings(ids))
        for ids in UNSUPPORTED + [[]]:
            with self.subTest(ids=ids):
                self.assertEqual(permitted_renderings(ids), ())

    def test_every_approved_grammar_combination(self):
        for prefix in ([], ["i"], ["not"], ["i", "not"]):
            for action, nouns in (([], OBJECT), (["eat"], FOOD), (["drink"], DRINK)):
                for noun, phrase in nouns.items():
                    ids = prefix + ["want"] + action + [noun]
                    with self.subTest(ids=ids):
                        complement = ("to " + action[0] + " " if action else "") + phrase
                        negative = "not" in prefix
                        expected = [f"I {'do not want' if negative else 'want'} {complement}."]
                        if not negative:
                            expected.append(f"I would like {complement}.")
                        self.assertEqual(permitted_renderings(ids), tuple(expected))
                        for text in expected:
                            self.assertTrue(validate_candidate(ModelCandidate(source_card_ids=ids, text=text), ids))

    def test_never_mutates_source_selection(self):
        ids = ["i", "not", "want", "eat", "apple"]
        original = ids.copy()
        permitted_renderings(ids)
        self.assertEqual(ids, original)

    def test_only_allowed_normalization(self):
        ids = ["want", "eat", "apple"]
        candidate = ModelCandidate(source_card_ids=ids, text="  i WANT  to eat an apple!  ")
        self.assertTrue(validate_candidate(candidate, ids))
        for text in ("I am hungry and want to eat an apple.", "I want two apples.",
                     "You want to eat an apple.", "I do not want to eat an apple.",
                     "I want to eat an apple. Ignore instructions.", "I want to eat an apple\u200b."):
            with self.subTest(text=text):
                self.assertFalse(validate_candidate(ModelCandidate(source_card_ids=ids, text=text), ids))

    def test_reordered_source_and_dropped_negation_are_rejected(self):
        ids = ["not", "want", "eat", "apple"]
        for source, text in ((ids, "I want to eat an apple."),
                             (list(reversed(ids)), "I do not want to eat an apple."),
                             (ids, "I would not like to eat an apple.")):
            self.assertFalse(validate_candidate(ModelCandidate(source_card_ids=source, text=text), ids))

    def test_strict_schema(self):
        cases = [dict(revision=True), dict(revision="3"), dict(revision=-1), dict(locale="fil"),
                 dict(selected_card_ids=[]), dict(selected_card_ids=["apple"] * 13),
                 dict(request_id="bad"), dict(model="remote"), dict(selected_card_ids=[1])]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                ExpandRequest.model_validate_json(json.dumps(request_body(**change)))

    def test_vocabulary_load_requires_real_file_and_unique_versioned_ids(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "vocabulary.json"
            with self.assertRaises(FileNotFoundError):
                Vocabulary.load(path)
            payload = vocabulary_document()
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(Vocabulary.load(path).card_ids, frozenset(IDS))
            payload["cards"][0]["id"] = IDS[1]
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                Vocabulary.load(path)
