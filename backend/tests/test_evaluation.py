import unittest

from fixtures import SUPPORTED
from app.ai.evaluate import FIXTURES, percentile
from app.validation.grammar import permitted_renderings


class EvaluationTests(unittest.TestCase):
    def test_twelve_distinct_supported_model_fixtures_match_contract_tests(self):
        self.assertEqual(len(set(FIXTURES)), 12)
        self.assertEqual([list(ids) for ids in FIXTURES], SUPPORTED)
        self.assertTrue(all(permitted_renderings(list(ids)) for ids in FIXTURES))

    def test_p95_uses_nearest_rank_including_failed_call_durations(self):
        self.assertEqual(percentile(list(range(1, 31)), 0.95), 29)
        self.assertEqual(percentile([5000] * 2 + [10] * 28, 0.95), 5000)
