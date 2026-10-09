"""Health/expansion router for Lead-owned app assembly; suggestions stay absent."""

import logging
from time import perf_counter

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..ai.ollama import InferenceError, OllamaRuntime
from ..validation.contracts import ExpandRequest
from ..validation.grammar import permitted_renderings
from ..validation.vocabulary import Vocabulary
from .errors import error_response

logger = logging.getLogger(__name__)
MAX_BODY_BYTES = 16 * 1024
ALLOWED_ORIGINS = frozenset({"http://127.0.0.1:5173", "http://localhost:5173",
                             "http://127.0.0.1:8000", "http://localhost:8000"})


def boundary_error(request: Request) -> JSONResponse | None:
    host = request.url.hostname
    origin = request.headers.get("origin")
    if host not in {"localhost", "127.0.0.1"} or (origin is not None and origin not in ALLOWED_ORIGINS):
        return error_response("invalid_request")
    return None


def create_router(vocabulary: Vocabulary, runtime: OllamaRuntime) -> APIRouter:
    """One router/runtime per single-process app; the caller closes runtime at shutdown."""
    router = APIRouter(prefix="/api")

    @router.get("/health")
    async def health(request: Request):
        rejected = boundary_error(request)
        if rejected is not None:
            return rejected
        return {"status": "ok", "vocabulary_version": vocabulary.version,
                "ai": {"state": await runtime.health(), "suggestions_enabled": False}}

    @router.post("/expand")
    async def expand(request: Request):
        rejected = boundary_error(request)
        if rejected is not None:
            return rejected
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            return error_response("invalid_request")
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_BODY_BYTES:
                return error_response("request_too_large")
            body.extend(chunk)
        try:
            selection = ExpandRequest.model_validate_json(bytes(body))
        except ValidationError:
            return error_response("invalid_request")
        request_id = str(selection.request_id)
        if selection.vocabulary_version != vocabulary.version:
            return error_response("vocabulary_mismatch", request_id)
        if not all(card in vocabulary.card_ids for card in selection.selected_card_ids):
            return error_response("invalid_request", request_id)
        result = {"request_id": request_id, "revision": selection.revision,
                  "vocabulary_version": vocabulary.version,
                  "source_card_ids": selection.selected_card_ids, "status": "unsupported", "text": None}
        if not permitted_renderings(selection.selected_card_ids):
            return result
        started = perf_counter()
        outcome = "candidate"
        try:
            candidate = await runtime.expand(selection.selected_card_ids)
            result.update(status="candidate", text=candidate.text)
            return result
        except InferenceError as exc:
            outcome = exc.code
            return error_response(exc.code, request_id)
        finally:
            logger.info("request_id=%s outcome=%s duration_ms=%.1f", request_id, outcome,
                        (perf_counter() - started) * 1000)

    return router
