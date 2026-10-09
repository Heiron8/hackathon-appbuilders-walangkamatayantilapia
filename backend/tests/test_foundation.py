import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from backend.app.main import ROOT, create_app
from shared.vocabulary import load_vocabulary, validate_vocabulary


class VocabularyTests(unittest.TestCase):
    def test_exact_approved_seed_and_paths(self):
        # The approved table is the label/category authority, not a second product seed.
        text = (ROOT / "docs/architecture/contracts.md").read_text(encoding="utf-8")
        expected = []
        for category, entries in re.findall(r"^\| (Essential|Core|Actions|Drinks|Food|Activities|Places|People) \| (.*?) \|$", text, re.M):
            for card_id, label in re.findall(r"`([a-z_]+)` ([^;]+)(?:;|$)", entries):
                expected.append((card_id, label, category.lower()))
        vocabulary = load_vocabulary()
        self.assertEqual(len(expected), 32)
        self.assertEqual([(c["id"], c["label"], c["category"]) for c in vocabulary["cards"]], expected)
        self.assertEqual([c["order"] for c in vocabulary["cards"]], list(range(32)))

    def test_bad_contract_data_fails_closed(self):
        original = load_vocabulary()
        for field, value in [("id", "../no"), ("order", True), ("symbol_path", "https://example.com/no.svg"),
                             ("audio_path", "../no.wav"), ("label", ""), ("category", "unknown")]:
            with self.subTest(field=field):
                data = copy.deepcopy(original)
                data["cards"][0][field] = value
                with self.assertRaises(ValueError):
                    validate_vocabulary(data)
        for change in [lambda data: data.update(version="tanaw-v2"),
                       lambda data: data["cards"].pop(),
                       lambda data: data["cards"][0].update(extra=True),
                       lambda data: data["cards"][1].update(id="no")]:
            data = copy.deepcopy(original)
            change(data)
            with self.assertRaises(ValueError):
                validate_vocabulary(data)

    def test_shared_limits_match_approved_contract(self):
        limits = json.loads((ROOT / "shared/contracts.json").read_text(encoding="utf-8"))
        self.assertEqual(limits, {
            "vocabulary_version": "tanaw-v1", "locale": "en", "max_selected_cards": 12,
            "max_request_bytes": 16384, "max_question_characters": 240, "max_suggested_cards": 6,
            "inference_timeout_seconds": 5, "frontend_timeout_seconds": 6, "suggestions_enabled": False,
        })


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(frontend_dist=ROOT / "backend" / "no-build")
        self.client = TestClient(self.app, base_url="http://127.0.0.1:8000")

    def test_health_needs_no_ollama_and_uses_shared_vocabulary(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "vocabulary_version": "tanaw-v1",
                                         "ai": {"state": "unknown", "suggestions_enabled": False}})
        self.assertEqual(self.app.state.vocabulary, load_vocabulary())

    def test_ai_routes_are_not_implemented(self):
        for route in ["expand", "suggest"]:
            response = self.client.post(f"/api/{route}", json={})
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["error"]["code"], "invalid_request")
            self.assertIsNone(response.json()["request_id"])

    def test_only_exact_local_hosts_and_origins(self):
        for host in ["evil.example", "127.0.0.1.evil.example", "localhost.evil.example"]:
            response = self.client.get("/api/health", headers={"host": host})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["error"]["code"], "invalid_request")
        response = self.client.post("/api/expand", json={}, headers={"origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "invalid_request")
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_final_static_build_and_missing_api_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "index.html").write_text("<h1>Local build</h1>", encoding="utf-8")
            client = TestClient(create_app(directory), base_url="http://localhost:8000")
            self.assertEqual(client.get("/").text, "<h1>Local build</h1>")
            self.assertEqual(client.get("/api/missing").status_code, 404)
            self.assertEqual(client.get("/api/missing").json()["error"]["code"], "invalid_request")
            self.assertEqual(client.get("/missing.js").json()["error"]["code"], "invalid_request")


if __name__ == "__main__":
    unittest.main()
