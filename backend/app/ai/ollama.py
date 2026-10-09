"""Bounded local-only Ollama calls. No downloads, retries, tools, or text logging."""

import asyncio
import json

import httpx
from pydantic import ValidationError

from ..validation.contracts import ModelCandidate
from ..validation.grammar import permitted_renderings, validate_candidate

BASE_URL = "http://127.0.0.1:11434"
INFERENCE_DEADLINE = 5.0
MAX_RESPONSE_BYTES = 64 * 1024


def chat_request(model: str, source_ids: list[str]) -> dict:
    """Shared by bounded product inference and explicit setup warm-up."""
    return {
        "model": model, "stream": False, "think": False, "keep_alive": "10m",
        "format": ModelCandidate.model_json_schema(),
        "options": {"temperature": 0, "num_ctx": 2048, "num_predict": 256},
        "messages": [
            {"role": "system", "content": (
                "Expand selected communication cards into one sentence. Return only JSON "
                "with source_card_ids copied exactly in order and text. Preserve negation. "
                "Use one permitted sentence, without adding needs, feelings, quantities, "
                "or preferences. No commentary or tools.")},
            {"role": "user", "content": json.dumps({"source_card_ids": source_ids,
                "permitted_sentences": permitted_renderings(source_ids)})},
        ],
    }


class InferenceError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class OllamaRuntime:
    def __init__(self, model: str = "qwen3:1.7b", *, client: httpx.AsyncClient | None = None):
        if not model or ":" not in model or any(char in model for char in "/\\ \t\n") or model.endswith("-cloud"):
            raise ValueError("Use a server-configured local model tag.")
        self.model = model
        self._client = client or httpx.AsyncClient(timeout=INFERENCE_DEADLINE, trust_env=False,
                                                 follow_redirects=False)
        self._owns_client = client is None
        self._busy = False

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _json(self, method: str, path: str, **kwargs) -> dict:
        async with self._client.stream(method, BASE_URL + path, **kwargs) as response:
            if response.status_code != 200:
                raise InferenceError("ai_unavailable")
            payload = bytearray()
            async for chunk in response.aiter_bytes(chunk_size=16 * 1024):
                if len(payload) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise InferenceError("invalid_ai_output")
                payload.extend(chunk)
        try:
            document = json.loads(payload)
        except (ValueError, UnicodeError):
            raise InferenceError("invalid_ai_output") from None
        if not isinstance(document, dict):
            raise InferenceError("invalid_ai_output")
        return document

    async def health(self) -> str:
        try:
            async with asyncio.timeout(2.0):
                tags = await self._json("GET", "/api/tags")
            return "ready" if any(isinstance(model, dict) and model.get("name") == self.model
                                  for model in tags.get("models", [])) else "unavailable"
        except (TimeoutError, httpx.HTTPError, InferenceError, TypeError):
            return "unavailable"

    async def expand(self, source_ids: list[str]) -> ModelCandidate:
        if self._busy:
            raise InferenceError("ai_busy")
        # No await between the check and assignment: callers never form a queue.
        self._busy = True
        try:
            async with asyncio.timeout(INFERENCE_DEADLINE):
                result = await self._json("POST", "/api/chat", json=chat_request(self.model, source_ids))
                if result.get("done") is not True:
                    raise InferenceError("invalid_ai_output")
                content = result.get("message", {}).get("content")
                if not isinstance(content, str):
                    raise InferenceError("invalid_ai_output")
                try:
                    candidate = ModelCandidate.model_validate_json(content)
                except ValidationError:
                    raise InferenceError("invalid_ai_output") from None
                if not validate_candidate(candidate, source_ids):
                    raise InferenceError("invalid_ai_output")
                return candidate
        except (TimeoutError, httpx.TimeoutException):
            raise InferenceError("ai_timeout") from None
        except httpx.HTTPError:
            raise InferenceError("ai_unavailable") from None
        except (AttributeError, TypeError):
            raise InferenceError("invalid_ai_output") from None
        finally:
            self._busy = False
