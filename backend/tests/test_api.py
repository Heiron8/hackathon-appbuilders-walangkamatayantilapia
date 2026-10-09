import asyncio
import json
import unittest
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from fastapi import HTTPException

from fixtures import SUPPORTED, UNSUPPORTED, VOCABULARY, request_body
from app.ai.ollama import OllamaRuntime
from app.api.communication import create_router
from app.api.errors import install_error_handlers
from app.validation.grammar import permitted_renderings


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.calls = []
        self.reply = None

        async def transport(request):
            self.calls.append(request)
            if self.reply:
                return await self.reply(request)
            if request.url.path == "/api/tags":
                return httpx.Response(200, json={"models": [{"name": "qwen3:1.7b"}]})
            body = json.loads(request.content)
            data = json.loads(body["messages"][1]["content"])
            return httpx.Response(200, json={"done": True, "message": {"content": json.dumps({
                "source_card_ids": data["source_card_ids"], "text": data["permitted_sentences"][0]})}})

        self.runtime_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        self.runtime = OllamaRuntime(client=self.runtime_client)
        app = FastAPI()
        install_error_handlers(app)
        app.include_router(create_router(VOCABULARY, self.runtime))
        self.app = app
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000")

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.runtime_client.aclose()

    async def test_all_supported_fixtures_echo_snapshot(self):
        for ids in SUPPORTED:
            with self.subTest(ids=ids):
                response = await self.client.post("/api/expand", json=request_body(ids))
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertEqual(result["request_id"], request_body()["request_id"])
                self.assertEqual(result["revision"], 3)
                self.assertEqual(result["source_card_ids"], ids)
                self.assertEqual(result["text"], permitted_renderings(ids)[0])
                self.assertEqual(result["status"], "candidate")
        outgoing = json.loads(self.calls[0].content)
        self.assertFalse(outgoing["think"])
        self.assertFalse(outgoing["stream"])
        self.assertIsInstance(outgoing["format"], dict)
        self.assertEqual(outgoing["options"]["num_predict"], 256)
        self.assertEqual(str(self.calls[0].url), "http://127.0.0.1:11434/api/chat")
        self.assertNotIn("tools", outgoing)

    async def test_unsupported_retains_order_duplicates_without_model_call(self):
        for ids in UNSUPPORTED:
            response = await self.client.post("/api/expand", json=request_body(ids))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["source_card_ids"], ids)
            self.assertIsNone(response.json()["text"])
            self.assertEqual(response.json()["status"], "unsupported")
        self.assertEqual(self.calls, [])

    async def test_input_failures_and_envelopes(self):
        for changes, status, code in ((dict(selected_card_ids=["unknown"]), 422, "invalid_request"),
                                     (dict(vocabulary_version="tanaw-v2"), 409, "vocabulary_mismatch"),
                                     (dict(selected_card_ids=[]), 422, "invalid_request"),
                                     (dict(revision=True), 422, "invalid_request"),
                                     (dict(runtime_url="https://example.org"), 422, "invalid_request")):
            with self.subTest(changes=changes):
                response = await self.client.post("/api/expand", json=request_body(**changes))
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()["error"]["code"], code)
                self.assertIn("request_id", response.json())
        self.assertEqual(self.calls, [])

    async def test_body_content_type_size_and_host_origin_boundaries(self):
        for body, headers, status in (("{", {"content-type": "application/json"}, 422),
                                     (json.dumps(request_body()), {"content-type": "text/plain"}, 422),
                                     (" " * 16385, {"content-type": "application/json"}, 413),
                                     (json.dumps(request_body()), {"content-type": "application/json", "origin": "https://evil.test"}, 422),
                                     (json.dumps(request_body()), {"content-type": "application/json", "host": "evil.test"}, 422)):
            with self.subTest(headers=headers, status=status):
                response = await self.client.post("/api/expand", content=body, headers=headers)
                self.assertEqual(response.status_code, status)
        async def chunks():
            yield b" " * 10000
            yield b" " * 10000
        response = await self.client.post("/api/expand", content=chunks(), headers={"content-type": "application/json"})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.calls, [])

    async def test_accepts_only_exact_allowed_origins(self):
        response = await self.client.post("/api/expand", json=request_body(), headers={"origin": "http://127.0.0.1:5173"})
        self.assertEqual(response.status_code, 200)
        response = await self.client.post("/api/expand", json=request_body(), headers={"origin": "http://127.0.0.1:9999"})
        self.assertEqual(response.status_code, 422)

    async def test_invalid_model_outputs_never_escape(self):
        ids = request_body()["selected_card_ids"]
        invalid = ["not json", "[]", json.dumps({"source_card_ids": ids, "text": "I am hungry."}),
                   json.dumps({"source_card_ids": list(reversed(ids)), "text": "I want to eat an apple."}),
                   json.dumps({"source_card_ids": ids, "text": "I want to eat an apple.", "extra": "x"})]
        for content in invalid:
            async def reply(request, content=content):
                return httpx.Response(200, json={"done": True, "message": {"content": content}})
            self.reply = reply
            with self.subTest(content=content):
                response = await self.client.post("/api/expand", json=request_body())
                self.assertEqual(response.status_code, 502)
                self.assertEqual(response.json()["error"]["code"], "invalid_ai_output")
                self.assertNotIn("I am hungry", response.text)

    async def test_dropped_negation_is_rejected_end_to_end(self):
        ids = ["not", "want", "eat", "apple"]
        async def reply(request):
            return httpx.Response(200, json={"done": True, "message": {"content": json.dumps({
                "source_card_ids": ids, "text": "I want to eat an apple."})}})
        self.reply = reply
        response = await self.client.post("/api/expand", json=request_body(ids))
        self.assertEqual(response.status_code, 502)

    async def test_bounded_response_and_malformed_runtime_envelope(self):
        for payload in ([1], {"done": False}, {"done": True, "message": None}, {"large": "x" * 65536}):
            async def reply(request, payload=payload):
                return httpx.Response(200, json=payload)
            self.reply = reply
            response = await self.client.post("/api/expand", json=request_body())
            self.assertEqual(response.status_code, 502)

    async def test_health_is_ready_only_for_present_model(self):
        response = await self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ai"], {"state": "ready", "suggestions_enabled": False})
        self.assertEqual(self.calls[0].url.path, "/api/tags")

    async def test_unavailable_model_never_breaks_health(self):
        async def reply(request):
            raise httpx.ConnectError("private runtime detail")
        self.reply = reply
        response = await self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ai"]["state"], "unavailable")
        response = await self.client.post("/api/expand", json=request_body())
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private runtime detail", response.text)

    async def test_redirects_and_missing_models_do_not_trigger_download_or_remote_request(self):
        async def redirect(request):
            return httpx.Response(302, headers={"location": "https://evil.test/api/chat"})
        self.reply = redirect
        self.assertEqual((await self.client.post("/api/expand", json=request_body())).status_code, 503)
        self.assertEqual(len(self.calls), 1)
        async def missing(request):
            return httpx.Response(200, json={"models": []})
        self.reply = missing
        self.assertEqual((await self.client.get("/api/health")).json()["ai"]["state"], "unavailable")

    async def test_real_five_second_deadline_then_recovery(self):
        async def stall(request):
            await asyncio.sleep(30)
        self.reply = stall
        started = asyncio.get_running_loop().time()
        response = await self.client.post("/api/expand", json=request_body())
        duration = asyncio.get_running_loop().time() - started
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["error"]["code"], "ai_timeout")
        self.assertGreaterEqual(duration, 4.9)
        self.assertLess(duration, 6)
        self.reply = None
        self.assertEqual((await self.client.post("/api/expand", json=request_body())).status_code, 200)

    async def test_concurrent_inference_is_busy_not_queued(self):
        started, release = asyncio.Event(), asyncio.Event()
        async def wait(request):
            started.set()
            await release.wait()
            return httpx.Response(503)
        self.reply = wait
        first = asyncio.create_task(self.client.post("/api/expand", json=request_body()))
        await started.wait()
        second = await self.client.post("/api/expand", json=request_body())
        self.assertEqual(second.status_code, 429)
        self.assertEqual(len(self.calls), 1)
        release.set()
        self.assertEqual((await first).status_code, 503)

    async def test_cancellation_releases_busy_slot(self):
        started = asyncio.Event()
        async def stall(request):
            started.set()
            await asyncio.sleep(30)
        self.reply = stall
        task = asyncio.create_task(self.runtime.expand(request_body()["selected_card_ids"]))
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.reply = None
        self.assertEqual((await self.client.post("/api/expand", json=request_body())).status_code, 200)

    async def test_logs_only_id_outcome_duration(self):
        with self.assertLogs("app.api.communication", level="INFO") as captured:
            await self.client.post("/api/expand", json=request_body())
        logged = " ".join(captured.output)
        self.assertIn("duration_ms=", logged)
        self.assertNotIn("apple", logged)
        self.assertNotIn("want", logged)
        self.assertNotIn("text", logged)

    async def test_not_found_uses_envelope_without_changing_404(self):
        response = await self.client.get("/api/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"request_id": None, "error": {
            "code": "invalid_request", "message": "Request could not be served."}})

    async def test_wrong_methods_preserve_405_allow_and_envelope(self):
        for method, path, allowed in (("GET", "/api/expand", {"POST"}),
                                      ("PUT", "/api/expand", {"POST"}),
                                      ("POST", "/api/health", {"GET"})):
            with self.subTest(method=method, path=path):
                response = await self.client.request(method, path)
                self.assertEqual(response.status_code, 405)
                self.assertEqual({m.strip() for m in response.headers["allow"].split(",")}, allowed)
                self.assertEqual(response.json()["error"]["code"], "invalid_request")
                self.assertIsNone(response.json()["request_id"])

    async def test_http_exception_details_are_private_and_headers_status_preserved(self):
        @self.app.get("/api/test-http-error")
        async def fail():
            raise HTTPException(status_code=418, detail="private model output", headers={"X-Test": "preserved"})
        response = await self.client.get("/api/test-http-error")
        self.assertEqual(response.status_code, 418)
        self.assertEqual(response.headers["x-test"], "preserved")
        self.assertNotIn("private model output", response.text)
        self.assertEqual(response.json()["error"]["code"], "invalid_request")

    async def test_framework_validation_errors_use_safe_422_envelope(self):
        @self.app.get("/api/test-validation")
        async def number(count: int):
            return count
        response = await self.client.get("/api/test-validation", params={"count": "private question text"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "invalid_request")
        self.assertNotIn("private question text", response.text)
