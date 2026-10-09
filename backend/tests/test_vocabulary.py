import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fixtures import IDS, vocabulary_document
from app.validation.vocabulary import Vocabulary


class VocabularyRegressionTests(unittest.TestCase):
    def test_complete_approved_document_is_accepted_without_mutation(self):
        document = vocabulary_document()
        before = copy.deepcopy(document)
        self.assertEqual(Vocabulary.from_document(document), Vocabulary("tanaw-v1", frozenset(IDS)))
        self.assertEqual(document, before)

    def test_unknown_id_cannot_replace_a_missing_id_in_a_32_card_document(self):
        document = vocabulary_document()
        document["cards"][0].update(id="unknown", symbol_path="symbols/unknown.svg", audio_path="audio/en/unknown.wav")
        with self.assertRaises(ValueError):
            Vocabulary.from_document(document)

    def test_missing_duplicated_and_reordered_ids_are_rejected(self):
        for change in (
            lambda d: d["cards"].pop(),
            lambda d: d["cards"].append(copy.deepcopy(d["cards"][0])),
            lambda d: d["cards"].__setitem__(1, copy.deepcopy(d["cards"][0])),
            lambda d: d["cards"].reverse(),
        ):
            document = vocabulary_document()
            change(document)
            with self.subTest(document=document), self.assertRaises(ValueError):
                Vocabulary.from_document(document)

    def test_root_data_and_fields_fail_closed(self):
        valid = vocabulary_document()
        for document in (None, [], "tanaw-v1", {}, {"version": "tanaw-v1", "cards": None},
                         valid | {"extra": True}, valid | {"version": "tanaw-v2"},
                         valid | {"cards": tuple(valid["cards"])}):
            with self.subTest(document=document), self.assertRaises(ValueError):
                Vocabulary.from_document(document)

    def test_malformed_card_objects_fields_and_types_are_rejected(self):
        for card in (None, [], "no", 1, {"id": "no"}):
            document = vocabulary_document()
            document["cards"][0] = card
            with self.subTest(card=card), self.assertRaises(ValueError):
                Vocabulary.from_document(document)
        cases = {"id": (None, [], "NO"), "label": (None, 1, "", " ", "Yes"),
                 "category": (None, [], "unknown", "food"), "order": (True, 0.0, "0", -1, 1),
                 "symbol_path": (None, 1, "https://example.org/no.svg", "../no.svg", "symbols/yes.svg"),
                 "audio_path": (None, [], "https://example.org/no.wav", "../no.wav", "audio/en/yes.wav")}
        for field, values in cases.items():
            for value in values:
                document = vocabulary_document()
                document["cards"][0][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    Vocabulary.from_document(document)
        for field in vocabulary_document()["cards"][0]:
            document = vocabulary_document()
            del document["cards"][0][field]
            with self.subTest(missing_field=field), self.assertRaises(ValueError):
                Vocabulary.from_document(document)
        document = vocabulary_document()
        document["cards"][0]["extra"] = True
        with self.assertRaises(ValueError):
            Vocabulary.from_document(document)

    def test_direct_construction_cannot_bypass_id_and_version_guard(self):
        for version, ids in (("tanaw-v2", frozenset(IDS)), ("tanaw-v1", frozenset(IDS[1:])),
                             ("tanaw-v1", frozenset(["unknown"] + IDS[1:])), ("tanaw-v1", set(IDS))):
            with self.subTest(version=version, ids=ids), self.assertRaises(ValueError):
                Vocabulary(version, ids)

    def test_bad_files_are_not_repaired_or_replaced_with_fixtures(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "vocabulary.json"
            for content in ("{", json.dumps({"version": "tanaw-v1", "cards": [{"id": value} for value in IDS]})):
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    Vocabulary.load(path)
                self.assertEqual(path.read_text(encoding="utf-8"), content)
